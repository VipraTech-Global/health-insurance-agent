"""Refine missing base fields using focused H queries, reusing validated other fields."""

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.adviser_v2.demo.card_answers import answer_card_field
from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.demo.fact_cards_v3 import CARD_FIELDS, build
from apps.adviser_v2.demo.fact_rules_v6 import clauses, project
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.models import DemoFactCard, DemoPlanIndex

QUERIES = {
    "family": "Family composition and relationships: show the actual premium chart Plan type rows 2A, 2A+1C, 2A+2C, 2A+3C, with A=Adult and C=Child, and the operative family-size/definition clause Self, Spouse and Dependent Children. Actual tariff rows are distinct from benefit illustrations; exclude worked illustrative premiums. For other products quote Eligibility / Family Definition / max up to 2A2C or Up to 2 Adults, 4 Children and allowed floater relationships.",
    "geography": "Zonal pricing / Premium zones / geographical premium rate: quote the residential-address rule, Zone I/II/III or Zone A/B/C lists, Pune if listed, and Rest of India. Include the heading and complete country coverage; distinguish premium differences from restrictions on sale or treatment territory.",
    "plan_type": "Customer Information Sheet section 3 Type of Insurance Product / Policy: Indemnity and Benefit. Quote this exact field and headings. Alternatively quote the Company's promise to indemnify actual Hospitalization Medical Expenses. Do not quote the deductible definition or multiple-policy coordination clause.",
    "sum_insured": "Prospectus Eligibility Sum Insured Options: Rs.5,00,000; Rs.7,50,000; Rs.10,00,000; Rs.15,00,000; Rs.20,00,000; Rs.25,00,000; Rs.50,00,000; Rs.75,00,000; Rs.1,00,00,000. Quote the actual complete base options printed for THIS policy, not benefit sublimits, illustrations, room limits, or bonus examples.",
}
FORCE_FIELDS = set(QUERIES)


def requested(field, index):
    if field == "family":
        return any(n in index.name for n in ("Comprehensive", "Activ One", "ProHealth"))
    if field == "geography":
        return any(n in index.name for n in ("Optima Secure", "ProHealth", "ReAssure"))
    if field == "plan_type":
        return any(n in index.name for n in ("Comprehensive", "Optima Secure", "ProHealth"))
    return any(n in index.name for n in ("Comprehensive", "Care Supreme", "Elevate", "ProHealth"))


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--source-run", required=True)
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--workers", type=int, default=2)

    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError("Local isolated cards only.")
        base = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/fact-card-runs"
        source, target = base / options["source_run"], base / options["run_id"]
        code = Path(__file__).resolve().parents[2] / "demo"
        manifest = {
            "run_id": options["run_id"],
            "source": json.loads((source / "manifest.json").read_text()),
            "queries": QUERIES,
            "method": "H",
            "packet_budget": 16000,
            "source_code": {
                n: hashlib.sha256((code / n).read_bytes()).hexdigest()
                for n in [
                    "fact_rules_v6.py",
                    "card_answers.py",
                    "card_assembly.py",
                    "card_clauses.py",
                    "search.py",
                    "validation.py",
                    "fact_cards_v3.py",
                ]
            },
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }
        if (target / "manifest.json").exists() and json.loads(
            (target / "manifest.json").read_text()
        ) != manifest:
            raise CommandError("Refinement changed; use a fresh run ID.")
        atomic_json(target / "manifest.json", manifest)
        done = (
            json.loads((target / "progress.json").read_text())["completed"]
            if (target / "progress.json").exists()
            else []
        )
        failures = []
        scheduled = {r["index"] for r in done}

        def one(item):
            close_old_connections()
            try:
                index = DemoPlanIndex.objects.get(pk=item["index"])
                bundle = bundle_for(index)
                cache = target / "fields" / index.id
                for field in CARD_FIELDS:
                    original = json.loads(
                        (source / "fields" / index.id / (field + ".json")).read_text()
                    )
                    path = cache / (field + ".json")
                    if path.exists():
                        continue
                    result = original["result"]
                    base_statements, optional_statements, _ = clauses(result, field, bundle)
                    rules = project(field, base_statements, index.variant)
                    if (
                        field in QUERIES
                        and requested(field, index)
                        and (field in FORCE_FIELDS or not base_statements or not rules)
                    ):
                        fresh = answer_card_field(
                            bundle, QUERIES[field], method="H", priority="background"
                        )
                        atomic_json(cache / (field + ".refinement.json"), fresh)
                        if fresh["status"] == "temporarily_unavailable":
                            raise RuntimeError(
                                f"{index.name}/{field}: temporary refinement failure"
                            )
                        fresh_base, fresh_optional, _ = clauses(fresh, field, bundle)
                        # Preserve previously validated independent units. A focused
                        # query must not erase valid rider evidence or base clauses.
                        if fresh["status"] == "answered" and (fresh_base or fresh_optional):
                            combined = list(fresh["answer"]["statements"])
                            for statement in (result.get("answer") or {}).get("statements", []):
                                if statement not in combined:
                                    combined.append(statement)
                            fresh["answer"]["statements"] = combined
                            original = {
                                "result": fresh,
                                "provenance": {
                                    "method": "focused_base_query",
                                    "index": index.id,
                                    "query": QUERIES[field],
                                    "source_run": options["source_run"],
                                    "source_result": result,
                                },
                            }
                        else:
                            original["provenance"] = {
                                **original["provenance"],
                                "refinement_status": fresh["status"],
                                "refinement_reason": fresh.get("reason"),
                                "query": QUERIES[field],
                            }
                    atomic_json(path, original)
                identity, card, audit = build(index, target, {}, {})
                DemoFactCard.objects.get_or_create(
                    id=identity, defaults={"index": index, "card": card, "audit_path": str(audit)}
                )
                return {
                    **item,
                    "id": identity,
                    "quoted": sum(card["field_coverage"].values()),
                    "executable": sum(card["rule_coverage"].values()),
                }
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=min(4, max(1, options["workers"]))) as pool:
            pending = {}
            while True:
                progress = (
                    json.loads((source / "progress.json").read_text())
                    if (source / "progress.json").exists()
                    else {"completed": []}
                )
                for item in progress["completed"]:
                    if item["index"] not in scheduled:
                        scheduled.add(item["index"])
                        pending[pool.submit(one, item)] = item
                for future in list(pending):
                    if not future.done():
                        continue
                    item = pending.pop(future)
                    try:
                        row = future.result()
                    except (RuntimeError, ValueError, OSError) as exc:
                        failures.append({"index": item["index"], "error": str(exc)})
                        self.stderr.write(str(exc))
                    else:
                        done.append(row)
                        self.stdout.write(json.dumps(row))
                    atomic_json(target / "progress.json", {"completed": done, "failures": failures})
                    self.stdout.flush()
                if (source / "priority.json").exists():
                    priority = {
                        r["index"]
                        for r in json.loads((source / "priority.json").read_text())["cards"]
                    }
                    if priority <= {r["index"] for r in done}:
                        atomic_json(
                            target / "priority.json",
                            {"cards": [r for r in done if r["index"] in priority], "failures": []},
                        )
                if (source / "complete.json").exists() and not pending:
                    break
                time.sleep(5)
        if failures:
            raise CommandError(
                f"{len(failures)} refinements remain pending; completed fields are cached."
            )
        atomic_json(target / "complete.json", {"cards": done, "manifest": manifest})
