from __future__ import annotations

import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


def default_workspace_expiry():
    return timezone.now() + timedelta(days=7)


class WorkspaceSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=64, unique=True)
    current_source_document = models.ForeignKey(
        "intake.SourceDocument",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    current_job_target = models.ForeignKey(
        "intake.JobTarget",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(default=default_workspace_expiry)

    class Meta:
        ordering = ["-updated_at"]

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()

    def bump_expiry(self, *, days: int = 7) -> None:
        self.expires_at = timezone.now() + timedelta(days=days)

    def __str__(self) -> str:
        return f"WorkspaceSession({self.session_key})"