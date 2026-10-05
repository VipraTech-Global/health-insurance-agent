"""Create new immutable projection versions without repeating validated AI calls."""

import hashlib
import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pydantic import ValidationError

from apps.adviser_v2.demo.contracts import Answer, CardField, Statement
from apps.adviser_v2.demo.evidence import Packet, Section, atomic_json, digest
from apps.adviser_v2.demo.fact_cards_v3 import freeze_prices
from apps.adviser_v2.demo.fact_projection import clauses, project
from apps.adviser_v2.demo.fact_rule_contracts import FactRule
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.demo.validation import validate
from apps.adviser_v2.models import DemoFactCard


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--source-run", required=True)
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--retain-run", action="append", default=[])
        parser.add_argument(
            "--refresh-prices",
            action="store_true",
            help="Pin each index's current validated premium chart instead of the source card's.",
        )

    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError("Isolated local cards only.")
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/fact-card-runs"
        source = root / options["source_run"]
        target = root / options["run_id"]
        state = json.loads((source / "progress.json").read_text())
        code = Path(__file__).resolve().parents[2] / "demo/fact_projection.py"
        retained = {}
        retained_manifests = {}
        for name in options["retain_run"]:
            retained_manifests[name] = json.loads((root / name / "manifest.json").read_text())
            for item in json.loads((root / name / "progress.json").read_text())["completed"]:
                saved = DemoFactCard.objects.get(pk=item["id"])
                retained.setdefault(saved.index_id, []).append(
                    json.loads(Path(saved.audit_path).read_text())
                )
        manifest = {
            "retained_source_manifests": retained_manifests,
            "schema_version": 9,
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "source_manifest": json.loads((source / "manifest.json").read_text()),
            "fit_projection_sha256": hashlib.sha256(
                code.with_name("fact_fit_projection.py").read_bytes()
            ).hexdigest(),
            "packet_recovery_sha256": hashlib.sha256(
                code.with_name("fact_packet_recovery.py").read_bytes()
            ).hexdigest(),
            "projection_sha256": hashlib.sha256(code.read_bytes()).hexdigest(),
            "parser_sha256": hashlib.sha256(
                code.with_name("fact_rules_v6.py").read_bytes()
            ).hexdigest(),
            "list_projection_sha256": hashlib.sha256(
                code.with_name("fact_list_projection.py").read_bytes()
            ).hexdigest(),
            "grounding_sha256": hashlib.sha256(
                code.with_name("fact_rule_grounding.py").read_bytes()
            ).hexdigest(),
            "governing_sha256": hashlib.sha256(
                code.with_name("fact_governing.py").read_bytes()
            ).hexdigest(),
            "age_projection_sha256": hashlib.sha256(
                code.with_name("fact_age_projection.py").read_bytes()
            ).hexdigest(),
            "table_projection_sha256": hashlib.sha256(
                code.with_name("fact_table_projection.py").read_bytes()
            ).hexdigest(),
            "rule_schema_sha256": hashlib.sha256(
                code.with_name("fact_rule_contracts.py").read_bytes()
            ).hexdigest(),
            "run_id": options["run_id"],
        }
        if options["refresh_prices"]:
            manifest["refresh_prices"] = True
        if (target / "manifest.json").exists() and json.loads(
            (target / "manifest.json").read_text()
        ) != manifest:
            raise CommandError("Projection code changed; create a fresh versioned run.")
        atomic_json(target / "manifest.json", manifest)
        completed = []
        for item in state["completed"]:
            old = DemoFactCard.objects.select_related("index").get(pk=item["id"])
            audit = json.loads(Path(old.audit_path).read_text())
            bundle = bundle_for(old.index)
            card = {k: v for k, v in old.card.items() if k != "card_version"}
            quoted = {}
            rules = []
            optional = {}
            statuses = {}
            projection_omissions = {}
            for field, result in audit["fields"].items():
                sources = [result]
                for prior in retained.get(old.index_id, []):
                    candidate = prior["fields"].get(field)
                    if candidate and candidate.get("index_version") == old.index_id:
                        sources.append(candidate)
                    previous = prior["provenance"].get(field, {}).get("source_result")
                    if previous and previous.get("index_version") == old.index_id:
                        sources.append(previous)
                previous_result = audit["provenance"].get(field, {}).get("source_result")
                if previous_result and previous_result.get("index_version") == old.index_id:
                    sources.append(previous_result)
                # Reuse a validated governing unit from another field query only
                # when it names this same hard check. Revalidate its complete
                # unit below against its original pinned packet, never stitch
                # fragments or PageIndex navigation into new evidence.
                markers = {
                    "plan_type": r"(?:Type of Insurance|shall indemnify|will indemnify)",
                    "coverage_basis": r"Coverage Options|Cover Type|Type of Policy|can be issued to individual|Individual Sum [Ii]nsured|In case of Individual Policies",
                    "family": r"[Ff]loater.{0,160}(?:[Ss]elf|[Ss]pouse|\d+\s*A\d*\s*C|\d+\s*Adults)",
                    "sum_insured": r"Sum\s*Insured\s*Options",
                    "geography": r"[Zz]onal pricing|[Pp]ricing [Zz]one|[Pp]remium [Pp]ayment [Zz]ones",
                    "entry_age": r"[Ee]ntry [Aa]ge|[Ee]ligibility",
                }
                if field in markers:
                    for evidence in [audit, *retained.get(old.index_id, [])]:
                        for source_field, candidate in evidence["fields"].items():
                            if (
                                source_field == field
                                or candidate.get("status") != "answered"
                                or candidate.get("index_version") != old.index_id
                            ):
                                continue
                            text = " ".join(
                                c["quote"]
                                for unit in candidate["answer"]["statements"]
                                for c in unit["citations"]
                            )
                            if re.search(markers[field], text, re.S) and candidate not in sources:
                                sources.append(candidate)
                from apps.adviser_v2.demo.fact_packet_recovery import recover

                # Repeated retained audit wrappers may point to exactly the
                # same answer and packet. Revalidate each distinct source once.
                sources = list(
                    {
                        digest(
                            {
                                k: source_result.get(k)
                                for k in ("index_version", "status", "answer", "packet")
                            }
                        ): source_result
                        for source_result in sources
                    }.values()
                )
                recovered = []
                for source_result in sources:
                    recovered.extend(recover(source_result, field, bundle))
                sources.extend(recovered)
                if recovered:
                    audit["provenance"].setdefault(field, {})["literal_recovery"] = recovered
                base, extra = [], []
                rejected = []
                for source_result in sources:
                    if source_result["status"] != "answered":
                        continue
                    source_base, source_extra, _ = clauses(source_result, field, bundle)
                    for statement in source_base:
                        if not statement.get("variant_axis_verified") and not statement.get(
                            "complete_options"
                        ):
                            data = source_result["packet"]
                            packet = Packet(
                                old.index.plan_key,
                                tuple(Section.from_payload(s) for s in data["sections"]),
                                tuple(data.get("omitted_ids", [])),
                                data["tokens"],
                                tables=tuple(data.get("tables", [])),
                            )
                            candidate = Statement.model_validate(
                                {k: v for k, v in statement.items() if k in Statement.model_fields}
                            )
                            check = validate(
                                Answer(
                                    plan_id=packet.plan_id,
                                    status="answered",
                                    statements=[candidate],
                                ),
                                packet,
                                variant=old.index.variant,
                                known_variants=tuple(bundle.get("variants", [])),
                            )
                            source_result.setdefault("projection_validation", []).append(
                                {
                                    "checks": list(check.checks),
                                    "passed": check.passed,
                                    "problems": check.problems,
                                }
                            )
                            if not check.passed:
                                message = "Trimmed governing unit rejected: " + "; ".join(
                                    check.problems
                                )
                                source_result.setdefault("projection_omissions", []).append(message)
                                # Sources are de-duplicated copies; surface the
                                # rejection on the card, not only on the copy.
                                rejected.append(message)
                                continue
                        if statement not in base:
                            base.append(statement)
                    for statement in source_extra:
                        if statement not in extra:
                            extra.append(statement)
                stated = bool(base)
                value = CardField(
                    state="stated" if stated else "not_stated",
                    labels=[s["text"] for s in base],
                    citations=[c for s in base for c in s["citations"]],
                    conditions=[c for s in base for c in [*s["conditions"], *s["restrictions"]]],
                ).model_dump()
                quoted[field] = value
                projected = project(field, base, card["variant"])
                checked = []
                projection_omissions[field] = list(result.get("projection_omissions", []))
                projection_omissions[field].extend(
                    m for m in rejected if m not in projection_omissions[field]
                )
                if base and not projected:
                    projection_omissions[field].append(
                        "No bounded field-specific rule passed the value, unit, applicability and completeness gates."
                    )
                for rule in projected:
                    if rule.get("restricted_scope"):
                        projection_omissions[field].append(
                            "The printed condition is outside supported executable checks."
                        )
                        continue
                    try:
                        checked.append(FactRule.model_validate(rule).model_dump(exclude_none=True))
                    except ValidationError as exc:
                        projection_omissions[field].append(str(exc))
                projected = checked
                coverage_values = {r["value"] for r in projected if r["kind"] == "coverage"}
                if len(coverage_values) > 1:
                    projected = [r for r in projected if r["kind"] != "coverage"]
                    coverage_values = set()
                    projection_omissions[field].append(
                        "Contradictory coverage values remain unresolved."
                    )
                rules.extend(projected)
                statuses[field] = (
                    "not covered"
                    if coverage_values == {"not_covered"}
                    else "stated"
                    if stated
                    else "not stated"
                )
                optional[field] = (
                    {"status": "optional, extra premium", "statements": extra} if extra else None
                )
                if field in {
                    "sum_insured",
                    "geography",
                    "copay",
                    "room_limit",
                    "ped_waiting",
                    "maternity",
                    "opd",
                }:
                    card[field] = value
            card.update(
                card_schema_version=9,
                quoted_fields=quoted,
                executable_rules=rules,
                optional_covers=optional,
                field_statuses=statuses,
                projection_omissions=projection_omissions,
                field_coverage={
                    f: v["state"] == "stated" and bool(v["citations"]) for f, v in quoted.items()
                },
                rule_coverage={f: any(r["field"] == f for r in rules) for f in quoted},
                common_needs=[{"field": f, "value": v} for f, v in quoted.items()],
            )
            if options["refresh_prices"]:
                for key in ("pricing_artifact", "pricing_sha256"):
                    card.pop(key, None)
                card.update(freeze_prices(old.index_id, target))
            identity = digest({"card": card, "source_version": old.id, "manifest": manifest})
            card["card_version"] = identity
            path = target / "cards" / (identity + ".json")
            atomic_json(
                path,
                {
                    "card": card,
                    "fields": audit["fields"],
                    "provenance": audit["provenance"],
                    "source_card_version": old.id,
                },
            )
            DemoFactCard.objects.get_or_create(
                id=identity, defaults={"index": old.index, "card": card, "audit_path": str(path)}
            )
            completed.append(
                {
                    **item,
                    "id": identity,
                    "quoted": sum(card["field_coverage"].values()),
                    "executable": sum(card["rule_coverage"].values()),
                }
            )
        atomic_json(
            target / "progress.json", {"completed": completed, "failures": state["failures"]}
        )
        if (source / "priority.json").exists():
            priority = {
                r["index"] for r in json.loads((source / "priority.json").read_text())["cards"]
            }
            atomic_json(
                target / "priority.json",
                {
                    "cards": [r for r in completed if r["index"] in priority],
                    "failures": state["failures"],
                },
            )
        if (source / "complete.json").exists():
            atomic_json(target / "complete.json", {"cards": completed, "manifest": manifest})
        self.stdout.write(
            json.dumps(
                {
                    "cards": len(completed),
                    "quoted": sum(c["quoted"] for c in completed),
                    "executable": sum(c["executable"] for c in completed),
                }
            )
        )
