from __future__ import annotations


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_resume_lines(run_data: dict) -> list[str]:
    lines: list[str] = ["Tailored Resume"]

    summary = str(run_data.get("professional_summary", "")).strip()
    if summary:
        lines.extend(["", "Professional Summary", summary])

    skills = run_data.get("tailored_skills") or []
    if skills:
        lines.extend(["", "Skills", ", ".join(str(skill) for skill in skills)])

    sections = run_data.get("tailored_experience_sections") or []
    if sections:
        lines.extend(["", "Experience"])
        for section in sections:
            company = str(section.get("company", "")).strip()
            role = str(section.get("role", "")).strip()
            dates = str(section.get("dates", "")).strip()
            heading = " - ".join([item for item in [role, company, dates] if item])
            if heading:
                lines.append(heading)
            for bullet in section.get("bullets", []):
                lines.append(f"* {bullet}")

    approved_bullets = run_data.get("approved_bullets") or []
    if approved_bullets:
        lines.extend(["", "Selected Project Bullets"])
        for bullet in approved_bullets:
            lines.append(f"* {bullet}")

    return lines[:120]


def build_ats_safe_resume_pdf(run_data: dict) -> bytes:
    lines = _build_resume_lines(run_data)

    content_lines = ["BT", "/F1 11 Tf", "72 760 Td", "14 TL"]
    first_line = True
    for line in lines:
        escaped = _escape_pdf_text(line)
        if first_line:
            content_lines.append(f"({escaped}) Tj")
            first_line = False
        else:
            content_lines.append(f"T* ({escaped}) Tj")
    content_lines.append("ET")
    content = "\n".join(content_lines) + "\n"
    content_bytes = content.encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\n"
            b"endobj\n"
        ),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        (
            f"5 0 obj\n<< /Length {len(content_bytes)} >>\nstream\n".encode("ascii")
            + content_bytes
            + b"endstream\nendobj\n"
        ),
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF\n"
    )
    pdf.extend(trailer.encode("ascii"))
    return bytes(pdf)
