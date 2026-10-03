"""Exact printed price axes are collected one at a time through chat."""

import json
import re
from pathlib import Path

from django.conf import settings

from .charts import load_prices
from .conversation import question
from .pricing import lookup


def price_step(state, cards):
    card = next((c for c in cards if c["plan_id"] == state.price_plan), None)
    if not card:
        state.price_plan = None
        return
    root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
    path = (
        Path(card["pricing_artifact"])
        if card.get("pricing_artifact")
        else root / "premiums" / (card["index_version"] + ".json")
    )
    if not path.exists():
        state.price = {"status": "source_unavailable", "amount_printed": None, "citations": []}
        return
    chart = json.loads(path.read_text())
    if chart["index_id"] != card["index_version"]:
        raise ValueError("Price source differs from the pinned index.")
    if card.get("pricing_sha256"):
        import hashlib

        if hashlib.sha256(path.read_bytes()).hexdigest() != card["pricing_sha256"]:
            raise ValueError("Pinned pricing artifact changed.")
    prices, cells = load_prices(chart)
    result = lookup(
        prices=prices,
        cells=cells,
        required_axes=set(chart["required_axes"]),
        selected=state.price_axes,
        published=True,
    )
    state.price = result.model_dump()
    state.price["axis_options"] = {
        a: sorted({p.axes[a] for p in prices}) for a in chart["required_axes"]
    }
    if result.status == "missing_details":
        axis = sorted(result.missing_axes)[0]
        if state.pending is not None:
            state.question_count -= 1
        state.pending = None
        question(
            state,
            "price_axis",
            "price:" + axis,
            prefix="Use an exact printed chart value: "
            + ", ".join(state.price["axis_options"][axis])
            + ".",
        )
    elif result.status == "available":
        # Indicative budget comparison is separate from eligibility/requirements.
        amount = re.fullmatch(
            r"(?:Rs\.?\s*|INR\s*|₹\s*)?([0-9][0-9,]*)(?:/-)?", result.amount_printed or ""
        )
        if amount and state.profile.annual_budget:
            printed = int(amount[1].replace(",", ""))
            state.price["budget_comparison"] = {
                "status": "within_printed_budget"
                if printed <= state.profile.annual_budget
                else "above_printed_budget",
                "printed_annual_amount": printed,
                "annual_budget": state.profile.annual_budget,
                "note": "Indicative printed-price comparison only; separate from fit. No tax, discount or loading inferred.",
            }
