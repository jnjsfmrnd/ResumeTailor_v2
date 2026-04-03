from __future__ import annotations

import hashlib
from uuid import uuid4

from apps.ai.client import GitHubModelsClient
from apps.intake.repositories import DurableStorageBackend, get_storage_backend
from apps.outputs.models import CoverLetterDraft, GeneratedArtifact
from apps.tailoring.models import TailoringRun


def build_cover_letter_messages(
    *,
    resume_text: str,
    job_description: str,
    professional_summary: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a truthful cover letter assistant. Only use information that is "
                "supported by the provided resume text and tailoring summary."
            ),
        },
        {
            "role": "user",
            "content": (
                "Write a concise cover letter in markdown with factual claims only.\n\n"
                f"Professional summary:\n{professional_summary}\n\n"
                f"Resume text:\n{resume_text}\n\n"
                f"Job description:\n{job_description}"
            ),
        },
    ]


class CoverLetterService:
    def __init__(
        self,
        *,
        ai_client: GitHubModelsClient | None = None,
        storage_backend: DurableStorageBackend | None = None,
    ) -> None:
        self.ai_client = ai_client or GitHubModelsClient()
        self.storage_backend = storage_backend or get_storage_backend()

    def generate(self, *, tailoring_run: TailoringRun) -> CoverLetterDraft:
        draft = CoverLetterDraft.objects.create(
            tailoring_run=tailoring_run,
            job_target=tailoring_run.job_target,
            status=CoverLetterDraft.Status.PROCESSING,
        )

        try:
            response = self.ai_client.complete(
                build_cover_letter_messages(
                    resume_text=tailoring_run.source_document.extracted_text,
                    job_description=tailoring_run.job_target.description_text,
                    professional_summary=tailoring_run.professional_summary,
                ),
                temperature=0.2,
                max_tokens=900,
            )
        except Exception:
            draft.status = CoverLetterDraft.Status.FAILED
            draft.save(update_fields=["status"])
            raise

        body_markdown = response.content.strip()
        draft.body_markdown = body_markdown
        draft.status = CoverLetterDraft.Status.READY
        draft.save(update_fields=["body_markdown", "status"])

        body_bytes = body_markdown.encode("utf-8")
        blob_path = f"artifacts/{tailoring_run.id}/cover-letter-{uuid4()}.md"
        self.storage_backend.save_bytes(blob_path, body_bytes, content_type="text/markdown")

        GeneratedArtifact.objects.create(
            tailoring_run=tailoring_run,
            artifact_type=GeneratedArtifact.ArtifactType.COVER_LETTER_FILE,
            blob_path=blob_path,
            content_hash=hashlib.sha256(body_bytes).hexdigest(),
        )
        return draft
