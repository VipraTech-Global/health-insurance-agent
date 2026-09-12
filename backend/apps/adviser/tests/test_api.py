import json
import uuid

import pytest
from asgiref.sync import async_to_sync
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser.management.commands.discover_ditto import plan_identity
from apps.adviser.models import (
    AnswerArtifact,
    Conversation,
    CorpusRelease,
    DocumentPage,
    DocumentVersion,
    EvidenceBundle,
    EvidenceBundleSpan,
    EvidenceSpan,
    ExtractionRevision,
    Insurer,
    Message,
    PlanVersion,
    ProfileRevision,
    RecommendationSnapshot,
    SourceBlob,
    Turn,
    TurnAttempt,
    VerifiedFact,
)
from apps.adviser.services import accept_turn
from apps.adviser.source_maps import DocumentValidationError


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create_user(email="pilot@example.com", password="Valid-Pilot-Password-42")


@pytest.fixture
def client(user: User) -> Client:
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(user)
    return browser


def csrf_post(client: Client, path: str, body: dict[str, object]):
    client.get(reverse("csrf"))
    token = client.cookies["csrftoken"].value
    return client.post(
        path, data=json.dumps(body), content_type="application/json", HTTP_X_CSRFTOKEN=token
    )


async def collect_stream(streaming_content) -> bytes:
    return b"".join([chunk async for chunk in streaming_content])


@pytest.mark.django_db
def test_login_requires_csrf(user: User) -> None:
    browser = Client(enforce_csrf_checks=True)
    response = browser.post(
        reverse("login"),
        data=json.dumps({"email": user.email, "password": "Valid-Pilot-Password-42"}),
        content_type="application/json",
    )
    assert response.status_code == 403


def test_plan_identity_rejects_comparisons_and_other_hosts() -> None:
    assert plan_identity("https://joinditto.in/health-insurance/care/care-supreme/") == (
        "care",
        "care-supreme",
    )
    assert plan_identity("https://joinditto.in/health-insurance/compare-plans/a-vs-b/") is None
    assert plan_identity("https://localhost/health-insurance/care/care-supreme/") is None


@pytest.mark.django_db
def test_conversation_is_owner_scoped(client: Client) -> None:
    response = csrf_post(client, reverse("conversations"), {"title": "Family cover"})
    assert response.status_code == 201
    conversation_id = response.json()["id"]
    other = User.objects.create_user(email="other@example.com", password="Other-Password-42")
    other_client = Client()
    other_client.force_login(other)
    forbidden = other_client.get(reverse("conversation-detail", args=[conversation_id]))
    assert forbidden.status_code == 404


@pytest.mark.django_db
def test_profile_revisions_and_stale_write_conflict(client: Client) -> None:
    created = csrf_post(client, reverse("conversations"), {"title": "My cover"}).json()
    path = reverse("conversation-profile", args=[created["id"]])
    updated = client.patch(
        path,
        data=json.dumps({"expected_revision": 1, "patch": {"location": "Bengaluru"}}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    stale = client.patch(
        path,
        data=json.dumps({"expected_revision": 1, "patch": {"budget": "25000"}}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert stale.status_code == 409


@pytest.mark.django_db(transaction=True)
def test_turn_is_idempotent_and_publishes_only_controlled_text(client: Client) -> None:
    created = csrf_post(client, reverse("conversations"), {"title": "Questions"}).json()
    request_id = str(uuid.uuid4())
    path = reverse("stream-turn", args=[created["id"]])
    body = {
        "request_id": request_id,
        "text": "Which plan should I buy?",
        "operation": "chat",
        "expected_profile_revision": 1,
    }
    response = csrf_post(client, path, body)
    assert response.status_code == 200
    chunks = async_to_sync(collect_stream)(response.streaming_content)
    assert b"event: accepted" in chunks
    assert b"event: result" in chunks
    assert Turn.objects.count() == 1
    assert Message.objects.filter(role="user").count() == 1
    assert AnswerArtifact.objects.get().verification_status == "controlled_template"
    assert Conversation.objects.get(id=created["id"]).active_attempt_id is None

    repeated = csrf_post(client, path, body)
    repeated_chunks = async_to_sync(collect_stream)(repeated.streaming_content)
    assert b"event: result" in repeated_chunks
    assert b'"answer":' not in repeated_chunks
    assert Turn.objects.count() == 1
    assert Message.objects.filter(role="user").count() == 1


@pytest.mark.django_db(transaction=True)
def test_running_idempotent_turn_returns_status_without_failure(client: Client) -> None:
    created = csrf_post(client, reverse("conversations"), {"title": "Running"}).json()
    body = {
        "request_id": str(uuid.uuid4()),
        "text": "Keep checking",
        "operation": "chat",
        "expected_profile_revision": 1,
    }
    accept_turn(uuid.UUID(client.session["_auth_user_id"]), uuid.UUID(created["id"]), body)
    response = csrf_post(client, reverse("stream-turn", args=[created["id"]]), body)
    chunks = async_to_sync(collect_stream)(response.streaming_content)
    assert b"event: result" in chunks
    assert b'"status":"accepted"' in chunks
    assert b"event: error" not in chunks


@pytest.mark.django_db
def test_recommendation_fails_closed_without_confirmed_profile(client: Client) -> None:
    created = csrf_post(client, reverse("conversations"), {"title": "Recommendation"}).json()
    conversation = Conversation.objects.get(id=created["id"])
    turn = Turn.objects.create(
        conversation=conversation,
        request_id=uuid.uuid4(),
        payload_hash="a" * 64,
        input_text="Recommend",
        operation="recommend",
        expected_profile_revision=1,
    )
    attempt = TurnAttempt.objects.create(
        turn=turn,
        conversation=conversation,
        status=TurnAttempt.Status.RUNNING,
        profile_revision=1,
        deadline_at=conversation.created_at,
    )
    from apps.adviser.services import publish_controlled_answer

    answer = publish_controlled_answer(client.session["_auth_user_id"], attempt.id)
    assert answer["outcome"] == TurnAttempt.Status.NEEDS_INPUT
    assert answer["claims"] == []


@pytest.mark.django_db
def test_active_pilot_publishes_cited_conditional_option(user: User, monkeypatch) -> None:
    monkeypatch.setattr("apps.adviser.services.validate_evidence_span", lambda _span: None)
    insurer = Insurer.objects.create(name="Care Health Insurance Limited")
    plan = PlanVersion.objects.create(
        insurer=insurer,
        uin="CHIHLIP27061V032627",
        name="Care Supreme",
        variant="Base policy wording",
    )
    blob = SourceBlob.objects.create(
        sha256="1" * 64,
        stored_path="sources/care.pdf",
        byte_size=100,
        media_type="application/pdf",
    )
    document = DocumentVersion.objects.create(
        blob=blob, document_type="policy_wording", identity="Care Supreme"
    )
    extraction = ExtractionRevision.objects.create(
        document_version=document,
        revision=1,
        artifact_sha256="2" * 64,
        source_map_path="extractions/care.json.gz",
        published=True,
    )
    page = DocumentPage.objects.create(
        extraction_revision=extraction,
        physical_index=33,
        width="600",
        height="800",
    )
    span = EvidenceSpan.objects.create(
        page=page,
        region_id="body",
        start_line=15,
        end_line=17,
        source_word_ids=["p33-w1"],
        quote=(
            "excluded until the expiry of 36 months; portability credit applies; declared at "
            "application and accepted by insurer"
        ),
        geometry=[[10, 10, 40, 20]],
    )
    bundle = EvidenceBundle.objects.create(
        label="Care Supreme pre-existing disease waiting period",
        review_state="verified",
    )
    EvidenceBundleSpan.objects.create(bundle=bundle, span=span, role="primary")
    fact = VerifiedFact.objects.create(
        plan_version=plan,
        category="pre_existing_disease_waiting_period",
        value_type="duration",
        value={"months": "36"},
        applicability={
            "portability_credit": True,
            "declaration_and_acceptance_required": True,
        },
        evidence_bundle=bundle,
        verification_state="verified",
    )
    facts = [fact]
    for index, (category, value_type, value, applicability, quote) in enumerate(
        (
            (
                "named_ailment_waiting_period",
                "duration",
                {"months": "24"},
                {"accident_exception": True},
                "24 months; accident",
            ),
            (
                "initial_waiting_period",
                "duration",
                {"days": "30"},
                {"accident_exception": True, "continuous_coverage_condition": True},
                "30 days; continuous coverage",
            ),
            (
                "optional_copayment",
                "structured_text",
                {"optional": True, "amount_source": "policy_schedule"},
                {"only_if_selected": True},
                "co-payment in policy schedule applies to each and every claim",
            ),
        ),
        start=1,
    ):
        extra_span = EvidenceSpan.objects.create(
            page=page,
            region_id="body",
            start_line=17 + index,
            end_line=17 + index,
            source_word_ids=[f"p33-w{index + 1}"],
            quote=quote,
            geometry=[[10, 10 + index, 40, 20 + index]],
        )
        extra_bundle = EvidenceBundle.objects.create(label=category, review_state="verified")
        EvidenceBundleSpan.objects.create(bundle=extra_bundle, span=extra_span, role="primary")
        facts.append(
            VerifiedFact.objects.create(
                plan_version=plan,
                category=category,
                value_type=value_type,
                value=value,
                applicability=applicability,
                evidence_bundle=extra_bundle,
                verification_state="verified",
            )
        )
    release = CorpusRelease.objects.create(
        name="test-release",
        manifest={
            "fact_ids": [str(item.id) for item in facts],
            "extraction_revision_id": str(extraction.id),
        },
        activated_at=timezone.now(),
        is_current=True,
    )
    conversation = Conversation.objects.create(owner=user)
    profile = ProfileRevision.objects.create(
        conversation=conversation,
        revision=1,
        data={"members": "Me (32)"},
        confirmed_at=timezone.now(),
    )
    conversation.current_profile = profile
    conversation.save(update_fields=["current_profile"])
    turn = Turn.objects.create(
        conversation=conversation,
        request_id=uuid.uuid4(),
        payload_hash="a" * 64,
        input_text="Recommend a plan",
        operation="recommend",
        expected_profile_revision=1,
    )
    attempt = TurnAttempt.objects.create(
        turn=turn,
        conversation=conversation,
        status=TurnAttempt.Status.RUNNING,
        profile_revision=1,
        corpus_release=release,
        deadline_at=timezone.now(),
    )

    from apps.adviser.services import publish_controlled_answer

    answer = publish_controlled_answer(user.id, attempt.id)

    assert answer["outcome"] == TurnAttempt.Status.SUCCEEDED
    assert answer["claims"][0]["citations"][0]["page"] == 34
    assert answer["claims"][0]["citations"][0]["quote"] == span.quote
    assert RecommendationSnapshot.objects.get(answer_id=answer["id"]).rankings == []
    assert Message.objects.get(role="assistant").answer_id == uuid.UUID(answer["id"])

    unsupported_turn = Turn.objects.create(
        conversation=conversation,
        request_id=uuid.uuid4(),
        payload_hash="b" * 64,
        input_text="What room rent is covered?",
        operation="policy_question",
        expected_profile_revision=1,
    )
    unsupported_attempt = TurnAttempt.objects.create(
        turn=unsupported_turn,
        conversation=conversation,
        status=TurnAttempt.Status.RUNNING,
        profile_revision=1,
        corpus_release=release,
        deadline_at=timezone.now(),
    )
    unsupported = publish_controlled_answer(user.id, unsupported_attempt.id)
    assert unsupported["outcome"] == TurnAttempt.Status.INSUFFICIENT_EVIDENCE
    assert unsupported["claims"] == []

    def reject_tampered_span(_span) -> None:
        raise DocumentValidationError("Stored evidence span differs from its frozen source map.")

    monkeypatch.setattr("apps.adviser.services.validate_evidence_span", reject_tampered_span)
    tampered_turn = Turn.objects.create(
        conversation=conversation,
        request_id=uuid.uuid4(),
        payload_hash="c" * 64,
        input_text="Recommend a plan",
        operation="recommend",
        expected_profile_revision=1,
    )
    tampered_attempt = TurnAttempt.objects.create(
        turn=tampered_turn,
        conversation=conversation,
        status=TurnAttempt.Status.RUNNING,
        profile_revision=1,
        corpus_release=release,
        deadline_at=timezone.now(),
    )
    tampered = publish_controlled_answer(user.id, tampered_attempt.id)
    assert tampered["outcome"] == TurnAttempt.Status.INSUFFICIENT_EVIDENCE
    assert tampered["claims"] == []

    release.is_current = False
    release.save(update_fields=["is_current"])
    CorpusRelease.objects.create(
        name="new-current-release", manifest={}, activated_at=timezone.now(), is_current=True
    )
    stale_turn = Turn.objects.create(
        conversation=conversation,
        request_id=uuid.uuid4(),
        payload_hash="c" * 64,
        input_text="What is the waiting period?",
        operation="policy_question",
        expected_profile_revision=1,
    )
    stale_attempt = TurnAttempt.objects.create(
        turn=stale_turn,
        conversation=conversation,
        status=TurnAttempt.Status.RUNNING,
        profile_revision=1,
        corpus_release=release,
        deadline_at=timezone.now(),
    )
    from apps.adviser.services import ConflictError

    with pytest.raises(ConflictError, match="corpus changed"):
        publish_controlled_answer(user.id, stale_attempt.id)


@pytest.mark.django_db(transaction=True)
def test_database_rejects_two_active_attempts_for_one_conversation(user: User) -> None:
    conversation = Conversation.objects.create(owner=user)
    first_turn = Turn.objects.create(
        conversation=conversation,
        request_id=uuid.uuid4(),
        payload_hash="a" * 64,
        input_text="first",
    )
    second_turn = Turn.objects.create(
        conversation=conversation,
        request_id=uuid.uuid4(),
        payload_hash="b" * 64,
        input_text="second",
    )
    TurnAttempt.objects.create(
        turn=first_turn,
        conversation=conversation,
        deadline_at=conversation.created_at,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        TurnAttempt.objects.create(
            turn=second_turn,
            conversation=conversation,
            deadline_at=conversation.created_at,
        )
