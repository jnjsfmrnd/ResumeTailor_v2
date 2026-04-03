from __future__ import annotations

import json
import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from apps.common.views import get_or_create_workspace_session
from apps.intake.forms import ResumeUploadForm
from apps.intake.models import JobTarget
from apps.intake.repositories import SourceDocumentRepository
from apps.intake.services import ResumeParsingService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Upload page (HTML)
# ---------------------------------------------------------------------------


@require_GET
def upload_page(request: HttpRequest) -> HttpResponse:
    workspace = get_or_create_workspace_session(request)
    return render(request, "intake/upload.html", {"workspace": workspace})


# ---------------------------------------------------------------------------
# POST /api/uploads  — resume upload JSON endpoint
# ---------------------------------------------------------------------------


@csrf_exempt
@require_http_methods(["POST"])
def upload_resume(request: HttpRequest) -> JsonResponse:
    workspace = get_or_create_workspace_session(request)
    form = ResumeUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    uploaded_file = form.cleaned_data["file"]
    content: bytes = uploaded_file.read()

    repo = SourceDocumentRepository()
    try:
        stored = repo.create_uploaded_document(
            workspace_session=workspace,
            filename=uploaded_file.name,
            content_type=uploaded_file.content_type,
            content=content,
        )
    except Exception as exc:
        logger.error("Failed to store uploaded document: %s", exc)
        return JsonResponse({"error": "Failed to store uploaded document."}, status=500)

    # Parse synchronously for MVP — errors downgrade parse_status but don't
    # fail the upload response.
    try:
        parsing_service = ResumeParsingService(repository=repo)
        parsing_service.parse_source_document(stored.document)
    except Exception as exc:
        logger.warning("Parsing failed for document %s: %s", stored.document.id, exc)

    stored.document.refresh_from_db()
    doc = stored.document

    return JsonResponse(
        {
            "id": str(doc.id),
            "originalFilename": doc.original_filename,
            "parseStatus": doc.parse_status,
            "isCurrent": doc.is_current,
        },
        status=201,
    )


# ---------------------------------------------------------------------------
# Job target page (HTML)
# ---------------------------------------------------------------------------


@require_GET
def job_target_page(request: HttpRequest) -> HttpResponse:
    workspace = get_or_create_workspace_session(request)
    return render(request, "intake/job_target.html", {"workspace": workspace})


# ---------------------------------------------------------------------------
# POST /api/job-targets  — job description JSON endpoint
# ---------------------------------------------------------------------------


@csrf_exempt
@require_http_methods(["POST"])
def create_job_target(request: HttpRequest) -> JsonResponse:
    workspace = get_or_create_workspace_session(request)

    try:
        data: dict = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    description_text: str = data.get("descriptionText", "").strip()
    if not description_text:
        return JsonResponse(
            {"error": "descriptionText is required and cannot be blank."}, status=400
        )

    job_target = JobTarget.objects.create(
        workspace_session=workspace,
        company_name=data.get("companyName", ""),
        role_title=data.get("roleTitle", ""),
        description_text=description_text,
    )
    workspace.current_job_target = job_target
    workspace.save(update_fields=["current_job_target", "updated_at"])

    return JsonResponse(
        {
            "id": str(job_target.id),
            "companyName": job_target.company_name,
            "roleTitle": job_target.role_title,
            "descriptionText": job_target.description_text,
            "topKeywords": job_target.top_keywords,
        },
        status=201,
    )
