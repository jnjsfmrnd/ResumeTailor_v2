from __future__ import annotations

from datetime import timedelta

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.common.models import WorkspaceSession


def get_or_create_workspace_session(request: HttpRequest) -> WorkspaceSession:
    if not request.session.session_key:
        request.session.save()

    workspace, created = WorkspaceSession.objects.get_or_create(
        session_key=request.session.session_key,
        defaults={"expires_at": timezone.now() + timedelta(days=7)},
    )
    if not created and workspace.is_expired:
        workspace.bump_expiry()
        workspace.save(update_fields=["expires_at", "updated_at"])
    return workspace


def get_workspace_tailoring_run_queryset(request: HttpRequest, queryset=None):
    workspace = get_or_create_workspace_session(request)
    if queryset is None:
        from apps.tailoring.models import TailoringRun

        queryset = TailoringRun.objects.all()
    return workspace, queryset.filter(workspace_session=workspace)


def serialize_source_document(document) -> dict | None:
    if not document:
        return None
    return {
        "id": str(document.id),
        "originalFilename": document.original_filename,
        "parseStatus": document.parse_status,
        "isCurrent": document.is_current,
    }


def serialize_job_target(job_target) -> dict | None:
    if not job_target:
        return None
    return {
        "id": str(job_target.id),
        "companyName": job_target.company_name,
        "roleTitle": job_target.role_title,
        "descriptionText": job_target.description_text,
        "topKeywords": job_target.top_keywords,
    }


def serialize_tailoring_run(tailoring_run) -> dict | None:
    if not tailoring_run:
        return None
    return {
        "id": str(tailoring_run.id),
        "status": tailoring_run.status,
    }


def home(request: HttpRequest) -> HttpResponse:
    workspace = get_or_create_workspace_session(request)
    context = {
        "workspace": workspace,
        "workspace_state": {
            "sessionId": str(workspace.id),
            "currentSourceDocument": serialize_source_document(workspace.current_source_document),
            "currentJobTarget": serialize_job_target(workspace.current_job_target),
            "latestTailoringRun": serialize_tailoring_run(workspace.tailoring_runs.first()),
        },
    }
    return render(request, "base.html", context)


@require_GET
def current_workspace(request: HttpRequest) -> JsonResponse:
    workspace = get_or_create_workspace_session(request)
    payload = {
        "sessionId": str(workspace.id),
        "currentSourceDocument": serialize_source_document(workspace.current_source_document),
        "currentJobTarget": serialize_job_target(workspace.current_job_target),
        "latestTailoringRun": serialize_tailoring_run(workspace.tailoring_runs.first()),
    }
    return JsonResponse(payload)


def bad_request(request: HttpRequest, exception: Exception) -> HttpResponse:
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Bad request."}, status=400)
    return render(request, "base.html", status=400)


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Not found."}, status=404)
    return render(request, "base.html", status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Server error."}, status=500)
    return render(request, "base.html", status=500)