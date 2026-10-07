from dataclasses import replace

import pytest

from apps.adviser_v2.demo.contracts import (
    AgeRule,
    Answer,
    CardField,
    Citation,
    FamilyRule,
    PersonInput,
    PlanCard,
    Profile,
    Statement,
)
from apps.adviser_v2.demo.evidence import Packet, Section, Segment
from apps.adviser_v2.demo.matching import all_fits, evaluate, validate_selection
from apps.adviser_v2.demo.pricing import PrintedPrice, TableCell, lookup, validate_price
from apps.adviser_v2.demo.validation import locate, validate


def citation(text="Cover is 5 lakh for 30 days."):
    return Citation(section_id="s", page_id="p", quote=text)


def packet(text="Cover is 5 lakh for 30 days. Only for the Gold variant."):
    segment = Segment("p", 1, 100, 100 + len(text), 100, 100 + len(text), text)
    section = Section("s", "plan", "doc", "sha", "base_wording", ("Original",), (segment,))
    return Packet("plan", (section,), (), 15)


def answer(text="Cover is 5 lakh for 30 days.", quote=None):
    return Answer(
        plan_id="plan",
        status="answered",
        statements=[Statement(text=text, citations=[citation(quote or text)])],
    )


def test_whitespace_is_only_quote_normalization_and_highlight_maps_to_original():
    raw = "Benefits\nCover is 5 lakh\nfor 30 days."
    a, b = locate(raw, "Cover is 5 lakh for 30 days.")
    assert raw[a:b] == "Cover is 5 lakh\nfor 30 days."
    checked = validate(answer(), packet(raw))
    assert checked.passed
    assert checked.anchors[0]["start"] == 100 + a
    assert checked.anchors[0]["quote"] == raw[a:b]
    assert checked.statement_anchors == ((0,),)
    with pytest.raises(ValueError):
        locate("Rs. 5,000", "Rs. 5000")


def test_wrong_plan_and_edition_rejected():
    draft = answer().model_copy(update={"plan_id": "other"})
    assert validate(draft, packet()).rejected_wrong_plan == 1
    draft = answer()
    draft.statements[0].citations[0].section_id = "foreign"
    checked = validate(draft, packet())
    assert not checked.checks[0] and checked.rejected_wrong_plan == 1


@pytest.mark.parametrize(
    "text",
    ["Cover is 10 lakh for 30 days.", "Cover is 5 lakh for 30 months.", "Your claim will be paid."],
)
def test_unsupported_numeric_units_and_substantive_claims(text):
    checked = validate(answer(text, "Cover is 5 lakh for 30 days."), packet())
    assert not checked.passed


def test_missing_following_condition_and_restriction():
    checked = validate(
        answer("Maternity is covered", "Maternity is covered"),
        packet("Maternity is covered subject to a 24 month waiting period."),
    )
    assert not checked.checks[2]
    checked = validate(
        answer("Cover is 5 lakh.", "Cover is 5 lakh only for Gold variant."),
        packet("Cover is 5 lakh only for Gold variant."),
    )
    assert not checked.checks[4]


def test_pdf_bel_layout_marker_after_a_clause_end_is_not_a_cut_clause():
    # Star wordings print "ii.\t\x07\n" list markers; matching skips BEL, so the
    # located span ends before it. That is still a clause boundary.
    text = "Cover is 5 lakh for 30 days.\nii.\t\x07\nPre-hospitalization expenses are paid."
    quote = "Cover is 5 lakh for 30 days.\nii.\t\x07\n"
    assert validate(answer(quote, quote), packet(text)).passed
    cut = "Cover is 5 lakh\x07 for 30 days only within India."
    assert not validate(answer("Cover is 5 lakh.", "Cover is 5 lakh\x07"), packet(cut)).checks[2]


def test_neutrality_preserves_original_quotes_but_rejects_generated_direction():
    raw = "Ambulance transport for better treatment is covered."
    assert validate(answer(raw), packet(raw)).passed
    checked = validate(answer("Buy this plan for the best cover.", raw), packet(raw))
    assert not checked.checks[5]


def card(key="plan", insurer="Z insurer"):
    cited = [citation()]
    unknown = CardField(state="not_stated")
    return PlanCard(
        plan_id=key,
        index_version="index",
        insurer=insurer,
        name=key,
        variant="Default",
        plan_type="medical_indemnity",
        model="gpt-5.6-luna",
        status="ready",
        entry_ages=[
            AgeRule(
                relationship="self", minimum_days=18 * 365, maximum_days=65 * 365, citations=cited
            )
        ],
        renewal_ages=[
            AgeRule(
                relationship="self",
                minimum_days=0,
                maximum_days=None,
                maximum_unbounded=True,
                citations=cited,
            )
        ],
        family_rule=FamilyRule(
            allowed_relationships=["self", "spouse", "child"],
            maximum_adults=2,
            maximum_children=2,
            children_must_be_dependent=True,
            citations=cited,
        ),
        sum_insured=CardField(state="stated", numbers=[500000], citations=cited, exhaustive=True),
        geography=CardField(state="stated", labels=["all_india"], citations=cited, exhaustive=True),
        copay=unknown,
        room_limit=unknown,
        ped_waiting=unknown,
        maternity=unknown,
        opd=unknown,
    )


def profile(age=40):
    return Profile(
        people=[PersonInput(id="me", relationship="self", age_days=age * 365)],
        sum_insured=500000,
        city="Pune",
        zone=None,
        plan_type="medical_indemnity",
    )


def test_entry_not_renewal_age_decides_new_application():
    assert evaluate(card(), profile()).status == "fits"
    assert evaluate(card(), profile(70)).status == "doesnt_fit"


def test_missing_evidence_is_unresolved_and_explicit_failure_takes_precedence():
    c = card().model_copy(update={"entry_ages": []})
    assert evaluate(c, profile()).status == "unresolved"
    assert evaluate(c, profile().model_copy(update={"sum_insured": 1000000})).status == "doesnt_fit"
    c.sum_insured.exhaustive = False
    assert evaluate(c, profile().model_copy(update={"sum_insured": 1000000})).status == "unresolved"


def test_complete_neutral_lists_and_selection_outside_fits():
    cards = [card(str(i), "A insurer" if i % 2 else "Z insurer") for i in range(24)]
    result = all_fits(cards, profile(70))
    assert len(result) == 24 and all(r.status == "doesnt_fit" for r in result)
    assert result[0].plan_id == "1"
    assert len(validate_selection(cards, ["0", "1", "2", "3", "4"])) == 5
    for ids in [["0"], ["0", "0"], [str(i) for i in range(6)], ["0", "outside"]]:
        with pytest.raises(ValueError):
            validate_selection(cards, ids)
    cards[0].plan_type = "critical_illness"
    with pytest.raises(ValueError, match="same"):
        validate_selection(cards, ["0", "1"])


def test_family_restrictions_and_unmapped_need_visible():
    p = profile()
    p.people.append(PersonInput(id="father", relationship="parent", age_days=60 * 365))
    p.typed_needs = "covers father's diabetes"
    result = evaluate(card(), p)
    assert result.status == "doesnt_fit"
    assert "Can't check" in result.other_needs[0].explanation


def test_annual_tax_excluded_price_label_requires_printed_support():
    cells = {
        key: TableCell(key, "table", row, col, text, citation(text))
        for key, row, col, text in [
            ("amount", 2, 2, "10,000"),
            ("term", 2, 0, "Annual premium"),
            ("tax", 2, 1, "Excluding applicable taxes"),
            ("header", 0, 2, "Premium in Rs."),
        ]
    }
    price = PrintedPrice(
        "amount",
        {"term": "Annual premium", "tax_basis": "Excluding applicable taxes"},
        {"term": "term", "tax_basis": "tax"},
        ("header",),
    )
    assert validate_price(price, cells, {"term", "tax_basis"})
    for term, tax in [
        ("2 years", "Excluding applicable taxes"),
        ("Annual premium", "Gross premium"),
    ]:
        changed = {
            **cells,
            "term": replace(cells["term"], text=term),
            "tax": replace(cells["tax"], text=tax),
        }
        assert not validate_price(
            replace(price, axes={"term": term, "tax_basis": tax}), changed, {"term", "tax_basis"}
        )


def price_data():
    def cell(key, row, col, text):
        return TableCell(key, "table", row, col, text, citation(text))

    cells = {
        c.id: c
        for c in [
            cell("amount", 2, 2, "15,000/-"),
            cell("age", 2, 0, "56–59"),
            cell("sum", 0, 2, "5 lakh"),
            cell("heading", 0, 0, "Annual premium / Zone A"),
        ]
    }
    price = PrintedPrice(
        "amount", {"age": "56–59", "sum": "5 lakh"}, {"age": "age", "sum": "sum"}, ("heading",)
    )
    return cells, price


def test_premium_needs_all_axes_and_never_interpolates():
    cells, price = price_data()
    args = {"prices": [price], "cells": cells, "required_axes": {"age", "sum"}, "published": True}
    result = lookup(**args, selected={"age": "56–59", "sum": "5 lakh"})
    assert result.status == "available" and result.amount_printed == "15,000/-"
    assert lookup(**args, selected={"sum": "5 lakh"}).status == "missing_details"
    assert lookup(**args, selected={"age": "60", "sum": "5 lakh"}).status == "no_exact_combination"
    assert lookup(**{**args, "published": False}, selected={}).status == "unpublished"
    # The same label exists, but on the wrong row and column: this is not support.
    cells["age"] = replace(cells["age"], row=3, column=0)
    assert lookup(**args, selected=price.axes).status == "invalid_chart"


def test_similar_variant_names_do_not_accept_a_different_variant():
    raw = "Cover applies only to Optima Secure+."
    checked = validate(
        answer(raw),
        packet(raw),
        variant="Optima Secure",
        known_variants=("Optima Secure", "Optima Secure+"),
    )
    assert not checked.checks[4]


def table_answer():
    from apps.adviser_v2.demo.contracts import TableSupport

    raw = "Benefit     Gold     Silver\nRoom rent   5 lakh   3 lakh\nICU         8 lakh   4 lakh"
    base = packet(raw)
    data = [
        ("benefit", 1, 0, "Room rent"),
        ("gold", 0, 1, "Gold"),
        ("silver", 0, 2, "Silver"),
        ("amount", 1, 1, "5 lakh"),
        ("icu", 2, 0, "ICU"),
    ]
    cells = {
        key: {"row": row, "column": col, "citation": citation(text).model_dump()}
        for key, row, col, text in data
    }
    original = replace(base, tables=({"id": "region", "cells": cells},))
    draft = Answer(
        plan_id="plan",
        status="answered",
        statements=[
            Statement(
                text="Room rent Gold 5 lakh",
                citations=[citation(s) for s in ["Room rent", "Gold", "5 lakh"]],
                table=TableSupport(
                    region_id="region",
                    value_cell_id="amount",
                    row_label_ids=["benefit"],
                    column_label_ids=["gold"],
                ),
            )
        ],
    )
    return original, draft


def test_table_answer_requires_separate_exact_cells_on_correct_axes():
    original, draft = table_answer()
    checked = validate(draft, original)
    assert checked.passed and len(checked.anchors) == 3
    assert checked.statement_anchors == ((0, 1, 2),)
    draft.statements[0].table.row_label_ids = ["icu"]
    assert not validate(draft, original).checks[1]
    draft.statements[0].table.row_label_ids = ["benefit"]
    draft.statements[0].table.column_label_ids = ["silver"]
    assert not validate(draft, original).checks[1]


def test_table_answer_missing_label_and_orphan_amount_rejected():
    original, draft = table_answer()
    draft.statements[0].citations.pop(1)
    assert not validate(draft, original).checks[3]
    assert not validate(answer("5 lakh"), packet("5 lakh")).checks[3]
