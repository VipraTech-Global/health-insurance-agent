"""Exact printed chart lookup. No interpolation, tax, discounts or loading math."""

import re
from dataclasses import dataclass

from .contracts import Citation, PremiumResult


@dataclass(frozen=True)
class TableCell:
    id: str
    table_id: str
    row: int
    column: int
    text: str
    citation: Citation


@dataclass(frozen=True)
class PrintedPrice:
    value_cell: str
    # Every axis is tied to original, server-extracted table cells. A model cannot
    # invent a row/column coordinate or merely find the same amount elsewhere.
    axes: dict[str, str]
    axis_cells: dict[str, str]
    heading_cells: tuple[str, ...]


def validate_price(price: PrintedPrice, cells: dict[str, TableCell], required_axes: set[str]) -> bool:
    if set(price.axes) != required_axes or set(price.axis_cells) != required_axes:
        return False
    value = cells.get(price.value_cell)
    if value is None or not price.heading_cells or not re.fullmatch(r"\s*(?:Rs\.?\s*|₹\s*)?-?\d[\d,.]*(?:/-)?\s*", value.text):
        return False
    for name, identifier in price.axis_cells.items():
        label = cells.get(identifier)
        if (label is None or label.id == value.id or label.table_id != value.table_id or label.text != price.axes[name]
                or (label.row != value.row and label.column != value.column)):
            return False
    for identifier in price.heading_cells:
        label = cells.get(identifier)
        if label is None or label.table_id != value.table_id or label.row >= value.row:
            return False
    return True


def lookup(*, prices: list[PrintedPrice], cells: dict[str, TableCell], required_axes: set[str],
           selected: dict[str, str], published: bool) -> PremiumResult:
    def result(status, amount=None, missing=(), citations=()):
        return PremiumResult(status=status, amount_printed=amount, missing_axes=list(missing), citations=list(citations))

    if not published:
        return result("unpublished")
    if not prices or not required_axes or any(not validate_price(p, cells, required_axes) for p in prices):
        return result("invalid_chart")
    missing = sorted(axis for axis in required_axes if axis not in selected or not selected[axis])
    if missing:
        return result("missing_details", missing=missing)
    matches = [p for p in prices if all(selected[axis] == p.axes[axis] for axis in required_axes)]
    if not matches:
        return result("no_exact_combination")
    if len(matches) != 1:
        return result("invalid_chart")
    match = matches[0]
    cited = [match.value_cell, *match.axis_cells.values(), *match.heading_cells]
    return result("available", amount=cells[match.value_cell].text,
                  citations=[cells[key].citation for key in dict.fromkeys(cited)])
