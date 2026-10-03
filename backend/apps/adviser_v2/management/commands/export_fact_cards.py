"""Export implementation cards for later independent reference comparison."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.demo.services import bundle_for
from apps.adviser_v2.models import DemoFactCard


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True)

    def handle(self, **options):
        root = (
            Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/fact-card-runs" / options["run_id"]
        )
        progress = json.loads((root / "progress.json").read_text())
        output = Path(settings.BASE_DIR).parent / "output/section16-cards"
        output.mkdir(parents=True, exist_ok=True)
        for existing in output.glob("*.json"):
            previous = json.loads(existing.read_text())
            if previous.get("generation_run") != options["run_id"]:
                archive = (
                    output.parent
                    / "section16-cards-archive"
                    / previous.get("generation_run", "unversioned")
                )
                archive.mkdir(parents=True, exist_ok=True)
                existing.replace(archive / existing.name)
        coverage = []
        for item in progress["completed"]:
            row = DemoFactCard.objects.select_related("index").get(pk=item["id"])
            card = row.card
            bundle = bundle_for(row.index)
            sections = {s["id"]: s for s in bundle["sections"]}
            documents = {d["sha256"]: d for d in bundle["documents"]}

            def quote(c, sections=sections, documents=documents):
                section = sections[c["section_id"]]
                segment = next(s for s in section["segments"] if s["page_id"] == c["page_id"])
                document = documents.get(section["document_sha256"], {})
                return {
                    **c,
                    "document_id": section["document_id"],
                    "document_sha256": section["document_sha256"],
                    "document_name": document.get("name")
                    or document.get("title")
                    or section["role"],
                    "physical_page": segment["page"],
                    "source_role": section["role"],
                }

            fields = {}
            for name, value in card["quoted_fields"].items():
                rules = [r for r in card["executable_rules"] if r["field"] == name]
                contrary = any(
                    r["kind"] == "coverage" and r["value"] == "not_covered" for r in rules
                )
                fields[name] = {
                    "status": "not covered"
                    if contrary
                    else "stated"
                    if value["state"] == "stated"
                    else "not stated",
                    "field_values": {
                        "printed": value["labels"],
                        "numbers": value["numbers"],
                        "variant": value["variant"],
                        "exhaustive": value["exhaustive"],
                    },
                    "typed_rules": rules,
                    "projection_omissions": card.get("projection_omissions", {}).get(name, []),
                    "unresolved_reason": None
                    if rules
                    else "No bounded executable projection from the available base-cover evidence.",
                    "quotes": [quote(c) for c in value["citations"]],
                    "conditions": [
                        {"text": c["text"], "quotes": [quote(q) for q in c["citations"]]}
                        for c in value["conditions"]
                    ],
                }
            optional = {}
            for name, group in card.get("optional_covers", {}).items():
                if not group:
                    continue
                optional[name] = {
                    "status": "optional, extra premium",
                    "satisfies_base_requirement": False,
                    "quotes": [
                        quote(c)
                        for statement in group["statements"]
                        for item in [
                            statement,
                            *statement.get("conditions", []),
                            *statement.get("restrictions", []),
                        ]
                        for c in item["citations"]
                    ],
                }
            exported = {
                "schema_version": card.get("card_schema_version", 2),
                "optional_covers": optional,
                "plan_id": card["plan_id"],
                "card_version": row.id,
                "index_version": row.index_id,
                "insurer": card["insurer"],
                "name": card["name"],
                "variant": card["variant"],
                "fields": fields,
                "quoted_field_coverage": card["field_coverage"],
                "executable_rule_coverage": card["rule_coverage"],
                "coverage_counts": {
                    "quoted": sum(card["field_coverage"].values()),
                    "executable": sum(card["rule_coverage"].values()),
                    "total": len(card["field_coverage"]),
                },
                "models": card["models"],
                "generation_run": options["run_id"],
                "pricing": {
                    k: card[k] for k in ("pricing_artifact", "pricing_sha256") if k in card
                },
                "note": "Implementation export for later independent comparison; not expert verified.",
            }
            atomic_json(output / (card["plan_id"] + ".json"), exported)
            coverage.append(exported)
        atomic_json(
            output.parent / "section16-cards-manifest.json",
            {
                "run_id": options["run_id"],
                "complete": (root / "complete.json").exists(),
                "cards": [
                    {"plan_id": c["plan_id"], "version": c["card_version"]} for c in coverage
                ],
                "failures": progress["failures"],
            },
        )
        ordered = sorted(coverage, key=lambda c: (c["insurer"], c["name"], c["variant"]))
        lines = [
            "# Section 16 card coverage",
            "",
            f"Run: `{options['run_id']}`. Q = quoted base evidence; E = supported executable field. Not stated is not filled. Optional covers are separate and never satisfy a base requirement.",
            "",
            "| Plan / variant | Quoted | Executable | Card version |",
            "|---|---:|---:|---|",
        ]
        for c in ordered:
            counts = c["coverage_counts"]
            lines.append(
                f"| {c['insurer']} — {c['name']} / {c['variant']} | {counts['quoted']}/{counts['total']} | {counts['executable']}/{counts['total']} | `{c['card_version']}` |"
            )
        for c in ordered:
            lines.extend(
                [
                    "",
                    f"## {c['insurer']} — {c['name']} / {c['variant']}",
                    "",
                    "| Field | Status | Q | E | Optional cover |",
                    "|---|---|---|---|---|",
                ]
            )
            for field, value in c["fields"].items():
                lines.append(
                    f"| {field} | {value['status']} | {'yes' if c['quoted_field_coverage'][field] else 'no'} | {'yes' if c['executable_rule_coverage'][field] else 'no'} | {'optional, extra premium' if field in c['optional_covers'] else '—'} |"
                )
        (output.parent / "section16-card-coverage.md").write_text("\n".join(lines) + "\n")
        self.stdout.write(f"Exported {len(progress['completed'])} immutable card versions.")
