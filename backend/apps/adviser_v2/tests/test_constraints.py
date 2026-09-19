from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from django.db import DatabaseError, connection, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser_v2.crypto import commitment
from apps.adviser_v2.models import (
    CustomerProfileRevision,
    CustomerUploadedDocument,
    Message,
    OriginalFile,
    ProcessingJob,
    Turn,
)
from apps.adviser_v2.services.customer import create_conversation


@pytest.mark.django_db(transaction=True)
def test_cross_owner_relationship_is_rejected() -> None:
    first = User.objects.create_user(email="owner-a@example.com")
    second = User.objects.create_user(email="owner-b@example.com")
    conversation = create_conversation(first.id)
    with pytest.raises(DatabaseError, match="Cross-owner"):
        with transaction.atomic():
            Message.objects.create(
                owner=second,
                conversation=conversation,
                sequence=1,
                role="customer",
                content="wrong owner",
                origin="text",
                payload_commitment=commitment("wrong owner"),
                submitted_at=timezone.now(),
            )


@pytest.mark.django_db(transaction=True)
def test_revision_and_message_sequences_cannot_skip(v2_user: User) -> None:
    conversation = create_conversation(v2_user.id)
    with pytest.raises(DatabaseError, match="next value"):
        CustomerProfileRevision.objects.create(owner=v2_user, conversation=conversation, revision=3)
    with pytest.raises(DatabaseError, match="next value"):
        Message.objects.create(
            owner=v2_user,
            conversation=conversation,
            sequence=2,
            role="customer",
            content="skip",
            origin="text",
            payload_commitment=commitment("skip"),
            submitted_at=timezone.now(),
        )


@pytest.mark.django_db(transaction=True)
def test_running_turn_requires_current_worker_fence(v2_user: User) -> None:
    conversation = create_conversation(v2_user.id)
    message = Message.objects.create(
        owner=v2_user,
        conversation=conversation,
        sequence=1,
        role="customer",
        content="question",
        origin="text",
        payload_commitment=commitment("question"),
        submitted_at=timezone.now(),
    )
    token = uuid.uuid4()
    turn = Turn.objects.create(
        owner=v2_user,
        conversation=conversation,
        request_id=uuid.uuid4(),
        input_message=message,
        starting_profile_revision=conversation.current_profile_revision,
        state="running",
        lease_token=token,
        lease_until=timezone.now() + timedelta(minutes=1),
        deadline=timezone.now() + timedelta(minutes=2),
    )
    with pytest.raises(DatabaseError, match="unfenced"):
        with transaction.atomic():
            Turn.objects.filter(pk=turn.pk).update(state="completed")
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('coverguide.lease_token', %s, true)", [str(token)])
        Turn.objects.filter(pk=turn.pk).update(state="completed")
    turn.refresh_from_db()
    assert turn.state == "completed"


@pytest.mark.django_db(transaction=True)
def test_expired_processing_lease_allows_only_explicit_clean_requeue(
    v2_user: User,
) -> None:
    original = OriginalFile.objects.create(
        owner=v2_user,
        sha256="a" * 64,
        storage_key=f"private/{v2_user.id}/lease-test.cg2",
        byte_size=1,
        media_type="application/pdf",
    )
    uploaded = CustomerUploadedDocument.objects.create(
        owner=v2_user,
        original_file=original,
        kind="quote",
    )
    job = ProcessingJob.objects.create(
        owner=v2_user,
        customer_uploaded_document=uploaded,
        stage="classify",
        adapter_version="lease-test/1",
        input_commitment="a" * 64,
        state="running",
        lease_token=uuid.uuid4(),
        lease_until=timezone.now() - timedelta(seconds=1),
    )

    with pytest.raises(DatabaseError, match="unfenced"):
        with transaction.atomic():
            ProcessingJob.objects.filter(pk=job.pk).update(
                state="queued", lease_token=None, lease_until=None
            )
    with pytest.raises(DatabaseError, match="unfenced"):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('coverguide.recover_expired_lease', 'true', true)"
                )
            ProcessingJob.objects.filter(pk=job.pk).update(
                state="queued",
                lease_token=None,
                lease_until=None,
                adapter_version="lease-test/tampered",
            )

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('coverguide.recover_expired_lease', 'true', true)")
        ProcessingJob.objects.filter(pk=job.pk).update(
            state="queued",
            lease_token=None,
            lease_until=None,
        )
    job.refresh_from_db()
    assert job.state == "queued"
    assert job.lease_token is None
    assert job.lease_until is None


@pytest.mark.django_db(transaction=True)
def test_expired_turn_lease_allows_only_fail_closed_recovery(v2_user: User) -> None:
    conversation = create_conversation(v2_user.id)
    message = Message.objects.create(
        owner=v2_user,
        conversation=conversation,
        sequence=1,
        role="customer",
        content="question",
        origin="text",
        payload_commitment=commitment("question"),
        submitted_at=timezone.now(),
    )
    turn = Turn.objects.create(
        owner=v2_user,
        conversation=conversation,
        request_id=uuid.uuid4(),
        input_message=message,
        starting_profile_revision=conversation.current_profile_revision,
        state="running",
        lease_token=uuid.uuid4(),
        lease_until=timezone.now() - timedelta(seconds=1),
        deadline=timezone.now() + timedelta(minutes=2),
    )

    with pytest.raises(DatabaseError, match="unfenced"):
        with transaction.atomic():
            Turn.objects.filter(pk=turn.pk).update(
                state="failed",
                error_code="worker_lease_expired",
                lease_token=None,
                lease_until=None,
            )
    with pytest.raises(DatabaseError, match="unfenced"):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('coverguide.recover_expired_lease', 'true', true)"
                )
            Turn.objects.filter(pk=turn.pk).update(
                state="failed",
                error_code="different_failure",
                lease_token=None,
                lease_until=None,
            )

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('coverguide.recover_expired_lease', 'true', true)")
        Turn.objects.filter(pk=turn.pk).update(
            state="failed",
            error_code="worker_lease_expired",
            lease_token=None,
            lease_until=None,
        )
    turn.refresh_from_db()
    assert turn.state == "failed"
    assert turn.error_code == "worker_lease_expired"
    assert turn.lease_token is None
    assert turn.lease_until is None
