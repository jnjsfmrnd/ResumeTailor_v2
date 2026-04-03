import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tailoring", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectRecommendation",
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
                ("title", models.CharField(max_length=255)),
                ("goal", models.TextField()),
                ("scope_markdown", models.TextField()),
                ("targeted_gaps", models.JSONField(blank=True, default=list)),
                ("is_included", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tailoring_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="project_recommendations",
                        to="tailoring.tailoringrun",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SkillGapAssessment",
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
                ("missing_requirements", models.JSONField(blank=True, default=list)),
                ("transferable_skills", models.JSONField(blank=True, default=list)),
                ("coverage_summary", models.TextField(blank=True)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tailoring_run",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="skill_gap_assessment",
                        to="tailoring.tailoringrun",
                    ),
                ),
            ],
            options={"ordering": ["-generated_at"]},
        ),
        migrations.CreateModel(
            name="ProjectBulletProposal",
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
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("generated_text", models.TextField()),
                ("edited_text", models.TextField(blank=True)),
                ("is_approved", models.BooleanField(default=False)),
                (
                    "project_recommendation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bullets",
                        to="tailoring.projectrecommendation",
                    ),
                ),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
    ]
