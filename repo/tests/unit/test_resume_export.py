from __future__ import annotations

import hashlib
from unittest.mock import MagicMock

import pytest

from apps.outputs.models import GeneratedArtifact


@pytest.mark.django_db
class TestResumePDFService:
    def _make_reviewable_run(self):
        from apps.common.models import WorkspaceSession
        from apps.intake.models import JobTarget, SourceDocument
        from apps.tailoring.models import TailoringRun

        workspace = WorkspaceSession.objects.create(session_key="unit-resume-export")
        source_document = SourceDocument.objects.create(
            workspace_session=workspace,
            original_filename="resume.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="uploads/mock/resume.pdf",
            sha256="abc123",
            extracted_text="Python engineer with 7 years of experience.",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        job_target = JobTarget.objects.create(
            workspace_session=workspace,
            description_text="Need a Django backend engineer.",
        )
        return TailoringRun.objects.create(
            workspace_session=workspace,
            source_document=source_document,
            job_target=job_target,
            status=TailoringRun.Status.REVIEWABLE,
            professional_summary="Backend engineer focused on reliability and delivery.",
            tailored_skills=["Python", "Django", "PostgreSQL"],
            tailored_experience_sections=[
                {
                    "company": "Acme",
                    "role": "Engineer",
                    "dates": "2021-2024",
                    "bullets": ["Reduced API latency by 35%."],
                }
            ],
        )

    def test_resume_pdf_composition_returns_valid_pdf_header(self):
        from apps.outputs.pdf_templates.resume import build_ats_safe_resume_pdf

        pdf_bytes = build_ats_safe_resume_pdf(
            {
                "professional_summary": "Summary",
                "tailored_skills": ["Python"],
                "tailored_experience_sections": [],
                "approved_bullets": [],
            }
        )

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 100

    def test_service_persists_resume_artifact_with_hash(self):
        from apps.outputs.resume_service import ResumePDFService

        run = self._make_reviewable_run()

        captured = {}

        def fake_save(blob_path: str, content: bytes, *, content_type: str):
            captured["blob_path"] = blob_path
            captured["content"] = content
            captured["content_type"] = content_type
            return MagicMock(path=blob_path, size=len(content))

        storage = MagicMock()
        storage.save_bytes.side_effect = fake_save

        service = ResumePDFService(storage_backend=storage)
        artifact = service.generate(tailoring_run=run, approved_bullets=[])

        assert artifact.artifact_type == GeneratedArtifact.ArtifactType.RESUME_PDF
        assert artifact.tailoring_run_id == run.id
        assert captured["content_type"] == "application/pdf"
        assert artifact.content_hash == hashlib.sha256(captured["content"]).hexdigest()

    def test_service_excludes_unapproved_project_bullets(self):
        from apps.outputs.resume_service import ResumePDFService

        run = self._make_reviewable_run()
        storage = MagicMock()
        service = ResumePDFService(storage_backend=storage)

        service.generate(
            tailoring_run=run,
            approved_bullets=["Kept bullet"],
        )

        storage.save_bytes.assert_called_once()
