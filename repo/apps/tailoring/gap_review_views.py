from __future__ import annotations

import json
from time import perf_counter

from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from apps.common.metrics import record_latency
from apps.tailoring.gap_service import (
    GapServiceError,
    apply_review_updates,
    refresh_gap_intelligence,
    serialize_gap_review,
)
from apps.tailoring.models import TailoringRun


@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def gap_review_detail(request: HttpRequest, run_id: str) -> JsonResponse:
    run = get_object_or_404(
        TailoringRun.objects.select_related("job_target", "source_document"),
        id=run_id,
    )

    if request.method == "GET":
        return JsonResponse(serialize_gap_review(run))

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    project_recommendations = payload.get("projectRecommendations", [])
    try:
        apply_review_updates(run, project_recommendations)
    except GapServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    run.refresh_from_db()
    return JsonResponse(serialize_gap_review(run))


@csrf_exempt
@require_http_methods(["POST"])
def refresh_gap_review(request: HttpRequest, run_id: str) -> JsonResponse:
    qs = TailoringRun.objects.select_related("job_target", "source_document")
    run = get_object_or_404(qs, id=run_id)

    started = perf_counter()
    try:
        refresh_gap_intelligence(run)
    except GapServiceError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        return JsonResponse({"error": "Failed to refresh gap analysis."}, status=502)
    finally:
        elapsed = perf_counter() - started
        record_latency("gap_review_refresh", elapsed, threshold_seconds=2.0)

    run.refresh_from_db()
    return JsonResponse(serialize_gap_review(run))


@require_GET
def review_gap_panel(request: HttpRequest, run_id: str) -> HttpResponse:
    try:
        run = TailoringRun.objects.select_related(
            "workspace_session",
            "job_target",
            "source_document",
        ).prefetch_related("project_recommendations__bullets").get(id=run_id)
    except TailoringRun.DoesNotExist as exc:
        raise Http404("Tailoring run not found.") from exc

    payload = serialize_gap_review(run)
    return render(
        request,
        "tailoring/partials/review_gap_panel.html",
        {
            "run": run,
            "gap_payload": payload,
        },
    )
