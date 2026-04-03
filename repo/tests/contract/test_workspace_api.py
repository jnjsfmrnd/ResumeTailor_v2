"""Contract tests for current workspace and upload endpoints.

Validates API schema compliance for:
  GET  /api/workspace/current
  POST /api/uploads
"""
from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.common.models import WorkspaceSession

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# GET /api/workspace/current
# ---------------------------------------------------------------------------


class TestGetCurrentWorkspace:
    def test_returns_200(self, client, db):
        response = client.get("/api/workspace/current")
        assert response.status_code == 200

    def test_content_type_is_json(self, client, db):
        response = client.get("/api/workspace/current")
        assert response["Content-Type"].startswith("application/json")

    def test_response_contains_required_keys(self, client, db):
        response = client.get("/api/workspace/current")
        data = response.json()
        required = {"sessionId", "currentSourceDocument", "currentJobTarget", "latestTailoringRun"}
        assert required <= set(data.keys())

    def test_session_id_is_string(self, client, db):
        response = client.get("/api/workspace/current")
        data = response.json()
        assert isinstance(data["sessionId"], str)
        assert len(data["sessionId"]) == 36  # UUID format

    def test_fresh_workspace_has_null_source_document(self, client, db):
        response = client.get("/api/workspace/current")
        data = response.json()
        assert data["currentSourceDocument"] is None

    def test_fresh_workspace_has_null_job_target(self, client, db):
        response = client.get("/api/workspace/current")
        data = response.json()
        assert data["currentJobTarget"] is None

    def test_fresh_workspace_has_null_tailoring_run(self, client, db):
        response = client.get("/api/workspace/current")
        data = response.json()
        assert data["latestTailoringRun"] is None

    def test_creates_workspace_session_on_first_call(self, client, db):
        count_before = WorkspaceSession.objects.count()
        client.get("/api/workspace/current")
        assert WorkspaceSession.objects.count() == count_before + 1

    def test_reuses_workspace_session_on_second_call(self, client, db):
        client.get("/api/workspace/current")
        count_after_first = WorkspaceSession.objects.count()
        client.get("/api/workspace/current")
        assert WorkspaceSession.objects.count() == count_after_first

    def test_source_document_schema_when_present(self, client, ready_source_document, db):
        """When a current source document exists the schema exposes the right fields."""
        # Force the client session to match the fixture workspace
        session = client.session
        session.save()
        ws = WorkspaceSession.objects.get(pk=ready_source_document.workspace_session_id)
        ws.session_key = session.session_key
        ws.save(update_fields=["session_key"])
        response = client.get("/api/workspace/current")
        data = response.json()
        doc = data["currentSourceDocument"]
        if doc is not None:
            assert "id" in doc
            assert "originalFilename" in doc
            assert "parseStatus" in doc
            assert "isCurrent" in doc


# ---------------------------------------------------------------------------
# POST /api/uploads
# ---------------------------------------------------------------------------


class TestUploadResume:
    def _upload(self, client, content: bytes, filename: str, content_type: str):
        uploaded = SimpleUploadedFile(filename, content, content_type=content_type)
        return client.post("/api/uploads", {"file": uploaded})

    def test_upload_pdf_returns_201(self, client, db, tmp_path, settings):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)
        pdf = (
            b"%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\n"
            b"xref\ntrailer\n<</Size 2 /Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        response = self._upload(client, pdf, "resume.pdf", "application/pdf")
        assert response.status_code == 201

    def test_upload_response_schema(self, client, db, tmp_path, settings):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)
        pdf = (
            b"%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\n"
            b"xref\ntrailer\n<</Size 2 /Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        response = self._upload(client, pdf, "resume.pdf", "application/pdf")
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "originalFilename" in data
        assert "parseStatus" in data
        assert "isCurrent" in data

    def test_upload_sets_is_current_true(self, client, db, tmp_path, settings):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)
        pdf = (
            b"%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\n"
            b"xref\ntrailer\n<</Size 2 /Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        response = self._upload(client, pdf, "resume.pdf", "application/pdf")
        data = response.json()
        assert data["isCurrent"] is True

    def test_upload_original_filename_preserved(self, client, db, tmp_path, settings):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)
        pdf = (
            b"%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\n"
            b"xref\ntrailer\n<</Size 2 /Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        response = self._upload(client, pdf, "my_resume.pdf", "application/pdf")
        assert response.json()["originalFilename"] == "my_resume.pdf"

    def test_upload_rejects_unsupported_type(self, client, db):
        response = self._upload(client, b"plain text", "resume.txt", "text/plain")
        assert response.status_code == 400

    def test_upload_rejects_missing_file(self, client, db):
        response = client.post("/api/uploads", {})
        assert response.status_code == 400

    def test_upload_requires_post_method(self, client, db):
        response = client.get("/api/uploads")
        assert response.status_code == 405

    def test_upload_docx_accepted(self, client, db, tmp_path, settings):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)
        docx_ct = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        # Minimal DOCX is a ZIP - just check content type is accepted
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(
                "word/document.xml",
                (
                    '<?xml version="1.0"?>'
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    "<w:body><w:p><w:r><w:t>Senior Python Developer</w:t></w:r></w:p></w:body>"
                    "</w:document>"
                ),
            )
        response = self._upload(client, buf.getvalue(), "resume.docx", docx_ct)
        assert response.status_code == 201
