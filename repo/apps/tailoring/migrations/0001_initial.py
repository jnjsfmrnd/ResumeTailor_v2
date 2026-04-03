import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("common", "0002_workspace_current_links"),
        ("intake", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TailoringRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("reviewable", "Reviewable"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("professional_summary", models.TextField(blank=True)),
                ("tailored_skills", models.JSONField(blank=True, default=list)),
                ("tailored_experience_sections", models.JSONField(blank=True, default=list)),
                ("truthfulness_notes", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "job_target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tailoring_runs",
                        to="intake.jobtarget",
                    ),
                ),
                (
                    "source_document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tailoring_runs",
                        to="intake.sourcedocument",
                    ),
                ),
                (
                    "workspace_session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tailoring_runs",
                        to="common.workspacesession",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        )
    ]