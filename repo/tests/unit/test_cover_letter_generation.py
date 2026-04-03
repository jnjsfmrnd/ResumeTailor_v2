from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from apps.outputs.models import CoverLetterDraft


@pytest.mark.django_db
class TestCoverLetterService:
    def _make_reviewable_run(self):
        from apps.common.models import WorkspaceSession
        from apps.intake.models import JobTarget, SourceDocument
        from apps.tailoring.models import TailoringRun

        workspace = WorkspaceSession.objects.create(session_key="unit-cover-letter")
        source_document = SourceDocument.objects.create(
            workspace_session=workspace,
            original_filename="resume.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="uploads/mock/resume.pdf",
            sha256="def456",
            extracted_text="Built APIs and backend systems.",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        job_target = JobTarget.objects.create(
            workspace_session=workspace,
            company_name="Example Co",
            role_title="Software Engineer",
            description_text="Seeking Python engineer with API experience.",
        )
        return TailoringRun.objects.create(
            workspace_session=workspace,
            source_document=source_document,
            job_target=job_target,
            status=TailoringRun.Status.REVIEWABLE,
            professional_summary="Engineer with practical backend delivery experience.",
            tailored_skills=["Python", "APIs"],
            tailored_experience_sections=[],
        )

    def test_cover_letter_generation_creates_ready_draft(self):
        from apps.outputs.cover_letter_service import CoverLetterService

        run = self._make_reviewable_run()
        ai_client = MagicMock()
        ai_client.complete.return_value = MagicMock(
            content="Dear Hiring Team,\n\nI am excited to apply...",
            model="test-model",
            request_id="req_1",
        )

        service = CoverLetterService(ai_client=ai_client)
        draft = service.generate(tailoring_run=run)

        assert draft.status == CoverLetterDraft.Status.READY
        assert "Dear Hiring Team" in draft.body_markdown
        assert draft.tailoring_run_id == run.id

    def test_cover_letter_generation_marks_failed_on_client_error(self):
        from apps.outputs.cover_letter_service import CoverLetterService

        run = self._make_reviewable_run()
        ai_client = MagicMock()
        ai_client.complete.side_effect = RuntimeError("model unavailable")

        service = CoverLetterService(ai_client=ai_client)

        with pytest.raises(RuntimeError):
            service.generate(tailoring_run=run)

        draft = CoverLetterDraft.objects.filter(tailoring_run=run).first()
        assert draft is not None
        assert draft.status == CoverLetterDraft.Status.FAILED

    def test_cover_letter_prompt_contains_resume_and_job_text(self):
        from apps.outputs.cover_letter_service import build_cover_letter_messages

        messages = build_cover_letter_messages(
            resume_text="Resume facts",
            job_description="Job details",
            professional_summary="Summary",
        )

        merged = "\n".join(message["content"] for message in messages)
        assert "Resume facts" in merged
        assert "Job details" in merged
