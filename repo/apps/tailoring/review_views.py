from __future__ import annotations

import json
import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from apps.common.views import (
    get_or_create_workspace_session,
    get_workspace_tailoring_run_queryset,
    serialize_job_target,
    serialize_source_document,
    serialize_tailoring_run,
)
from apps.intake.models import JobTarget, SourceDocument
from apps.tailoring.draft_service import DraftOrchestrationError, DraftOrchestrationService
from apps.tailoring.models import TailoringRun

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared serialiser
# ---------------------------------------------------------------------------


def _serialize_run(run: TailoringRun) -> dict:
    return {
        "id": str(run.id),
        "status": run.status,
        "professionalSummary": run.professional_summary,
        "tailoredSkills": run.tailored_skills,
        "tailoredExperienceSections": run.tailored_experience_sections,
        "truthfulnessNotes": run.truthfulness_notes,
        "sourceDocumentId": str(run.source_document_id),
        "jobTargetId": str(run.job_target_id),
    }


# ---------------------------------------------------------------------------
# POST /api/tailorings  — start a tailoring run
# ---------------------------------------------------------------------------


@require_http_methods(["POST"])
def start_tailoring_run(request: HttpRequest) -> JsonResponse:
    workspace = get_or_create_workspace_session(request)

    try:
        data: dict = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    source_doc_id: str | None = data.get("sourceDocumentId")
    job_target_id: str | None = data.get("jobTargetId")

    if not source_doc_id:
        return JsonResponse({"error": "sourceDocumentId is required."}, status=400)
    if not job_target_id:
        return JsonResponse({"error": "jobTargetId is required."}, status=400)

    # Validate both objects belong to this workspace
    try:
        source_doc = SourceDocument.objects.get(
            id=source_doc_id, workspace_session=workspace
        )
    except (SourceDocument.DoesNotExist, ValueError):
        return JsonResponse(
            {"error": "Source document not found in this workspace."}, status=400
        )

    try:
        job_target = JobTarget.objects.get(
            id=job_target_id, workspace_session=workspace
        )
    except (JobTarget.DoesNotExist, ValueError):
        return JsonResponse(
            {"error": "Job target not found in this workspace."}, status=400
        )

    # Guard: document must be fully parsed
    if source_doc.parse_status != SourceDocument.ParseStatus.READY:
        return JsonResponse(
            {
                "error": (
                    f"Source document parse status is '{source_doc.parse_status}'. "
                    "Wait for parsing to complete before starting a tailoring run."
                )
            },
            status=400,
        )

    # Create the run
    run = TailoringRun.objects.create(
        workspace_session=workspace,
        source_document=source_doc,
        job_target=job_target,
        status=TailoringRun.Status.PENDING,
    )

    # Run draft orchestration synchronously for MVP
    svc = DraftOrchestrationService()
    try:
        svc.run(run)
    except DraftOrchestrationError as exc:
        logger.error("Tailoring run %s failed: %s", run.id, exc)
        run.refresh_from_db()
        # Return 202 with failed status so the caller can handle it gracefully
        return JsonResponse(_serialize_run(run), status=202)

    run.refresh_from_db()
    return JsonResponse(_serialize_run(run), status=202)


# ---------------------------------------------------------------------------
# GET /api/tailorings/{run_id}  — retrieve run detail
# ---------------------------------------------------------------------------


@require_GET
def get_tailoring_run(request: HttpRequest, run_id: str) -> JsonResponse:
    _, scoped_runs = get_workspace_tailoring_run_queryset(
        request,
        TailoringRun.objects.select_related("source_document", "job_target"),
    )
    try:
        run = scoped_runs.get(id=run_id)
    except (TailoringRun.DoesNotExist, ValueError):
        return JsonResponse({"error": "Tailoring run not found."}, status=404)
    return JsonResponse(_serialize_run(run))


@require_http_methods(["GET", "PATCH"])
def tailoring_run_detail(request: HttpRequest, run_id: str) -> JsonResponse:
    if request.method == "GET":
        return get_tailoring_run(request, run_id)
    return update_tailoring_run(request, run_id)


# ---------------------------------------------------------------------------
# PATCH /api/tailorings/{run_id}  — save manual edits
# ---------------------------------------------------------------------------


@require_http_methods(["PATCH"])
def update_tailoring_run(request: HttpRequest, run_id: str) -> JsonResponse:
    _, scoped_runs = get_workspace_tailoring_run_queryset(request)
    try:
        run = scoped_runs.get(id=run_id)
    except (TailoringRun.DoesNotExist, ValueError):
        return JsonResponse({"error": "Tailoring run not found."}, status=404)

    try:
        data: dict = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    update_fields: list[str] = []

    if "professionalSummary" in data:
        run.professional_summary = str(data["professionalSummary"])
        update_fields.append("professional_summary")

    if "tailoredSkills" in data:
        skills = data["tailoredSkills"]
        if not isinstance(skills, list):
            return JsonResponse({"error": "tailoredSkills must be a list."}, status=400)
        run.tailored_skills = skills
        update_fields.append("tailored_skills")

    if "tailoredExperienceSections" in data:
        sections = data["tailoredExperienceSections"]
        if not isinstance(sections, list):
            return JsonResponse(
                {"error": "tailoredExperienceSections must be a list."}, status=400
            )
        run.tailored_experience_sections = sections
        update_fields.append("tailored_experience_sections")

    if "truthfulnessNotes" in data:
        notes = data["truthfulnessNotes"]
        if not isinstance(notes, list):
            return JsonResponse(
                {"error": "truthfulnessNotes must be a list."}, status=400
            )
        run.truthfulness_notes = notes
        update_fields.append("truthfulness_notes")

    if update_fields:
        update_fields.append("updated_at")
        run.save(update_fields=update_fields)

    return JsonResponse(_serialize_run(run))


# ---------------------------------------------------------------------------
# GET /tailoring/{run_id}/review  — review page (HTML)
# ---------------------------------------------------------------------------


def review_page(request: HttpRequest, run_id: str) -> HttpResponse:
    workspace, scoped_runs = get_workspace_tailoring_run_queryset(
        request,
        TailoringRun.objects.select_related(
            "source_document",
            "job_target",
            "workspace_session",
        ),
    )
    try:
        run = scoped_runs.get(id=run_id)
    except (TailoringRun.DoesNotExist, ValueError) as exc:
        from django.http import Http404

        raise Http404("Tailoring run not found.") from exc

    # Sync the request session's workspace reference for badge rendering
    request.session["workspace_id"] = str(workspace.id)

    workspace_state = {
        "sessionId": str(workspace.id),
        "currentSourceDocument": serialize_source_document(workspace.current_source_document),
        "currentJobTarget": serialize_job_target(workspace.current_job_target),
        "latestTailoringRun": serialize_tailoring_run(workspace.tailoring_runs.first()),
    }

    return render(
        request,
        "tailoring/review.html",
        {
            "run": run,
            "workspace": workspace,
            "workspace_state": workspace_state,
        },
    )
