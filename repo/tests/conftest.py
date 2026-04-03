from __future__ import annotations

import pytest
from django.test import Client

from apps.common.models import WorkspaceSession
from apps.intake.models import JobTarget, SourceDocument


@pytest.fixture
def client(db):
    return Client()


@pytest.fixture
def workspace_session(db):
    """Return a fresh WorkspaceSession tied to a test session key."""
    return WorkspaceSession.objects.create(session_key="test-session-key-001")


@pytest.fixture
def ready_source_document(workspace_session):
    """Return a SourceDocument in READY status for the test workspace."""
    doc = SourceDocument.objects.create(
        workspace_session=workspace_session,
        original_filename="test_resume.pdf",
        content_type=SourceDocument.ContentType.PDF,
        blob_path="uploads/test/test_resume.pdf",
        sha256="a" * 64,
        extracted_text="Python developer with 5 years of experience in Django and REST APIs.",
        parse_status=SourceDocument.ParseStatus.READY,
        is_current=True,
    )
    workspace_session.current_source_document = doc
    workspace_session.save(update_fields=["current_source_document", "updated_at"])
    return doc


@pytest.fixture
def job_target(workspace_session):
    """Return a JobTarget for the test workspace."""
    target = JobTarget.objects.create(
        workspace_session=workspace_session,
        company_name="Acme Corp",
        role_title="Senior Python Developer",
        description_text=(
            "We need a Python developer with experience in Django, REST APIs, "
            "PostgreSQL, and cloud deployments."
        ),
    )
    workspace_session.current_job_target = target
    workspace_session.save(update_fields=["current_job_target", "updated_at"])
    return target


@pytest.fixture
def minimal_pdf() -> bytes:
    """Return the smallest possible valid-looking PDF bytes."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
        b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n"
        b"3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        b"/Contents 4 0 R>>\nendobj\n"
        b"4 0 obj\n<</Length 44>>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (Test Resume) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f\n"
        b"trailer\n<</Size 5 /Root 1 0 R>>\n"
        b"startxref\n0\n%%EOF"
    )
