import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pdfplumber
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.charts import cell_payload, physical_cells
from apps.adviser_v2.demo.evidence import atomic_json, digest


def stored(payload):
    # Tables store these six fields; a span is added only on a cell that spans.
    return {
        k: v
        for k, v in payload.items()
        if k in ("id", "table_id", "row", "column", "text", "citation")
        or (k in ("row_end", "column_end") and v is not None)
    }


class Command(BaseCommand):
    help = (
        "Preserve original table coordinates and exact source cells before freezing scored packets."
    )

    def add_arguments(self, parser):
        parser.add_argument("--source-root", type=Path)
        parser.add_argument(
            "--plan-key",
            action="append",
            default=[],
            help="Re-read only these plans (policy version IDs), citing repeated table text "
            "by its printed position and recording merged cells' spans. Other plans keep "
            "their tables unchanged.",
        )

    def handle(self, **options):
        root = options["source_root"] or Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        corpus = json.loads((root / "sections.json").read_text())
        selected = set(options["plan_key"])
        plans = [p for p in corpus["plans"] if not selected or p["policy_version_id"] in selected]
        unknown = selected - {p["policy_version_id"] for p in plans}
        if unknown:
            raise CommandError("Unknown plan key: " + ", ".join(sorted(unknown)))
        geometry = bool(selected)
        # Version 3 adds merged cells' spans to version 2's position-cited repeated text.
        version = "physical-tables/3" if geometry else "physical-tables/1"

        def plan_tables(plan):
            regions = []
            for document in plan["documents"]:
                key = digest([document["sha256"], [s["id"] for s in plan["sections"]], version])
                path = root / "tables" / (key + ".json")
                if path.exists():
                    regions.extend(json.loads(path.read_text()))
                    continue
                found = []
                with pdfplumber.open(document["path"]) as pdf:
                    for number in range(1, len(pdf.pages) + 1):
                        for cells in physical_cells(
                            plan, document, number, pdf=pdf, geometry=geometry
                        ):
                            if len(cells) < 3:
                                continue
                            found.append(
                                {
                                    "id": next(iter(cells.values())).table_id,
                                    "document_id": document["document_version_id"],
                                    "page": number,
                                    "cells": {
                                        key: stored(cell_payload(cell))
                                        for key, cell in cells.items()
                                    },
                                }
                            )
                        pdf.pages[number - 1].close()
                atomic_json(path, found)
                regions.extend(found)
            return plan["policy_version_id"], regions

        with ThreadPoolExecutor(max_workers=2) as pool:
            for future in as_completed([pool.submit(plan_tables, p) for p in plans]):
                key, tables = future.result()
                next(p for p in corpus["plans"] if p["policy_version_id"] == key)["tables"] = tables
                self.stdout.write(
                    f"{key}: {len(tables)} physical table regions with exact source cells"
                )
                self.stdout.flush()
        corpus.pop("sha256", None)
        corpus["sha256"] = digest(corpus)
        atomic_json(root / "sections.json", corpus)
