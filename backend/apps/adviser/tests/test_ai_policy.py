import uuid

import pytest
from django.utils import timezone

from apps.adviser.ai import RelayFailure, StructuredAnswerDraft
from apps.adviser.ai_turns import prepare_turn, publish_ai_answer
from apps.adviser.models import (
    AnswerArtifact,
    CorpusRelease,
    DocumentPage,
    DocumentVersion,
    EvidenceBundle,
    EvidenceBundleSpan,
    EvidenceSpan,
    ExtractionRevision,
    Insurer,
    PlanVersion,
    SourceBlob,
    VerifiedFact,
)
from apps.adviser.services import (
    FACT_APPLICABILITY,
    FACT_REQUIRED_TERMS,
    FACT_TEXT,
    FACT_VALUE_TYPES,
    FACT_VALUES,
    ConflictError,
    accept_turn,
    create_conversation,
    mark_running,
)


@pytest.fixture
def policy_turn(user, qualified, monkeypatch):
    monkeypatch.setattr("apps.adviser.services.validate_evidence_span", lambda _: None)
    insurer = Insurer.objects.create(name="Test insurer")
    plan = PlanVersion.objects.create(insurer=insurer, name="Care Supreme")
    blob = SourceBlob.objects.create(
        sha256="a" * 64, stored_path="test.pdf", byte_size=1, media_type="application/pdf"
    )
    document = DocumentVersion.objects.create(
        blob=blob, document_type="policy_wording", identity="Care Supreme"
    )
    extraction = ExtractionRevision.objects.create(
        document_version=document, revision=1, artifact_sha256="b" * 64, source_map_path="map.gz"
    )
    page = DocumentPage.objects.create(
        extraction_revision=extraction, physical_index=33, width=600, height=800
    )
    facts = []
    for index, category in enumerate(FACT_TEXT):
        bundle = EvidenceBundle.objects.create(label=category, review_state="verified")
        span = EvidenceSpan.objects.create(
            page=page,
            region_id="body",
            start_line=index + 1,
            end_line=index + 1,
            source_word_ids=[f"word-{index}"],
            quote="; ".join(FACT_REQUIRED_TERMS[category]),
            geometry=[[1, 2, 3, 4]],
        )
        EvidenceBundleSpan.objects.create(bundle=bundle, span=span)
        facts.append(
            VerifiedFact.objects.create(
                plan_version=plan,
                category=category,
                value_type=FACT_VALUE_TYPES[category],
                value=FACT_VALUES[category],
                applicability=FACT_APPLICABILITY[category],
                evidence_bundle=bundle,
                verification_state="verified",
            )
        )
    release = CorpusRelease.objects.create(
        name="test",
        manifest={
            "fact_ids": [str(f.id) for f in facts],
            "extraction_revision_id": str(extraction.id),
        },
        activated_at=timezone.now(),
        is_current=True,
    )
    conversation = create_conversation(user.id)
    accepted = accept_turn(
        user.id,
        conversation.id,
        {
            "request_id": str(uuid.uuid4()),
            "text": "Care Supreme pre-existing disease waiting period?",
            "expected_profile_revision": 1,
        },
    )
    mark_running(user.id, uuid.UUID(accepted.attempt_id))
    prepared = prepare_turn(user.id, uuid.UUID(accepted.attempt_id))
    first = facts[0]
    draft = StructuredAnswerDraft.model_validate(
        {
            "outcome": "answer",
            "introduction": "UNVERIFIED INTRODUCTION MUST NOT BE PUBLISHED",
            "follow_up": None,
            "claims": [
                {
                    "claim_id": "ped",
                    "claim_type": "policy_fact",
                    "display_text": FACT_TEXT[first.category],
                    "fact_ids": [str(first.id)],
                    "evidence_bundle_ids": [str(first.evidence_bundle_id)],
                    "conditions": [],
                    "note": None,
                }
            ],
        }
    )
    return prepared, draft, first, release


def test_ai_policy_publishes_only_verified_text_and_resolved_citations(user, policy_turn):
    prepared, draft, fact, _ = policy_turn
    answer = publish_ai_answer(user.id, prepared, draft)
    assert answer["verification_status"] == "ai_validated"
    assert answer["claims"][0]["text"] == FACT_TEXT[fact.category]
    assert answer["claims"][0]["citations"][0]["page"] == 34
    assert "UNVERIFIED" not in str(answer)


@pytest.mark.parametrize(
    "change", ["text", "fact_id", "citation", "review", "corpus", "quote", "geometry"]
)
def test_policy_publication_fails_closed_on_changed_or_fabricated_evidence(
    user, policy_turn, change
):
    prepared, draft, fact, release = policy_turn
    if change == "text":
        draft.claims[0].display_text = "No waiting period."
    elif change == "fact_id":
        draft.claims[0].fact_ids = [str(uuid.uuid4())]
    elif change == "citation":
        draft.claims[0].evidence_bundle_ids = [str(uuid.uuid4())]
    elif change == "review":
        VerifiedFact.objects.filter(id=fact.id).update(verification_state="pending")
    elif change == "corpus":
        CorpusRelease.objects.filter(id=release.id).update(is_current=False)
    elif change == "quote":
        EvidenceSpan.objects.filter(evidencebundle__id=fact.evidence_bundle_id).update(
            quote="Changed source"
        )
    else:
        # Restore the real validator: altered geometry cannot match a frozen source map.
        from unittest.mock import patch

        from apps.adviser.evidence import validate_evidence_span

        with patch("apps.adviser.services.validate_evidence_span", validate_evidence_span):
            with pytest.raises(ConflictError):
                publish_ai_answer(user.id, prepared, draft)
        return
    with pytest.raises((ConflictError, RelayFailure)):
        publish_ai_answer(user.id, prepared, draft)
    assert not AnswerArtifact.objects.exists()
