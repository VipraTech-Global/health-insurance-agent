import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def populate_attempt_conversations(apps, schema_editor):
    TurnAttempt = apps.get_model("adviser", "TurnAttempt")
    Conversation = apps.get_model("adviser", "Conversation")
    for attempt in TurnAttempt.objects.select_related("turn").iterator():
        attempt.conversation_id = attempt.turn.conversation_id
        attempt.save(update_fields=["conversation"])

    active_states = ["accepted", "running"]
    for conversation in Conversation.objects.iterator():
        active = list(
            TurnAttempt.objects.filter(
                conversation_id=conversation.id, status__in=active_states
            ).order_by("-created_at", "-id")
        )
        keeper = active[0] if active else None
        if len(active) > 1:
            TurnAttempt.objects.filter(id__in=[item.id for item in active[1:]]).update(
                status="failed", terminal_code="migration_reconciled"
            )
        conversation.active_attempt_id = keeper.id if keeper else None
        conversation.save(update_fields=["active_attempt"])


class Migration(migrations.Migration):
    dependencies = [("adviser", "0005_remove_planversion_unique_plan_identity_and_more")]

    operations = [
        migrations.AddField(
            model_name="turnattempt",
            name="conversation",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attempts",
                to="adviser.conversation",
            ),
        ),
        migrations.RunPython(populate_attempt_conversations, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="turnattempt",
            name="conversation",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attempts",
                to="adviser.conversation",
            ),
        ),
        migrations.RemoveConstraint(model_name="turnattempt", name="one_active_attempt_per_turn"),
        migrations.AddConstraint(
            model_name="turnattempt",
            constraint=models.UniqueConstraint(
                fields=("conversation",),
                condition=Q(status__in=["accepted", "running"]),
                name="one_active_attempt_per_conversation",
            ),
        ),
    ]
