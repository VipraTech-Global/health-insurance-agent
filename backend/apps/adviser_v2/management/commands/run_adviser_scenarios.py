"""Inventory or execute all 400 scenarios without claiming unscored success."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.adviser_v2.scenarios import (
    acceptance_summary,
    classify_scenarios,
    load_assessments,
    load_scenarios,
    load_subset,
    release_inventory,
    run_scenario_attempt,
)


class Command(BaseCommand):
    help = "Inventory and optionally execute the 400-case adviser scenario corpus."

    def add_arguments(self, parser: CommandParser) -> None:
        root = Path(settings.BASE_DIR).parent
        parser.add_argument(
            "--reference",
            type=Path,
            default=root / "research/reference/assessments-200-r5.jsonl",
        )
        parser.add_argument(
            "--evaluation",
            type=Path,
            default=root / "research/evaluation/replacement-cases.jsonl",
        )
        parser.add_argument(
            "--subset",
            type=Path,
            default=root / "research/evaluation/five-product-50.jsonl",
        )
        parser.add_argument("--assessments", type=Path)
        parser.add_argument("--execute", action="store_true")
        parser.add_argument("--output", type=Path)

    def handle(self, *args: Any, **options: Any) -> None:
        paths = [options["reference"].resolve(), options["evaluation"].resolve()]
        try:
            records, corpus_sha256 = load_scenarios(paths)
        except (OSError, UnicodeError, ValueError) as exc:
            raise CommandError(f"Scenario corpus validation failed: {exc}") from exc
        if len(records) != 400:
            raise CommandError(f"Expected exactly 400 scenarios, found {len(records)}.")
        split_counts: dict[str, int] = {}
        for record in records:
            split = str(record.get("split", "unknown"))
            split_counts[split] = split_counts.get(split, 0) + 1
        release, release_uins, release_hashes, release_blockers = release_inventory()
        classified, classification_counts = classify_scenarios(
            records, release_uins, release_hashes
        )
        subset_path: Path = options["subset"].resolve()
        subset_ids, subset_blockers = load_subset(
            subset_path, {str(item["case_id"]) for item in records}
        )
        assessments_path = options.get("assessments")
        try:
            assessments = load_assessments(assessments_path.resolve() if assessments_path else None)
        except (OSError, ValueError) as exc:
            raise CommandError(f"Scenario assessments are invalid: {exc}") from exc
        execution: list[dict[str, object]] = []
        execution_blockers = [*release_blockers, *subset_blockers]
        if options["execute"]:
            if execution_blockers:
                raise CommandError(
                    "Scenario execution is blocked: " + "; ".join(execution_blockers)
                )
            for record in records:
                attempts = 3 if str(record["case_id"]) in subset_ids else 1
                for attempt in range(1, attempts + 1):
                    execution.append(run_scenario_attempt(record, attempt))
        technical_failures = sum(
            item["state"] == "failed" and item["error_code"] != "unsupported_answer"
            for item in execution
        )
        unsupported_failures = sum(item["error_code"] == "unsupported_answer" for item in execution)
        acceptance = acceptance_summary(subset_ids, assessments)
        raw_acceptance_blockers = acceptance.get("blockers", [])
        base_acceptance_blockers = (
            [str(item) for item in raw_acceptance_blockers]
            if isinstance(raw_acceptance_blockers, list)
            else ["invalid_acceptance_blocker_report"]
        )
        final_acceptance_blockers = sorted(
            set(
                [
                    *base_acceptance_blockers,
                    *release_blockers,
                    *subset_blockers,
                    *(["no_fresh_scenario_execution"] if not execution else []),
                    *(["independent_attempt_assessments_missing"] if not assessments else []),
                ]
            )
        )
        acceptance["blockers"] = final_acceptance_blockers
        acceptance["assessable"] = not acceptance["blockers"]
        acceptance["accepted"] = bool(acceptance["accepted"]) and bool(acceptance["assessable"])
        report = {
            "schema_version": 1,
            "scenario_corpus_sha256": corpus_sha256,
            "scenario_count": len(records),
            "split_counts": split_counts,
            "release": (
                {
                    "id": str(release.id),
                    "number": release.release_number,
                    "manifest_sha256": release.manifest_sha256,
                    "uins": sorted(release_uins),
                }
                if release
                else None
            ),
            "classification_counts": classification_counts,
            "classifications": classified,
            "execution": {
                "requested": bool(options["execute"]),
                "attempt_count": len(execution),
                "technical_failures": technical_failures,
                "unsupported_answer_failures": unsupported_failures,
                "results": execution,
                "blockers": execution_blockers,
            },
            "acceptance": acceptance,
        }
        output: Path = options.get("output") or (
            Path(settings.COVERGUIDE_REPORT_ROOT) / f"scenario-report-{corpus_sha256[:16]}.json"
        )
        output = output.resolve()
        report_root = Path(settings.COVERGUIDE_REPORT_ROOT).resolve()
        if output.parent != report_root:
            raise CommandError("Scenario report must be directly inside COVERGUIDE_REPORT_ROOT.")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(
                f"Inventoried 400 scenarios; executed {len(execution)} attempts; report {output}."
            )
        )
        if final_acceptance_blockers:
            self.stdout.write("Acceptance remains blocked: " + "; ".join(final_acceptance_blockers))
