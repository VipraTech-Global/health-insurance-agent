from dataclasses import replace
from datetime import UTC
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from research_workspace.legacy_v2.evidence_retrieval import (
    BM25,
    RawChunk,
    pack,
    raw_chunks,
    retrieve_plan,
    token_count,
)
from research_workspace.legacy_v2.processing.cited_facts import carrier_fact, fact_carrier
from research_workspace.legacy_v2.source_answers import (
    SourceAnswer,
    needs_source_retrieval,
    question_criterion,
    source_problems,
)

from apps.adviser_v2.tests.test_cited_facts import PAGE_ID, POLICY_ID, reviewed, sample


def chunk(key, text, policy=POLICY_ID):
    return RawChunk(key, policy, "document", text, token_count(text), ())


def test_raw_chunks_preserve_unicode_page_and_document_offsets():
    first = "Clause ₹5,00,000/- café.\n" * 310
    second = "Page two.\n" + ("Insuredtheexclusionshallapplyafresh\n" * 200)
    pages = [
        dict(
            document_version_id="doc",
            document_key="wording",
            physical_page=i,
            evidence_span_id=str(i),
            passage=text,
            document_char_start=offset,
        )
        for i, text, offset in [(1, first, 0), (2, second, len(first) + 1)]
    ]
    chunks = raw_chunks(POLICY_ID, pages)
    whole = first + "\f" + second
    covered = {str(i): set() for i in (1, 2)}
    for c in chunks:
        assert c.text in whole
        assert c.tokens == token_count(c.text)
        for segment in c.segments:
            page = pages[segment["page"] - 1]
            assert segment["text"] == page["passage"][segment["start"] : segment["end"]]
            assert segment["text"] == whole[segment["document_start"] : segment["document_end"]]
            covered[segment["page_span_id"]].update(range(segment["start"], segment["end"]))
    assert all(covered[p["evidence_span_id"]] == set(range(len(p["passage"]))) for p in pages)


def test_okapi_ranking_uses_term_frequency_length_and_document_frequency():
    documents = [
        chunk("a", "ambulance cover"),
        chunk("b", "ambulance " + "other " * 200),
        chunk("c", "room cover"),
    ]
    assert [c.id for c in BM25(documents).rank("ambulance")] == ["a", "b", "c"]
    assert BM25(documents).rank("room")[0].id == "c"


def test_budget_keeps_whole_chunks_and_reports_every_omission():
    documents = [chunk(str(i), "unchanged evidence " * (i + 1)) for i in range(5)]
    budget = documents[0].tokens + documents[1].tokens
    packet = pack(POLICY_ID, documents, budget=budget, method="bm25")
    assert packet.chunks == tuple(documents[:2])
    assert packet.tokens <= budget
    assert packet.omitted_chunks == 3
    with pytest.raises(ValueError, match="Wrong-plan"):
        pack(
            POLICY_ID,
            documents + [chunk("foreign", "text", "different")],
            budget=budget,
            method="bm25",
        )


def test_bm25_never_checks_dense_qualification(monkeypatch, settings):
    settings.COVERGUIDE_EVIDENCE_RETRIEVAL = "bm25"
    monkeypatch.setattr(
        "research_workspace.legacy_v2.embedding.qualified_embedding_status",
        lambda: pytest.fail("BM25 called dense qualification"),
    )
    monkeypatch.setattr(
        "research_workspace.legacy_v2.evidence_retrieval.plan_chunks",
        lambda p: [chunk(p, "ambulance cover", p)],
    )
    assert retrieve_plan("ambulance", POLICY_ID).chunks


def test_release_retrieval_passes_only_question_and_equal_budget_per_plan(monkeypatch, settings):
    from research_workspace.legacy_v2.retrieval import retrieve_policy_context

    query = MagicMock()
    query.values_list.return_value = ["one", "two", "three"]
    monkeypatch.setattr(
        "apps.adviser_v2.models.KnowledgeReleaseFact.objects.filter", lambda **kw: query
    )
    calls = []

    def search(question, policy, *, budget):
        calls.append((question, policy, budget))
        return pack(policy, [], budget=budget, method="bm25")

    monkeypatch.setattr("research_workspace.legacy_v2.evidence_retrieval.retrieve_plan", search)
    settings.COVERGUIDE_EVIDENCE_TOKEN_BUDGET = 16000
    result = retrieve_policy_context("Is ambulance covered?", SimpleNamespace(id="release"))
    assert len(result.packets) == 3
    assert calls == [("Is ambulance covered?", p, 16000) for p in ["one", "three", "two"]]


@pytest.mark.parametrize(
    ("question", "intent", "expected"),
    [
        ("Compare the three plans", "product_comparison", False),
        ("What room category is allowed?", "coverage_question", False),
        ("Is AYUSH covered?", "coverage_question", True),
        ("How about ambulance cover for this family?", "coverage_question", True),
        ("Does my family have psychiatric treatment cover?", "coverage_question", True),
        ("What family size does the floater allow?", "coverage_question", False),
        ("Does it cover something else?", "coverage_question", True),
    ],
)
def test_prepared_questions_do_not_retrieve(question, intent, expected):
    assert needs_source_retrieval(question, intent) is expected


def source_fixture(monkeypatch):
    _, result, pages = sample()
    criterion = question_criterion("How many children?")
    result.rules = [fact_carrier(criterion, carrier_fact(result.rules[0]))]
    review = reviewed(criterion, result)
    start = pages[0]["passage"].index("A maximum")
    end = start + len(carrier_fact(result.rules[0]).citations[0].quote)
    c = replace(
        chunk("c", pages[0]["passage"]),
        segments=({"page_span_id": PAGE_ID, "start": start, "end": end},),
    )
    packet = pack(POLICY_ID, [c], budget=16000, method="bm25")
    monkeypatch.setattr(
        "research_workspace.legacy_v2.source_answers.packet_pages", lambda packet: pages
    )
    return SourceAnswer(packet, criterion, result, result, review, None)


def test_source_answer_quotes_cannot_escape_retrieved_segments(monkeypatch):
    answer = source_fixture(monkeypatch)
    assert source_problems(answer) == []
    c = answer.packet.chunks[0]
    smaller = replace(c, segments=({**c.segments[0], "end": c.segments[0]["end"] - 1},))
    answer = replace(answer, packet=replace(answer.packet, chunks=(smaller,)))
    assert "outside the retrieved" in "; ".join(source_problems(answer))


def test_source_answer_material_review_failure_and_changed_value_block(monkeypatch):
    answer = source_fixture(monkeypatch)
    answer.review.reviews[0].material_issue = "missing_material_condition: only dependent children"
    assert source_problems(answer)
    answer = source_fixture(monkeypatch)
    altered = answer.extraction.model_copy(deep=True)
    fact = carrier_fact(altered.rules[0])
    fact.value = "Changed statement"
    altered.rules = [fact_carrier(answer.criterion, fact)]
    assert "differs" in "; ".join(source_problems(replace(answer, extraction=altered)))


def test_free_answer_serializes_profile_dates_without_polluting_retrieval(monkeypatch):
    import json
    from datetime import datetime

    from research_workspace.legacy_v2.source_answers import answer_question

    expected = source_fixture(monkeypatch)
    calls = []

    def relay(turn, **kwargs):
        calls.append(kwargs)
        return expected.extraction if len(calls) == 1 else expected.review

    monkeypatch.setattr("research_workspace.legacy_v2.source_answers._relay", relay)
    monkeypatch.setattr(
        "research_workspace.legacy_v2.source_answers._source_statement", lambda *args: {}
    )
    answer = answer_question(
        None,
        "How many children?",
        {"updated_at": datetime(2026, 1, 1, tzinfo=UTC)},
        expected.packet,
    )
    assert answer.unknown_reason is None
    payload = json.loads(calls[0]["messages"][-1]["content"])
    assert payload["customer_profile"]["updated_at"].startswith("2026-01-01")
    assert "updated_at" not in calls[0]["messages"][1]["content"]


def test_neutral_language_is_checked_before_the_corrective_retry(monkeypatch):
    answer = source_fixture(monkeypatch)
    candidate = answer.extraction.model_copy(deep=True)
    fact = carrier_fact(candidate.rules[0])
    fact.value = "This is the best policy."
    candidate.rules = [fact_carrier(answer.criterion, fact)]
    answer = replace(
        answer,
        extraction=candidate,
        reviewed_extraction=candidate,
        review=reviewed(answer.criterion, candidate),
    )
    assert "Neutral wording check" in "; ".join(source_problems(answer))


def test_unlisted_numeric_claim_in_answer_prose_is_rejected(monkeypatch):
    answer = source_fixture(monkeypatch)
    candidate = answer.extraction.model_copy(deep=True)
    fact = carrier_fact(candidate.rules[0])
    fact.value += " Cover is INR 5000."
    candidate.rules = [fact_carrier(answer.criterion, fact)]
    answer = replace(
        answer,
        extraction=candidate,
        reviewed_extraction=candidate,
        review=reviewed(answer.criterion, candidate),
    )
    assert "unsupported money" in "; ".join(source_problems(answer))


def test_relay_timeouts_retry_separately_from_validation(monkeypatch):
    from datetime import timedelta

    from django.utils import timezone
    from research_workspace.legacy_relay import RelayFailure
    from research_workspace.legacy_v2.source_answers import _relay

    _, result, _ = sample()
    attempts = []

    def call(**kwargs):
        attempts.append(kwargs)
        if len(attempts) < 3:
            raise RelayFailure("provider_timeout", "HTTP 408")
        return result

    monkeypatch.setattr("research_workspace.legacy_v2.source_answers.call_model", call)
    monkeypatch.setattr(
        "research_workspace.legacy_v2.source_answers.request_bytes_with_headroom",
        lambda *args: None,
    )
    turn = SimpleNamespace(deadline=timezone.now() + timedelta(seconds=900))
    actual = _relay(
        turn,
        model="test",
        schema_name="policy_extraction",
        output_type=type(result),
        messages=[],
        effort="low",
    )
    assert actual == result
    assert len(attempts) == 3


def test_invalid_source_answer_gets_only_one_corrective_attempt(monkeypatch):
    from research_workspace.legacy_v2.source_answers import answer_question

    expected = source_fixture(monkeypatch)
    invalid = expected.extraction.model_copy(deep=True)
    fact = carrier_fact(invalid.rules[0])
    fact.citations[0].quote = "A sentence absent from the source."
    invalid.rules = [fact_carrier(expected.criterion, fact)]
    attempts = []

    def relay(*args, **kwargs):
        attempts.append(kwargs)
        return invalid

    monkeypatch.setattr("research_workspace.legacy_v2.source_answers._relay", relay)
    answer = answer_question(None, "How many children?", {}, expected.packet)
    assert answer.extraction is None
    assert "after validation" in answer.unknown_reason
    assert len(attempts) == 2
