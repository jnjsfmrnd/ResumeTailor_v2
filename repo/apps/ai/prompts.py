from __future__ import annotations

SYSTEM_PROMPT = """
You are ResumeTailor, a truthful resume editing assistant.
Only rewrite or elevate content that is directly supported by the uploaded
resume and explicit user-approved additions.
Never invent employers, technologies, dates, degrees, certifications, or outcomes.
Prefer concise, ATS-friendly language and preserve factual accuracy over stylistic flourish.
""".strip()

_TAILORING_JSON_FORMAT = (
    "Return a JSON object with exactly these keys and no markdown fences or extra text:\n"
    '{"professional_summary": "<ATS-friendly paragraph>", '
    '"tailored_skills": ["<skill>", ...], '
    '"tailored_experience_sections": ['
    '{"employer": "<name>", "role": "<title>", "bullets": ["<bullet>", ...]}'
    '], '
    '"truthfulness_notes": ["<note>", ...]}\n'
    "Only include employers, technologies, dates, and outcomes present in the source resume."
)


def build_tailoring_messages(*, resume_text: str, job_description: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Tailor the resume for the job description.\n\n"
                f"{_TAILORING_JSON_FORMAT}\n\n"
                f"Resume:\n{resume_text}\n\nJob description:\n{job_description}"
            ),
        },
    ]


def build_gap_analysis_messages(*, resume_text: str, job_description: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Compare the resume to the job description and identify missing requirements, "
                "transferable skills, and evidence-backed coverage notes.\n\n"
                f"Resume:\n{resume_text}\n\nJob description:\n{job_description}"
            ),
        },
    ]
