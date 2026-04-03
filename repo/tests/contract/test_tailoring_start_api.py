"""Contract tests for job target creation and tailoring start endpoints.

Validates API schema compliance for:
  POST /api/job-targets
  POST /api/tailorings
  GET  /api/tailorings/{id}
  PATCH /api/tailorings/{id}
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client

from apps.common.models import WorkspaceSession
from apps.intake.models import JobTarget, SourceDocument
from apps.tailoring.models import TailoringRun

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# POST /api/job-targets
# ---------------------------------------------------------------------------


class TestCreateJobTarget:
    def test_create_returns_201(self, client, db):
        payload = {
            "descriptionText": "We need a senior Python developer.",
            "companyName": "Acme Corp",
            "roleTitle": "Senior Python Developer",
        }
        response = client.post(
            "/api/job-targets",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201

    def test_create_response_schema(self, client, db):
        payload = {
            "descriptionText": "We need a senior Python developer.",
            "companyName": "Acme Corp",
            "roleTitle": "Senior Python Developer",
        }
        response = client.post(
            "/api/job-targets",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = response.json()
        assert "id" in data
        assert "companyName" in data
        assert "roleTitle" in data
        assert "descriptionText" in data
        assert "topKeywords" in data

    def test_create_stores_description_text(self, client, db):
        payload = {"descriptionText": "Django developer needed for fintech startup."}
        response = client.post(
            "/api/job-targets",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.json()["descriptionText"] == "Django developer needed for fintech startup."

    def test_create_optional_fields_default_to_empty(self, client, db):
        payload = {"descriptionText": "Some job description."}
        response = client.post(
            "/api/job-targets",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = response.json()
        assert data["companyName"] == ""
        assert data["roleTitle"] == ""

    def test_create_rejects_empty_description(self, client, db):
        payload = {"descriptionText": "  "}
        response = client.post(
            "/api/job-targets",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_rejects_missing_description(self, client, db):
        payload = {"companyName": "Acme"}
        response = client.post(
            "/api/job-targets",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_rejects_invalid_json(self, client, db):
        response = client.post(
            "/api/job-targets",
            data="not-json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_requires_post_method(self, client, db):
        response = client.get("/api/job-targets")
        assert response.status_code == 405

    def test_create_rejects_missing_csrf_token(self, db):
        client = Client(enforce_csrf_checks=True)
        payload = {"descriptionText": "We need a senior Python developer."}

        response = client.post(
            "/api/job-targets",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 403

    def test_create_sets_workspace_current_job_target(self, client, db):
        payload = {"descriptionText": "Python developer."}
        client.post(
            "/api/job-targets",
            data=json.dumps(payload),
            content_type="application/json",
        )
        # A workspace session should have been created and linked
        assert WorkspaceSession.objects.filter(
            current_job_target__isnull=False
        ).exists()


# ---------------------------------------------------------------------------
# POST /api/tailorings
# ---------------------------------------------------------------------------


class TestStartTailoringRun:
    @pytest.fixture
    def prepared_workspace(self, client, db, tmp_path, settings):
        """Set up a workspace with a ready source document and job target."""
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        # Create workspace session tied to client session
        client.get("/api/workspace/current")

        session_key = client.session.session_key
        ws = WorkspaceSession.objects.get(session_key=session_key)

        doc = SourceDocument.objects.create(
            workspace_session=ws,
            original_filename="resume.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="test/resume.pdf",
            sha256="b" * 64,
            extracted_text=(
                "Python developer with 5 years of experience. "
                "Skilled in Django, REST APIs, PostgreSQL."
            ),
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        ws.current_source_document = doc
        ws.save(update_fields=["current_source_document", "updated_at"])

        target = JobTarget.objects.create(
            workspace_session=ws,
            company_name="Acme",
            role_title="Senior Python Dev",
            description_text="Need Django developer with REST API experience.",
        )
        ws.current_job_target = target
        ws.save(update_fields=["current_job_target", "updated_at"])

        return ws, doc, target

    def _mock_ai_result(self):
        return json.dumps(
            {
                "professional_summary": "Experienced Python developer skilled in Django.",
                "tailored_skills": ["Python", "Django", "REST APIs"],
                "tailored_experience_sections": [
                    {
                        "employer": "Previous Co",
                        "role": "Developer",
                        "bullets": ["Built REST APIs with Django."],
                    }
                ],
                "truthfulness_notes": [],
            }
        )

    def test_start_returns_202(self, client, prepared_workspace):
        ws, doc, target = prepared_workspace
        payload = {
            "sourceDocumentId": str(doc.id),
            "jobTargetId": str(target.id),
        }
        with patch(
            "apps.ai.client.GitHubModelsClient.complete",
            return_value=MagicMock(content=self._mock_ai_result(), model="test", request_id=None),
        ):
            response = client.post(
                "/api/tailorings",
                data=json.dumps(payload),
                content_type="application/json",
            )
        assert response.status_code == 202

    def test_start_response_schema(self, client, prepared_workspace):
        ws, doc, target = prepared_workspace
        payload = {
            "sourceDocumentId": str(doc.id),
            "jobTargetId": str(target.id),
        }
        with patch(
            "apps.ai.client.GitHubModelsClient.complete",
            return_value=MagicMock(content=self._mock_ai_result(), model="test", request_id=None),
        ):
            response = client.post(
                "/api/tailorings",
                data=json.dumps(payload),
                content_type="application/json",
            )
        data = response.json()
        assert "id" in data
        assert "status" in data

    def test_start_creates_run_in_reviewable_status(self, client, prepared_workspace):
        ws, doc, target = prepared_workspace
        payload = {
            "sourceDocumentId": str(doc.id),
            "jobTargetId": str(target.id),
        }
        with patch(
            "apps.ai.client.GitHubModelsClient.complete",
            return_value=MagicMock(content=self._mock_ai_result(), model="test", request_id=None),
        ):
            response = client.post(
                "/api/tailorings",
                data=json.dumps(payload),
                content_type="application/json",
            )
        assert response.json()["status"] == TailoringRun.Status.REVIEWABLE

    def test_start_rejects_missing_source_document_id(self, client, prepared_workspace):
        ws, doc, target = prepared_workspace
        payload = {"jobTargetId": str(target.id)}
        response = client.post(
            "/api/tailorings",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_start_rejects_missing_job_target_id(self, client, prepared_workspace):
        ws, doc, target = prepared_workspace
        payload = {"sourceDocumentId": str(doc.id)}
        response = client.post(
            "/api/tailorings",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_start_rejects_unparsed_source_document(self, client, prepared_workspace):
        ws, doc, target = prepared_workspace
        doc.parse_status = SourceDocument.ParseStatus.UPLOADED
        doc.save(update_fields=["parse_status"])
        payload = {
            "sourceDocumentId": str(doc.id),
            "jobTargetId": str(target.id),
        }
        response = client.post(
            "/api/tailorings",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_start_rejects_nonexistent_source_document(self, client, prepared_workspace):
        ws, doc, target = prepared_workspace
        payload = {
            "sourceDocumentId": str(uuid.uuid4()),
            "jobTargetId": str(target.id),
        }
        response = client.post(
            "/api/tailorings",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code in (400, 404)


# ---------------------------------------------------------------------------
# GET /api/tailorings/{id}
# ---------------------------------------------------------------------------


class TestGetTailoringRun:
    @pytest.fixture
    def reviewable_run(self, client, db):
        """Return a reviewable TailoringRun."""
        client.get("/api/workspace/current")
        ws = WorkspaceSession.objects.get(session_key=client.session.session_key)
        doc = SourceDocument.objects.create(
            workspace_session=ws,
            original_filename="r.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="t/r.pdf",
            sha256="c" * 64,
            extracted_text="Python developer.",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        target = JobTarget.objects.create(
            workspace_session=ws,
            description_text="Need Python devs.",
        )
        run = TailoringRun.objects.create(
            workspace_session=ws,
            source_document=doc,
            job_target=target,
            status=TailoringRun.Status.REVIEWABLE,
            professional_summary="Experienced Python developer.",
            tailored_skills=["Python", "Django"],
            tailored_experience_sections=[],
            truthfulness_notes=[],
        )
        return run

    def test_get_returns_200(self, client, reviewable_run):
        response = client.get(f"/api/tailorings/{reviewable_run.id}")
        assert response.status_code == 200

    def test_get_response_schema(self, client, reviewable_run):
        response = client.get(f"/api/tailorings/{reviewable_run.id}")
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "professionalSummary" in data
        assert "tailoredSkills" in data
        assert "tailoredExperienceSections" in data
        assert "truthfulnessNotes" in data

    def test_get_returns_404_for_nonexistent_run(self, client, db):
        response = client.get(f"/api/tailorings/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_get_returns_404_for_run_from_another_workspace(self, db, reviewable_run):
        other_client = pytest.importorskip("django.test").Client()

        response = other_client.get(f"/api/tailorings/{reviewable_run.id}")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/tailorings/{id}
# ---------------------------------------------------------------------------


class TestUpdateTailoringRun:
    @pytest.fixture
    def reviewable_run(self, client, db):
        client.get("/api/workspace/current")
        ws = WorkspaceSession.objects.get(session_key=client.session.session_key)
        doc = SourceDocument.objects.create(
            workspace_session=ws,
            original_filename="r.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="t/r.pdf",
            sha256="d" * 64,
            extracted_text="Python developer.",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        target = JobTarget.objects.create(
            workspace_session=ws,
            description_text="Need Python devs.",
        )
        return TailoringRun.objects.create(
            workspace_session=ws,
            source_document=doc,
            job_target=target,
            status=TailoringRun.Status.REVIEWABLE,
            professional_summary="Original summary.",
            tailored_skills=["Python"],
            tailored_experience_sections=[],
            truthfulness_notes=[],
        )

    def test_patch_returns_200(self, client, reviewable_run):
        payload = {"professionalSummary": "Updated summary."}
        response = client.patch(
            f"/api/tailorings/{reviewable_run.id}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_patch_updates_summary(self, client, reviewable_run):
        payload = {"professionalSummary": "My edited summary here."}
        response = client.patch(
            f"/api/tailorings/{reviewable_run.id}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = response.json()
        assert data["professionalSummary"] == "My edited summary here."

    def test_patch_updates_skills(self, client, reviewable_run):
        payload = {"tailoredSkills": ["Python", "Django", "PostgreSQL"]}
        response = client.patch(
            f"/api/tailorings/{reviewable_run.id}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.json()["tailoredSkills"] == ["Python", "Django", "PostgreSQL"]

    def test_patch_returns_404_for_nonexistent_run(self, client, db):
        payload = {"professionalSummary": "New summary."}
        response = client.patch(
            f"/api/tailorings/{uuid.uuid4()}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_patch_returns_404_for_run_from_another_workspace(self, db, reviewable_run):
        payload = {"professionalSummary": "Cross-session edit."}
        other_client = pytest.importorskip("django.test").Client()

        response = other_client.patch(
            f"/api/tailorings/{reviewable_run.id}",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_patch_rejects_invalid_json(self, client, reviewable_run):
        response = client.patch(
            f"/api/tailorings/{reviewable_run.id}",
            data="invalid",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_patch_rejects_missing_csrf_token(self, db, reviewable_run):
        client = Client(enforce_csrf_checks=True)
        token = "a" * 32
        client.cookies["csrftoken"] = token

        response = client.patch(
            f"/api/tailorings/{reviewable_run.id}",
            data=json.dumps({"professionalSummary": "Blocked."}),
            content_type="application/json",
        )

        assert response.status_code == 403
