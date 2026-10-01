import json
from copy import deepcopy

import pytest

from apps.adviser_v2.processing.cited_fact_pipeline import _messages
from apps.adviser_v2.processing.cited_facts import (
    CitedFact,
    Clause,
    anchor_transcribed_quotes,
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


def test_frequency_words_have_numeric_support():
    from decimal import Decimal

    from apps.adviser_v2.processing.criterion_evidence import quoted_quantities

    assert quoted_quantities("Restored once during the policy period.")["count"] == {Decimal(1)}
    assert quoted_quantities("A maximum of three dependent children.")["count"] == {Decimal(3)}


def test_line_wrapping_restores_raw_substring_but_never_changes_words():
    criterion, result, pages = sample()
    pages[0]["passage"] = pages[0]["passage"].replace("three dependent", "three\ndependent")
    unchanged = deepcopy(result.model_dump())
    anchored, changes = anchor_transcribed_quotes(criterion, result, pages)
    assert len(changes) == 1
    assert "three\ndependent" in changes[0]["raw_quote"]
    assert fact_problems(POLICY_ID, criterion, anchored, pages) == []
    assert result.model_dump() == unchanged
    pages[0]["passage"] = pages[0]["passage"].replace("three\ndependent", "two\ndependent")
    rejected, changes = anchor_transcribed_quotes(criterion, result, pages)
    assert changes == []
    assert fact_problems(POLICY_ID, criterion, rejected, pages)


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
    blockers, notes = review_disposition(review, result, criterion)
    assert not blockers
    assert notes[0].startswith("rule_not_executable:")


def test_review_agreement_compares_fact_content_not_json_spacing():
    criterion, result, _pages = sample()
    review = reviewed(criterion, result)
    body = deepcopy(review.reviews[0].independent_body)
    literal = body["effects"][0]["value"]["value"]
    fact = json.loads(literal["value"])
    literal["value"] = json.dumps(fact, indent=2)
    review.reviews[0].independent_body = body
    assert not review_disposition(review, result, criterion)[0]
    fact["value"] = "A materially different value"
    literal["value"] = json.dumps(fact)
    assert review_disposition(review, result, criterion)[0][0].startswith("wrong_value:")


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


def test_live_orchestration_reuses_accepted_criteria_and_forces_only_required_prospectuses(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from apps.adviser_v2.processing import cited_fact_pipeline as pipeline
    from apps.adviser_v2.processing.criterion_attempts import new_criterion_state
    from apps.adviser_v2.processing.criterion_evidence import PROGRESS_KEY

    version = SimpleNamespace(id=POLICY_ID, uin="test")
    _criterion, _result, core = sample()
    core[0]["document_role"] = "base_wording"
    full = core + [{"evidence_span_id": "33333333-3333-4333-8333-333333333333", "passage": "Prospectus", "document_role": "prospectus"}]
    progress = {"criteria": {}}
    for key in ("deductible", "portability", "geography"):
        _c, accepted, _p = sample(key)
        state = new_criterion_state()
        state.update(complete=True, result=accepted.model_dump(mode="json"), review_complete=True)
        progress["criteria"][key] = state
    monkeypatch.setattr(pipeline, "_progress", lambda *_a: progress)
    monkeypatch.setattr(pipeline, "_checkpoint", lambda *_a: None)
    monkeypatch.setattr(pipeline, "ModelAttempt", MagicMock())
    monkeypatch.setattr(pipeline, "raw_bundle_passages", lambda _v, include_prospectus=False: full if include_prospectus else core)
    monkeypatch.setattr("apps.adviser_v2.processing.stages._policy_version", lambda _j: version)
    monkeypatch.setattr("apps.adviser_v2.processing.stages._selected_variant_name", lambda _v: "base")
    monkeypatch.setattr("apps.adviser_v2.processing.stages._renew_rule_lease", lambda _j: None)
    calls = []

    def invoke(**kwargs):
        key = kwargs["messages"][2]["content"].split(":", 1)[0].removeprefix("Criterion ")
        calls.append((key, "Prospectus" in kwargs["messages"][1]["content"]))
        return sample(key)[1]

    monkeypatch.setattr(pipeline, "call_model", invoke)
    result = pipeline.run_criterion_extraction(SimpleNamespace())
    assert len(calls) == 10
    assert {key for key, supplied in calls if supplied} == {"sum_insured", "eligibility"}
    assert not {"deductible", "portability", "geography"}.intersection(key for key, _ in calls)
    assert len(result[PROGRESS_KEY]["criteria"]) == 13


def test_supported_facts_do_not_require_executable_rule_ids_and_stop_before_indexing(monkeypatch):
    from types import SimpleNamespace

    from apps.adviser_v2.processing import cited_fact_pipeline as pipeline
    from apps.adviser_v2.processing.criterion_evidence import PROGRESS_KEY

    _criterion, _result, pages = sample()
    pages[0].update(document_key="wording", document_version_id="document")
    progress = {"criteria": {}, "prior_validation_id": None}
    for criterion in CRITERIA:
        _c, result, _p = sample(criterion.key)
        progress["criteria"][criterion.key] = {
            "result": result.model_dump(mode="json"), "review_blockers": [],
            "prospectus_used": False, "review_notes": [],
        }
    monkeypatch.setattr(pipeline, "read_artifact", lambda _j: {PROGRESS_KEY: progress})
    monkeypatch.setattr(pipeline, "raw_bundle_passages", lambda *_a, **_kw: pages)
    monkeypatch.setattr("apps.adviser_v2.processing.stages._policy_version", lambda _j: SimpleNamespace(id=POLICY_ID))
    monkeypatch.setattr(pipeline, "store_clause", lambda c, _p: SimpleNamespace(
        id=PAGE_ID, page=SimpleNamespace(page_number=1), quote=c.quote, context={}, locator={}))
    from unittest.mock import MagicMock

    monkeypatch.setattr(pipeline, "ModelAttempt", MagicMock())
    result = pipeline.validate_facts(SimpleNamespace(parent_job=None, source_capture=None))
    assert result["criterion_count"] == 13
    assert result["unresolved_criterion_count"] == 0
    assert all(c["status"] == "supported" and c["rule_status"] == "rule not executable" for c in result["criteria"])
    assert result["verified_rule_ids"] == []
    assert result["budget"]["status"] == "unavailable"
    assert result["no_copay"]["status"] == "unknown"  # No ratio was quoted; not in the 13.
    assert result["review_checkpoint_only"] and not result["index_pending"]
    for state in list(progress["criteria"].values())[:7]:
        state["review_blockers"] = ["missing_material_condition: continuous coverage"]
    blocked = pipeline.validate_facts(SimpleNamespace(parent_job=None, source_capture=None))
    assert blocked["unresolved_criterion_count"] == 7
    assert blocked["issues"][0]["code"] == "criterion_stop_threshold"


def test_genuine_source_unknown_does_not_trigger_an_extraction_correction(monkeypatch):
    from types import SimpleNamespace

    from apps.adviser_v2.processing import cited_fact_pipeline as pipeline
    from apps.adviser_v2.processing.criterion_attempts import new_criterion_state, unknown_result
    from apps.adviser_v2.processing.criterion_evidence import PROGRESS_KEY

    progress = {"criteria": {c.key: {"review_complete": True} for c in CRITERIA}}
    state = new_criterion_state()
    state.update(complete=True, validation_attempts=1,
        result=unknown_result(POLICY_ID, CRITERIA[0], "No available-purchase choices are stated.").model_dump(mode="json"))
    progress["criteria"]["sum_insured"] = state
    monkeypatch.setattr(pipeline, "read_artifact", lambda _j: {PROGRESS_KEY: progress})
    monkeypatch.setattr(pipeline, "raw_bundle_passages", lambda _v: [])
    monkeypatch.setattr(pipeline, "_checkpoint", lambda *_a: None)
    monkeypatch.setattr("apps.adviser_v2.processing.stages._policy_version", lambda _j: SimpleNamespace(id=POLICY_ID))
    pipeline.run_criterion_review(SimpleNamespace(parent_job=None))
    assert state["complete"]
    assert state["validation_attempts"] == 1
    assert "No available-purchase choices" in state["review_blockers"][0]


def test_indian_table_cells_and_separate_labels_keep_exact_quotes():
    from apps.adviser_v2.processing.criterion_evidence import quoted_quantities

    criterion, result, pages = sample('maternity')
    labels = 'Normal\nDelivery\nRs.'
    row = '5,00,000/- 15,000/- 20,000/- 1,00,000/-'
    fact = CitedFact(value='At Rs.5 lakh sum insured, normal delivery has a Rs.15,000 limit.',
        value_kind='text', conditions=[], notes=[],
        citations=[Clause(page_span_id=PAGE_ID, quote=labels), Clause(page_span_id=PAGE_ID, quote=row)],
        table_regions=[{'citation_indexes': [0, 1], 'label_indexes': [0]}],
        quantities=[{'value': '15000', 'unit': 'money', 'citation_indexes': [0, 1]}])
    result.rules = [fact_carrier(criterion, fact)]
    pages[0]['passage'] = 'Delivery table\n' + labels + '\n' + row + '\nOther terms'
    assert not fact_problems(POLICY_ID, criterion, result, pages)
    assert 15000 in quoted_quantities('15,000/-')['money']
    assert 15000 in quoted_quantities('Rs.15,000')['money']
    assert 15000 not in quoted_quantities('15,000')['money']
    # Rewriting the row is never allowed, even when the amount is correct.
    fact.citations[1].quote = 'Normal delivery Rs.15,000 for Rs.5,00,000 sum insured'
    result.rules = [fact_carrier(criterion, fact)]
    assert fact_problems(POLICY_ID, criterion, result, pages)


def test_table_units_cannot_be_borrowed_from_other_pages_or_distant_sections():
    criterion, result, pages = sample('maternity')
    fact = CitedFact(value='Limit Rs.15000', value_kind='text', conditions=[], notes=[],
        citations=[Clause(page_span_id=PAGE_ID, quote='Limit Rs.'), Clause(page_span_id=PAGE_ID, quote='15,000')],
        table_regions=[{'citation_indexes': [0, 1], 'label_indexes': [0]}],
        quantities=[{'value': '15000', 'unit': 'money', 'citation_indexes': [0, 1]}])
    result.rules = [fact_carrier(criterion, fact)]
    pages[0]['passage'] = 'Header Limit Rs.\n15,000 Footer'
    assert not fact_problems(POLICY_ID, criterion, result, pages)
    pages[0]['passage'] = 'Limit Rs.' + 'x' * 3500 + '15,000'
    assert 'local table region' in ' '.join(fact_problems(POLICY_ID, criterion, result, pages))
    fact.citations[1].page_span_id = '33333333-3333-4333-8333-333333333333'
    pages.append({'evidence_span_id': fact.citations[1].page_span_id, 'passage': 'Header 15,000 Footer'})
    result.rules = [fact_carrier(criterion, fact)]
    assert 'different pages' in ' '.join(fact_problems(POLICY_ID, criterion, result, pages))


def test_secondary_condition_failure_drops_only_that_statement():
    from apps.adviser_v2.processing.cited_facts import carrier_fact, omit_secondary_statements

    criterion, result, _pages = sample('ped_waiting_period')
    fact = carrier_fact(result.rules[0])
    fact.value = '36 months continuous coverage; the longer waiting period applies on overlap.'
    data = fact.model_dump()
    data['secondary_statements'] = [
        {'text': 'There is no coverage during grace periods.', 'citation_indexes': [0], 'conditions': []}
    ]
    fact = CitedFact.model_validate(data)
    result.rules = [fact_carrier(criterion, fact)]
    review = reviewed(criterion, result, reason='drop_secondary: {"indexes":[0],"reason":"Missing instalment exception"}')
    assert not review_disposition(review, result, criterion)[0]
    projected = carrier_fact(omit_secondary_statements(review, result, criterion).rules[0])
    assert projected.value == fact.value
    assert not projected.secondary_statements
    assert 'omitted' in projected.notes[0]
    assert carrier_fact(result.rules[0]).secondary_statements  # Audit output untouched.
    review.reviews[0].material_issue = 'drop_secondary: {"indexes":[3]}'
    assert review_disposition(review, result, criterion)[0]
    review.reviews[0].material_issue = 'missing_material_condition: no continuity condition on core wait'
    assert review_disposition(review, result, criterion)[0]


def test_approved_rerun_resets_only_six_and_archives_pipeline_bug_attempts():
    from apps.adviser_v2.processing.cited_fact_pipeline import apply_approved_rerun
    from apps.adviser_v2.processing.criterion_attempts import new_criterion_state

    progress = {'policy_version_id': POLICY_ID, 'core_evidence_sha256': 'hash', 'criteria': {}}
    for c in CRITERIA:
        state = new_criterion_state()
        state.update(complete=True, validation_attempts=2, attempt_ids=['old-first', 'old-correction'])
        progress['criteria'][c.key] = state
    before = deepcopy(progress)
    affected = ['sum_insured', 'ped_waiting_period', 'maternity', 'newborn', 'family_floater', 'eligibility']
    authorization = {'id': 'user-approved', 'policy_version_id': POLICY_ID, 'core_evidence_sha256': 'hash',
        'criteria': {k: {'instruction': 'Fix table quotes'} for k in affected}}
    authorization['criteria']['sum_insured'].update(include_prospectus=True, pipeline_bug_attempt_ids=['old-first'])
    apply_approved_rerun(progress, authorization)
    for key, state in progress['criteria'].items():
        if key in affected:
            assert state['validation_attempts'] == 0
            assert state['prior_runs'][0] == before['criteria'][key]
        else:
            assert state == before['criteria'][key]
    assert progress['criteria']['sum_insured']['prospectus_used']
    assert progress['criteria']['sum_insured']['excluded_pipeline_bug_attempt_ids'] == ['old-first']
    once = deepcopy(progress)
    apply_approved_rerun(progress, authorization)
    assert progress == once


def test_long_v2_error_is_retained_in_artifact_but_issue_summary_fits_contract():
    from apps.adviser_v2.contracts import validate_contract
    from apps.adviser_v2.pipeline import _material_issues
    from apps.adviser_v2.processing.criterion_evidence import PROGRESS_KEY

    result = {'material_issues': ['A' * 20000], PROGRESS_KEY: {'protocol': 'cited-fact'}}
    issues = _material_issues(result, 'extract')
    validate_contract('ProcessingIssuesV1', issues)
    assert 'Full diagnostic retained' in issues[0]['description']
    assert len(result['material_issues'][0]) == 20000


def test_our_old_wrapper_exception_does_not_consume_a_corrective_attempt():
    from apps.adviser_v2.processing.cited_fact_pipeline import resume_pipeline_failure
    from apps.adviser_v2.processing.criterion_attempts import new_criterion_state, unknown_result

    state = new_criterion_state()
    state.update(complete=True, schema_diagnostics=[{'retained': 'public response'}],
        result=unknown_result(POLICY_ID, CRITERIA[0], 'Complete extraction request validation failed: local wrapper error').model_dump(mode='json'))
    before = deepcopy(state)
    resume_pipeline_failure(state)
    assert not state['complete'] and state['result'] is None
    assert state['validation_attempts'] == 0
    assert state['pipeline_failure_resumed']['prior_result'] == before['result']
    counted_model_failure = deepcopy(before)
    counted_model_failure['validation_attempts'] = 2
    resume_pipeline_failure(counted_model_failure)
    assert counted_model_failure['complete']
    assert 'pipeline_failure_resumed' not in counted_model_failure


def test_family_table_counts_need_the_exact_abbreviation_legend():
    from apps.adviser_v2.processing.criterion_evidence import quoted_quantities

    assert quoted_quantities('2A+3C')['count'] == set()
    assert quoted_quantities('2A+3C A-Adult | C-Child')['count'] == {2, 3}
    criterion, result, pages = sample('family_floater')
    fact = CitedFact(value='Two adults and three children.', value_kind='text', conditions=[], notes=[],
        citations=[Clause(page_span_id=PAGE_ID, quote='2A+3C'), Clause(page_span_id=PAGE_ID, quote='A-Adult | C-Child')],
        table_regions=[{'citation_indexes': [0, 1], 'label_indexes': [1]}],
        quantities=[{'value': '2', 'unit': 'count', 'citation_indexes': [0, 1]},
                    {'value': '3', 'unit': 'count', 'citation_indexes': [0, 1]}])
    result.rules = [fact_carrier(criterion, fact)]
    pages[0]['passage'] = 'Plan type\n2A+3C\nA-Adult | C-Child\nOther terms'
    assert not fact_problems(POLICY_ID, criterion, result, pages)
    fact.table_regions = []
    result.rules = [fact_carrier(criterion, fact)]
    assert fact_problems(POLICY_ID, criterion, result, pages)


def test_secondary_projection_only_deletes_complete_retained_assertions():
    from apps.adviser_v2.processing.cited_facts import carrier_fact
    from apps.adviser_v2.processing.fact_projection import fact_digest, primary_projection

    criterion, result, pages = sample('maternity')
    fact = carrier_fact(result.rules[0])
    fact.value = 'Delivery has a stated limit. Newborn coverage is also discussed.'
    selection = {'source_fact_sha256': fact_digest(fact), 'value_sentence_indexes': [0],
        'condition_indexes': [], 'quantity_indexes': [0], 'citation_indexes': [0],
        'reason': 'Keep newborn statements in the separate criterion.'}
    projected = primary_projection(fact, selection)
    assert projected.value == 'Delivery has a stated limit.'
    assert projected.citations == fact.citations
    assert projected.quantities == fact.quantities
    assert fact.value.endswith('Newborn coverage is also discussed.')
    with pytest.raises(ValueError, match='complete core'):
        primary_projection(fact, {**selection, 'value_sentence_indexes': []})
    with pytest.raises(ValueError, match='differs'):
        primary_projection(fact, {**selection, 'source_fact_sha256': 'wrong'})
    with pytest.raises(ValueError, match='original quotation'):
        primary_projection(fact, {**selection, 'citation_indexes': []})


def test_review_prompt_does_not_also_request_an_extraction_response(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr('apps.adviser_v2.processing.stages._selected_variant_name', lambda _v: 'base')
    criterion, result, pages = sample()
    messages = _messages(SimpleNamespace(id=POLICY_ID, uin='test'), pages, criterion, candidate=result)
    assert 'Return ONE rule' not in messages[2]['content']
    assert 'independent_body null' in messages[0]['content']
    assert 'PolicyRuleReviewV1' in messages[2]['content']
    assert 'EXACT BODY TEMPLATE' not in messages[2]['content']
