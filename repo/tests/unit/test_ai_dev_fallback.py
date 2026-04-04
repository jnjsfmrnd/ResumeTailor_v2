from __future__ import annotations

import pytest

from apps.ai.client import GitHubModelsClient, GitHubModelsError
from apps.ai.services import ResumeTailorAIService


def test_generate_tailoring_draft_uses_local_fallback_when_enabled(settings) -> None:
    settings.GITHUB_MODELS_TOKEN = ""
    settings.GITHUB_MODELS_ENABLE_DEV_FALLBACK = True

    service = ResumeTailorAIService(client=GitHubModelsClient(token=""))

    result = service.generate_tailoring_draft(
        resume_text="Python developer. Built Django REST APIs. PostgreSQL.",
        job_description="Need Django developer with REST API and PostgreSQL experience.",
    )

    payload = service.parse_json_payload(result.raw_content)
    assert result.response.model == "local-dev-fallback"
    assert payload["professional_summary"]
    assert payload["tailored_skills"]
    assert payload["truthfulness_notes"]
    assert "Local development fallback" in payload["truthfulness_notes"][0]


def test_generate_tailoring_draft_stays_strict_when_fallback_is_disabled(settings) -> None:
    settings.GITHUB_MODELS_TOKEN = ""
    settings.GITHUB_MODELS_ENABLE_DEV_FALLBACK = False

    service = ResumeTailorAIService(client=GitHubModelsClient(token=""))

    with pytest.raises(GitHubModelsError, match="GITHUB_MODELS_TOKEN is not configured"):
        service.generate_tailoring_draft(
            resume_text="Python developer.",
            job_description="Need Django developer.",
        )