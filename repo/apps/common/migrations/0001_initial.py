import uuid

from django.db import migrations, models

from apps.common.models import default_workspace_expiry


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WorkspaceSession",
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
                ("session_key", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "expires_at",
                    models.DateTimeField(default=default_workspace_expiry),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        )
    ]