from __future__ import annotations

import json
from io import BytesIO

from django.core.exceptions import ValidationError
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from apps.intake.repositories import get_storage_backend
from apps.outputs.models import GeneratedArtifact
from apps.outputs.services import generate_cover_letter_artifact, generate_resume_artifact
from apps.tailoring.models import TailoringRun


@csrf_exempt
@require_http_methods(["POST"])
def create_resume_artifact(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    tailoring_run_id = payload.get("tailoringRunId")
    if not tailoring_run_id:
        return JsonResponse({"error": "tailoringRunId is required."}, status=400)

    try:
        artifact = generate_resume_artifact(tailoring_run_id=tailoring_run_id)
    except TailoringRun.DoesNotExist:
        return JsonResponse({"error": "Tailoring run not found."}, status=404)
    except ValidationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "id": str(artifact.id),
            "artifactType": artifact.artifact_type,
            "downloadUrl": f"/api/artifacts/{artifact.id}/download",
        },
        status=201,
    )


@csrf_exempt
@require_http_methods(["POST"])
def create_cover_letter_artifact(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    tailoring_run_id = payload.get("tailoringRunId")
    if not tailoring_run_id:
        return JsonResponse({"error": "tailoringRunId is required."}, status=400)

    try:
        draft = generate_cover_letter_artifact(tailoring_run_id=tailoring_run_id)
    except TailoringRun.DoesNotExist:
        return JsonResponse({"error": "Tailoring run not found."}, status=404)
    except ValidationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    latest_artifact = GeneratedArtifact.objects.filter(
        tailoring_run=draft.tailoring_run,
        artifact_type=GeneratedArtifact.ArtifactType.COVER_LETTER_FILE,
    ).first()

    response_payload = {
        "id": str(draft.id),
        "status": draft.status,
        "bodyMarkdown": draft.body_markdown,
    }
    if latest_artifact:
        response_payload["downloadUrl"] = f"/api/artifacts/{latest_artifact.id}/download"

    return JsonResponse(response_payload, status=201)


@require_GET
def download_artifact(request, artifact_id: str):
    try:
        artifact = GeneratedArtifact.objects.get(id=artifact_id)
    except (GeneratedArtifact.DoesNotExist, ValueError):
        return JsonResponse({"error": "Artifact not found."}, status=404)

    storage = get_storage_backend()
    content = storage.open_bytes(artifact.blob_path)

    if artifact.artifact_type == GeneratedArtifact.ArtifactType.RESUME_PDF:
        content_type = "application/pdf"
        filename = "tailored-resume.pdf"
    else:
        content_type = "text/markdown"
        filename = "cover-letter.md"

    return FileResponse(
        BytesIO(content),
        as_attachment=True,
        filename=filename,
        content_type=content_type,
    )
