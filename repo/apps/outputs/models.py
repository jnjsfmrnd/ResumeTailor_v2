from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class CoverLetterDraft(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tailoring_run = models.ForeignKey(
        "tailoring.TailoringRun",
        related_name="cover_letter_drafts",
        on_delete=models.CASCADE,
    )
    job_target = models.ForeignKey(
        "intake.JobTarget",
        related_name="cover_letter_drafts",
        on_delete=models.CASCADE,
    )
    body_markdown = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self) -> None:
        from apps.tailoring.models import TailoringRun

        if self.tailoring_run_id and self.tailoring_run.status != TailoringRun.Status.REVIEWABLE:
            raise ValidationError(
                "A cover letter can only be generated from a reviewable tailoring run."
            )

    def __str__(self) -> str:
        return f"CoverLetterDraft({self.id})"


class GeneratedArtifact(models.Model):
    class ArtifactType(models.TextChoices):
        RESUME_PDF = "resume_pdf", "Resume PDF"
        COVER_LETTER_FILE = "cover_letter_file", "Cover Letter File"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tailoring_run = models.ForeignKey(
        "tailoring.TailoringRun",
        related_name="generated_artifacts",
        on_delete=models.CASCADE,
    )
    artifact_type = models.CharField(max_length=32, choices=ArtifactType.choices)
    blob_path = models.CharField(max_length=500)
    content_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"GeneratedArtifact({self.id}, {self.artifact_type})"
