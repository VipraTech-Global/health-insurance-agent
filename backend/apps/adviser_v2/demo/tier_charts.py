"""Compile a reviewed per-age, city-tier rate chart that spans several pages.

The HDFC my: Optima Secure prospectus prints, per plan and tier, one title and
sum-insured header followed by an age row for every year over four pages. Its
table borders do not survive extraction (whole rows go missing), so rows are
read from word positions: every amount must sit in exactly one printed sum
insured column, and ages must run in the printed order without a gap.

The charts are headed "Gross Premium". Their term, tax and coverage basis are
printed in the prospectus's own premium illustration instead, which prices a
1-year individual cover from these very cells and totals it "Excl. GST". The
compiler re-checks those illustration amounts against the parsed chart and
rejects the whole chart if any differs.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import pdfplumber

from .annual_charts import row_cells, source_quote
from .evidence import atomic_json
from .pricing import PrintedPrice, validate_price
from .validation import locate

REQUIRED_AXES = {"age", "sum_insured", "zone", "variant", "term", "tax_basis", "coverage_basis"}
SUM_INSURED = re.compile(r"\d{1,2}(?:,\d{2})*,\d{3}")
AMOUNT = re.compile(r"\d{1,2}(?:,\d{2})*,\d{3}")


@dataclass(frozen=True)
class TierAdapter:
    sha256: str
    version: str
    title: re.Pattern  # Named groups: variant, zone.
    variants: tuple[str, ...]  # Plans reviewed for this edition.
    sums_insured: tuple[str, ...]
    ages: tuple[str, ...]
    illustration: re.Pattern  # Named groups: variant, term, zone, coverage_basis, tax_basis.
    illustrated: re.Pattern  # Rows: age, amount, sum insured in lakh.


# HDFC ERGO my: Optima Secure prospectus (UIN HDFHLIP26058V082526), rate charts
# from page 69; premium computation illustration on page 55.
HDFC_OPTIMA_SECURE = TierAdapter(
    sha256="c882c2b1bd9bb25d02e47f1d1e59996bf7058ddb7016b773262eda9e5caf4726",
    version="hdfc-optima-tier-chart/1",
    title=re.compile(
        r"my: Optima Secure - (?P<variant>Optima [A-Za-z ]+?) Gross Premium - "
        r"(?P<zone>Tier [1-6]) \([^)]*\)"
    ),
    variants=("Optima Secure",),
    sums_insured=(
        "5,00,000",
        "10,00,000",
        "15,00,000",
        "20,00,000",
        "25,00,000",
        "50,00,000",
        "1,00,00,000",
        "2,00,00,000",
    ),
    ages=(*(str(n) for n in range(90)), ">=90"),
    illustration=re.compile(
        r"Illustration 1 • Plan Name – (?P<variant>Optima Secure) • Tenure – (?P<term>1 Year)"
        r" \| Location: Delhi \((?P<zone>Tier 1)\) .*? Coverage opted on "
        r"(?P<coverage_basis>individual basis) covering each member of the family separately"
        r" .*? Total premium \((?P<tax_basis>Excl\. GST)\) for all members"
    ),
    illustrated=re.compile(r"\b(\d{1,2}) (\d{1,2},\d{3}) (\d{1,2}) \d{1,2},\d{3} \d{1,2},\d{3}\b"),
)


def lines(page):
    """Printed lines as (top, words) in reading order."""
    rows = {}
    for word in page.extract_words():
        rows.setdefault(round(word["top"]), []).append(word)
    merged = []
    for top in sorted(rows):
        if merged and top - merged[-1][0] <= 2:
            merged[-1][1].extend(rows[top])
        else:
            merged.append((top, list(rows[top])))
    return [(top, sorted(words, key=lambda w: w["x0"])) for top, words in merged]


def columns(words, labels):
    """Each printed sum-insured header's x-span, or None when they differ."""
    found = [w for w in words if SUM_INSURED.fullmatch(w["text"])]
    if tuple(w["text"] for w in found) != labels:
        return None
    centres = [(w["x0"] + w["x1"]) / 2 for w in found]
    bounds = [(a + b) / 2 for a, b in zip(centres, centres[1:], strict=False)]
    return [-1e9, *bounds, 1e9]


def basis(bundle, adapter):
    """Cited term, tax and coverage basis from the premium illustration."""
    for raw in bundle["pages"]:
        if raw["document_sha256"] != adapter.sha256:
            continue
        text = " ".join(raw["passage"].split())
        match = adapter.illustration.search(text)
        if not match:
            continue
        # Map whitespace-joined offsets back to the original passage.
        index = [i for i, ch in enumerate(raw["passage"]) if not ch.isspace()]
        squeezed = [i for i, ch in enumerate(text) if ch != " "]
        position = dict(zip(squeezed, index, strict=True))
        quotes = {}
        for name in ("variant", "term", "zone", "coverage_basis", "tax_basis"):
            start, end = match.span(name)
            citation = source_quote(bundle, raw, position[start], position[end - 1] + 1)
            quotes[name] = (match[name], citation)
        rows = adapter.illustrated.findall(text[match.start() : match.end()])
        return raw, quotes, [(age, amount, lakh) for age, amount, lakh in rows]
    raise ValueError("The premium illustration that states the chart's tax basis is missing.")


def parse_tier_chart(bundle: dict, document: dict, root: Path, adapter: TierAdapter) -> dict:
    prices, cells, failures = [], {}, []
    pages = sorted(
        (p for p in bundle["pages"] if p["document_sha256"] == adapter.sha256),
        key=lambda p: p["physical_page"],
    )
    try:
        _, quotes, illustrated = basis(bundle, adapter)
    except ValueError as exc:
        quotes, illustrated = None, []
        failures.append({"reason": str(exc)})
    table = None  # The open logical table: id, heading cells, columns, next age.
    with pdfplumber.open(document["path"]) as pdf:
        for raw in pages if quotes else []:
            passage = " ".join(raw["passage"].split())
            title = adapter.title.search(passage)
            page = pdf.pages[raw["physical_page"] - 1]
            printed = lines(page)
            if title:
                table = None
                if title["variant"] not in adapter.variants:
                    continue
                table_id = f"{adapter.sha256}:{raw['physical_page']}:tier"
                header = next(
                    (words for _, words in printed if any(w["text"] == "5,00,000" for w in words)),
                    [],
                )
                bounds = columns(header, adapter.sums_insured)
                try:
                    if bounds is None:
                        raise ValueError(
                            "Printed sum-insured columns differ from the reviewed chart."
                        )
                    heading = row_cells(bundle, raw, table_id, 0, [title[0]], 0)[0]
                    heading = replace(heading, column_end=len(adapter.sums_insured))
                    headers = row_cells(bundle, raw, table_id, 1, list(adapter.sums_insured), 1)
                except ValueError as exc:
                    failures.append({"page": raw["physical_page"], "reason": str(exc)})
                    continue
                table_cells = {heading.id: heading, **{c.id: c for c in headers}}
                axes = {}
                heading_start, _ = locate(raw["passage"], heading.text)
                for name in ("variant", "zone"):
                    start, end = locate(raw["passage"][heading_start:], title[name])
                    key = heading.id + ":" + name
                    table_cells[key] = replace(
                        heading,
                        id=key,
                        text=title[name],
                        citation=source_quote(
                            bundle, raw, heading_start + start, heading_start + end
                        ),
                    )
                    axes[name] = key
                for name in ("term", "tax_basis", "coverage_basis"):
                    text, citation = quotes[name]
                    key = f"{table_id}:basis:{name}"
                    table_cells[key] = replace(
                        heading, id=key, text=text, citation=citation, outside_grid=True
                    )
                    axes[name] = key
                cells.update(table_cells)
                table = {
                    "id": table_id,
                    "axes": axes,
                    "headers": headers,
                    "heading": heading.id,
                    "bounds": bounds,
                    "next": 0,
                }
            elif table is None:
                continue
            for _, words in printed:
                if table is None or table["next"] >= len(adapter.ages):
                    break
                if not words or words[0]["text"] not in adapter.ages:
                    continue
                age, amounts = words[0]["text"], words[1:]
                row_number = 2 + table["next"]
                try:
                    if age != adapter.ages[table["next"]]:
                        raise ValueError(
                            f"Expected age {adapter.ages[table['next']]}, printed {age}."
                        )
                    if len(amounts) != len(adapter.sums_insured) or not all(
                        AMOUNT.fullmatch(w["text"]) for w in amounts
                    ):
                        raise ValueError("Amount cells are incomplete.")
                    for column, word in enumerate(amounts, 1):
                        centre = (word["x0"] + word["x1"]) / 2
                        if not table["bounds"][column - 1] <= centre < table["bounds"][column]:
                            raise ValueError("An amount sits outside its sum-insured column.")
                    values = row_cells(
                        bundle,
                        raw,
                        table["id"],
                        row_number,
                        [age, *(w["text"] for w in amounts)],
                        0,
                    )
                except ValueError as exc:
                    failures.append(
                        {"page": raw["physical_page"], "table": table["id"], "reason": str(exc)}
                    )
                    table = None
                    break
                table["next"] += 1
                cells.update({cell.id: cell for cell in values})
                for value in values[1:]:
                    axis_ids = {
                        **table["axes"],
                        "age": values[0].id,
                        "sum_insured": table["headers"][value.column - 1].id,
                    }
                    price = PrintedPrice(
                        value.id,
                        {name: cells[key].text for name, key in axis_ids.items()},
                        axis_ids,
                        (table["heading"],),
                    )
                    if not validate_price(price, cells, REQUIRED_AXES):
                        raise ValueError("Printed amount or aligned axes failed validation.")
                    prices.append(price)
            if table and table["next"] == len(adapter.ages):
                table = None
    if prices:
        # The illustration must price from these very cells, or the stated basis
        # cannot be carried over to the chart.
        for age, amount, lakh in illustrated:
            si = next(
                (s for s in adapter.sums_insured if int(s.replace(",", "")) == int(lakh) * 100_000),
                None,
            )
            match = [
                cells[p.value_cell].text
                for p in prices
                if p.axes["age"] == age
                and p.axes["sum_insured"] == si
                and p.axes["zone"] == quotes["zone"][0]
                and p.axes["variant"] == quotes["variant"][0]
            ]
            if match != [amount]:
                failures.append({"reason": f"Illustration amount {amount} is not the chart cell."})
                prices = []
                break
        if not illustrated:
            failures.append({"reason": "The illustration prints no chart amounts to check."})
            prices = []
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
        "models": [],
        "failures": failures,
        "status": "parsed" if prices else "invalid_chart",
        "scope": "Exact printed choices for the reviewed plans of this prospectus edition. "
        "Term, tax and coverage basis are cited from its premium illustration.",
    }
    atomic_json(root / "premiums" / (bundle["index_id"] + ".json"), result)
    return result
