"""Read physical table grids, then ask the allowed relay to label printed axes.

Unresolvable merged cells, missing context, ambiguous raw offsets and unsupported
axes remain invalid. There is no amount interpolation or inferred tax treatment.
"""

from __future__ import annotations

import fcntl
import json
from contextlib import nullcontext
from dataclasses import asdict
from pathlib import Path

import pdfplumber
from django.conf import settings
from pydantic import Field

from .contracts import Citation, Closed
from .evidence import Section, atomic_json
from .pricing import PrintedPrice, TableCell, validate_price
from .relay import InvalidOutput, Relay, RelayUnavailable
from .validation import fold, locate

AXES = {
    "age",
    "sum_insured",
    "variant",
    "zone",
    "composition",
    "term",
    "coverage_basis",
    "tax_basis",
}


class Axes(Closed):
    age: str
    sum_insured: str
    variant: str
    zone: str
    composition: str
    term: str
    coverage_basis: str
    tax_basis: str


class PriceRow(Closed):
    value_cell: str
    axes: Axes
    axis_cells: Axes
    heading_cells: list[str]


class ChartLabels(Closed):
    prices: list[PriceRow] = Field(max_length=120)


def cell_payload(cell):
    return {**asdict(cell), "citation": cell.citation.model_dump()}


def source_citation(sources, page_id, text):
    matches = []
    for section_id, segments in sources:
        for segment in segments:
            try:
                locate(segment.text, text)
            except ValueError:
                continue
            if fold(segment.text).count(fold(text)) == 1:
                matches.append(Citation(section_id=section_id, page_id=page_id, quote=text))
    return matches[0] if len(matches) == 1 else None


def physical_grids(document, page_number, pdf):
    """Extract a physical page grid once, then bind it to each plan's sections."""
    root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/physical-grids"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{document['sha256']}-{page_number}.json"
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            saved = json.loads(path.read_text())
            if (
                saved.get("version") != "pdfplumber-grid/1"
                or saved.get("pdf_sha256") != document["sha256"]
                or saved.get("page") != page_number
                or saved.get("pdfplumber") != pdfplumber.__version__
            ):
                raise ValueError("Physical table cache identity differs.")
            return saved["grids"]
        with nullcontext(pdf) if pdf is not None else pdfplumber.open(document["path"]) as opened:
            grids = [table.extract() for table in opened.pages[page_number - 1].find_tables()]
        atomic_json(
            path,
            {
                "version": "pdfplumber-grid/1",
                "pdf_sha256": document["sha256"],
                "page": page_number,
                "pdfplumber": pdfplumber.__version__,
                "grids": grids,
            },
        )
        return grids


def physical_cells(bundle, document, page_number, pdf=None):
    raw = next(
        p
        for p in bundle["pages"]
        if p["document_sha256"] == document["sha256"] and p["physical_page"] == page_number
    )
    sources = [
        (s.id, [p for p in s.segments if p.page_id == raw["evidence_span_id"]])
        for s in (Section.from_payload(payload) for payload in bundle["sections"])
    ]
    sources = [(key, segments) for key, segments in sources if segments]
    result = []
    for n, grid in enumerate(physical_grids(document, page_number, pdf)):
        table_id = f"{document['sha256']}:{page_number}:{n}"
        cells = {}
        for r, row in enumerate(grid):
            for c, text in enumerate(row):
                if not text or len(text) > 1600:
                    continue
                citation = source_citation(sources, raw["evidence_span_id"], text)
                if citation:
                    key = f"{table_id}:{r}:{c}"
                    cells[key] = TableCell(key, table_id, r, c, text, citation)
        if cells:
            result.append(cells)
    return result


def parse_chart(bundle: dict, root: Path, relay=None) -> dict:
    relay = relay or Relay.configured()
    from .annual_charts import SOURCE_SHA, parse_annual_chart
    from .reviewed_charts import ADAPTERS, parse_reviewed_chart

    annual = next((d for d in bundle["documents"] if d["sha256"] == SOURCE_SHA), None)
    if annual:
        return parse_annual_chart(bundle, annual, root, relay)
    reviewed = next((d for d in bundle["documents"] if d["sha256"] in ADAPTERS), None)
    if reviewed:
        return parse_reviewed_chart(bundle, reviewed, root, ADAPTERS[reviewed["sha256"]])
    directory = root / "charts" / bundle["index_id"]
    accepted, all_cells, failures, models = [], {}, [], set()
    # Charts may be included in a prospectus or brochure. Titles/summary maps are
    # intentionally absent from this source-only parser.
    documents = [
        d for d in bundle["documents"] if d["role"] in {"premium_chart", "prospectus", "brochure"}
    ]
    found = False
    for document in documents:
        pages = [p for p in bundle["pages"] if p["document_sha256"] == document["sha256"]]
        for page in pages:
            text = page["passage"].casefold()
            if document["role"] != "premium_chart" and not (
                "premium" in text and ("chart" in text or "rate table" in text)
            ):
                continue
            for cells in physical_cells(bundle, document, page["physical_page"]):
                if len(cells) < 10:
                    continue
                found = True
                table_id = next(iter(cells.values())).table_id
                path = directory / (table_id.replace(":", "-") + ".json")
                if path.exists():
                    saved = json.loads(path.read_text())
                else:
                    messages = [
                        {
                            "role": "user",
                            "content": json.dumps(
                                {
                                    "table": [cell_payload(c) for c in cells.values()],
                                    "page_text": page["passage"],
                                    "selected_variant": bundle.get("variant", "Default"),
                                }
                            ),
                        }
                    ]
                    try:
                        result = relay.call(
                            instructions=(
                                "Label exact printed premium cells and their axes using the supplied physical grid. "
                                "Return each amount only if ALL axes age, sum_insured, variant, zone, composition, term, "
                                "coverage_basis, tax_basis are explicit in supplied cells. axes values must equal their original cell text. "
                                "Only annual, explicitly tax-excluded premiums qualify for this display. "
                                "Use existing cell IDs. Every axis label must be in the value cell row or column. Include "
                                "all necessary table headings. Keep printed anomalies unchanged. Do not derive defaults, "
                                "calculate amounts, tax, loadings or discounts. Skip ambiguous or incomplete tables."
                            ),
                            messages=messages,
                            schema=ChartLabels.model_json_schema(),
                            stage="premium_chart",
                            max_tokens=8192,
                            timeout=1800,
                        )
                        draft = ChartLabels.model_validate(result.value)
                        saved = {
                            "model": result.model,
                            "call_ids": result.call_ids,
                            "prices": draft.model_dump()["prices"],
                        }
                        atomic_json(path, saved)
                    except (RelayUnavailable, InvalidOutput, ValueError) as exc:
                        failures.append({"table": table_id, "reason": str(exc)})
                        continue
                models.add(saved["model"])
                all_cells.update(cells)
                if not saved["prices"]:
                    failures.append(
                        {
                            "table": table_id,
                            "reason": "Parser could not establish every required printed axis.",
                        }
                    )
                for payload in saved["prices"]:
                    price = PrintedPrice(
                        **{**payload, "heading_cells": tuple(payload["heading_cells"])}
                    )
                    if validate_price(price, cells, AXES):
                        accepted.append(price)
                    else:
                        failures.append(
                            {
                                "table": table_id,
                                "reason": "Printed row/column/variant axes failed validation.",
                            }
                        )
    result = {
        "index_id": bundle["index_id"],
        "required_axes": sorted(AXES),
        "prices": [asdict(p) for p in accepted],
        "cells": {key: cell_payload(c) for key, c in all_cells.items()},
        "models": sorted(models),
        "failures": failures,
        "status": "parsed" if accepted else ("invalid_chart" if found else "source_unavailable"),
    }
    atomic_json(root / "premiums" / (bundle["index_id"] + ".json"), result)
    return result


def load_prices(payload: dict):
    cells = {
        key: TableCell(**{**value, "citation": Citation.model_validate(value["citation"])})
        for key, value in payload["cells"].items()
    }
    prices = [
        PrintedPrice(**{**value, "heading_cells": tuple(value["heading_cells"])})
        for value in payload["prices"]
    ]
    return prices, cells
