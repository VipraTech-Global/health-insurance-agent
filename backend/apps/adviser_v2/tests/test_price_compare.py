import hashlib
import json
from dataclasses import asdict

from apps.adviser_v2.demo.chat_rules import fit_groups
from apps.adviser_v2.demo.conversation import interpret, list_plans, question, transition
from apps.adviser_v2.demo.conversation_contracts import (
    ChatPerson,
    ChatState,
    IncompleteProfile,
    ProposedChanges,
)
from apps.adviser_v2.demo.price_compare import band, compare, parse_zones, plan_price, zone_for
from apps.adviser_v2.demo.pricing import PrintedPrice, TableCell
from apps.adviser_v2.tests.test_demo_contracts import citation
from apps.adviser_v2.tests.test_guided_conversation import NoCalls
from apps.adviser_v2.tests.test_guided_conversation import cards as numbered

NAMES = ["Secure Alpha", "Secure Beta", "Secure Gamma", "Secure Delta", "Secure Epsilon"]


def cards(n):
    source = numbered(n)
    for c in source:
        c["name"] = NAMES[int(c["plan_id"]) % 5] + " " + "IVX"[int(c["plan_id"]) // 5]
    return source


ZONES = (
    "Zone A: Delhi, New Delhi, Alwar, Gurugram and Mumbai (including suburban)\n"
    "Zone B: Pune, Rest of Rajasthan, Rest of Maharashtra and Punjab\n"
    "Zone C: Rest Of India\nFavourable Claim Experience Discount: up to 5%."
)
# zone -> composition -> age band -> (5 lakh, 10 lakh)
GRID = {
    "Zone A": {
        "1A": {"3m-35": ("9,849", "13,129"), "36-45": ("11,000", "14,500")},
        "2A": {"18-35": ("15,000", "20,000")},
    },
    "Zone B": {
        "1A": {"3m-35": ("8,334", "11,028"), "36-45": ("9,593", "12,700")},
        "2A": {"18-35": ("13,000", "18,000")},
    },
    "Zone C": {
        "1A": {"3m-35": ("7,955", "11,028"), "36-45": ("9,100", "12,000")},
        "2A": {"18-35": ("12,000", "17,000")},
    },
}


def chart(grid=GRID):
    cells, prices = {}, []

    def cell(table, row, col, text, column_end=None):
        key = f"{table}:{row}:{col}"
        cells[key] = TableCell(key, table, row, col, text, citation(text), column_end=column_end)
        return key

    for table, rows in grid.items():
        heading = cell(table, 0, 0, "Premium chart")
        zone = cell(table, 0, 2, table, column_end=3)
        term = cell(table, 1, 2, "1 year", column_end=3)
        tax = cell(table, 2, 2, "Excluding Tax", column_end=3)
        sums = [cell(table, 3, 2, "5,00,000"), cell(table, 3, 3, "10,00,000")]
        row = 4
        for composition, ages in rows.items():
            for age, amounts in ages.items():
                labels = {
                    "composition": cell(table, row, 0, composition),
                    "age": cell(table, row, 1, age),
                    "zone": zone,
                    "term": term,
                    "tax_basis": tax,
                }
                for col, (amount, si) in enumerate(zip(amounts, sums, strict=True), start=2):
                    axis_cells = {**labels, "sum_insured": si}
                    prices.append(
                        PrintedPrice(
                            cell(table, row, col, amount),
                            {k: cells[v].text for k, v in axis_cells.items()},
                            axis_cells,
                            (heading,),
                        )
                    )
                row += 1
    payload = {
        "index_id": "index",
        "status": "parsed",
        "required_axes": sorted(prices[0].axes),
        "prices": [asdict(p) for p in prices],
        "cells": {k: asdict(v) for k, v in cells.items()},
    }
    for value in payload["cells"].values():
        value["citation"] = value["citation"].model_dump()
    return payload


def priced(source, tmp_path, index=0, payload=None, name="prices.json"):
    raw = json.dumps(payload or chart()).encode()
    path = tmp_path / name
    path.write_bytes(raw)
    source[index].update(
        pricing_artifact=str(path),
        pricing_sha256=hashlib.sha256(raw).hexdigest(),
        quoted_fields={"geography": {"citations": [{**citation(ZONES).model_dump()}]}},
    )
    return source


def one_adult(city="Kota, Rajasthan", age=35, si=500000):
    return IncompleteProfile(
        people=[ChatPerson(id="me", relationship="self", age=age)],
        city=city,
        sum_insured=si,
        plan_type="medical_indemnity",
    )


def test_zone_comes_only_from_the_printed_list():
    zones = parse_zones(ZONES)
    assert zone_for(zones, "Gurugram") == "Zone A"
    assert zone_for(zones, "New Delhi") == "Zone A"
    assert zone_for(zones, "Mumbai") == "Zone A"
    # A named district beats its state's remainder.
    assert zone_for(zones, "Alwar, Rajasthan") == "Zone A"
    assert zone_for(zones, "Kota, Rajasthan") == "Zone B"
    assert zone_for(zones, "Patna, Bihar") == "Zone C"
    # Without the state, a "Rest of <state>" entry may apply: never guess.
    assert zone_for(zones, "Kota") is None
    assert zone_for(zones, "") is None


def test_age_band_containment_is_exact():
    assert band("3m-35", 35) and band("18-35", 18) and not band("18-35", 36)
    assert band("Above 75", 76) and not band("Above 75", 75)
    assert band("60", 60) and not band("60", 61)


def test_plan_price_matches_every_axis_and_cites_zone(tmp_path):
    source = priced(cards(1), tmp_path)
    found = plan_price(source[0], one_adult(si=1000000))
    assert found["status"] == "available" and found["amount_printed"] == "11,028"
    assert found["axes"]["zone"] == "Zone B" and found["axes"]["age"] == "3m-35"
    assert found["zone_citations"][0]["quote"] == ZONES
    assert {c["quote"] for c in found["citations"]} >= {"11,028", "Zone B", "3m-35"}
    assert plan_price(source[0], one_adult(age=36))["amount_printed"] == "9,593"
    # The city's zone is not printed without the state: not found, not estimated.
    missing = plan_price(source[0], one_adult(city="Kota"))
    assert missing == {"status": "no_exact_combination", "unmatched_axes": ["zone"]}
    assert plan_price(source[0], one_adult(si=2500000))["status"] == "no_exact_combination"


def test_comparison_is_lowest_first_cited_and_names_unpriced_plans(tmp_path):
    source = priced(cards(4), tmp_path)
    cheaper = chart({z: {"1A": {"3m-35": ("7,000", "9,000")}} for z in GRID})
    priced(source, tmp_path, 2, cheaper, "cheaper.json")
    source[3]["pricing_artifact"] = str(tmp_path / "absent.json")
    state = ChatState(profile=one_adult())
    state.fit_groups = fit_groups(source, state.profile)
    record, text = compare(state, source, count=3)
    assert [r["amount_printed"] for r in record["rows"]] == ["7,000", "8,334"]
    assert text.index("₹7,000") < text.index("₹8,334")
    assert "lowest first" in text and "not a recommendation" in text
    assert "Only 2 plans of the 4 open to you have a printed premium" in text
    assert "No premium chart in its documents" in text
    assert "recommend " not in text.replace("not a recommendation", "")
    assert "best" not in text.casefold()
    names = {m["plan_id"] for m in record["not_found"]}
    assert names == {"1", "3"}


def test_family_comparison_is_declined_rather_than_guessed(tmp_path):
    source = priced(cards(1), tmp_path)
    state = ChatState(profile=one_adult())
    state.profile.people.append(ChatPerson(id="wife", relationship="spouse", age=33))
    record, text = compare(state, source)
    assert record is None and "one adult" in text


def test_premium_asks_get_a_comparison_never_a_reask(tmp_path):
    source = priced(cards(7), tmp_path)
    state = ChatState(
        profile=one_adult(si=None),
        skipped=["sum_insured", "annual_budget", "health_details"],
        answered=["needs", "options_shown"],
    )
    state.fit_groups = fit_groups(source, state.profile)
    state.plans_requested = True
    state = list_plans(state, source, lambda t, **kw: question(state, t, **kw))
    assert state.pending.template == "batch"
    changes, model = interpret(
        "provide 3 plans which are lowest budget annual", state, source, NoCalls()
    )
    assert changes.compare_prices and changes.compare_count == 3 and model is None
    state = transition(state, changes, source, relay=NoCalls())
    assert "didn’t quite catch" not in state.message
    assert state.pending.field == "price_sum_insured"
    assert state.message.startswith("Printed premiums depend on the sum insured")
    state = transition(state, ProposedChanges(sum_insured=500000), source, relay=NoCalls())
    assert "lowest first: Insurer 7 Secure Alpha I ₹8,334 (Zone B)" in state.message
    assert state.price_comparison["rows"][0]["amount_printed"] == "8,334"
    # The plan list is still on offer after the comparison.
    assert state.pending.template == "batch" and "next five" in state.message
    changes, _ = interpret(
        "tell me the annual budget premium of each plan", state, source, NoCalls()
    )
    assert changes.compare_prices and changes.compare_count is None
    state = transition(state, changes, source, relay=NoCalls())
    assert "didn’t quite catch" not in state.message and "₹8,334" in state.message


def test_unsure_sum_insured_for_a_comparison_is_not_asked_again(tmp_path):
    source = priced(cards(2), tmp_path)
    state = ChatState(
        profile=one_adult(si=None),
        skipped=["sum_insured", "annual_budget", "health_details"],
        answered=["needs", "options_shown"],
    )
    state.fit_groups = fit_groups(source, state.profile)
    state = transition(state, ProposedChanges(compare_prices=True), source, relay=NoCalls())
    assert state.pending.field == "price_sum_insured"
    changes, model = interpret("not sure", state, source, NoCalls())
    assert changes.skip and model is None
    state = transition(state, changes, source, relay=NoCalls())
    assert "I need a sum insured to look up printed premiums" in state.message
    assert state.pending.field != "price_sum_insured" and not state.compare_requested


def test_suggest_one_says_no_single_plan_is_picked():
    source = cards(3)
    state = ChatState(
        profile=one_adult(),
        skipped=["annual_budget", "health_details"],
        answered=["needs", "options_shown"],
    )
    state.fit_groups = fit_groups(source, state.profile)
    state = transition(
        state, ProposedChanges(show_plans=True, suggest=True), source, relay=NoCalls()
    )
    assert state.message.startswith("I don’t pick a single plan for you.")
    assert "A–Z order; this is not a ranking" in state.message
