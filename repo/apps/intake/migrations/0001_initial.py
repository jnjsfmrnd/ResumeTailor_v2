import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [("common", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="JobTarget",
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
                ("company_name", models.CharField(blank=True, max_length=255)),
                ("role_title", models.CharField(blank=True, max_length=255)),
                ("description_text", models.TextField()),
                ("top_keywords", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "workspace_session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="job_targets",
                        to="common.workspacesession",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SourceDocument",
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
                ("original_filename", models.CharField(max_length=255)),
                (
                    "content_type",
                    models.CharField(
                        choices=[
                            ("application/pdf", "PDF"),
                            ("application/msword", "DOC"),
                            (
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                "DOCX",
                            ),
                        ],
                        max_length=100,
                    ),
                ),
                ("blob_path", models.CharField(max_length=500)),
                ("sha256", models.CharField(max_length=64)),
                ("extracted_text", models.TextField(blank=True)),
                (
                    "parse_status",
                    models.CharField(
                        choices=[
                            ("uploaded", "Uploaded"),
                            ("processing", "Processing"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                        ],
                        default="uploaded",
                        max_length=20,
                    ),
                ),
                ("parse_error", models.TextField(blank=True)),
                ("is_current", models.BooleanField(default=False)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "workspace_session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_documents",
                        to="common.workspacesession",
                    ),
                ),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.AddConstraint(
            model_name="sourcedocument",
            constraint=models.UniqueConstraint(
                condition=Q(is_current=True),
                fields=("workspace_session",),
                name="unique_current_source_per_workspace",
            ),
        ),
    ]