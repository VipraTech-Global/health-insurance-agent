import json
from copy import deepcopy

import pytest

from apps.adviser_v2.processing.cited_fact_pipeline import _messages
from apps.adviser_v2.processing.cited_facts import (
    CitedFact,
    Clause,
    clause_offsets,
    fact_carrier,
    fact_problems,
    recover_fact_encoding,
    review_disposition,
)
from apps.adviser_v2.processing.clause_citations import clause_rectangles
from apps.adviser_v2.processing.criterion_evidence import CRITERIA
from apps.adviser_v2.schemas import PolicyRuleExtractionV1, PolicyRuleReviewV1, ReviewedPolicyRule

PAGE_ID = "11111111-1111-4111-8111-111111111111"
POLICY_ID = "22222222-2222-4222-8222-222222222222"


def sample(key="family_floater"):
    criterion = next(c for c in CRITERIA if c.key == key)
    quote = "A maximum of three dependent children are covered."
    fact = CitedFact(value=quote, value_kind="category" if key == "room_category" else "text",
        conditions=[], citations=[Clause(page_span_id=PAGE_ID, quote=quote)],
        quantities=[{"value": "3", "unit": "count", "citation_indexes": [0]}], notes=[])
    result = PolicyRuleExtractionV1(schema_version=1, policy_version_id=POLICY_ID,
        rules=[fact_carrier(criterion, fact)], material_issues=[], omitted_inventory_categories=[])
    pages = [{"evidence_span_id": PAGE_ID, "passage": "Header\n" + quote + "\nOther terms."}]
    return criterion, result, pages


def reviewed(criterion, result, verdict="agree", reason=None):
    rule = result.rules[0]
    return PolicyRuleReviewV1(schema_version=1, policy_version_id=POLICY_ID,
        inventory_categories=[criterion.category], missing_rules=[], reviews=[ReviewedPolicyRule(
            rule_key=rule.rule_key, verdict=verdict, independent_body=rule.body,
            evidence_span_ids=[PAGE_ID], material_issue=reason)])


def test_number_words_and_exact_clause_offsets():
    criterion, result, pages = sample()
    assert fact_problems(POLICY_ID, criterion, result, pages) == []
    text = pages[0]["passage"]
    clause = Clause(page_span_id=PAGE_ID, quote="three dependent children")
    start, end = clause_offsets(clause, text)
    assert 0 < start < end < len(text)
    assert text[start:end] == clause.quote
    with pytest.raises(ValueError, match="word for word"):
        clause_offsets(Clause(page_span_id=PAGE_ID, quote="3 dependent children"), text)
    with pytest.raises(ValueError, match="entire page"):
        clause_offsets(Clause(page_span_id=PAGE_ID, quote=text), text)


@pytest.mark.parametrize("reason", ["wrong_value", "wrong_section", "missing_material_condition", "wrong_variant"])
def test_material_source_failures_block_even_an_agree_verdict(reason):
    criterion, result, _pages = sample()
    blockers, _notes = review_disposition(reviewed(criterion, result, reason=reason + ": source differs"), result, criterion)
    assert blockers


@pytest.mark.parametrize("reason", ["underwriting", "other_terms", "day_boundary", "rule_not_executable"])
def test_rule_encoding_and_nonmaterial_notes_do_not_make_fact_unknown(reason):
    criterion, result, _pages = sample()
    blockers, notes = review_disposition(reviewed(criterion, result, "disagree", reason + ": observation"), result, criterion)
    assert not blockers
    assert notes == [reason + ": observation"]


def test_review_cannot_skip_evidence_or_change_the_agreed_fact():
    criterion, result, _pages = sample()
    review = reviewed(criterion, result)
    review.reviews[0].evidence_span_ids = []
    assert review_disposition(review, result, criterion)[0]
    review = reviewed(criterion, result)
    review.reviews[0].independent_body = None
    assert review_disposition(review, result, criterion)[0]


def test_room_category_does_not_need_a_money_amount():
    criterion, result, pages = sample("room_category")
    fact = json.loads(result.rules[0].body["effects"][0]["value"]["value"]["value"])
    fact.update(value="Single private A/C room", quantities=[])
    result.rules[0] = fact_carrier(criterion, CitedFact.model_validate(fact))
    assert fact_problems(POLICY_ID, criterion, result, pages) == []


def test_wrong_page_and_unsupported_number_are_rejected():
    criterion, result, pages = sample()
    pages[0]["passage"] = "Only two dependent children are covered."
    assert fact_problems(POLICY_ID, criterion, result, pages)
    criterion, result, pages = sample()
    fact = json.loads(result.rules[0].body["effects"][0]["value"]["value"]["value"])
    fact["quantities"][0]["value"] = "4"
    result.rules[0] = fact_carrier(criterion, CitedFact.model_validate(fact))
    assert "numeric support" in " ".join(fact_problems(POLICY_ID, criterion, result, pages))


def test_fact_prompts_keep_bundle_prefix_identical(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr("apps.adviser_v2.processing.stages._selected_variant_name", lambda _v: "base")
    version = SimpleNamespace(id=POLICY_ID, uin="test")
    _, result, pages = sample()
    for candidate in (None, result):
        first = _messages(version, pages, CRITERIA[0], candidate=candidate)
        second = _messages(version, pages, CRITERIA[1], candidate=candidate, feedback="retry")
        assert first[:2] == second[:2]
        assert pages[0]["passage"] in first[1]["content"].replace("\\n", "\n")
        assert second[-1]["content"] == "retry"


def test_clause_geometry_highlights_only_selected_characters():
    chars = tuple({"text": c, "x0": i * 5, "x1": (i + 1) * 5, "top": 10, "bottom": 20} for i, c in enumerate("Before three after"))
    assert clause_rectangles(chars, "three") == [[35.0, 10.0, 60.0, 20.0]]
    with pytest.raises(ValueError, match="geometry"):
        clause_rectangles(chars, "four")


def test_fact_review_does_not_mutate_model_outputs():
    criterion, result, _pages = sample()
    review = reviewed(criterion, result, "disagree", "rule_not_executable: categorical value")
    before = deepcopy(review.model_dump())
    assert not review_disposition(review, result, criterion)[0]
    assert review.model_dump() == before


def test_intact_fact_survives_invalid_rule_wrapper_without_repairing_source():
    criterion, result, pages = sample()
    body = deepcopy(result.rules[0].body)
    body["scope"] = body["effects"][0].pop("scope")
    diagnostics = [{"loc": ["rules", 0, "body"], "input": json.dumps(body)}]
    fact = recover_fact_encoding(criterion, diagnostics)
    assert fact is not None
    result.rules[0] = fact_carrier(criterion, fact)
    assert fact_problems(POLICY_ID, criterion, result, pages) == []
    assert recover_fact_encoding(criterion, [{"loc": ["policy_version_id"], "input": body}]) is None
    assert recover_fact_encoding(criterion, [{"loc": ["rules", 0, "body"], "input": "broken JSON"}]) is None
