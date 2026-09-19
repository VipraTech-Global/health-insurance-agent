from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser_v2.crypto import commitment
from apps.adviser_v2.models import (
    ConversationMessageChunk,
    CustomerUploadedDocument,
    DeletionRequest,
    Message,
    OriginalFile,
)
from apps.adviser_v2.retrieval import index_message
from apps.adviser_v2.services.customer import create_conversation
from apps.adviser_v2.services.erasure import ERASED_TEXT
from apps.adviser_v2.storage import store_private


@pytest.mark.django_db
def test_v2_account_deletion_erases_content_files_and_indexes(
    v2_client: Client,
    v2_user: User,
    settings: Any,
    tmp_path: Path,
) -> None:
    settings.COVERGUIDE_V2_STORAGE_ROOT = tmp_path / "coverguide"
    conversation = create_conversation(v2_user.id, "Private family planning")
    message = Message.objects.create(
        owner=v2_user,
        conversation=conversation,
        sequence=1,
        role="customer",
        content="My mother has diabetes.",
        origin="text",
        payload_commitment=commitment("My mother has diabetes."),
        submitted_at=timezone.now(),
    )
    index_message(message)
    stored = store_private(v2_user.id, "customer-document", b"private schedule bytes")
    original = OriginalFile.objects.create(
        owner=v2_user,
        sha256=stored.plaintext_sha256,
        storage_key=stored.storage_key,
        byte_size=stored.plaintext_size,
        media_type="application/pdf",
    )
    upload = CustomerUploadedDocument.objects.create(
        owner=v2_user,
        original_file=original,
        source_message=message,
        display_name="private-schedule.pdf",
        kind="policy_schedule",
    )
    stored_path = Path(settings.COVERGUIDE_V2_STORAGE_ROOT) / stored.storage_key
    assert stored_path.exists()

    response = v2_client.delete(
        reverse("delete-account"),
        HTTP_X_CSRFTOKEN=v2_client.cookies["csrftoken"].value,
    )

    assert response.status_code == 204
    v2_user.refresh_from_db()
    assert not v2_user.is_active
    assert v2_user.deleted_at is not None
    assert v2_user.erasure_generation == 1
    assert v2_user.email == f"deleted+{v2_user.id}@coverguide.invalid"
    message.refresh_from_db()
    conversation.refresh_from_db()
    original.refresh_from_db()
    upload.refresh_from_db()
    assert message.content == ERASED_TEXT
    assert message.redacted_at is not None
    assert conversation.title == ERASED_TEXT
    assert conversation.status == "deleted"
    assert original.availability == "deleted"
    assert original.byte_size == 0
    assert upload.display_name is None
    assert upload.kind == "other"
    assert not stored_path.exists()
    assert not ConversationMessageChunk.objects.filter(owner=v2_user).exists()
    deletion = DeletionRequest.objects.get(owner=v2_user)
    assert deletion.state == "completed"
    assert all(item["status"] == "erased" for item in deletion.verification["stores"])
