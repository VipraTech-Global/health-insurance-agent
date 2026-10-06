import pytest

from apps.adviser_v2.demo.cards import CardSources, FieldSource, entry_rules, projected_field
from apps.adviser_v2.demo.charts import ChartLabels, cell_payload
from apps.adviser_v2.demo.contracts import Citation, Statement
from apps.adviser_v2.demo.pricing import TableCell
from apps.adviser_v2.demo.relay import strict_schema


def source(text, field="entry_age"):
    return FieldSource(
        field=field,
        status="answered",
        statements=[
            Statement(text=text, citations=[Citation(section_id="s", page_id="p", quote=text)])
        ],
    )


def test_card_projection_does_not_treat_renewal_as_entry_or_territory_as_purchase_geography():
    assert entry_rules(source("Renewals are allowed at any age.")) == []
    assert entry_rules(source("Maximum age at renewal is 90 years.")) == []
    field = projected_field(source("Treatment is covered in India.", field="geography"))
    assert "all_india" not in field.labels and not field.exhaustive
    assert not field.numbers


def test_entry_age_includes_completed_upper_year_without_inventing_spouse_rules():
    rules = entry_rules(
        source("Any person aged between 18 years and 65 years can take this insurance.")
    )
    assert len(rules) == 1 and rules[0].relationship == "self"
    assert rules[0].minimum_days == 18 * 365 and rules[0].maximum_days == 66 * 365 - 1


def test_card_and_chart_schemas_are_closed_and_cells_serialize_exactly():
    import json

    import jsonschema

    for schema in [CardSources.model_json_schema(), ChartLabels.model_json_schema()]:
        jsonschema.Draft202012Validator.check_schema(strict_schema(schema))
    c = Citation(section_id="s", page_id="p", quote="1,005")
    cell = TableCell("c", "t", 1, 1, "1,005", c)
    assert json.loads(json.dumps(cell_payload(cell)))["citation"]["quote"] == "1,005"
    with pytest.raises(ValueError):
        ChartLabels.model_validate(
            {"prices": [{"value_cell": "c", "axes": {}, "axis_cells": {}, "heading_cells": []}]}
        )


def test_sum_insured_projection_requires_explicit_new_business_amount_list():
    from apps.adviser_v2.demo.cards import sum_insured_field

    field = sum_insured_field(
        source(
            "Sum Insured Options: Rs.5,00,000/-, Rs.10,00,000/- and Rs.25,00,000/-", "sum_insured"
        )
    )
    assert field.numbers == [500000, 1000000, 2500000] and field.exhaustive
    for text in [
        "Maternity is limited to Rs.5,00,000/-",
        "Sum Insured Options: Rs.1,00,000/- available only for renewals",
        "Sum Insured Options: Rs.5,00,000/- only for ages under 65",
    ]:
        assert not sum_insured_field(source(text, "sum_insured")).numbers


def test_typed_family_and_entry_projection_keeps_child_and_adult_limits_separate():
    from apps.adviser_v2.demo.cards import family_rule

    adult = source(
        "The minimum entry age for an adult is 18 years and there is no limit on maximum entry age."
    )
    child = source(
        "The minimum entry age for a dependent child (i.e. natural or legally adopted) is 91 days and maximum entry age is 25 years."
    )
    adult.statements.extend(child.statements)
    rules = {rule.relationship: rule for rule in entry_rules(adult)}
    assert rules["parent"].maximum_unbounded and rules["parent"].minimum_days == 18 * 365
    assert rules["child"].minimum_days == 91 and rules["child"].maximum_days == 26 * 365 - 1
    text = (
        "In a family floater Policy, a maximum of 4 adults and a maximum of 6 dependent children "
        "can be included in a single Policy. The 4 adults can be a combination of self, spouse, parents and parents- in-law."
    )
    family = family_rule(source(text, "family"))
    assert family.maximum_adults == 4 and family.maximum_children == 6
    assert family.children_must_be_dependent and "parent_in_law" in family.allowed_relationships
    assert family_rule(source(text + " Subject to one parent only.", "family")) is None
    assert family_rule(source(text.replace("The 4 adults", "The 2 adults"), "family")) is None


def test_decimal_lakh_choices_keep_exact_values_and_reject_extra_conditions():
    from apps.adviser_v2.demo.cards import sum_insured_field

    text = "Sum Insured option (in Rs.) 3/4/5/7.5/10/12.5/100 Lacs"
    assert sum_insured_field(source(text, "sum_insured")).numbers == [
        300000,
        400000,
        500000,
        750000,
        1000000,
        1250000,
        10000000,
    ]
    assert not sum_insured_field(source(text + " only for renewals", "sum_insured")).numbers


def test_failed_selector_is_cached_as_missing_fields_but_transport_remains_pending(
    tmp_path, monkeypatch
):
    from apps.adviser_v2.demo import cards
    from apps.adviser_v2.demo.relay import RelayUnavailable
    from apps.adviser_v2.tests.test_demo_contracts import card

    calls = []

    def invalid(*args):
        calls.append(True)
        raise ValueError("Outside immutable map")

    monkeypatch.setattr(cards, "extract_fields", invalid)
    first, audit = cards.build_card(
        {}, card(), "H", relay=object(), cache_root=tmp_path / "complete"
    )
    assert len(calls) == 5 and all(g["failure"] for g in audit["groups"])
    assert all(f.value.state == "not_stated" for f in first.common_needs)
    cards.build_card({}, card(), "H", relay=object(), cache_root=tmp_path / "complete")
    assert len(calls) == 5

    def unavailable(*args):
        raise RelayUnavailable("Subscription paused")

    monkeypatch.setattr(cards, "extract_fields", unavailable)
    with pytest.raises(RelayUnavailable):
        cards.build_card({}, card(), "H", relay=object(), cache_root=tmp_path / "pending")
    assert not list((tmp_path / "pending").glob("*.json"))


def test_published_card_citation_preserves_original_offsets_and_rejects_foreign_text():
    from apps.adviser_v2.demo.citations import card_anchor
    from apps.adviser_v2.tests.test_demo_contracts import packet

    section = packet("Cover is 5 lakh\nfor 30 days.").sections[0]
    quote = Citation(section_id="s", page_id="p", quote="Cover is 5 lakh for 30 days.")
    value = {"plan_id": "plan", "field": {"citations": [quote.model_dump()]}}
    bundle = {"sections": [section.payload()]}
    anchor = card_anchor(value, bundle, quote)
    assert anchor["start"] == 100 and anchor["quote"] == "Cover is 5 lakh\nfor 30 days."
    with pytest.raises(ValueError, match="published"):
        card_anchor(value, bundle, quote.model_copy(update={"quote": "10 lakh"}))
    with pytest.raises(ValueError, match="edition"):
        card_anchor({**value, "plan_id": "other"}, bundle, quote)


def test_physical_grid_cache_reuses_pdf_work_but_binds_each_plans_citations(tmp_path, settings):
    from dataclasses import replace
    from types import SimpleNamespace
    from unittest.mock import Mock

    from apps.adviser_v2.demo.charts import physical_cells, physical_grids
    from apps.adviser_v2.tests.test_demo_contracts import packet

    settings.COVERGUIDE_REPORT_ROOT = str(tmp_path)
    table = Mock()
    table.extract.return_value = [["Cover is 5 lakh for 30 days."]]
    page = Mock()
    page.find_tables.return_value = [table]
    pdf = SimpleNamespace(pages=[page])
    document = {"sha256": "a" * 64}
    original = packet("Cover is 5 lakh for 30 days.").sections[0]

    def bundle(section):
        return {
            "pages": [
                {"document_sha256": document["sha256"], "physical_page": 1, "evidence_span_id": "p"}
            ],
            "sections": [section.payload()],
        }

    first = physical_cells(bundle(original), document, 1, pdf)
    second = physical_cells(
        bundle(replace(original, id="second-plan-section", plan_id="other")), document, 1, pdf
    )
    page.find_tables.assert_called_once()
    assert next(iter(first[0].values())).citation.section_id == "s"
    assert next(iter(second[0].values())).citation.section_id == "second-plan-section"
    import json

    cache = next(tmp_path.rglob("*.json"))
    cached = json.loads(cache.read_text())
    cached["pdfplumber"] = "obsolete"
    cache.write_text(json.dumps(cached))
    with pytest.raises(ValueError, match="identity"):
        physical_grids(document, 1, pdf)
