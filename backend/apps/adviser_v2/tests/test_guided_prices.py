import hashlib
import json
from dataclasses import asdict

import pytest

from apps.adviser_v2.demo.chat_prices import price_step
from apps.adviser_v2.demo.conversation import merge, question
from apps.adviser_v2.demo.conversation_contracts import ChatState, ProposedChanges
from apps.adviser_v2.demo.relay import strict_schema
from apps.adviser_v2.tests.test_demo_contracts import price_data


def price_card(tmp_path):
    cells, price = price_data()
    chart = {
        "index_id": "index",
        "prices": [asdict(price)],
        "cells": {k: asdict(v) for k, v in cells.items()},
        "required_axes": ["age", "sum"],
    }
    for v in chart["cells"].values():
        v["citation"] = v["citation"].model_dump()
    raw = json.dumps(chart).encode()
    path = tmp_path / "prices.json"
    path.write_bytes(raw)
    return {
        "plan_id": "plan",
        "index_version": "index",
        "pricing_artifact": str(path),
        "pricing_sha256": hashlib.sha256(raw).hexdigest(),
    }


def test_all_volunteered_price_axes_are_retained_and_no_extra_axis_question(tmp_path):
    card = price_card(tmp_path)
    state = ChatState(price_plan="plan")
    merge(
        state,
        ProposedChanges(
            price_axes=[{"axis": "age", "value": "56–59"}, {"axis": "sum", "value": "5 lakh"}]
        ),
    )
    question(state, "city")
    state.profile.annual_budget = 20000
    price_step(state, [card])
    assert state.price["status"] == "available" and state.price["amount_printed"] == "15,000/-"
    assert state.price["budget_comparison"]["status"] == "within_printed_budget"
    assert state.pending.field == "city" and state.question_count == 1
    schema = strict_schema(ProposedChanges.model_json_schema())
    assert schema["$defs"]["PriceChoice"]["required"] == ["axis", "value"]
    assert schema["$defs"]["PriceChoice"]["additionalProperties"] is False


def test_one_missing_axis_question_and_no_inferred_age_band(tmp_path):
    card = price_card(tmp_path)
    state = ChatState(price_plan="plan", price_axes={"age": "57", "sum": "5 lakh"})
    question(state, "city")
    price_step(state, [card])
    assert state.pending.field == "price:age" and state.question_count == 1
    assert state.price["status"] == "missing_details" and state.price["amount_printed"] is None
    assert "age" not in state.price_axes
    assert state.message.count("?") == 1
    state.price_axes["age"] = "56–59"
    card["pricing_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="changed"):
        price_step(state, [card])
