from __future__ import annotations

from django.core.exceptions import ValidationError

from apps.tailoring.models import TailoringRun


def ensure_export_allowed(tailoring_run: TailoringRun) -> None:
    if tailoring_run.status != TailoringRun.Status.REVIEWABLE:
        raise ValidationError(
            "Exports are only allowed for reviewable tailoring runs."
        )
