"""Encrypted, release-pinned guided conversations and idempotent turn receipts."""

import uuid

from django.db import models


class DemoConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        "adviser_v2.DemoSession", on_delete=models.CASCADE, related_name="guided"
    )
    release = models.ForeignKey("adviser_v2.DemoRelease", on_delete=models.PROTECT)
    state_ciphertext = models.BinaryField()
    revision = models.PositiveIntegerField(default=0)
    # The customer's opening words for the history sidebar, encrypted like the state.
    title_ciphertext = models.BinaryField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DemoChatTurn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        DemoConversation, on_delete=models.CASCADE, related_name="receipts"
    )
    request_id = models.UUIDField()
    base_revision = models.PositiveIntegerField()
    input_ciphertext = models.BinaryField()
    output_ciphertext = models.BinaryField()
    elapsed_ms = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "request_id"], name="demo_chat_idempotency_uq"
            )
        ]
