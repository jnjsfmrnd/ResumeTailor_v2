import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("intake", "0001_initial"),
        ("tailoring", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CoverLetterDraft",
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
                ("body_markdown", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "job_target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cover_letter_drafts",
                        to="intake.jobtarget",
                    ),
                ),
                (
                    "tailoring_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cover_letter_drafts",
                        to="tailoring.tailoringrun",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="GeneratedArtifact",
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
                    "artifact_type",
                    models.CharField(
                        choices=[
                            ("resume_pdf", "Resume PDF"),
                            ("cover_letter_file", "Cover Letter File"),
                        ],
                        max_length=32,
                    ),
                ),
                ("blob_path", models.CharField(max_length=500)),
                ("content_hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tailoring_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="generated_artifacts",
                        to="tailoring.tailoringrun",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
