from types import SimpleNamespace

import pytest

from apps.adviser_v2.demo.answer_scope import ScopedLabels, ScopeIndex, ScopeViolation, canon
from apps.adviser_v2.demo.answers import answer_plan, known_variants
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


def test_selected_variant_cell_decides_scope_over_family_optional_wording():
    from apps.adviser_v2.demo.contracts import Statement, TableSupport

    raw = "2. Optional Covers\n2.6. Restore Benefit\nThe sum insured is restored once."
    quote = "The sum insured is restored once."
    cells = {
        "field": {"text": "Restore Benefit", "row": 3, "column": 0},
        "gold": {"text": "Gold", "row": 0, "column": 1},
        "silver": {"text": "Silver", "row": 0, "column": 2},
        "value": {"text": "Equal to 100% of sum insured", "row": 3, "column": 1},
    }
    b, p, scope = fixture(raw, tables=[{"id": "table", "cells": cells}])
    labels = ScopedLabels(p, scope)
    question = "What restoration benefit applies?"

    def check(kind):
        unit = ScopedDraftUnit(
            coverage_scope=kind,
            benefit=[{"passage": "P1", "quote": quote}],
            table={"table": "T1", "value": "C4", "rows": ["C1"], "columns": ["C2"]},
        )
        statement = Statement(
            text=quote,
            citations=[{"section_id": "s1", "page_id": "p1", "quote": quote}],
            table=TableSupport(
                region_id="table",
                value_cell_id="value",
                row_label_ids=["field"],
                column_label_ids=["gold"],
            ),
        )
        return scope.check(unit, labels, statement, question).coverage_scope

    # The prose is filed under optional covers; the selected column's value is the
    # variant's own cover.
    assert scope.context(*labels.passages["P1"], quote)["coverage_scope"] != "base"
    assert check("base") == "base"
    with pytest.raises(ScopeViolation, match="no original-source support"):
        check("optional, extra premium")
    for text in ("Optional (100% of sum insured)", "Choose to pay additional premium"):
        cells["value"]["text"] = text
        with pytest.raises(ScopeViolation, match="labelled"):
            check("base")
        assert check("optional, extra premium") == "optional, extra premium"


def test_variant_table_continued_on_the_next_page_keeps_its_optional_section():
    from dataclasses import replace

    from apps.adviser_v2.demo.contracts import Statement, TableSupport

    def table(page, rows, header=("Benefits", "Gold", "Silver")):
        cite = {"section_id": "s1", "page_id": "p1", "occurrence": 0}
        cells = {
            f"{page}:{r}:{c}": {
                "text": text,
                "row": r,
                "column": c,
                "citation": {**cite, "quote": text},
            }
            for r, row in enumerate([header, *rows])
            for c, text in enumerate(row)
        }
        return {"id": f"doc:{page}:0", "cells": cells}

    earlier = table(
        4,
        [["Room Rent", "At actuals", "1%"], ["Optional Covers"], ["Deductible", "INR 5,000", "NA"]],
    )
    later = table(
        5,
        [
            ["Deductible", "INR 10,000", "NA"],
            ["Waiting Period"],
            ["Initial Waiting", "30 days", "30 days"],
        ],
    )
    quote = "A deductible applies to each claim."
    b, p, scope = fixture(quote, tables=[earlier, later])
    labels = ScopedLabels(p, scope)

    def check(kind, row, question="What deductible applies?"):
        unit = ScopedDraftUnit(
            coverage_scope=kind,
            benefit=[{"passage": "P1", "quote": quote}],
            table={"table": "T2", "value": "C1", "rows": ["C1"], "columns": ["C1"]},
        )
        statement = Statement(
            text=quote,
            citations=[{"section_id": "s1", "page_id": "p1", "quote": quote}],
            table=TableSupport(
                region_id=later["id"],
                value_cell_id=f"5:{row}:1",
                row_label_ids=[f"5:{row}:0"],
                column_label_ids=["5:0:1"],
            ),
        )
        return scope.check(unit, labels, statement, question).coverage_scope

    # Page 5 repeats page 4's header and carries on its optional covers until the
    # next heading row.
    assert scope.optional_rows(later) == {1}
    payload = ScopedLabels(replace(p, tables=(later,)), scope).payload()
    assert payload["tables"][0]["scope"]["optional_rows_continued_from_previous_page"] == [1]
    with pytest.raises(ScopeViolation, match="labelled"):
        check("base", 1)
    assert check("optional, extra premium", 1) == "optional, extra premium"
    assert check("base", 3, "What initial waiting period applies?") == "base"
    # Another header, or a previous page without optional covers, starts afresh.
    for page in (
        table(
            4,
            [["Optional Covers"], ["Deductible", "INR 5,000", "NA"]],
            header=("Benefits", "Silver", "Gold"),
        ),
        table(4, [["Room Rent", "At actuals", "1%"]]),
    ):
        b, p, scope = fixture(quote, tables=[page, later])
        assert scope.optional_rows(later) == set()


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


def test_definition_alone_is_not_an_answer_about_plan_limits():
    b, p, s = fixture(
        "Room Rent means the amount charged by a Hospital towards Room and Boarding expenses."
    )
    with pytest.raises(ScopeViolation, match="definition alone"):
        scoped(b, p, s, p.sections[0].text, question="What room limits apply?")
    assert scoped(b, p, s, p.sections[0].text, question="What does Room Rent mean?")


def test_bullet_benefit_heading_stops_preceding_illness_list():
    b, p, s = fixture(
        "iv. Treatment of all diseases.\n• Pre-existing diseases\nPED is excluded for 36 months.\n"
    )
    statement, _ = scoped(b, p, s, "Pre-existing diseases", question="What PED wait applies?")
    assert "Treatment of all" not in statement.text
    assert "36 months" in statement.text


def test_packet_reserves_selected_variant_table_axes_without_neighbour_values():
    from apps.adviser_v2.demo.answer_packet import scoped_packet

    raw = "OPD Gold Silver Covered Not Available"
    cite = {"section_id": "s1", "page_id": "p1", "quote": "OPD", "occurrence": 0}
    cells = {"label": {"text": "OPD", "row": 3, "column": 0, "citation": cite}}
    for key, text, row, col in [
        ("gold", "Gold", 0, 1),
        ("silver", "Silver", 0, 2),
        ("yes", "Covered", 3, 1),
        ("no", "Not Available", 3, 2),
    ]:
        cells[key] = {"text": text, "row": row, "column": col, "citation": {**cite, "quote": text}}
    b, p, scope = fixture(raw, tables=[{"id": "t", "cells": cells}])
    result = scoped_packet(p, scope, "What OPD cover applies?")
    assert set(result.tables[0]["cells"]) == {"label", "gold", "yes"}
    assert result.tokens <= 16000
    assert "not exhaustive" in result.tables[0]["projection"]


def test_optional_discount_is_not_mislabelled_as_extra_premium():
    raw = "Optional co-payment: choose 20% co-payment for a 10% premium discount."
    b, p, s = fixture(raw)
    a, _ = scoped(b, p, s, raw, "optional, extra premium", question="What co-pay applies?")
    assert a.coverage_scope == "optional premium adjustment"


def test_expansion_rebudgets_when_preserved_omissions_are_large():
    from dataclasses import replace

    from apps.adviser_v2.demo.answer_retrieval import expanded_packet

    b, p, s = fixture("Room rent is covered. " * 900)
    p = replace(p, omitted_ids=tuple("f" * 60 + str(n) for n in range(550)))
    result = expanded_packet(p, p)
    assert result.tokens <= 16000 and len(result.omitted_ids) >= 550


def test_failed_governing_condition_rejects_whole_benefit_but_retains_independent_unit(monkeypatch):
    b, p, scope = fixture("Room rent is covered. OPD is covered.")
    monkeypatch.setattr(
        "apps.adviser_v2.demo.answers.search",
        lambda **kw: SimpleNamespace(packet=p, model="gpt-5.6-luna", call_ids=[]),
    )
    units = [
        {"coverage_scope": "base", "benefit": [{"passage": "P1", "quote": q}]}
        for q in [
            "Room rent is covered.",
            "If room category is breached, a deduction applies.",
            "OPD is covered.",
        ]
    ]
    values = iter(
        [
            {"schema_version": 3, "status": "answered", "units": units},
            {"schema_version": 3, "status": "not_found", "units": []},
        ]
    )
    relay = SimpleNamespace(
        call=lambda **kw: SimpleNamespace(value=next(values), model="gpt-5.6-luna", call_ids=[])
    )
    result = answer_plan(b, "What room and OPD cover applies?", method="H", relay=relay)
    assert result["completeness"] == "partial"
    assert [u["text"] for u in result["answer"]["statements"]] == ["OPD is covered."]


def test_standalone_condition_stays_unmatched_for_rejection():
    from apps.adviser_v2.demo.answer_units import conditional_unit, governing_units

    unit = ScopedDraftUnit(
        coverage_scope="base",
        benefit=[{"passage": "P1", "quote": "If room category is breached, a deduction applies."}],
    )
    assert conditional_unit(governing_units([unit])[0])


def test_product_named_like_its_variant_still_rejects_foreign_owner():
    b, p, scope = fixture("Product Name: Beta Cover\nOPD is covered.", variant="Alpha Cover")
    with pytest.raises(ScopeViolation, match="another product"):
        scoped(b, p, scope, "OPD is covered.")


@pytest.mark.parametrize(
    "heading",
    [
        "Optional Packages (Applicable only if opted)",
        "Optional Covers (Applicable only if opted)",
        "Optional Benefits (if selected)",
    ],
)
def test_optional_package_qualification_governs_named_children_across_pages(heading):
    raw = heading + "\n1. Enhance\nRoom upgrade is covered.\f2. Freedom\nOPD is covered."
    b, p, scope = fixture(raw)
    with pytest.raises(ScopeViolation, match="labelled"):
        scoped(b, p, scope, "OPD is covered.")
    assert (
        scoped(b, p, scope, "OPD is covered.", "optional, extra premium")[0].coverage_scope
        == "optional, extra premium"
    )


@pytest.mark.parametrize(
    ("raw", "question"),
    [
        (
            "Reset Benefit: 100% of the sum insured is reinstated once a year.",
            "What restoration benefit applies?",
        ),
        ("Home Health Care is covered up to sum insured.", "Is home care treatment covered?"),
        ("Ambulance charges are covered up to Rs. 2,000.", "Is road ambulance covered?"),
        (
            "Pre - hospitalization expenses for 60 days.",
            "What pre and post hospitalisation cover applies?",
        ),
        (
            "Booster benefit carries forward 100% of unutilised sum insured.",
            "What no claim bonus applies?",
        ),
    ],
)
def test_insurer_names_for_common_fields_identify_the_requested_field(raw, question):
    b, p, s = fixture(raw)
    assert scoped(b, p, s, raw, question=question)[0].coverage_scope == "base"


def test_variant_names_in_table_cells_do_not_own_following_prose():
    b, p, s = fixture(
        "Room Rent\nSilver\nSingle room\nTreatment\nRoom expenses are covered for all insured persons."
    )
    answer, _ = scoped(
        b,
        p,
        s,
        "Room expenses are covered for all insured persons.",
        question="What room cover applies?",
    )
    assert answer.coverage_scope == "base"


def test_column_headings_are_not_variant_names():
    b, _, s = fixture(
        "Benefits.",
        tables=[
            {
                "id": "t",
                "cells": {
                    "1": {"text": "TITLE", "row": 0, "column": 0},
                    "2": {"text": "Gold", "row": 0, "column": 1},
                    "3": {"text": "Silver", "row": 0, "column": 2},
                    "4": {"text": "Policy Clause Number", "row": 0, "column": 3},
                },
            }
        ],
    )
    assert not {"TITLE", "Policy Clause Number"} & set(s.names)


def heading_row(*texts, row=0):
    return {f"{row}:{n}": {"text": t, "row": row, "column": n} for n, t in enumerate(texts)}


def test_other_variant_columns_are_known_and_a_wrapped_plus_is_the_same_name():
    assert canon("VIP +") == canon("VIP+") != canon("VIP")
    table = {
        "id": "t",
        "cells": {
            **heading_row("Benefits", "MAX", "MAX+", "VIP +"),
            **heading_row("Room", "Covered", "Covered", "Covered", row=1),
        },
    }
    b, _, s = fixture(
        "Benefits.", tables=[table], name="Activ One", variant="MAX", variants=["MAX"]
    )
    assert s.matrices["t"]["names"] == ["MAX", "MAX+", "VIP +"]
    assert known_variants(b, s) == ("MAX", "MAX+", "VIP +")
    # Without variant tables the bundle's own variants are all there is.
    b, _, s = fixture("Benefits.")
    assert known_variants(b, s) == ("Gold", "Silver")


def test_wrapped_headings_and_value_rows_do_not_become_variant_names():
    wrapped = {
        "id": "w",
        "cells": {
            **heading_row("Benefit", "Optima Secure", "Optima", "Optima", "Optima Lite"),
            **heading_row("", "", "Secure Global", "Secure Global Plus", "", row=1),
        },
    }
    b, _, s = fixture(
        "Benefits.",
        tables=[wrapped],
        name="my: Optima Secure",
        variant="Optima Secure",
        variants=["Optima Secure"],
    )
    assert "Optima" not in s.names and "Optima Lite" in s.names
    assert known_variants(b, s) == ("Optima Secure", "Optima Lite")
    # A first row of values under a variant heading printed lower down names nothing.
    values = {
        "id": "v",
        "cells": {
            **heading_row("Room Rent", "Covered", "Single room"),
            **heading_row("", "Gold", "Silver", row=1),
        },
    }
    _, _, s = fixture("Benefits.", tables=[values])
    assert s.names == {"Gold", "Silver"}


def test_packet_adds_an_unretrieved_variant_table_only_for_the_variants_own_value():
    from apps.adviser_v2.demo.answer_packet import scoped_packet

    page = source("Benefit Gold Silver OPD Covered Not Available", page="p2", identity="s2")

    def table(identity, *rows):
        cells = {}
        for r, texts in enumerate(rows):
            for c, text in enumerate(texts):
                if text:
                    cite = {"section_id": "s2", "page_id": "p2", "quote": text, "occurrence": 0}
                    cells[f"{r}:{c}"] = {"text": text, "row": r, "column": c, "citation": cite}
        return {"id": identity, "cells": cells}

    own = table(
        "own",
        ("Benefit", "Gold", "Silver"),
        # A benefit row above row 3 is no header; it joins only when queried.
        ("Entry Age", "18 years", "18 years"),
        ("OPD", "Covered", "Not Available"),
    )
    # Gold's heading prints but its OPD value is merged under Silver.
    merged = table("merged", ("Benefit", "Silver", "Gold"), ("OPD", "Covered", ""))
    plain = table("plain", ("Benefit", "Limit"), ("OPD", "Covered"))
    b, p, scope = fixture(
        "Outpatient treatment is described in the schedule.",
        sections=[
            source("Outpatient treatment is described in the schedule.").payload(),
            page.payload(),
        ],
        tables=[plain, merged, own],
    )
    result = scoped_packet(p, scope, "What OPD cover applies?")
    assert [t["id"] for t in result.tables] == ["own"]
    assert {c["text"] for c in result.tables[0]["cells"].values()} == {
        "Benefit",
        "Gold",
        "OPD",
        "Covered",
    }
    assert [s.id for s in result.sections] == ["s2", "s1"]
    # Without a variant table nothing unretrieved is added.
    b, p, scope = fixture(
        "Outpatient treatment is described in the schedule.",
        sections=[
            source("Outpatient treatment is described in the schedule.").payload(),
            page.payload(),
        ],
        tables=[plain],
    )
    assert scoped_packet(p, scope, "What OPD cover applies?") is p


def test_variant_table_cells_named_by_printed_text_resolve_under_the_selected_column():
    from apps.adviser_v2.demo.assembly import UnknownLabel

    raw = "OPD consultations are covered.\nSection Plans Gold Silver\n1.4 OPD Covered Covered"
    cells = {}
    for r, texts in enumerate(
        [("Section", "Plans", "Gold", "Silver"), ("1.4", "OPD", "Covered", "Covered")]
    ):
        for c, text in enumerate(texts):
            # The table's "OPD" and second "Covered" are each the text's second occurrence.
            occurrence = int((r, c) in {(1, 1), (1, 3)})
            cite = {"section_id": "s1", "page_id": "p1", "quote": text, "occurrence": occurrence}
            cells[f"{r}:{c}"] = {"text": text, "row": r, "column": c, "citation": cite}
    b, p, scope = fixture(raw, tables=[{"id": "t", "cells": cells}])
    p = Packet("plan", p.sections, (), 16000, tables=({"id": "t", "cells": cells},))
    labels = ScopedLabels(p, scope)

    def draft(**table):
        return ScopedDraftUnit(
            coverage_scope="base",
            benefit=[{"passage": "P1", "quote": "OPD consultations are covered."}],
            table={"table": "T1", **table},
        )

    # The joined section number and benefit name, and the extra headings, as printed.
    unit = draft(value="Covered", rows=["1.4 — OPD"], columns=["Section", "Plans", "Gold"])
    _, ref = labels.table_ref(unit.table)
    names = {alias: cells[key]["text"] for alias, key in labels.cells["T1"].items()}
    assert [names[a] for a in ref.rows] == ["1.4", "OPD"]
    assert [names[a] for a in ref.columns] == ["Gold"]
    assert labels.cells["T1"][ref.value] == "1:2"
    statement, extended = assemble(unit, labels, p, list(scope.sections.values()))
    statement = scope.check(unit, labels, statement, "What OPD cover applies?")
    assert statement.table.value_cell_id == "1:2"
    assert validate(
        Answer(plan_id="plan", status="answered", statements=[statement]),
        extended,
        variant="Gold",
        known_variants=("Gold", "Silver"),
    ).passed
    # Another variant's column stays another variant's column.
    unit = draft(value="Covered", rows=["OPD"], columns=["Silver"])
    statement, _ = assemble(unit, labels, p, list(scope.sections.values()))
    with pytest.raises(ScopeViolation, match="selected variant/product axis"):
        scope.check(unit, labels, statement, "What OPD cover applies?")
    # A value no kept column names, or text naming no cell, is still unknown.
    for table in (
        {"value": "Covered", "rows": ["OPD"], "columns": ["Section"]},
        {"value": "Covered", "rows": ["Room"], "columns": ["Gold"]},
        {"value": "Covered at actuals", "rows": ["OPD"], "columns": ["Gold"]},
    ):
        with pytest.raises(UnknownLabel):
            labels.table_ref(draft(**table).table)
