"""Persist the explicit development-alpha label and partial coverage summary."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0009_turn_lease_recovery")]

    operations = [
        migrations.AddField(
            model_name="knowledgerelease",
            name="release_label",
            field=models.CharField(default="development_alpha", max_length=32),
        ),
        migrations.AddField(
            model_name="knowledgerelease",
            name="readiness",
            field=models.JSONField(default=dict),
        ),
    ]
