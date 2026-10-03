from types import SimpleNamespace

import pytest

from apps.adviser_v2.demo.answer_scope import ScopedLabels, ScopeIndex, ScopeViolation
from apps.adviser_v2.demo.answers import answer_plan
from apps.adviser_v2.demo.assembly import assemble
from apps.adviser_v2.demo.contracts import Answer, ScopedDraftUnit
from apps.adviser_v2.demo.evidence import Packet
from apps.adviser_v2.demo.relay import RelayUnavailable
from apps.adviser_v2.demo.validation import validate
from apps.adviser_v2.tests.test_demo_assembly import source


def fixture(raw, **extras):
    s = source(raw)
    bundle = {
        "policy_version_id": "plan",
        "index_id": "index",
        "name": "Alpha Cover",
        "variant": "Gold",
        "variants": ["Gold", "Silver"],
        "sections": [s.payload()],
        **extras,
    }
    packet = Packet("plan", (s,), (), 100)
    return bundle, packet, ScopeIndex(bundle)


def scoped(bundle, packet, scope, quote, kind="base", question="What OPD cover applies?"):
    unit = ScopedDraftUnit(coverage_scope=kind, benefit=[{"passage": "P1", "quote": quote}])
    labels = ScopedLabels(packet, scope)
    statement, extended = assemble(unit, labels, packet, list(scope.sections.values()))
    return scope.check(unit, labels, statement, question), extended


def test_optional_enclosing_heading_cannot_be_omitted_or_called_base():
    b, p, s = fixture(
        "4. Optional Covers\n4.1. Outpatient\nOPD consultations are covered.\n5. Base benefits\nRoom expenses are covered."
    )
    with pytest.raises(ScopeViolation, match="labelled"):
        scoped(b, p, s, "OPD consultations are covered.")
    answer, packet = scoped(b, p, s, "OPD consultations are covered.", "optional, extra premium")
    assert answer.coverage_scope == "optional, extra premium"
    assert validate(
        Answer(plan_id="plan", status="answered", statements=[answer]), packet, variant="Gold"
    ).passed
    room, _ = scoped(b, p, s, "Room expenses are covered.", question="What room cover applies?")
    assert room.coverage_scope == "base"


def test_other_product_heading_is_not_masked_by_selected_variant_name():
    b, p, s = fixture("Product Name: Beta Cover\nGold\nOPD is covered.")
    with pytest.raises(ScopeViolation, match="another product"):
        scoped(b, p, s, "OPD is covered.")


def test_named_other_variant_is_rejected_even_when_document_is_selected_product():
    b, p, s = fixture("Product Name: Alpha Cover\nSilver\nOPD is covered.")
    with pytest.raises(ScopeViolation, match="another variant"):
        scoped(b, p, s, "OPD is covered.")


def test_variant_prefix_does_not_turn_plus_into_base_variant():
    from apps.adviser_v2.demo.answer_scope import named

    assert not named("MAX+ only", "MAX")
    assert not named("Optima Secure+", "Optima Secure")


def test_wrong_wait_and_copay_do_not_answer_other_fields():
    b, p, s = fixture("Specified disease waiting period is 24 months.\nCo-payment is 20%.")
    with pytest.raises(ScopeViolation):
        scoped(
            b,
            p,
            s,
            "Specified disease waiting period is 24 months.",
            question="What is the pre-existing disease wait?",
        )
    with pytest.raises(ScopeViolation):
        scoped(b, p, s, "Co-payment is 20%.", question="What deductible applies?")


def test_validator_rejects_unlabelled_optional_in_new_answer_contract():
    b, p, s = fixture("Optional OPD benefit is covered.")
    a, _ = scoped(b, p, s, p.sections[0].text, "optional, extra premium")
    a.coverage_scope = "base"
    assert not validate(Answer(plan_id="plan", status="answered", statements=[a]), p).checks[4]


def test_second_h_packet_is_attempted_before_not_found_and_recovers(monkeypatch):
    b, p, s = fixture("Room rent is 1% of sum insured per day.")
    queries = []

    def search(**kw):
        queries.append(kw["question"])
        return SimpleNamespace(packet=p, model="gpt-5.6-luna", call_ids=[])

    monkeypatch.setattr("apps.adviser_v2.demo.answers.search", search)
    values = iter(
        [
            {"schema_version": 3, "status": "not_found", "units": []},
            {
                "schema_version": 3,
                "status": "answered",
                "units": [
                    {
                        "coverage_scope": "base",
                        "benefit": [{"passage": "P1", "quote": p.sections[0].text}],
                    }
                ],
            },
        ]
    )
    relay = SimpleNamespace(
        call=lambda **kw: SimpleNamespace(value=next(values), model="gpt-5.6-luna", call_ids=[])
    )
    result = answer_plan(b, "What room rent applies?", method="H", relay=relay)
    assert result["status"] == "answered" and len(queries) == 2
    assert "customer information sheet" in queries[1]
    assert len(result["retrieval_attempts"]) == 2 and result["validation_ms"] >= 0


def test_exhausted_packets_and_operational_recovery_failure_are_distinct(monkeypatch):
    b, p, s = fixture("Original source.")
    calls = []

    def search(**kw):
        calls.append(kw)
        if len(calls) == 2:
            raise RelayUnavailable("temporary relay outage")
        return SimpleNamespace(packet=p, model="gpt-5.6-luna", call_ids=[])

    monkeypatch.setattr("apps.adviser_v2.demo.answers.search", search)
    relay = SimpleNamespace(
        call=lambda **kw: SimpleNamespace(
            value={"schema_version": 3, "status": "not_found", "units": []},
            model="gpt-5.6-luna",
            call_ids=[],
        )
    )
    result = answer_plan(b, "What room rent applies?", method="H", relay=relay)
    assert result["status"] == "temporarily_unavailable" and len(calls) == 2


def test_scope_ignores_navigation_summaries():
    b, p, s = fixture(
        "OPD is covered.", navigation=[{"summary": "Optional benefit only for Silver"}]
    )
    a, _ = scoped(b, p, s, "OPD is covered.")
    assert a.coverage_scope == "base"
    assert "summary" not in str(ScopedLabels(p, s).payload())


def test_optional_positive_sentence_does_not_borrow_neighbouring_exclusion():
    from apps.adviser_v2.demo.answer_scope import optional_cover

    assert optional_cover("Dental care is not covered. Optional OPD benefit is covered.")
    assert not optional_cover("OPD is not covered unless the optional rider is purchased.")


def test_expanded_packet_keeps_unresolved_omissions_and_removes_recovered_ones():
    from dataclasses import replace

    from apps.adviser_v2.demo.answer_retrieval import expanded_packet

    b, p, s = fixture("OPD is covered.")
    result = expanded_packet(replace(p, omitted_ids=("missing", "s1")), p)
    assert result.omitted_ids == ("missing",)
    assert result.tokens <= result.budget == 16000


def test_shared_wording_requires_selected_variant_axis_and_labels_optional_rows():
    from apps.adviser_v2.demo.contracts import Statement, TableSupport

    raw = "OPD consultations are covered."
    table = {
        "id": "table",
        "cells": {
            "field": {"text": "OPD", "row": 3, "column": 0},
            "gold": {"text": "Gold", "row": 0, "column": 1},
            "silver": {"text": "Silver", "row": 0, "column": 2},
            "value": {"text": "Covered", "row": 3, "column": 1},
        },
    }
    b, p, scope = fixture(raw, tables=[table])
    with pytest.raises(ScopeViolation, match="Shared wording"):
        scoped(b, p, scope, raw)
    unit = ScopedDraftUnit(
        coverage_scope="base",
        benefit=[{"passage": "P1", "quote": raw}],
        table={"table": "T1", "value": "C4", "rows": ["C1"], "columns": ["C2"]},
    )
    statement = Statement(
        text=raw,
        citations=[{"section_id": "s1", "page_id": "p1", "quote": raw}],
        table=TableSupport(
            region_id="table",
            value_cell_id="value",
            row_label_ids=["field"],
            column_label_ids=["silver"],
        ),
    )
    with pytest.raises(ScopeViolation, match="selected variant/product axis"):
        scope.check(unit, ScopedLabels(p, scope), statement, "What OPD cover applies?")
    statement.table.column_label_ids = ["gold"]
    assert (
        scope.check(
            unit, ScopedLabels(p, scope), statement, "What OPD cover applies?"
        ).coverage_scope
        == "base"
    )
    table["cells"]["optional"] = {"text": "Optional Benefits", "row": 2, "column": 0}
    with pytest.raises(ScopeViolation, match="labelled"):
        scope.check(unit, ScopedLabels(p, scope), statement, "What OPD cover applies?")


def test_shared_illustration_is_not_selected_variant_availability_proof():
    from dataclasses import replace

    b, p, scope = fixture("OPD consultations are covered.")
    scope.matrices = {"shared": {"topics": ["opd"], "names": ["Gold", "Silver"]}}
    cis = replace(p.sections[0], role="customer_information_sheet")
    scope.document_labels = {"doc": "Gold benefit illustration"}
    p = replace(p, sections=(cis,))
    with pytest.raises(ScopeViolation, match="Shared wording"):
        scoped(b, p, scope, cis.text)


@pytest.mark.parametrize(
    "earlier",
    [
        "Cover): On payment of additional premium the Insured Person",
        "S. No. Optional Benefits",
        "What are the optional covers available?",
    ],
)
def test_mentions_and_table_headers_do_not_make_later_base_benefits_optional(earlier):
    b, p, s = fixture(earlier + "\nSub Limits\nRoom Eligibility No limit.")
    answer, _ = scoped(b, p, s, "Room Eligibility No limit.", question="What room limit applies?")
    assert answer.coverage_scope == "base"


def test_product_owner_can_omit_selected_variant_but_not_change_product():
    b, p, s = fixture("Product Name: Alpha Cover\nOPD is covered.", name="Alpha Cover Gold")
    assert scoped(b, p, s, "OPD is covered.")[0].coverage_scope == "base"


def test_invisible_pdf_layout_marker_is_offset_preserving():
    from apps.adviser_v2.demo.quotations import locate

    raw = "1.\t\x07In-patient Treatment: Room charges are covered."
    a, b = locate(raw, "1. In-patient Treatment: Room charges are covered.")
    assert raw[a:b] == raw
