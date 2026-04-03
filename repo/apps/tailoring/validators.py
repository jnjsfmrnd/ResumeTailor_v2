from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Common English filler words that the AI is allowed to use freely
# even if they're not in the source resume text.
# ---------------------------------------------------------------------------
_FILLER_WORDS: frozenset[str] = frozenset(
    {
        "that", "with", "this", "have", "from", "your", "will", "been", "were",
        "they", "their", "what", "when", "where", "which", "such", "more", "most",
        "also", "into", "over", "than", "then", "both", "very", "well", "each",
        "much", "these", "those", "about", "after", "before", "under", "while",
        "through", "between", "during", "including", "across", "within", "without",
        "against", "among", "leveraging", "utilizing", "collaborating", "delivering",
        "proven", "experienced", "skilled", "proficient", "strong", "results",
        "driven", "focused", "oriented", "based", "team", "cross", "functional",
        "business", "technical", "professional", "motivated", "dedicated",
        "passionate", "dynamic", "innovative", "strategic", "responsible",
        "contributing", "supporting", "ensuring", "managing", "developing",
        "creating", "designing", "implementing", "providing", "working",
        "using", "used", "built", "build", "helped", "help", "lead", "leading",
        "summary", "objective", "profile", "overview",
    }
)


def _tokenize(text: str) -> set[str]:
    """Extract lowercase alphabetic tokens of 4+ characters from *text*."""
    return {token.lower() for token in re.findall(r"[A-Za-z]{4,}", text)}


def _extract_experience_text(sections: list) -> str:
    chunks: list[str] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        employer = section.get("employer", "")
        role = section.get("role", "")
        bullets = section.get("bullets", [])
        chunks.append(str(employer))
        chunks.append(str(role))
        if isinstance(bullets, list):
            for bullet in bullets:
                chunks.append(str(bullet))
    return " ".join(chunks)


def validate_draft_truthfulness(
    *,
    source_text: str,
    professional_summary: str,
    tailored_skills: list,
    tailored_experience_sections: list,
) -> list[str]:
    """Return warning notes for generated content that may be unsupported by the source.

    This is a best-effort heuristic, not a definitive audit. The AI system prompt
    already instructs the model not to invent facts; this validator surfaces
    suspicious tokens for human review.
    """
    if not professional_summary.strip():
        return []

    notes: list[str] = []
    source_tokens = _tokenize(source_text)

    if professional_summary.strip():
        summary_tokens = _tokenize(professional_summary)
        unknown_summary = summary_tokens - source_tokens - _FILLER_WORDS
        if unknown_summary:
            flagged = sorted(unknown_summary)[:5]
            notes.append(
                f"Professional summary contains terms not found in the source resume "
                f"({', '.join(flagged)}). Please verify these are accurate."
            )

    if isinstance(tailored_skills, list) and tailored_skills:
        skills_tokens: set[str] = set()
        for skill in tailored_skills:
            if isinstance(skill, str):
                skills_tokens.update(_tokenize(skill))
        unknown_skills = skills_tokens - source_tokens - _FILLER_WORDS
        if unknown_skills:
            flagged = sorted(unknown_skills)[:5]
            notes.append(
                f"Tailored skills include terms not found in the source resume "
                f"({', '.join(flagged)})."
            )

    experience_text = _extract_experience_text(tailored_experience_sections)
    if experience_text.strip():
        exp_tokens = _tokenize(experience_text)
        unknown_exp = exp_tokens - source_tokens - _FILLER_WORDS
        if unknown_exp:
            flagged = sorted(unknown_exp)[:5]
            notes.append(
                f"Tailored experience includes terms not found in the source resume "
                f"({', '.join(flagged)})."
            )

    return notes
