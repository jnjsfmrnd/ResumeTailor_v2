from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from apps.ai.client import GitHubModelsError
from apps.ai.services import ResumeTailorAIService
from apps.tailoring.models import TailoringRun
from apps.tailoring.validators import validate_draft_truthfulness

logger = logging.getLogger(__name__)


class DraftOrchestrationError(Exception):
    """Raised when the draft orchestration pipeline cannot complete."""


@dataclass(slots=True)
class DraftResult:
    run: TailoringRun
    truthfulness_notes: list[str] = field(default_factory=list)


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` fences that the model may produce despite instructions."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


class DraftOrchestrationService:
    """Orchestrates AI-assisted draft generation for a :class:`TailoringRun`."""

    def __init__(self, ai_service: ResumeTailorAIService | None = None) -> None:
        self.ai_service = ai_service or ResumeTailorAIService()

    def run(self, tailoring_run: TailoringRun) -> DraftResult:
        """Generate, validate, and persist the draft for *tailoring_run*.

        Transitions:
          pending → processing → reviewable  (success)
          pending → processing → failed      (any error)
        """
        source_doc = tailoring_run.source_document
        job_target = tailoring_run.job_target

        # Guard: source document must be fully parsed before we can tailor
        if source_doc.parse_status != source_doc.ParseStatus.READY:
            tailoring_run.status = TailoringRun.Status.FAILED
            tailoring_run.save(update_fields=["status", "updated_at"])
            raise DraftOrchestrationError(
                f"Source document parse_status is {source_doc.parse_status!r}, "
                "expected 'ready'. Parse the document before starting a tailoring run."
            )

        # Transition: pending → processing
        tailoring_run.status = TailoringRun.Status.PROCESSING
        tailoring_run.save(update_fields=["status", "updated_at"])

        try:
            ai_result = self.ai_service.generate_tailoring_draft(
                resume_text=source_doc.extracted_text,
                job_description=job_target.description_text,
            )
            clean_content = _strip_markdown_fences(ai_result.raw_content)
            payload: dict = self.ai_service.parse_json_payload(clean_content)
        except (GitHubModelsError, Exception) as exc:
            tailoring_run.status = TailoringRun.Status.FAILED
            tailoring_run.save(update_fields=["status", "updated_at"])
            logger.error(
                "Draft generation failed for run %s: %s",
                tailoring_run.id,
                exc,
                exc_info=True,
            )
            raise DraftOrchestrationError(str(exc)) from exc

        professional_summary: str = payload.get("professional_summary", "")
        tailored_skills: list = payload.get("tailored_skills", [])
        tailored_experience_sections: list = payload.get(
            "tailored_experience_sections", []
        )
        raw_truthfulness_notes: list = payload.get("truthfulness_notes", [])

        # Run lightweight truthfulness validation
        validation_notes = validate_draft_truthfulness(
            source_text=source_doc.extracted_text,
            professional_summary=professional_summary,
            tailored_skills=tailored_skills,
            tailored_experience_sections=tailored_experience_sections,
        )

        all_notes = list(raw_truthfulness_notes) + validation_notes

        # Transition: processing → reviewable
        tailoring_run.professional_summary = professional_summary
        tailoring_run.tailored_skills = tailored_skills
        tailoring_run.tailored_experience_sections = tailored_experience_sections
        tailoring_run.truthfulness_notes = all_notes
        tailoring_run.status = TailoringRun.Status.REVIEWABLE
        tailoring_run.save(
            update_fields=[
                "professional_summary",
                "tailored_skills",
                "tailored_experience_sections",
                "truthfulness_notes",
                "status",
                "updated_at",
            ]
        )

        return DraftResult(run=tailoring_run, truthfulness_notes=all_notes)
