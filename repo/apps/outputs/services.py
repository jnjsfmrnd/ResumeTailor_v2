from __future__ import annotations

from time import perf_counter

from apps.common.metrics import record_latency
from apps.outputs.cover_letter_service import CoverLetterService
from apps.outputs.models import CoverLetterDraft, GeneratedArtifact
from apps.outputs.policies import ensure_export_allowed
from apps.outputs.resume_service import ResumePDFService
from apps.tailoring.models import TailoringRun


def generate_resume_artifact(*, tailoring_run_id: str) -> GeneratedArtifact:
    started = perf_counter()
    run = TailoringRun.objects.select_related(
        "job_target",
        "source_document",
    ).get(id=tailoring_run_id)
    ensure_export_allowed(run)

    service = ResumePDFService()
    artifact = service.generate(tailoring_run=run, approved_bullets=[])

    record_latency(
        "resume_export",
        perf_counter() - started,
        threshold_seconds=30,
    )
    return artifact


def generate_cover_letter_artifact(*, tailoring_run_id: str) -> CoverLetterDraft:
    started = perf_counter()
    run = TailoringRun.objects.select_related(
        "job_target",
        "source_document",
    ).get(id=tailoring_run_id)
    ensure_export_allowed(run)

    service = CoverLetterService()
    draft = service.generate(tailoring_run=run)

    record_latency(
        "cover_letter_generation",
        perf_counter() - started,
        threshold_seconds=90,
    )
    return draft
