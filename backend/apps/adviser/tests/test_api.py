import json
import uuid

import pytest
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser.management.commands.discover_ditto import plan_identity
from apps.adviser.models import (
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
from apps.adviser.source_maps import DocumentValidationError


@pytest.fixture
def user(db: None) -> User:
    return User.objects.create_user(email="pilot@example.com", password="Valid-Pilot-Password-42")


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
def test_v1_adviser_routes_are_retired_while_auth_remains(user: User) -> None:
    browser = Client()
    browser.force_login(user)
    identifier = uuid.uuid4()
    retired_paths = (
        "/api/v1/conversations/",
        f"/api/v1/conversations/{identifier}/",
        f"/api/v1/conversations/{identifier}/profile/",
        f"/api/v1/conversations/{identifier}/turns/",
        f"/api/v1/recommendations/{identifier}/",
        "/api/v1/ai/models/",
        "/api/v1/ai/preferences/",
        "/api/v1/admin/ai-relay/",
        "/api/v1/admin/ai-relay/accounts/",
        "/api/v1/admin/ai-relay/qualifications/",
    )

    assert browser.get("/api/v1/auth/csrf/").status_code == 200
    assert all(browser.get(path).status_code == 404 for path in retired_paths)


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
