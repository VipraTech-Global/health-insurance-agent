from dataclasses import replace
from types import SimpleNamespace

import pytest

from apps.adviser_v2.demo.answers import PARTIAL, answer_plan
from apps.adviser_v2.demo.assembly import PacketLabels, UnknownLabel, assemble
from apps.adviser_v2.demo.contracts import ScopedDraftUnit as DraftUnit
from apps.adviser_v2.demo.evidence import Packet, Section, Segment
from apps.adviser_v2.demo.quotations import QuoteMismatch, locate
from apps.adviser_v2.demo.relay import RelayUnavailable


def source(text, *, page="p1", start=0, identity="s1"):
    return Section(
        identity,
        "plan",
        "doc",
        "sha",
        "base_wording",
        (),
        (Segment(page, 1, 0, len(text), start, start + len(text), text),),
    )


def unit(quote, label="P1"):
    return DraftUnit(
        coverage_scope="base", benefit=[{"passage": label, "quote": quote, "occurrence": 0}]
    )


def test_original_offsets_artifacts_and_repeated_quotes():
    text = "air-\nconditioned and soft\u00adhyphen; air-\nconditioned"
    a, b = locate(text, "air-conditioned", 1)
    assert text[a:b] == "air-\nconditioned" and a > 0
    a, b = locate(text, "softhyphen")
    assert text[a:b] == "soft\u00adhyphen"
    assert locate(text, "airconditioned") == (0, len("air-\nconditioned"))
    for other in ["air–conditioned"]:
        with pytest.raises(QuoteMismatch):
            locate(text, other)
    with pytest.raises(QuoteMismatch):
        locate("not covered, Rs. 5,000", "covered Rs. 5000")


def test_preceding_negation_and_following_condition_are_original_excerpts():
    s = source("Maternity is not covered unless the waiting period is complete.")
    packet = Packet("plan", (s,), (), 100)
    statement, _ = assemble(unit("covered"), PacketLabels(packet), packet, [s])
    assert statement.excerpts == [s.text]
    assert "not covered unless" in statement.text
    with pytest.raises(UnknownLabel):
        assemble(unit("covered", "P2"), PacketLabels(packet), packet, [s])


def test_cross_page_completion_keeps_page_anchors_and_edition():
    first = source("Room expenses are covered subject to")
    second = source(
        " a maximum of Rs. 5,000 per day.", page="p2", start=len(first.text) + 1, identity="s2"
    )
    foreign = replace(second, plan_id="other", document_sha256="other")
    packet = Packet("plan", (first,), (), 100)
    statement, extended = assemble(
        unit("Room expenses are covered"), PacketLabels(packet), packet, [first, second, foreign]
    )
    assert [c.page_id for c in statement.citations] == ["p1", "p2"]
    assert all(s.plan_id == "plan" for s in extended.sections)
    assert extended.tokens <= 16000


def test_successful_unit_survives_failed_correction(monkeypatch):
    s = source("Room expenses are covered. Maternity is excluded.")
    packet = Packet("plan", (s,), (), 100)
    monkeypatch.setattr(
        "apps.adviser_v2.demo.answers.search",
        lambda **kw: SimpleNamespace(packet=packet, model="gpt-5.6-luna", call_ids=[]),
    )
    values = iter(
        [
            SimpleNamespace(
                value={
                    "schema_version": 3,
                    "status": "answered",
                    "units": [
                        unit("Room expenses are covered.").model_dump(),
                        unit("invented").model_dump(),
                    ],
                },
                model="gpt-5.6-luna",
                call_ids=[],
            ),
            RelayUnavailable("offline"),
        ]
    )

    def call(**kw):
        value = next(values)
        if isinstance(value, Exception):
            raise value
        return value

    result = answer_plan(
        {"policy_version_id": "plan", "index_id": "index", "sections": [s.payload()]},
        "Room?",
        method="H",
        relay=SimpleNamespace(call=call),
    )
    assert result["status"] == "answered" and result["completeness"] == "partial"
    assert result["message"] == PARTIAL
    assert result["answer"]["statements"][0]["text"] == s.text
    assert result["rejections"][0]["category"] == "copying_error"
    assert result["failure_category"] == "operational"


def test_following_nonprefix_qualification_is_kept_until_next_heading():
    s = source(
        "ICU and stents are covered. With regard to stents, we will pay only the notified price.\n2. Other benefits are covered."
    )
    packet = Packet("plan", (s,), (), 100)
    statement, _ = assemble(unit("ICU and stents are covered."), PacketLabels(packet), packet, [s])
    assert "notified price" in statement.text
    assert "Other benefits" not in statement.text


def test_table_labels_cannot_resolve_a_foreign_region_or_cell():
    from apps.adviser_v2.demo.contracts import DraftTable

    s = source("Room Gold 5 lakh.")
    packet = Packet("plan", (s,), (), 100)
    draft = unit("Room Gold 5 lakh.")
    draft.table = DraftTable(table="T9", value="C1", rows=["C2"], columns=["C3"])
    with pytest.raises(UnknownLabel):
        assemble(draft, PacketLabels(packet), packet, [s])


def test_context_budget_overflow_rejects_whole_benefit():
    from apps.adviser_v2.demo.assembly import EvidenceInsufficient

    first = source("Room expenses are covered subject to")
    second = source(
        " ".join(["additional conditions"] * 1000) + ".",
        page="p2",
        start=len(first.text) + 1,
        identity="s2",
    )
    packet = Packet("plan", (first,), (), 100, budget=200)
    with pytest.raises(EvidenceInsufficient, match="budget"):
        assemble(unit("Room expenses are covered"), PacketLabels(packet), packet, [first, second])


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("empty", "not_found"),
        ("transport", "temporarily_unavailable"),
        ("model", "temporarily_unavailable"),
    ],
)
def test_no_units_distinguishes_evidence_from_operational_failures(monkeypatch, kind, expected):
    from apps.adviser_v2.demo.relay import InvalidOutput

    s = source("Original source.")
    packet = Packet("plan", (s,), (), 100)
    monkeypatch.setattr(
        "apps.adviser_v2.demo.answers.search",
        lambda **kw: SimpleNamespace(packet=packet, model="gpt-5.6-luna", call_ids=[]),
    )

    def call(**kwargs):
        if kind == "transport":
            raise RelayUnavailable("offline")
        if kind == "model":
            raise InvalidOutput("invalid JSON after one repair")
        return SimpleNamespace(
            value={"schema_version": 3, "status": "not_found", "units": []},
            model="gpt-5.6-luna",
            call_ids=[],
        )

    r = answer_plan(
        {"policy_version_id": "plan", "index_id": "index", "sections": [s.payload()]},
        "Cover?",
        method="H",
        relay=SimpleNamespace(call=call),
    )
    assert r["status"] == expected
    assert r["answer"] is None
    assert r["message"] == (
        "Not found in this plan’s documents."
        if kind == "empty"
        else "Temporarily unavailable — try again"
    )


def test_wrapped_numbered_heading_stops_unrelated_benefits():
    s = source(
        "1.\t\x07In-patient Treatment: Room charges are covered. With regard to rooms, only AC rooms apply.\n2.\t\x07\nDay Care Treatment: Other cover applies."
    )
    packet = Packet("plan", (s,), (), 100)
    statement, _ = assemble(unit("Room charges are covered."), PacketLabels(packet), packet, [s])
    assert "only AC rooms" in statement.text and "Day Care" not in statement.text


def test_enumeration_end_optimization_matches_original_regex():
    import random
    import re

    from apps.adviser_v2.demo.quotations import enumeration_end

    rng = random.Random(16)
    alphabet = " ABCxyz0123456789_é½١\n\t.-"
    examples = [
        "Mr.",
        "1.",
        "III.",
        "A.",
        "ABC123.",
        "9" * 500 + ".",
        "a" + "9" * 500 + ".",
        "١٢.",
        "½.",
    ]
    examples.extend(
        "".join(rng.choices(alphabet, k=rng.randrange(1, 100))) + "." for _ in range(5000)
    )
    for text in examples:
        assert enumeration_end(text, len(text)) == bool(re.search(r"(?:\b[A-Z]|\b\d+)\.$", text))


def test_pdf_ligatures_and_private_use_bullets_match_plain_quotes():
    text = " Speciﬁc illness waiting period is 24 months."
    a, b = locate(text, "Specific illness waiting period is 24 months.")
    assert text[a:b] == text[2:]
    with pytest.raises(QuoteMismatch):
        locate(text, "Specific illness waiting period is 12 months.")


def test_quote_continuing_across_a_page_break_resolves_to_original_offsets():
    from apps.adviser_v2.demo.assembly import locate_passage

    first = source("Room expenses are covered subject to")
    second = source(
        " a maximum of Rs. 5,000 per day.", page="p2", start=len(first.text) + 1, identity="s2"
    )
    text = first.text + "\n" + second.segments[0].text
    quote = "covered subject to a maximum of Rs. 5,000 per day."
    a, b = locate_passage(first, first.segments[0], quote, 0, text)
    assert text[a:b].startswith("covered") and text[a:b].endswith("per day.")
    with pytest.raises(QuoteMismatch):
        locate_passage(first, first.segments[0], "a maximum of Rs. 9,000 per day.", 0, text)


def test_table_cell_may_be_named_by_its_unique_printed_text():
    from apps.adviser_v2.demo.assembly import table_key

    region = {
        "cells": {
            "a": {"text": "Room rent", "row": 1, "column": 0},
            "b": {"text": "Gold", "row": 0, "column": 1},
            "c": {"text": "Single private room", "row": 1, "column": 1},
            "d": {"text": "Gold", "row": 2, "column": 0},
        }
    }
    mapping = {"C1": "a", "C2": "b", "C3": "c", "C4": "d"}
    assert table_key("C3", mapping, region) == "C3"
    assert table_key("single  private room", mapping, region) == "C3"
    assert table_key("Gold", mapping, region, row=0) == "C2"
    for ambiguous_or_absent in ["Gold", "Shared room"]:
        with pytest.raises(UnknownLabel):
            table_key(ambiguous_or_absent, mapping, region)
