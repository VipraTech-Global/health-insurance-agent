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
    "geography": "Purchase eligibility and residential geography: is this policy available to Indian residents across India? Quote the eligibility/residence clause and any geographic sales restriction. If zones apply only to premium payment or pricing, quote that heading and all-India/rest-of-India applicability. Do not substitute treatment territory for purchase eligibility.",
    "coverage_basis": "Eligibility / Type of Policy / Basis of Cover: quote whether available as Individual and Family Floater, and how the sum insured applies. Include operative policy/prospectus headings and all bases. Exclude benefit illustrations, Coverage opted examples and assumed premiums.",
    "maternity": "Base Benefit — Delivery Expenses / Maternity Expenses / Maternity Cover: quote the operative clause reimbursing normal or caesarean delivery, the waiting period, age and delivery-count conditions and sublimits. Identify any general maternity exclusion exception for this base benefit. Do not substitute optional Parenthood or rider coverage.",
    "opd": "Permanent exclusions — Outpatient / OPD treatment: quote the base-policy exclusion for outpatient medical treatment and its governing exclusion introduction. Separately identify optional BeFit or Optima Wellbeing; an optional cover is not base. Health-check vouchers are not OPD.",
    "sum_insured": "Base Sum Insured options for this variant: quote the complete selectable choices and headings, including 5 lakh, 10 lakh and Unlimited if printed. Do not quote Booster+, accumulated cover, worked examples, benefit sublimits or premium amounts. Preserve the complete list and its units.",
    "copay": "Mandatory base co-payment for this selected variant, distinct from optional Co-Payment choice/menu requiring a discount or customer selection. Quote the baseline co-pay and optional heading separately; do not label an optional 10 percent choice as base.",
    "room_limit": "Base Room Rent / Room Category entitlement for this selected variant. Quote its actual row and column: exclusions of Deluxe or Suite must be retained. Distinguish the base single-private entitlement from an optional Room Modifier/upgrade. Do not use general room definitions as entitlement.",
    "family": "Eligibility — Family Floater composition: quote adult and dependent child maximums, allowed relationships including self/spouse/parents, and combination conditions. Use operative policy/prospectus eligibility, not benefit illustrations.",
    "entry_age": "Eligibility — minimum and maximum entry age: quote separate adult and dependent child ranges including no maximum, lifelong or unlimited entry where stated. Keep entry distinct from lifetime renewal and preserve original units and qualifications.",
    "plan_type": "Type of Insurance / Product Type: quote the operative statement that this policy provides indemnity health insurance or reimbursement of actual hospitalization expenses. Do not substitute individual/floater basis or optional benefit riders.",
}
FORCE_FIELDS = set(QUERIES)


def requested(field, index):
    if field in {"geography", "coverage_basis", "family", "entry_age", "plan_type"}:
        return True
    if field == "maternity":
        return any(n in index.name for n in ("Comprehensive", "Assure Insurance", "Premier"))
    if field == "opd":
        return "Optima Secure" in index.name or "Elevate" in index.name
    if field == "sum_insured":
        return True
    return "ReAssure" in index.name or (field == "room_limit" and "Elevate" in index.name)


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
                    if field in QUERIES and requested(field, index) and (
                        field in FORCE_FIELDS or not base_statements or not rules
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
