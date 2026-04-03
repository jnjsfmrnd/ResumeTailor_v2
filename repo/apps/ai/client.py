from __future__ import annotations

from dataclasses import dataclass
from time import sleep

import httpx
from django.conf import settings


class GitHubModelsError(Exception):
    pass


@dataclass(slots=True)
class CompletionResponse:
    content: str
    model: str
    request_id: str | None


class GitHubModelsClient:
    def __init__(
        self,
        *,
        token: str | None = None,
        endpoint: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        retries: int = 3,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.token = token or settings.GITHUB_MODELS_TOKEN
        self.endpoint = endpoint or settings.GITHUB_MODELS_ENDPOINT.rstrip("/")
        self.model = model or settings.GITHUB_MODELS_MODEL
        self.timeout = timeout or settings.GITHUB_MODELS_TIMEOUT
        self.retries = retries
        self.transport = transport

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 1_200,
    ) -> CompletionResponse:
        if not self.token:
            raise GitHubModelsError("GITHUB_MODELS_TOKEN is not configured.")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                    response = client.post(
                        f"{self.endpoint}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt == self.retries:
                    break
                sleep(min(attempt, 3))
                continue

            data = response.json()
            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise GitHubModelsError("The GitHub Models response was malformed.") from exc

            return CompletionResponse(
                content=content,
                model=data.get("model", self.model),
                request_id=response.headers.get("x-request-id"),
            )

        raise GitHubModelsError("GitHub Models request failed after retries.") from last_error