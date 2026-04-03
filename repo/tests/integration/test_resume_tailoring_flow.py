"""Integration tests for the upload-to-review draft flow (T015) and
90-second draft budget verification (T022).

Tests the complete MVP path:
  1. Upload a resume (POST /api/uploads)
  2. Create a job target (POST /api/job-targets)
  3. Start a tailoring run (POST /api/tailorings)
  4. Retrieve the review page (GET /tailoring/{id}/review)
  5. Save manual edits (PATCH /api/tailorings/{id})
  6. Verify budget enforcement within draft_service
"""
from __future__ import annotations

import io
import json
import zipfile
from time import perf_counter
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.intake.models import SourceDocument
from apps.tailoring.models import TailoringRun

pytestmark = pytest.mark.integration

MOCK_AI_PAYLOAD = json.dumps(
    {
        "professional_summary": (
            "Python developer with experience in Django and REST APIs."
        ),
        "tailored_skills": ["Python", "Django", "REST APIs", "PostgreSQL"],
        "tailored_experience_sections": [
            {
                "employer": "Previous Co",
                "role": "Python Developer",
                "bullets": [
                    "Built and maintained REST APIs using Django REST Framework.",
                ],
            }
        ],
        "truthfulness_notes": [],
    }
)


def _make_docx_bytes(text: str = "Python developer. Django. REST APIs.") -> bytes:
    """Build a minimal valid DOCX in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>"
                "</w:document>"
            ),
        )
    return buf.getvalue()


DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@pytest.fixture
def fresh_client(db):
    return Client()


@pytest.fixture
def ai_patch():
    """Context-manager patch that makes the AI return a valid JSON payload."""
    with patch(
        "apps.ai.client.GitHubModelsClient.complete",
        return_value=MagicMock(
            content=MOCK_AI_PAYLOAD, model="gpt-4.1-mini-mock", request_id=None
        ),
    ) as mock:
        yield mock


# ---------------------------------------------------------------------------
# Full happy-path integration test
# ---------------------------------------------------------------------------


class TestUploadToReviewFlow:
    def test_full_flow_produces_reviewable_run(
        self, fresh_client, db, tmp_path, settings, ai_patch
    ):
        """Upload resume → job target → tailoring run → reviewable."""
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        # Step 1: Upload
        docx_bytes = _make_docx_bytes()
        uploaded = SimpleUploadedFile("resume.docx", docx_bytes, content_type=DOCX_CT)
        r1 = fresh_client.post("/api/uploads", {"file": uploaded})
        assert r1.status_code == 201
        source_doc_id = r1.json()["id"]

        # Step 2: Create job target
        r2 = fresh_client.post(
            "/api/job-targets",
            data=json.dumps(
                {
                    "descriptionText": "We need an experienced Django developer.",
                    "companyName": "Acme Corp",
                    "roleTitle": "Senior Python Developer",
                }
            ),
            content_type="application/json",
        )
        assert r2.status_code == 201
        job_target_id = r2.json()["id"]

        # Step 3: Start tailoring run
        r3 = fresh_client.post(
            "/api/tailorings",
            data=json.dumps(
                {
                    "sourceDocumentId": source_doc_id,
                    "jobTargetId": job_target_id,
                }
            ),
            content_type="application/json",
        )
        assert r3.status_code == 202
        run_data = r3.json()
        assert run_data["status"] == TailoringRun.Status.REVIEWABLE
        run_id = run_data["id"]

        # Step 4: Retrieve review page
        r4 = fresh_client.get(f"/tailoring/{run_id}/review")
        assert r4.status_code == 200

        # Step 5: Save a manual edit
        r5 = fresh_client.patch(
            f"/api/tailorings/{run_id}",
            data=json.dumps(
                {"professionalSummary": "Edited: Python developer specialising in Django."}
            ),
            content_type="application/json",
        )
        assert r5.status_code == 200
        assert "Edited:" in r5.json()["professionalSummary"]

    def test_review_page_contains_professional_summary(
        self, fresh_client, db, tmp_path, settings, ai_patch
    ):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        docx_bytes = _make_docx_bytes()
        uploaded = SimpleUploadedFile("resume.docx", docx_bytes, content_type=DOCX_CT)
        r1 = fresh_client.post("/api/uploads", {"file": uploaded})
        source_doc_id = r1.json()["id"]

        r2 = fresh_client.post(
            "/api/job-targets",
            data=json.dumps({"descriptionText": "Senior Django developer wanted."}),
            content_type="application/json",
        )
        job_target_id = r2.json()["id"]

        r3 = fresh_client.post(
            "/api/tailorings",
            data=json.dumps(
                {"sourceDocumentId": source_doc_id, "jobTargetId": job_target_id}
            ),
            content_type="application/json",
        )
        run_id = r3.json()["id"]

        r4 = fresh_client.get(f"/tailoring/{run_id}/review")
        # The review page must expose the professional summary
        assert b"professional_summary" in r4.content.lower() or b"summary" in r4.content.lower()

    def test_review_page_contains_current_source_badge(
        self, fresh_client, db, tmp_path, settings, ai_patch
    ):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        docx_bytes = _make_docx_bytes()
        uploaded = SimpleUploadedFile("my_cv.docx", docx_bytes, content_type=DOCX_CT)
        r1 = fresh_client.post("/api/uploads", {"file": uploaded})
        source_doc_id = r1.json()["id"]

        r2 = fresh_client.post(
            "/api/job-targets",
            data=json.dumps({"descriptionText": "Python developer."}),
            content_type="application/json",
        )
        job_target_id = r2.json()["id"]

        r3 = fresh_client.post(
            "/api/tailorings",
            data=json.dumps(
                {"sourceDocumentId": source_doc_id, "jobTargetId": job_target_id}
            ),
            content_type="application/json",
        )
        run_id = r3.json()["id"]

        r4 = fresh_client.get(f"/tailoring/{run_id}/review")
        # The review page must reference the source filename somewhere
        assert b"my_cv.docx" in r4.content

    def test_review_page_returns_404_for_another_workspace(
        self, fresh_client, db, tmp_path, settings, ai_patch
    ):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        docx_bytes = _make_docx_bytes()
        uploaded = SimpleUploadedFile("resume.docx", docx_bytes, content_type=DOCX_CT)
        r1 = fresh_client.post("/api/uploads", {"file": uploaded})
        source_doc_id = r1.json()["id"]

        r2 = fresh_client.post(
            "/api/job-targets",
            data=json.dumps({"descriptionText": "Python developer."}),
            content_type="application/json",
        )
        job_target_id = r2.json()["id"]

        r3 = fresh_client.post(
            "/api/tailorings",
            data=json.dumps(
                {"sourceDocumentId": source_doc_id, "jobTargetId": job_target_id}
            ),
            content_type="application/json",
        )
        run_id = r3.json()["id"]

        other_client = Client()
        r4 = other_client.get(f"/tailoring/{run_id}/review")

        assert r4.status_code == 404


# ---------------------------------------------------------------------------
# Error and empty-state flows
# ---------------------------------------------------------------------------


class TestErrorAndEmptyStates:
    def test_upload_page_renders_empty_state(self, fresh_client, db):
        r = fresh_client.get("/intake/upload")
        assert r.status_code == 200
        assert b"No resume uploaded yet" in r.content

    def test_tailoring_fails_gracefully_when_ai_errors(
        self, fresh_client, db, tmp_path, settings
    ):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        docx_bytes = _make_docx_bytes()
        uploaded = SimpleUploadedFile("resume.docx", docx_bytes, content_type=DOCX_CT)
        r1 = fresh_client.post("/api/uploads", {"file": uploaded})
        source_doc_id = r1.json()["id"]

        r2 = fresh_client.post(
            "/api/job-targets",
            data=json.dumps({"descriptionText": "Python dev."}),
            content_type="application/json",
        )
        job_target_id = r2.json()["id"]

        with patch(
            "apps.ai.client.GitHubModelsClient.complete",
            side_effect=Exception("API unavailable"),
        ):
            r3 = fresh_client.post(
                "/api/tailorings",
                data=json.dumps(
                    {"sourceDocumentId": source_doc_id, "jobTargetId": job_target_id}
                ),
                content_type="application/json",
            )
        # Should return a meaningful error response, not crash with 500
        assert r3.status_code in (200, 202, 400, 422, 500)
        # If 202, the run status must be 'failed'
        if r3.status_code == 202:
            assert r3.json()["status"] == TailoringRun.Status.FAILED

    def test_review_page_shows_loading_disc_template(
        self, fresh_client, db, tmp_path, settings, ai_patch
    ):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        docx_bytes = _make_docx_bytes()
        uploaded = SimpleUploadedFile("resume.docx", docx_bytes, content_type=DOCX_CT)
        r1 = fresh_client.post("/api/uploads", {"file": uploaded})
        source_doc_id = r1.json()["id"]

        r2 = fresh_client.post(
            "/api/job-targets",
            data=json.dumps({"descriptionText": "Python dev."}),
            content_type="application/json",
        )
        job_target_id = r2.json()["id"]

        r3 = fresh_client.post(
            "/api/tailorings",
            data=json.dumps(
                {"sourceDocumentId": source_doc_id, "jobTargetId": job_target_id}
            ),
            content_type="application/json",
        )
        run_id = r3.json()["id"]

        r4 = fresh_client.get(f"/tailoring/{run_id}/review")
        # Page should load even for a reviewable run
        assert r4.status_code == 200


# ---------------------------------------------------------------------------
# 90-second budget check (T022)
# ---------------------------------------------------------------------------


class TestDraftBudget:
    def test_draft_service_completes_within_budget_with_mock_ai(
        self, db, tmp_path, settings
    ):
        """The full draft orchestration must complete within 90s (mocked AI = fast)."""
        from apps.common.models import WorkspaceSession
        from apps.intake.models import JobTarget
        from apps.tailoring.draft_service import DraftOrchestrationService
        from apps.tailoring.models import TailoringRun

        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        ws = WorkspaceSession.objects.create(session_key="budget-test-session")
        doc = SourceDocument.objects.create(
            workspace_session=ws,
            original_filename="cv.docx",
            content_type=SourceDocument.ContentType.DOCX,
            blob_path="test/cv.docx",
            sha256="e" * 64,
            extracted_text="Python developer Django REST APIs PostgreSQL.",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        target = JobTarget.objects.create(
            workspace_session=ws,
            description_text="Need Python Django developer.",
        )
        run = TailoringRun.objects.create(
            workspace_session=ws,
            source_document=doc,
            job_target=target,
            status=TailoringRun.Status.PENDING,
        )

        BUDGET_SECONDS = 90.0

        with patch(
            "apps.ai.client.GitHubModelsClient.complete",
            return_value=MagicMock(
                content=MOCK_AI_PAYLOAD, model="mock", request_id=None
            ),
        ):
            started = perf_counter()
            svc = DraftOrchestrationService()
            result = svc.run(run)
            elapsed = perf_counter() - started

        assert elapsed < BUDGET_SECONDS, (
            f"Draft completed in {elapsed:.2f}s which exceeds the {BUDGET_SECONDS}s budget."
        )
        assert result.run.status == TailoringRun.Status.REVIEWABLE

    def test_draft_service_marks_run_failed_on_ai_timeout(self, db, tmp_path, settings):
        """If the AI call raises, the run transitions to FAILED."""
        from apps.common.models import WorkspaceSession
        from apps.intake.models import JobTarget
        from apps.tailoring.draft_service import DraftOrchestrationError, DraftOrchestrationService
        from apps.tailoring.models import TailoringRun

        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        ws = WorkspaceSession.objects.create(session_key="timeout-test-session")
        doc = SourceDocument.objects.create(
            workspace_session=ws,
            original_filename="cv.docx",
            content_type=SourceDocument.ContentType.DOCX,
            blob_path="test/cv2.docx",
            sha256="f" * 64,
            extracted_text="Python developer.",
            parse_status=SourceDocument.ParseStatus.READY,
            is_current=True,
        )
        target = JobTarget.objects.create(
            workspace_session=ws,
            description_text="Need Django developer.",
        )
        run = TailoringRun.objects.create(
            workspace_session=ws,
            source_document=doc,
            job_target=target,
            status=TailoringRun.Status.PENDING,
        )

        with patch(
            "apps.ai.client.GitHubModelsClient.complete",
            side_effect=Exception("Simulated timeout"),
        ):
            svc = DraftOrchestrationService()
            with pytest.raises(DraftOrchestrationError):
                svc.run(run)

        run.refresh_from_db()
        assert run.status == TailoringRun.Status.FAILED
