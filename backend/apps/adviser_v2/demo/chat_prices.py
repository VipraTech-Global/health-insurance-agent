"""Exact printed price axes are collected one at a time through chat."""

import re

from .charts import load_prices
from .conversation import question
from .price_compare import load_chart
from .pricing import lookup


def price_step(state, cards):
    card = next((c for c in cards if c["plan_id"] == state.price_plan), None)
    if not card:
        state.price_plan = None
        return
    chart = load_chart(card)
    if chart is None:
        state.price = {"status": "source_unavailable", "amount_printed": None, "citations": []}
        return
    prices, cells = load_prices(chart)
    options = {a: sorted({p.axes[a] for p in prices}) for a in chart["required_axes"]}
    state.price_axes = {
        k: v for k, v in state.price_axes.items() if k in options and v in options[k]
    }
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
