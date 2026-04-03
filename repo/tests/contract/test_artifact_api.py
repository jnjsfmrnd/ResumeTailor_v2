from __future__ import annotations

import json

import pytest
from django.test import Client


@pytest.mark.django_db
class TestArtifactAPI:
    def _seed_reviewable_run(self):
        from apps.common.models import WorkspaceSession
        from apps.intake.models import JobTarget, SourceDocument
        from apps.tailoring.models import TailoringRun

        workspace = WorkspaceSession.objects.create(session_key="contract-artifact")
        source_document = SourceDocument.objects.create(
            workspace_session=workspace,
            original_filename="resume.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="uploads/mock/resume.pdf",
            sha256="abc",
            extracted_text="Resume text",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        job_target = JobTarget.objects.create(
            workspace_session=workspace,
            description_text="Need Python engineer",
        )
        return TailoringRun.objects.create(
            workspace_session=workspace,
            source_document=source_document,
            job_target=job_target,
            status=TailoringRun.Status.REVIEWABLE,
            professional_summary="Summary",
            tailored_skills=["Python"],
            tailored_experience_sections=[],
        )

    def test_post_resume_artifact_returns_201_and_schema(self, monkeypatch):
        run = self._seed_reviewable_run()
        client = Client()

        from apps.outputs.models import GeneratedArtifact

        def _fake_resume(*, tailoring_run_id):
            return GeneratedArtifact.objects.create(
                tailoring_run_id=tailoring_run_id,
                artifact_type=GeneratedArtifact.ArtifactType.RESUME_PDF,
                blob_path="artifacts/resume.pdf",
                content_hash="h1",
            )

        monkeypatch.setattr(
            "apps.outputs.views.generate_resume_artifact",
            _fake_resume,
        )

        response = client.post(
            "/api/artifacts/resume",
            data=json.dumps({"tailoringRunId": str(run.id)}),
            content_type="application/json",
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["artifactType"] == "resume_pdf"
        assert "id" in payload
        assert "downloadUrl" in payload

    def test_post_cover_letter_returns_201_and_schema(self, monkeypatch):
        run = self._seed_reviewable_run()
        client = Client()

        from apps.outputs.models import CoverLetterDraft

        def _fake_cover_letter(*, tailoring_run_id):
            return CoverLetterDraft.objects.create(
                tailoring_run_id=tailoring_run_id,
                job_target_id=run.job_target_id,
                status=CoverLetterDraft.Status.READY,
                body_markdown="Cover letter body",
            )

        monkeypatch.setattr(
            "apps.outputs.views.generate_cover_letter_artifact",
            _fake_cover_letter,
        )

        response = client.post(
            "/api/artifacts/cover-letter",
            data=json.dumps({"tailoringRunId": str(run.id)}),
            content_type="application/json",
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["bodyMarkdown"] == "Cover letter body"
        assert "id" in payload
