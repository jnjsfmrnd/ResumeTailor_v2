from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from apps.intake.models import SourceDocument
from apps.intake.parsers import ParseError, parse_doc, parse_docx, parse_pdf
from apps.intake.repositories import SourceDocumentRepository


@dataclass(slots=True)
class ResumeParseResult:
    text: str
    keywords: list[str]


class ResumeParsingService:
    def __init__(self, repository: SourceDocumentRepository | None = None) -> None:
        self.repository = repository or SourceDocumentRepository()

    def parse_source_document(self, document: SourceDocument) -> ResumeParseResult:
        document.parse_status = SourceDocument.ParseStatus.PROCESSING
        document.parse_error = ""
        document.save(update_fields=["parse_status", "parse_error"])

        try:
            content = self.repository.read_content(document)
            parser = self._get_parser(document.content_type)
            text = parser(content)
            keywords = self.extract_keywords(text)
        except ParseError as exc:
            document.parse_status = SourceDocument.ParseStatus.FAILED
            document.parse_error = str(exc)
            document.save(update_fields=["parse_status", "parse_error"])
            raise

        document.extracted_text = text
        document.parse_status = SourceDocument.ParseStatus.READY
        document.parse_error = ""
        document.save(update_fields=["extracted_text", "parse_status", "parse_error"])
        return ResumeParseResult(text=text, keywords=keywords)

    def extract_keywords(self, text: str, *, limit: int = 15) -> list[str]:
        tokens = [token.lower() for token in text.split() if len(token) >= 4 and token.isascii()]
        most_common = Counter(tokens).most_common(limit)
        return [token for token, _count in most_common]

    def _get_parser(self, content_type: str):
        parsers = {
            SourceDocument.ContentType.PDF: parse_pdf,
            SourceDocument.ContentType.DOC: parse_doc,
            SourceDocument.ContentType.DOCX: parse_docx,
        }
        try:
            return parsers[content_type]
        except KeyError as exc:
            raise ParseError(f"Unsupported content type: {content_type}") from exc