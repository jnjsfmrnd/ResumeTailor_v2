"""Unit tests for resume document parsing services (T016).

Tests parse_pdf, parse_docx, parse_doc, normalize_text, and the
ResumeParsingService state machine without touching the database.
"""
from __future__ import annotations

import io
import zipfile

import pytest

from apps.intake.parsers import (
    ParseError,
    normalize_text,
    parse_doc,
    parse_docx,
    parse_pdf,
)

# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------


class TestNormalizeText:
    def test_collapses_multiple_blank_lines(self):
        result = normalize_text("Line 1\n\n\n\nLine 2")
        assert result == "Line 1\n\nLine 2"

    def test_collapses_tabs_and_spaces(self):
        result = normalize_text("hello   \t  world")
        assert result == "hello world"

    def test_normalises_carriage_returns(self):
        result = normalize_text("line1\r\nline2\rline3")
        assert result == "line1\nline2\nline3"

    def test_strips_leading_trailing_whitespace(self):
        result = normalize_text("   hello   ")
        assert result == "hello"

    def test_returns_empty_for_blank_input(self):
        result = normalize_text("   \n\n  ")
        assert result == ""


# ---------------------------------------------------------------------------
# parse_pdf
# ---------------------------------------------------------------------------


class TestParsePdf:
    def test_raises_parse_error_for_empty_pdf(self):
        """A PDF with no extractable text must raise ParseError."""
        # Minimal PDF bytes with no text stream — pypdf will return empty strings
        empty_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
            b"2 0 obj\n<</Type /Pages /Kids [] /Count 0>>\nendobj\n"
            b"xref\n0 3\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"trailer\n<</Size 3 /Root 1 0 R>>\nstartxref\n116\n%%EOF"
        )
        with pytest.raises(ParseError, match="extractable text"):
            parse_pdf(empty_pdf)

    def test_raises_parse_error_for_non_pdf(self):
        with pytest.raises(ParseError):
            parse_pdf(b"this is not a pdf at all")


# ---------------------------------------------------------------------------
# parse_docx
# ---------------------------------------------------------------------------


def _make_docx(text: str) -> bytes:
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


class TestParseDocx:
    def test_extracts_text(self):
        docx_bytes = _make_docx("Python developer Django REST APIs")
        result = parse_docx(docx_bytes)
        assert "Python" in result
        assert "Django" in result

    def test_raises_parse_error_for_empty_text(self):
        docx_bytes = _make_docx("   ")
        with pytest.raises(ParseError, match="extractable text"):
            parse_docx(docx_bytes)

    def test_raises_parse_error_for_non_docx(self):
        with pytest.raises(ParseError):
            parse_docx(b"not a docx file")

    def test_result_is_normalised(self):
        docx_bytes = _make_docx("Hello   World")
        result = parse_docx(docx_bytes)
        assert "  " not in result  # double spaces collapsed


# ---------------------------------------------------------------------------
# parse_doc
# ---------------------------------------------------------------------------


class TestParseDoc:
    def test_extracts_ascii_text(self):
        content = (
            b"Senior Python Developer with Django experience in REST API design, "
            b"database modeling, and production support workflows."
        )
        result = parse_doc(content)
        assert "Python" in result

    def test_raises_parse_error_for_too_short_content(self):
        with pytest.raises(ParseError, match="parsed into useful text"):
            parse_doc(b"\x00\x01\x02")

    def test_strips_non_printable_bytes(self):
        content = (
            b"Python\x00\x01\x02 developer \x80\x90\xa0experience leading cross-team "
            b"delivery and backend API integration in enterprise systems."
        )
        result = parse_doc(content)
        # Non-printable bytes replaced; readable words must remain
        assert "Python" in result


# ---------------------------------------------------------------------------
# ResumeParsingService state machine
# ---------------------------------------------------------------------------


class TestResumeParsingServiceStateMachine:
    def test_transitions_to_ready_on_success(self, db, tmp_path, settings):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        from unittest.mock import MagicMock

        from apps.common.models import WorkspaceSession
        from apps.intake.models import SourceDocument
        from apps.intake.services import ResumeParsingService

        ws = WorkspaceSession.objects.create(session_key="parse-test-001")
        doc = SourceDocument.objects.create(
            workspace_session=ws,
            original_filename="cv.docx",
            content_type=SourceDocument.ContentType.DOCX,
            blob_path="test/cv.docx",
            sha256="a" * 64,
            parse_status=SourceDocument.ParseStatus.UPLOADED,
        )

        docx_bytes = _make_docx("Experienced Python developer skilled in Django.")
        mock_repo = MagicMock()
        mock_repo.read_content.return_value = docx_bytes

        svc = ResumeParsingService(repository=mock_repo)
        result = svc.parse_source_document(doc)

        doc.refresh_from_db()
        assert doc.parse_status == SourceDocument.ParseStatus.READY
        assert "Python" in doc.extracted_text
        assert len(result.keywords) > 0

    def test_transitions_to_failed_on_parse_error(self, db, tmp_path, settings):
        settings.USE_LOCAL_FILE_STORAGE = True
        settings.MEDIA_ROOT = str(tmp_path)

        from unittest.mock import MagicMock

        from apps.common.models import WorkspaceSession
        from apps.intake.models import SourceDocument
        from apps.intake.parsers import ParseError
        from apps.intake.services import ResumeParsingService

        ws = WorkspaceSession.objects.create(session_key="parse-test-002")
        doc = SourceDocument.objects.create(
            workspace_session=ws,
            original_filename="cv.pdf",
            content_type=SourceDocument.ContentType.PDF,
            blob_path="test/cv.pdf",
            sha256="b" * 64,
            parse_status=SourceDocument.ParseStatus.UPLOADED,
        )

        mock_repo = MagicMock()
        mock_repo.read_content.return_value = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
            b"2 0 obj\n<</Type /Pages /Kids [] /Count 0>>\nendobj\n"
            b"xref\n0 3\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"trailer\n<</Size 3 /Root 1 0 R>>\nstartxref\n116\n%%EOF"
        )

        svc = ResumeParsingService(repository=mock_repo)
        with pytest.raises(ParseError):
            svc.parse_source_document(doc)

        doc.refresh_from_db()
        assert doc.parse_status == SourceDocument.ParseStatus.FAILED
        assert doc.parse_error != ""
