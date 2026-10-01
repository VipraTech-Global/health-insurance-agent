"""Export the checkpoint review from validated rules and exact raw-page evidence."""

from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.models import (
    PolicyRule,
    PolicyRuleEvidence,
    PolicyRuleTableCell,
    PolicyVersion,
    ProcessingJob,
)
from apps.adviser_v2.processing.artifacts import read_artifact
from apps.adviser_v2.processing.criterion_evidence import PROCESSING_VERSION
from apps.adviser_v2.processing.manifest_v2 import raw_bundle_passages
from apps.adviser_v2.readiness import load_captured_manifest


def fenced(value: str, language: str = "text") -> str:
    fence = "`" * max(3, max((len(part) for part in re.findall(r"`+", value)), default=0) + 1)
    return f"{fence}{language}\n{value}\n{fence}"


def shown(value: object) -> str:
    if not isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if value.get("node") == "literal":
        return shown(value["value"])
    if value.get("state") == "finite":
        number = Decimal(str(value["value"]))
        if value.get("unit") == "ratio":
            return f"{number * 100:g}%"
        if value.get("unit") == "money":
            return f"{value.get('currency', '')} {number:,f}".strip()
        return f"{value.get('currency', '')} {number:g} {value['unit']}".strip()
    if value.get("state") in {"not_applicable", "unknown"}:
        return f"{value['state'].replace('_', ' ').capitalize()}: {value.get('reason', '')}"
    if value.get("kind") in {"text", "code", "boolean"}:
        return str(value["value"])
    if value.get("node") == "input":
        return str(value["key"]).replace("_", " ") + " (input)"
    if value.get("node") == "table_lookup":
        return f"Table `{value['table_key']}`; see the validated cells below"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def condition(value: dict[str, Any]) -> str:
    node = value.get("node")
    if node == "constant":
        return {
            "true": "Applies within the stated scope",
            "false": "Does not apply",
            "unknown": "Applicability is unresolved",
        }[value["value"]]
    if node == "present":
        return str(value["input_key"]).replace("_", " ") + " must be provided"
    if node == "not":
        return "NOT (" + condition(value["argument"]) + ")"
    if node in {"all", "any"}:
        separator = " AND " if node == "all" else " OR "
        return separator.join("(" + condition(item) + ")" for item in value["arguments"])
    if node == "compare":
        operator = {"eq": "=", "ne": "!=", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="}
        return f"{shown(value['left'])} {operator[value['operator']]} {shown(value['right'])}"
    if node == "membership":
        return shown(value["item"]) + " is one of: " + ", ".join(map(shown, value["members"]))
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class Command(BaseCommand):
    help = "Write the Star Checkpoint 2 review without building or publishing a release."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("manifest", type=Path)
        parser.add_argument("--output", type=Path, default=Path("output/star-three-plan-review.md"))

    def handle(self, *args: Any, **options: Any) -> None:
        manifest = load_captured_manifest(options["manifest"])
        if manifest["schema_version"] != 2:
            raise CommandError("This review requires the approved three-plan version-2 manifest.")
        lines = [
            "# Star three-plan rule review — Checkpoint 2",
            "",
            "Selected variant: **Base policy without optional covers**. Prices and budget remain unavailable.",
            "This file reports validated source rules, their conditions and exact quotations. It does not rank or choose a policy.",
            f"Captured manifest SHA-256: `{manifest['manifest_sha256']}`.",
            "Physical PDF pages are used throughout. Character offsets refer to preserved `pdftotext -raw` text and are end-exclusive.",
            "",
        ]
        summary = []
        citations: dict[str, dict[str, Any]] = {}
        for product in manifest["products"]:
            lines.extend([f"## {product['name']}", "", f"UIN: `{product['uin']}`.", ""])
            base = next(d for d in product["documents"] if d["role"] == "base_wording")
            validation = (
                ProcessingJob.objects.filter(source_capture_id=base["capture_id"], stage="validate")
                .order_by("-created_at", "-attempt_number")
                .first()
            )
            if validation is None or not validation.result_storage_key:
                lines.extend(
                    [
                        "**Pending:** no completed criterion-validation artifact is available. No source criterion is reported as supported.",
                        "",
                    ]
                )
                summary.append(
                    {
                        "product": product["product_key"],
                        "name": product["name"],
                        "state": "pending",
                        "supported": 0,
                        "unresolved": None,
                    }
                )
                continue
            artifact = read_artifact(validation)
            if artifact.get("manifest_processing_version") != PROCESSING_VERSION:
                raise CommandError(
                    "A validation artifact lacks the current version-2 criterion/citation checks."
                )
            version = PolicyVersion.objects.get(pk=product["policy_version_id"])
            source_pages = {
                item["evidence_span_id"]: item
                for item in raw_bundle_passages(version, include_prospectus=True)
            }
            criteria = artifact["criteria"]
            supported = sum(item["status"] == "supported" for item in criteria)
            unresolved = artifact["unresolved_criterion_count"]
            prospectus_used = artifact.get("prospectus_criteria", [])
            prospectus_gaps = [
                item["criterion"]
                for item in criteria
                if item["criterion"] not in prospectus_used
                and any("needs_prospectus:" in reason for reason in item["unknown_reasons"])
            ]
            lines.extend(
                [
                    f"Validation job: `{validation.id}` ({validation.state}). **{supported}/13 supported; {unresolved}/13 unresolved.**",
                    "Prospectus used for: " + (", ".join(prospectus_used) or "none") + ".",
                    "Prospectus gaps reported but not supplemented: " + (", ".join(prospectus_gaps) or "none") + ". See the criterion's unknown reasons below.",
                    f"Timeout calls across retained and resumed processing: {artifact.get('timeout_call_count', 'unavailable')}.",
                    "",
                ]
            )
            if unresolved >= 7:
                lines.extend(
                    [
                        "**STOP: the plan's seven-unresolved-criteria threshold has been reached. This is not approval to publish or continue processing.**",
                        "",
                    ]
                )
            summary.append(
                {
                    "product": product["product_key"],
                    "name": product["name"],
                    "state": validation.state,
                    "supported": supported,
                    "unresolved": unresolved,
                }
            )
            rules = {
                str(rule.id): rule
                for rule in PolicyRule.objects.filter(
                    id__in=artifact["verified_rule_ids"],
                    policy_version=version,
                    review_status="verified",
                )
            }
            if set(rules) != set(artifact["verified_rule_ids"]):
                raise CommandError(
                    "The validation artifact and current verified rule set disagree."
                )
            rows = [
                *criteria,
                {"criterion": "no_copay (derived; outside the 13)", **artifact["no_copay"]},
            ]
            for item in rows:
                lines.extend([f"### {item['criterion']}", "", f"Status: **{item['status']}**.", ""])
                for reason in item["unknown_reasons"]:
                    lines.extend([f"Unknown reason: {reason}", ""])
                for rule_id in item["rule_ids"]:
                    rule = rules[rule_id]
                    lines.extend([f"Rule: `{rule.rule_key}` (`{rule.id}`).", ""])
                    lines.extend([f"Condition: {condition(rule.body['applies_when'])}.", ""])
                    for effect in rule.body["effects"]:
                        amount = effect.get(
                            "value",
                            effect.get(
                                "amount",
                                effect.get(
                                    "duration", effect.get("decision", effect.get("reason", effect))
                                ),
                            ),
                        )
                        lines.extend(
                            [
                                f"Value — `{effect.get('target_key', rule.rule_type)}`: {shown(amount)}.",
                                "",
                            ]
                        )
                        scope = effect.get("scope", {})
                        lines.extend(
                            [
                                "Scope: "
                                + json.dumps(scope, ensure_ascii=False, sort_keys=True)
                                + ".",
                                "",
                            ]
                        )
                    lines.extend(
                        [
                            "Conditions, scope and dependencies (complete validated contract):",
                            "",
                            fenced(json.dumps(rule.body, ensure_ascii=False, indent=2), "json"),
                            "",
                        ]
                    )
                    cells = list(
                        PolicyRuleTableCell.objects.filter(policy_rule=rule).values(
                            "selectors", "value", "evidence_span_id"
                        )
                    )
                    if cells:
                        lines.extend(
                            [
                                "Validated table cells:",
                                "",
                                fenced(
                                    json.dumps(cells, ensure_ascii=False, indent=2, default=str),
                                    "json",
                                ),
                                "",
                            ]
                        )
                    evidence = list(
                        PolicyRuleEvidence.objects.filter(policy_rule=rule).select_related(
                            "evidence_span"
                        )
                    )
                    if not evidence:
                        raise CommandError(
                            f"Verified rule {rule.rule_key} has no citation records."
                        )
                    for row in evidence:
                        span_id = str(row.evidence_span_id)
                        if (
                            span_id not in source_pages
                            or row.evidence_span.quote != source_pages[span_id]["passage"]
                        ):
                            raise CommandError(
                                f"Rule {rule.rule_key} cites evidence outside exact approved raw pages."
                            )
                        page = source_pages[span_id]
                        citations[span_id] = page
                        lines.extend(
                            [
                                f"Citation ({row.role}): [{page['document_key']}, physical page {page['physical_page']}](#citation-{span_id}); characters [{page['page_char_start']}, {page['page_char_end']}).",
                                "",
                            ]
                        )
            lines.extend(
                [
                    "### Price and budget (outside the 13)",
                    "",
                    f"**Unavailable.** {artifact['budget']['reason']}",
                    "",
                ]
            )
        overview = [
            "## Validation summary",
            "",
            "| Plan | Supported source criteria | Unresolved source criteria | Price |",
            "|---|---:|---:|---|",
            *[
                f"| {item['name']} | {item['supported']}/13 | "
                + ("Pending" if item["unresolved"] is None else f"{item['unresolved']}/13")
                + " | Unavailable |"
                for item in summary
            ],
            "",
            "Derived `no_copay` and price are outside the 13-criterion denominator.",
            "",
        ]
        lines[7:7] = overview
        lines.extend(
            [
                "## Approved document decisions and remaining scope limits",
                "",
                "All optional covers remain unselected: Comprehensive PED buyback; Optima voluntary copayment; Assure aggregate deductible.",
                "Comprehensive's captured 2025 document codes versus its 2026 UIN remain the accepted edition mismatch.",
                "Assure consumables use wording clause 27 (physical page 20, printed page 19) and the wording's List I (physical page 44, printed page 43). This approved document decision is separate from the 13 extracted criteria above.",
                "The separate Assure expense sheet remains reference only. Its 68 item descriptions match wording List I after case, whitespace and punctuation normalization. Differences are the title, presentation and column break (wording left column ends at item 35; separate sheet at 34). It cannot support executable rules.",
                "Brochures and proposal forms remain excluded. Prospectuses remain applicable; a criterion prompt adds the complete prospectus only when core evidence is insufficient or a cited definition/table requires it.",
                "",
                "## Verbatim citation pages",
                "",
            ]
        )
        for span_id, page in sorted(
            citations.items(), key=lambda pair: (pair[1]["document_key"], pair[1]["physical_page"])
        ):
            lines.extend(
                [
                    f'<a id="citation-{span_id}"></a>',
                    f"### {page['document_key']} — physical page {page['physical_page']}",
                    "",
                    f"PDF SHA-256: `{page['document_sha256']}`. Page characters [{page['page_char_start']}, {page['page_char_end']}); document characters [{page['document_char_start']}, {page['document_char_end']}).",
                    "",
                    fenced(page["passage"]),
                    "",
                ]
            )
        output: Path = options["output"]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(lines), encoding="utf-8")
        self.stdout.write(
            json.dumps(
                {
                    "path": str(output.resolve()),
                    "products": summary,
                    "citation_pages": len(citations),
                },
                indent=2,
            )
        )
