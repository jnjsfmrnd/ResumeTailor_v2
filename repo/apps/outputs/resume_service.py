from __future__ import annotations

import hashlib
from uuid import uuid4

from apps.intake.repositories import DurableStorageBackend, get_storage_backend
from apps.outputs.models import GeneratedArtifact
from apps.outputs.pdf_templates.resume import build_ats_safe_resume_pdf
from apps.tailoring.models import TailoringRun


class ResumePDFService:
    def __init__(self, storage_backend: DurableStorageBackend | None = None) -> None:
        self.storage_backend = storage_backend or get_storage_backend()

    def generate(
        self,
        *,
        tailoring_run: TailoringRun,
        approved_bullets: list[str],
    ) -> GeneratedArtifact:
        run_data = {
            "professional_summary": tailoring_run.professional_summary,
            "tailored_skills": tailoring_run.tailored_skills,
            "tailored_experience_sections": tailoring_run.tailored_experience_sections,
            "approved_bullets": approved_bullets,
        }
        pdf_bytes = build_ats_safe_resume_pdf(run_data)
        blob_path = f"artifacts/{tailoring_run.id}/resume-{uuid4()}.pdf"

        self.storage_backend.save_bytes(
            blob_path,
            pdf_bytes,
            content_type="application/pdf",
        )

        return GeneratedArtifact.objects.create(
            tailoring_run=tailoring_run,
            artifact_type=GeneratedArtifact.ArtifactType.RESUME_PDF,
            blob_path=blob_path,
            content_hash=hashlib.sha256(pdf_bytes).hexdigest(),
        )
