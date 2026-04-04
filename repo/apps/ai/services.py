from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from django.conf import settings

from apps.ai.client import CompletionResponse, GitHubModelsClient, GitHubModelsError
from apps.ai.prompts import build_gap_analysis_messages, build_tailoring_messages

logger = logging.getLogger(__name__)

_LOCAL_FALLBACK_NOTE = (
    "Local development fallback was used because GITHUB_MODELS_TOKEN is not configured. "
    "Configure a token to generate a live AI draft."
)
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "have",
    "into",
    "need",
    "needs",
    "role",
    "that",
    "the",
    "their",
    "this",
    "using",
    "with",
}
_DISPLAY_TERM_MAP = {
    "api": "API",
    "apis": "APIs",
    "aws": "AWS",
    "ci": "CI",
    "ci/cd": "CI/CD",
    "css": "CSS",
    "django": "Django",
    "graphql": "GraphQL",
    "html": "HTML",
    "javascript": "JavaScript",
    "kubernetes": "Kubernetes",
    "postgres": "Postgres",
    "postgresql": "PostgreSQL",
    "python": "Python",
    "rest": "REST",
    "sql": "SQL",
    "typescript": "TypeScript",
}


def _normalize_whitespace(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _extract_terms(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}", text or "")
    return [token for token in tokens if token.lower() not in _STOP_WORDS]


def _display_term(token: str) -> str:
    return _DISPLAY_TERM_MAP.get(token.lower(), token)


def _extract_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?:\r?\n)+|(?<=[.!?])\s+", text or "")
    return [_normalize_whitespace(chunk) for chunk in chunks if _normalize_whitespace(chunk)]


def _build_tailored_skills(resume_text: str, job_description: str, *, limit: int = 8) -> list[str]:
    resume_terms: dict[str, str] = {}
    for token in _extract_terms(resume_text):
        resume_terms.setdefault(token.lower(), _display_term(token))

    skills: list[str] = []
    seen: set[str] = set()
    for token in _extract_terms(job_description):
        normalized = token.lower()
        if normalized in seen or normalized not in resume_terms:
            continue
        skills.append(resume_terms[normalized])
        seen.add(normalized)
        if len(skills) >= limit:
            return skills

    for token in _extract_terms(resume_text):
        normalized = token.lower()
        if normalized in seen:
            continue
        skills.append(_display_term(token))
        seen.add(normalized)
        if len(skills) >= limit:
            break
    return skills


def _build_professional_summary(resume_text: str, tailored_skills: list[str]) -> str:
    sentences = _extract_sentences(resume_text)
    if not sentences:
        return ""

    lowered_skills = [skill.lower() for skill in tailored_skills]
    selected: list[str] = []
    for sentence in sentences:
        lowered_sentence = sentence.lower()
        if lowered_skills and not any(skill in lowered_sentence for skill in lowered_skills):
            continue
        selected.append(sentence)
        if len(selected) == 2:
            break

    if not selected:
        selected = sentences[:2]
    return " ".join(selected)


def _build_experience_sections(resume_text: str, tailored_skills: list[str]) -> list[dict[str, object]]:
    sentences = _extract_sentences(resume_text)
    if not sentences:
        return []

    lowered_skills = [skill.lower() for skill in tailored_skills]
    bullets: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        lowered_sentence = sentence.lower()
        if lowered_skills and not any(skill in lowered_sentence for skill in lowered_skills):
            continue
        if lowered_sentence in seen:
            continue
        bullets.append(sentence if sentence.endswith((".", "!", "?")) else f"{sentence}.")
        seen.add(lowered_sentence)
        if len(bullets) == 3:
            break

    if not bullets:
        bullets = [
            sentence if sentence.endswith((".", "!", "?")) else f"{sentence}."
            for sentence in sentences[:3]
        ]

    return [{"employer": "", "role": "", "bullets": bullets}]


def _build_local_tailoring_payload(*, resume_text: str, job_description: str) -> dict[str, object]:
    tailored_skills = _build_tailored_skills(resume_text, job_description)
    return {
        "professional_summary": _build_professional_summary(resume_text, tailored_skills),
        "tailored_skills": tailored_skills,
        "tailored_experience_sections": _build_experience_sections(
            resume_text, tailored_skills
        ),
        "truthfulness_notes": [_LOCAL_FALLBACK_NOTE],
    }


@dataclass(slots=True)
class AIResult:
    raw_content: str
    response: CompletionResponse


class ResumeTailorAIService:
    def __init__(self, client: GitHubModelsClient | None = None) -> None:
        self.client = client or GitHubModelsClient()

    def generate_tailoring_draft(self, *, resume_text: str, job_description: str) -> AIResult:
        if (
            getattr(settings, "GITHUB_MODELS_ENABLE_DEV_FALLBACK", False)
            and not getattr(self.client, "token", None)
        ):
            logger.warning(
                "Using local development tailoring fallback because GITHUB_MODELS_TOKEN is not configured."
            )
            payload = _build_local_tailoring_payload(
                resume_text=resume_text,
                job_description=job_description,
            )
            raw_content = json.dumps(payload)
            return AIResult(
                raw_content=raw_content,
                response=CompletionResponse(
                    content=raw_content,
                    model="local-dev-fallback",
                    request_id=None,
                ),
            )

        response = self.client.complete(
            build_tailoring_messages(
                resume_text=resume_text,
                job_description=job_description,
            )
        )
        return AIResult(raw_content=response.content, response=response)

    def analyze_skill_gaps(self, *, resume_text: str, job_description: str) -> AIResult:
        response = self.client.complete(
            build_gap_analysis_messages(
                resume_text=resume_text,
                job_description=job_description,
            )
        )
        return AIResult(raw_content=response.content, response=response)

    def parse_json_payload(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise GitHubModelsError("Model output was not valid JSON.") from exc