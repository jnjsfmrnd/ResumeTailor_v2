from __future__ import annotations

import json
from dataclasses import dataclass

from apps.ai.client import CompletionResponse, GitHubModelsClient, GitHubModelsError
from apps.ai.prompts import build_gap_analysis_messages, build_tailoring_messages


@dataclass(slots=True)
class AIResult:
    raw_content: str
    response: CompletionResponse


class ResumeTailorAIService:
    def __init__(self, client: GitHubModelsClient | None = None) -> None:
        self.client = client or GitHubModelsClient()

    def generate_tailoring_draft(self, *, resume_text: str, job_description: str) -> AIResult:
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