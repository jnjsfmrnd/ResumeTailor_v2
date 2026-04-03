from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from xml.etree import ElementTree

from pypdf import PdfReader


class ParseError(Exception):
    pass


@dataclass(slots=True)
class ParsedDocument:
    text: str
    content_type: str


def normalize_text(value: str) -> str:
    collapsed = re.sub(r"\r\n?", "\n", value)
    collapsed = re.sub(r"[ \t]+", " ", collapsed)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    return collapsed.strip()


def parse_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ParseError("The file could not be read as a PDF.") from exc
    text = "\n\n".join(pages)
    if not text.strip():
        raise ParseError("The PDF did not contain extractable text.")
    return normalize_text(text)


def parse_docx(content: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as document_zip:
            xml_bytes = document_zip.read("word/document.xml")
    except Exception as exc:
        raise ParseError("The file could not be read as a DOCX archive.") from exc
    root = ElementTree.fromstring(xml_bytes)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    text_nodes = [node.text or "" for node in root.findall(".//w:t", namespace)]
    text = " ".join(text_nodes)
    if not text.strip():
        raise ParseError("The DOCX file did not contain extractable text.")
    return normalize_text(text)


def parse_doc(content: bytes) -> str:
    candidate = content.decode("utf-8", errors="ignore")
    if len(candidate.strip()) < 50:
        candidate = content.decode("cp1252", errors="ignore")
    candidate = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", candidate)
    normalized = normalize_text(candidate)
    if len(normalized) < 50:
        raise ParseError("The legacy DOC file could not be parsed into useful text.")
    return normalized