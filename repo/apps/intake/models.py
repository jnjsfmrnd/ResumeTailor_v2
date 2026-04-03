from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class SourceDocument(models.Model):
    class ContentType(models.TextChoices):
        PDF = "application/pdf", "PDF"
        DOC = "application/msword", "DOC"
        DOCX = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "DOCX",
        )

    class ParseStatus(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_session = models.ForeignKey(
        "common.WorkspaceSession",
        related_name="source_documents",
        on_delete=models.CASCADE,
    )
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, choices=ContentType.choices)
    blob_path = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64)
    extracted_text = models.TextField(blank=True)
    parse_status = models.CharField(
        max_length=20,
        choices=ParseStatus.choices,
        default=ParseStatus.UPLOADED,
    )
    parse_error = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_session"],
                condition=Q(is_current=True),
                name="unique_current_source_per_workspace",
            )
        ]

    def clean(self) -> None:
        if self.parse_status == self.ParseStatus.READY and not self.extracted_text:
            raise ValidationError("Extracted text is required when the parse status is ready.")

    def __str__(self) -> str:
        return self.original_filename


class JobTarget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_session = models.ForeignKey(
        "common.WorkspaceSession",
        related_name="job_targets",
        on_delete=models.CASCADE,
    )
    company_name = models.CharField(max_length=255, blank=True)
    role_title = models.CharField(max_length=255, blank=True)
    description_text = models.TextField()
    top_keywords = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self) -> None:
        if not self.description_text.strip():
            raise ValidationError("Job description text cannot be empty.")

    def __str__(self) -> str:
        role = self.role_title or "Untitled role"
        company = self.company_name or "Unknown company"
        return f"{role} at {company}"