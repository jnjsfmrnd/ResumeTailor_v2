from __future__ import annotations

import json

import pytest
from django.test import Client

from apps.outputs.models import CoverLetterDraft


@pytest.mark.django_db
class TestArtifactGenerationFlow:
    def _seed_reviewable_run(self, client: Client):
        from apps.common.models import WorkspaceSession
        from apps.intake.models import JobTarget, SourceDocument
        from apps.tailoring.models import TailoringRun

        client.get("/api/workspace/current")
        workspace = WorkspaceSession.objects.get(session_key=client.session.session_key)
        source_document = SourceDocument.objects.create(
            workspace_session=workspace,
            original_filename="resume.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="uploads/mock/resume.pdf",
            sha256="sha",
            extracted_text="Resume facts",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        job_target = JobTarget.objects.create(
            workspace_session=workspace,
            description_text="Role description",
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

    def test_resume_and_cover_letter_generate_separately(self, monkeypatch):
        client = Client()
        run = self._seed_reviewable_run(client)

        def _fake_cover_letter(*, tailoring_run):
            return CoverLetterDraft.objects.create(
                tailoring_run=tailoring_run,
                job_target_id=run.job_target_id,
                status=CoverLetterDraft.Status.READY,
                body_markdown="Generated cover letter",
            )

        monkeypatch.setattr(
            "apps.outputs.views.generate_cover_letter_artifact",
            _fake_cover_letter,
        )

        resume_response = client.post(
            "/api/artifacts/resume",
            data=json.dumps({"tailoringRunId": str(run.id)}),
            content_type="application/json",
        )
        cover_response = client.post(
            "/api/artifacts/cover-letter",
            data=json.dumps({"tailoringRunId": str(run.id)}),
            content_type="application/json",
        )

        assert resume_response.status_code == 201
        assert cover_response.status_code == 201
        assert resume_response.json()["artifactType"] == "resume_pdf"
        assert cover_response.json()["status"] == "ready"

    def test_resume_export_records_30s_threshold_metric(self, monkeypatch):
        client = Client()
        run = self._seed_reviewable_run(client)
        captured = {}

        def _capture(name, elapsed_seconds, *, threshold_seconds=None):
            captured["name"] = name
            captured["threshold"] = threshold_seconds

        monkeypatch.setattr("apps.outputs.services.record_latency", _capture)

        response = client.post(
            "/api/artifacts/resume",
            data=json.dumps({"tailoringRunId": str(run.id)}),
            content_type="application/json",
        )

        assert response.status_code == 201
        assert captured["name"] == "resume_export"
        assert captured["threshold"] == 30

    def test_cover_letter_generation_records_90s_threshold_metric(self, monkeypatch):
        client = Client()
        run = self._seed_reviewable_run(client)
        captured = {}

        def _fake_cover_letter(*, tailoring_run):
            return CoverLetterDraft.objects.create(
                tailoring_run=tailoring_run,
                job_target_id=run.job_target_id,
                status=CoverLetterDraft.Status.READY,
                body_markdown="Generated cover letter",
            )

        def _capture(name, elapsed_seconds, *, threshold_seconds=None):
            captured["name"] = name
            captured["threshold"] = threshold_seconds

        monkeypatch.setattr("apps.outputs.services.record_latency", _capture)
        monkeypatch.setattr(
            "apps.outputs.services.CoverLetterService.generate",
            lambda self, *, tailoring_run: _fake_cover_letter(tailoring_run=tailoring_run),
        )

        response = client.post(
            "/api/artifacts/cover-letter",
            data=json.dumps({"tailoringRunId": str(run.id)}),
            content_type="application/json",
        )

        assert response.status_code == 201
        assert captured["name"] == "cover_letter_generation"
        assert captured["threshold"] == 90

    def test_non_reviewable_run_is_rejected(self):
        from apps.common.models import WorkspaceSession
        from apps.intake.models import JobTarget, SourceDocument
        from apps.tailoring.models import TailoringRun

        client = Client()
        client.get("/api/workspace/current")
        workspace = WorkspaceSession.objects.get(session_key=client.session.session_key)
        source_document = SourceDocument.objects.create(
            workspace_session=workspace,
            original_filename="resume.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="uploads/mock/resume.pdf",
            sha256="sha",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        job_target = JobTarget.objects.create(
            workspace_session=workspace,
            description_text="Role description",
        )
        run = TailoringRun.objects.create(
            workspace_session=workspace,
            source_document=source_document,
            job_target=job_target,
            status=TailoringRun.Status.PROCESSING,
        )

        response = client.post(
            "/api/artifacts/resume",
            data=json.dumps({"tailoringRunId": str(run.id)}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_download_returns_404_for_artifact_from_another_workspace(self):
        owner_client = Client()
        run = self._seed_reviewable_run(owner_client)

        from apps.outputs.models import GeneratedArtifact

        artifact = GeneratedArtifact.objects.create(
            tailoring_run=run,
            artifact_type=GeneratedArtifact.ArtifactType.RESUME_PDF,
            blob_path="artifacts/resume.pdf",
            content_hash="h2",
        )

        other_client = Client()
        response = other_client.get(f"/api/artifacts/{artifact.id}/download")

        assert response.status_code == 404
