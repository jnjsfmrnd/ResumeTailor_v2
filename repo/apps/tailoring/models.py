from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models


class TailoringRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        REVIEWABLE = "reviewable", "Reviewable"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_session = models.ForeignKey(
        "common.WorkspaceSession",
        related_name="tailoring_runs",
        on_delete=models.CASCADE,
    )
    source_document = models.ForeignKey(
        "intake.SourceDocument",
        related_name="tailoring_runs",
        on_delete=models.CASCADE,
    )
    job_target = models.ForeignKey(
        "intake.JobTarget",
        related_name="tailoring_runs",
        on_delete=models.CASCADE,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    professional_summary = models.TextField(blank=True)
    tailored_skills = models.JSONField(default=list, blank=True)
    tailored_experience_sections = models.JSONField(default=list, blank=True)
    truthfulness_notes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self) -> None:
        if self.status == self.Status.REVIEWABLE:
            if not self.professional_summary.strip() or not self.tailored_experience_sections:
                raise ValidationError(
                    "A tailoring run cannot be reviewable without summary and experience output."
                )

    def __str__(self) -> str:
        return f"TailoringRun({self.id})"


class SkillGapAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tailoring_run = models.OneToOneField(
        "tailoring.TailoringRun",
        related_name="skill_gap_assessment",
        on_delete=models.CASCADE,
    )
    missing_requirements = models.JSONField(default=list, blank=True)
    transferable_skills = models.JSONField(default=list, blank=True)
    coverage_summary = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"SkillGapAssessment({self.tailoring_run_id})"


class ProjectRecommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tailoring_run = models.ForeignKey(
        "tailoring.TailoringRun",
        related_name="project_recommendations",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    goal = models.TextField()
    scope_markdown = models.TextField()
    targeted_gaps = models.JSONField(default=list, blank=True)
    is_included = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self) -> None:
        if not self.targeted_gaps:
            raise ValidationError("At least one targeted gap is required.")

    def __str__(self) -> str:
        return f"ProjectRecommendation({self.id})"


class ProjectBulletProposal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_recommendation = models.ForeignKey(
        "tailoring.ProjectRecommendation",
        related_name="bullets",
        on_delete=models.CASCADE,
    )
    sort_order = models.PositiveIntegerField(default=0)
    generated_text = models.TextField()
    edited_text = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"ProjectBulletProposal({self.id})"