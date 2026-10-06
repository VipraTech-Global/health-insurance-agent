import json
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from apps.adviser_v2.demo import reviewed_charts
from apps.adviser_v2.demo.page_charts import NIVA_REASSURE_3, basis, compile_page, zone_list
from apps.adviser_v2.demo.premium_sources import VERSION, linked, with_premium_sources
from apps.adviser_v2.demo.price_compare import LISTED_ZONE, band, parse_zones, plan_price
from apps.adviser_v2.demo.pricing import PrintedPrice, TableCell
from apps.adviser_v2.tests.test_demo_contracts import citation, packet
from apps.adviser_v2.tests.test_price_compare import cards, one_adult
from apps.adviser_v2.tests.test_reviewed_charts import source

ADAPTER = replace(NIVA_REASSURE_3, compositions=("1A", "2A"), ages=("18-25", "91++"))
PAGE = [
    "Zone: 7",
    "Classic (1000000)",
    "Age 1A 2A",
    "18-25 6,361 10,100",
    "91++ 40,000 70,000",
    "All premiums are in INR, excluding GST.",
]


def printed(lines=PAGE, shift=None):
    """A page whose words sit in column order: Age, then one column per composition."""
    words = []
    for n, line in enumerate(lines):
        for column, text in enumerate(line.split()):
            x0 = 100 * column + (shift or {}).get((n, column), 0)
            words.append({"text": text, "x0": x0, "x1": x0 + 40, "top": 20 * n})
    return SimpleNamespace(extract_words=lambda: words)


def test_a_page_chart_binds_amounts_to_its_printed_zone_plan_and_tax_basis():
    bundle, raw = source([[line] for line in PAGE])
    cells, axes, headers, rows, heading = compile_page(bundle, raw, printed(), ADAPTER)
    assert {name: cells[key].text for name, key in axes.items()} == {
        "zone": "Zone: 7",
        "variant": "Classic",
        "sum_insured": "1000000",
        "tax_basis": "excluding GST",
    }
    # The footnote states the basis for the whole page, outside the grid.
    assert cells[axes["tax_basis"]].outside_grid
    assert cells[axes["tax_basis"]].citation.quote == "excluding GST"
    assert [h.text for h in headers] == ["Age", "1A", "2A"]
    assert [[c.text for c in row] for row in rows] == [
        ["18-25", "6,361", "10,100"],
        ["91++", "40,000", "70,000"],
    ]
    assert rows[1][2].citation.quote == "70,000" and heading == (
        axes["zone"],
        cells[axes["variant"]].id.rsplit(":", 1)[0],
    )


def test_a_page_chart_rejects_rather_than_guesses_a_differing_page():
    bundle, raw = source([[line] for line in PAGE])
    # An amount printed under the next composition's header.
    with pytest.raises(ValueError, match="outside its column"):
        compile_page(bundle, raw, printed(shift={(3, 1): 70}), ADAPTER)
    swapped = [*PAGE[:3], PAGE[4], PAGE[3], PAGE[5]]
    bundle, raw = source([[line] for line in swapped])
    with pytest.raises(ValueError, match="Age rows differ"):
        compile_page(bundle, raw, printed(swapped), ADAPTER)
    untaxed = PAGE[:5]
    bundle, raw = source([[line] for line in untaxed])
    with pytest.raises(ValueError, match="tax basis"):
        compile_page(bundle, raw, printed(untaxed), ADAPTER)


def test_the_term_is_cited_from_the_same_uin_prospectus():
    bundle, raw = source(
        [["Plans: Classic, Select. The default policy term for all plans is one year."]]
    )
    bundle["pages"] = [{**raw, "document_sha256": "chart"}]
    with pytest.raises(ValueError, match="policy term is missing"):
        basis(bundle, ADAPTER)
    bundle["pages"] = [{**raw, "document_sha256": ADAPTER.term_sha256}]
    term, quote = basis(bundle, ADAPTER)
    assert term == "one year" and quote.quote == "one year"


def test_the_charts_zone_list_is_cited_one_zone_at_a_time():
    text = (
        "Zone 1 Delhi, Mumbai Zone 2 Gujurat, Rest of Rajasthan "
        "Zone 3 Assam, Nagaland, Puducherry, Tripura"
    )
    bundle, raw = source([[text]])
    quotes = [c["quote"] for c in zone_list(bundle, [raw], ADAPTER)["zones"]]
    assert quotes == [
        "Zone 1 Delhi, Mumbai",
        "Zone 2 Gujurat, Rest of Rajasthan",
        "Zone 3 Assam, Nagaland, Puducherry, Tripura",
    ]
    zones = parse_zones(" ".join(quotes), LISTED_ZONE)
    # Insurers' state spellings are read as the state.
    assert zones["Zone 2"] == ["gujarat", "rest of rajasthan"]


def test_an_open_ended_double_plus_age_row():
    assert band("91++", 91) and band("91++", 99) and not band("91++", 90)


def chart(index="index"):
    cells, prices = {}, []

    def cell(table, row, col, text, **kw):
        key = f"{table}:{row}:{col}"
        cells[key] = TableCell(key, table, row, col, text, citation(text), **kw)
        return key

    for table, zone, variant, amount in (
        ("p1", "Zone: 1", "Classic", "6,638"),
        ("p2", "Zone: 7", "Classic", "6,361"),
        # Another page prints the plan's name in capitals.
        ("p3", "Zone: 7", "CLASSIC", "6,361"),
        ("p4", "Zone: 7", "Select", "7,306"),
    ):
        axis_cells = {
            "zone": cell(table, 0, 0, zone, column_end=2),
            "variant": cell(table, 1, 0, variant, column_end=2),
            "sum_insured": cell(table, 1, 1, "1000000" if table != "p3" else "500000"),
            "composition": cell(table, 2, 1, "1A"),
            "age": cell(table, 3, 0, "31-35"),
            "term": cell(table, 0, 1, "one year", outside_grid=True),
            "tax_basis": cell(table, 0, 2, "excluding GST", outside_grid=True),
        }
        value = cell(table, 3, 1, amount)
        prices.append(
            PrintedPrice(
                value,
                {k: cells[v].text for k, v in axis_cells.items()},
                axis_cells,
                (axis_cells["zone"],),
            )
        )
    zones = ["Zone 1 Delhi, Mumbai", "Zone 7 Rest of Rajasthan, Bihar"]
    payload = {
        "index_id": index,
        "status": "parsed",
        "required_axes": sorted(prices[0].axes),
        "prices": [asdict(p) for p in prices],
        "cells": {k: asdict(v) | {"citation": v.citation.model_dump()} for k, v in cells.items()},
        "zone_lists": [{"zones": [citation(z).model_dump() for z in zones]}],
    }
    return payload


def test_a_chart_printed_zone_list_places_the_city_and_opens_from_the_chart(tmp_path):
    path = tmp_path / "prices.json"
    path.write_text(json.dumps(chart()))
    card = {**cards(1)[0], "variant": "Classic", "pricing_artifact": str(path)}
    card.pop("pricing_sha256", None)
    card["quoted_fields"] = {}
    found = plan_price(card, one_adult(si=1000000))
    assert found["status"] == "available" and found["amount_printed"] == "6,361"
    assert found["axes"]["zone"] == "Zone: 7" and found["axes"]["term"] == "one year"
    # Only the one printed zone line naming the city, opened from the chart.
    assert [c["quote"] for c in found["chart_zone_citations"]] == [
        "Zone 7 Rest of Rajasthan, Bihar"
    ]
    assert found["zone_citations"] == []
    assert plan_price(card, one_adult(city="New Delhi", si=1000000))["amount_printed"] == "6,638"
    # Both spellings of the plan narrow to one page once the other axes are fixed.
    assert plan_price(card, one_adult(si=500000))["amount_printed"] == "6,361"
    assert plan_price({**card, "variant": "Select"}, one_adult(si=1000000))["amount_printed"] == (
        "7,306"
    )


def test_a_chart_zone_citation_anchors_only_within_its_own_list():
    from apps.adviser_v2.demo.citations import price_anchor

    text = "Zone 7 Rest of Rajasthan, Bihar"
    bundle = {"sections": [packet(text).sections[0].payload()]}
    payload = chart()
    payload["zone_lists"] = [{"zones": [citation(text).model_dump()]}]
    anchor = price_anchor(payload, bundle, "plan", citation(text))
    assert anchor["quote"] == text
    payload["zone_lists"] = []
    with pytest.raises(ValueError, match="not in a validated printed price"):
        price_anchor(payload, bundle, "plan", citation(text))


def manifest(root, sha, uins):
    passage = "Premium chart UIN: " + " ".join(uins)
    page = {
        "evidence_span_id": sha + ":1",
        "physical_page": 1,
        "document_char_start": 0,
        "document_sha256": sha,
        "passage": passage,
    }
    document = {
        "sha256": sha,
        "document_version_id": "chart-" + sha[:4],
        "observed_uins": uins,
        "role": "premium_chart",
    }
    record = {"version": VERSION, "document": document, "pages": [page]}
    path = root / "premium-sources" / (sha + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))
    return record


def test_a_premium_chart_links_only_by_its_printed_uin_and_a_reviewed_adapter(
    tmp_path, monkeypatch
):
    reviewed, unreviewed = "a" * 64, "b" * 64
    monkeypatch.setitem(reviewed_charts.ADAPTERS, reviewed, NIVA_REASSURE_3)
    manifest(tmp_path, reviewed, ["NBHHLIP26047V012526"])
    manifest(tmp_path, unreviewed, ["NBHHLIP26047V012526"])
    assert [m["document"]["sha256"] for m in linked("NBHHLIP26047V012526", tmp_path)] == [reviewed]
    # Another edition's UIN never links, nor does a missing one.
    assert linked("NBHHLIP26047V022526", tmp_path) == []
    assert linked("", tmp_path) == []
    bundle = {
        "documents": [{"sha256": "plan"}],
        "pages": [],
        "sections": [packet().sections[0].payload()],
    }
    merged = with_premium_sources(bundle, "NBHHLIP26047V012526", tmp_path)
    assert [d["sha256"] for d in merged["documents"]] == ["plan", reviewed]
    added = merged["sections"][1:]
    # The chart's sections join the plan's evidence under the plan's own ID.
    assert added and {s["plan_id"] for s in added} == {"plan"}
    assert bundle["sections"] == [packet().sections[0].payload()]
    assert with_premium_sources(bundle, "NIAHLIP25039V102425", tmp_path) is bundle
    # A record renamed away from its content hash is refused.
    (tmp_path / "premium-sources" / (reviewed + ".json")).rename(
        tmp_path / "premium-sources" / ("c" * 64 + ".json")
    )
    with pytest.raises(ValueError, match="pinned hash"):
        linked("NBHHLIP26047V012526", tmp_path)
