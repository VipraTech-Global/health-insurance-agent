"""Fail-closed benchmark accounting. Counts cannot replace evidence or independent runs."""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from research_workspace.contracts import CaseRecord, EvaluationAttempt
from research_workspace.evidence import verify_locations
from research_workspace.storage import digest


def load_cases(path: Path) -> list[CaseRecord]:
    rows = [CaseRecord.model_validate_json(line) for line in path.read_text().splitlines() if line]
    if len({r.case_id for r in rows}) != len(rows):
        raise ValueError("Duplicate case identity")
    if len({r.decision_distinction.casefold().strip() for r in rows}) != len(rows):
        raise ValueError("Repeated decision distinction")
    return rows


def library_report(cases: list[CaseRecord]) -> dict[str, Any]:
    families = []
    for split in ("reference", "evaluation"):
        for family in range(1, 21):
            rows = [c for c in cases if c.split == split and c.family == family]
            families.append(
                {
                    "split": split,
                    "family": family,
                    "records": len(rows),
                    "worked": sum(c.assessment == "worked" for c in rows),
                    "multi_factor": sum(len(c.factors) > 1 for c in rows),
                    "multi_turn": sum(len(c.conversation) > 1 for c in rows),
                    "essential_gaps": sum(bool(c.gaps) for c in rows),
                    "exposed": sum(c.evaluation_exposed for c in rows),
                    "ready": len(rows) >= 10
                    and all(c.assessment == "worked" for c in rows)
                    and sum(len(c.factors) > 1 for c in rows) >= 4
                    and any(len(c.conversation) > 1 for c in rows),
                }
            )
    return {
        "format_version": 1,
        "families": families,
        "ready": all(f["ready"] for f in families),
        "counts": dict(Counter(c.assessment for c in cases)),
        "distinctness_review": "Decision strings validated; substantive independence requires review",
    }


def freeze_evaluation(path: Path, target: Path, evidence_root: Path) -> str:
    """Freeze exact bytes once. A draft or exposed library cannot become an independent benchmark."""
    cases = load_cases(path)
    if len(cases) != 200 or any(c.split != "evaluation" or c.evaluation_exposed for c in cases):
        raise ValueError("Need exactly 200 unexposed evaluation cases")
    report = library_report(cases)
    if not all(row["ready"] for row in report["families"] if row["split"] == "evaluation"):
        raise ValueError("Evaluation library has unworked cases or incomplete family coverage")
    locations = [location for case in cases for location in case.evidence]
    locations.extend(
        location for case in cases for calc in case.calculations for location in calc.evidence
    )
    verify_locations(evidence_root, locations)
    data = path.read_bytes()
    sha = digest(data)
    target.mkdir(parents=True, exist_ok=True)
    # Exclusive create prevents silently replacing an earlier benchmark.
    with (target / "cases.jsonl").open("xb") as stream:
        stream.write(data)
    with (target / "manifest.json").open("x") as stream:
        json.dump(
            {
                "format_version": 1,
                "sha256": sha,
                "case_ids": [c.case_id for c in cases],
                "retrieval_allowed": False,
                "prompt_examples_allowed": False,
            },
            stream,
        )
    return sha


def evaluation_report(
    cases: list[CaseRecord],
    attempts: list[EvaluationAttempt],
    release_id: str,
) -> dict[str, Any]:
    expected = {c.case_id: c for c in cases if c.split == "evaluation"}
    if len(expected) != len([c for c in cases if c.split == "evaluation"]):
        raise ValueError("Duplicate evaluation case")
    grouped: dict[str, dict[int, EvaluationAttempt]] = defaultdict(dict)
    conversations: set[str] = set()
    critical: list[str] = []
    for attempt in attempts:
        if attempt.release_id != release_id or attempt.case_id not in expected:
            raise ValueError("Attempt does not belong to this release and benchmark")
        if attempt.attempt in grouped[attempt.case_id]:
            raise ValueError("Duplicate attempt; failed attempts cannot be overwritten")
        if attempt.conversation_id in conversations:
            raise ValueError("Each independent attempt requires fresh conversation state")
        conversations.add(attempt.conversation_id)
        grouped[attempt.case_id][attempt.attempt] = attempt
        critical.extend(attempt.critical_failures)
    passed = set()
    for identity, case in expected.items():
        runs = grouped[identity]
        if (
            set(runs) == {1, 2, 3}
            and case.assessment == "worked"
            and not case.gaps
            and all(
                a.result == "pass"
                and a.material_criteria_passed
                and a.essential_evidence_complete
                and not a.critical_failures
                for a in runs.values()
            )
        ):
            passed.add(identity)
    families = [
        {
            "family": f,
            "cases": sum(c.family == f for c in expected.values()),
            "passed": sum(expected[i].family == f for i in passed),
        }
        for f in range(1, 21)
    ]
    independent = not any(c.evaluation_exposed for c in expected.values())
    ready = (
        len(expected) == 200
        and len(passed) >= 180
        and independent
        and not critical
        and all(f["cases"] == 10 and f["passed"] >= 9 for f in families)
    )
    return {
        "format_version": 1,
        "release_id": release_id,
        "advice_target_passed": ready,
        "independent": independent,
        "cases": len(expected),
        "passed": len(passed),
        "attempts": len(attempts),
        "missing_attempts": len(expected) * 3 - len(attempts),
        "critical_failures": critical,
        "families": families,
        "release_ready": False,
        "other_gates": "Rule coverage, all 60 robustness checks and operational checks required",
    }
