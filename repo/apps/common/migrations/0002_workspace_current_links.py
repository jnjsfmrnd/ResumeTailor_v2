import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0001_initial"),
        ("intake", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="workspacesession",
            name="current_job_target",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="intake.jobtarget",
            ),
        ),
        migrations.AddField(
            model_name="workspacesession",
            name="current_source_document",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="intake.sourcedocument",
            ),
        ),
    ]