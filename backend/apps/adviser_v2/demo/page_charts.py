"""Compile a reviewed rate chart that prints one zone, plan and sum insured per page.

The Niva Bupa ReAssure 3.0 premium chart heads every page with its zone and a
"<variant> (<sum insured>)" line, prints member compositions across and ages
down, and footnotes every page "excluding GST". Rows are read from word
positions: every amount must sit in its printed composition column and ages
must run in the reviewed order.

The chart does not print a term. The same-UIN prospectus states the product's
default policy term ("one year", other terms carrying a discount), which is
cited for every chart amount. Its premium illustration is not used: it does
not reproduce this chart's cells. The chart's own zone list is cited for zones.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import pdfplumber

from .annual_charts import row_cells, source_quote
from .evidence import atomic_json
from .pricing import PrintedPrice, validate_price
from .tier_charts import lines
from .validation import locate

REQUIRED_AXES = {"age", "sum_insured", "composition", "zone", "variant", "term", "tax_basis"}
AMOUNT = re.compile(r"\d{1,2}(?:,\d{2})*,\d{3}|\d{1,3},\d{3}")


@dataclass(frozen=True)
class PageAdapter:
    sha256: str
    version: str
    zone: re.Pattern  # A page's zone line.
    table: re.Pattern  # Named groups: variant, sum_insured.
    tax_basis: re.Pattern  # Every page's footnote; named group tax_basis.
    compositions: tuple[str, ...]
    ages: tuple[str, ...]
    zone_list: re.Pattern  # The printed zone list.
    term_sha256: str  # The document that states the default term.
    term: re.Pattern  # Named group term.


# Niva Bupa ReAssure 3.0 premium chart (prints UIN NBHHLIP26047V012526): pages
# 2-33 unlimited sum insured, 37-100 Rs 5 and 10 lakh; zone list on page 34.
# Default term on page 1 of the ReAssure 3.0 prospectus.
NIVA_REASSURE_3 = PageAdapter(
    sha256="1a41cd628b0a3573588ac1af022ee2503313fd5f9c07f4c8bc36b63bf9ed8ef5",
    version="niva-reassure-page-chart/1",
    zone=re.compile(r"Zone: [1-8]"),
    table=re.compile(
        r"(?P<variant>Classic|Select|Elite|Black) "
        r"\((?P<sum_insured>500000|1000000|Unlimited Sum Insured\*)\)",
        re.I,
    ),
    tax_basis=re.compile(r"All premiums are in INR, (?P<tax_basis>excluding GST)\."),
    compositions=("1A", "1A1C", "1A2C", "1A3C", "1A4C", "2A", "2A1C", "2A2C", "2A3C", "2A4C"),
    ages=(
        "18-25",
        "26-30",
        "31-35",
        "36-40",
        "41-45",
        "46-50",
        "51-55",
        "56-59",
        *(str(n) for n in range(60, 91)),
        "91++",
    ),
    zone_list=re.compile(r"Zone 1 Delhi,.*? Nagaland, Puducherry, Tripura"),
    term_sha256="95cde57fc755b024a80610b8d4b61d59f593c8ff0f8990ac387a6a5efd498d3b",
    term=re.compile(r"The default policy term for all plans is (?P<term>one year)\."),
)


def squeezed(raw, pattern):
    """A pattern's match on the whitespace-joined page, with original offsets."""
    text = " ".join(raw["passage"].split())
    match = pattern.search(text)
    if not match:
        return None, None
    index = [i for i, ch in enumerate(raw["passage"]) if not ch.isspace()]
    joined = [i for i, ch in enumerate(text) if ch != " "]
    position = dict(zip(joined, index, strict=True))

    def span(name=0):
        start, end = match.span(name)
        return position[start], position[end - 1] + 1

    return match, span


def basis(bundle, adapter):
    """The cited default policy term."""
    for raw in bundle["pages"]:
        if raw["document_sha256"] != adapter.term_sha256:
            continue
        match, span = squeezed(raw, adapter.term)
        if match:
            return match["term"], source_quote(bundle, raw, *span("term"))
    raise ValueError("The statement of the chart's policy term is missing.")


def zone_list(bundle, pages, adapter):
    """The printed zone list, cited one zone at a time."""
    from .price_compare import LISTED_ZONE

    for raw in pages:
        match, span = squeezed(raw, adapter.zone_list)
        if not match:
            continue
        start, end = span()
        text = raw["passage"][start:end]
        heads = [m.start() for m in LISTED_ZONE.finditer(text)]
        citations = []
        for first, last in zip(heads, [*heads[1:], len(text)], strict=True):
            chunk = text[first:last].rstrip()
            citations.append(
                source_quote(bundle, raw, start + first, start + first + len(chunk)).model_dump()
            )
        return {"zones": citations}
    raise ValueError("The chart's printed zone list is missing.")


def bounds(words, labels):
    """Each printed composition header's x-span, or None when they differ."""
    found = words[1:]
    if not words or words[0]["text"] != "Age" or tuple(w["text"] for w in found) != labels:
        return None
    centres = [(w["x0"] + w["x1"]) / 2 for w in found]
    middles = [(a + b) / 2 for a, b in zip(centres, centres[1:], strict=False)]
    return [-1e9, *middles, 1e9]


def compile_page(bundle, raw, page, adapter):
    """One page's prices, cells and failures."""
    passage = " ".join(raw["passage"].split())
    zone = adapter.zone.search(passage)
    printed = lines(page)
    texts = [" ".join(w["text"] for w in words) for _, words in printed]
    table = next((t for t in texts if adapter.table.fullmatch(t)), None)
    tax, tax_span = squeezed(raw, adapter.tax_basis)
    if not zone or table is None or tax is None or zone[0] not in texts:
        raise ValueError("Printed zone, plan or tax basis differs from the reviewed layout.")
    title = adapter.table.fullmatch(table)
    table_id = f"{adapter.sha256}:{raw['physical_page']}:page"
    width = len(adapter.compositions)
    heading = replace(row_cells(bundle, raw, table_id, 0, [zone[0]], 0)[0], column_end=width)
    line = replace(row_cells(bundle, raw, table_id, 1, [table], 0)[0], column_end=width)
    header = next((words for _, words in printed if words and words[0]["text"] == "Age"), [])
    columns = bounds(header, adapter.compositions)
    if columns is None:
        raise ValueError("Printed composition columns differ from the reviewed chart.")
    headers = row_cells(bundle, raw, table_id, 2, ["Age", *adapter.compositions], 0)
    cells = {heading.id: heading, line.id: line, **{c.id: c for c in headers}}
    axes = {"zone": heading.id}
    line_start, _ = locate(raw["passage"], line.text)
    for name in ("variant", "sum_insured"):
        start, end = locate(raw["passage"][line_start:], title[name])
        key = line.id + ":" + name
        cells[key] = replace(
            line,
            id=key,
            text=title[name],
            citation=source_quote(bundle, raw, line_start + start, line_start + end),
        )
        axes[name] = key
    key = f"{table_id}:basis:tax_basis"
    cells[key] = replace(
        heading,
        id=key,
        text=tax["tax_basis"],
        citation=source_quote(bundle, raw, *tax_span("tax_basis")),
        outside_grid=True,
    )
    axes["tax_basis"] = key
    rows = [words for _, words in printed if words and words[0]["text"] in adapter.ages]
    if tuple(words[0]["text"] for words in rows) != adapter.ages:
        raise ValueError("Age rows differ from the reviewed printed order.")
    values_by_row = []
    for number, words in enumerate(rows, 3):
        amounts = words[1:]
        if len(amounts) != width or not all(AMOUNT.fullmatch(w["text"]) for w in amounts):
            raise ValueError(f"Row {words[0]['text']}: amount cells are incomplete.")
        for column, word in enumerate(amounts, 1):
            centre = (word["x0"] + word["x1"]) / 2
            if not columns[column - 1] <= centre < columns[column]:
                raise ValueError(f"Row {words[0]['text']}: an amount is outside its column.")
        values_by_row.append(
            row_cells(bundle, raw, table_id, number, [w["text"] for w in words], 0)
        )
    return cells, axes, headers, values_by_row, (heading.id, line.id)


def parse_page_chart(bundle: dict, document: dict, root: Path, adapter: PageAdapter) -> dict:
    prices, cells, failures, zones = [], {}, [], []
    pages = sorted(
        (p for p in bundle["pages"] if p["document_sha256"] == adapter.sha256),
        key=lambda p: p["physical_page"],
    )
    try:
        term, term_citation = basis(bundle, adapter)
        zones = [zone_list(bundle, pages, adapter)]
    except ValueError as exc:
        term = None
        failures.append({"reason": str(exc)})
    with pdfplumber.open(document["path"]) as pdf:
        for raw in pages if term else []:
            page = pdf.pages[raw["physical_page"] - 1]
            if not any(adapter.zone.fullmatch(t.strip()) for t in raw["passage"].split("\n")):
                continue
            try:
                table_cells, axes, headers, rows, heading = compile_page(bundle, raw, page, adapter)
            except ValueError as exc:
                failures.append({"page": raw["physical_page"], "reason": str(exc)})
                continue
            key = f"{adapter.sha256}:{raw['physical_page']}:page:basis:term"
            first = table_cells[heading[0]]
            table_cells[key] = replace(
                first, id=key, text=term, citation=term_citation, outside_grid=True
            )
            axes = {**axes, "term": key}
            cells.update(table_cells)
            for values in rows:
                cells.update({cell.id: cell for cell in values})
                for value in values[1:]:
                    axis_ids = {
                        **axes,
                        "age": values[0].id,
                        "composition": headers[value.column].id,
                    }
                    price = PrintedPrice(
                        value.id,
                        {name: cells[k].text for name, k in axis_ids.items()},
                        axis_ids,
                        heading,
                    )
                    if not validate_price(price, cells, REQUIRED_AXES):
                        raise ValueError("Printed amount or aligned axes failed validation.")
                    prices.append(price)
    result = {
        "index_id": bundle["index_id"],
        "parser_version": adapter.version,
        "required_axes": sorted(REQUIRED_AXES),
        "prices": [asdict(p) for p in prices],
        "cells": {
            key: asdict(c) | {"citation": c.citation.model_dump()} for key, c in cells.items()
        }
        if prices
        else {},
        "zone_lists": zones if prices else [],
        "models": [],
        "failures": failures,
        "status": "parsed" if prices else "invalid_chart",
        "scope": "Exact printed choices from the insurer's separately published premium chart. "
        "Its term is the prospectus's cited default policy term.",
    }
    atomic_json(root / "premiums" / (bundle["index_id"] + ".json"), result)
    return result
