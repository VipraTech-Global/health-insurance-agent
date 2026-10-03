"""Measure completed application cohorts from their saved questions and relay audit."""

import json
import math
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.models import DemoQuestion


def percentiles(values):
    ordered = sorted(values)
    return (
        {
            "n": len(values),
            "p50_ms": ordered[math.ceil(len(values) * 0.5) - 1],
            "p95_ms": ordered[math.ceil(len(values) * 0.95) - 1],
        }
        if ordered
        else {"n": 0}
    )


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True)

    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError("Only the isolated local demo cohort may be measured.")
        run_id = options["run_id"]
        if not run_id.replace("-", "").replace("_", "").isalnum():
            raise CommandError("Invalid run ID.")
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        directory = root / "application-acceptance" / run_id
        if not (directory / "summary.json").exists():
            raise CommandError("The cohort must be complete.")
        rows = [json.loads(p.read_text()) for p in sorted((directory / "results").glob("*.json"))]
        ids = {r["question_id"] for r in rows}
        questions = {str(q.id): q for q in DemoQuestion.objects.filter(pk__in=ids)}
        records = [
            json.loads(line) for line in (root / "relay-calls.jsonl").read_text().splitlines()
        ]
        calls = [r for r in records if (r.get("scope") or {}).get("question_id") in ids]
        samples = []
        for row in rows:
            q = questions[row["question_id"]]
            if not q.completed_at:
                raise CommandError("A saved question has no completion timestamp.")
            selected = [c for c in calls if c["scope"]["question_id"] == str(q.id)]
            chains = {}
            for c in selected:
                key = c["scope"]["answer_id"]
                start, end = c["started_at"], c["started_at"] + c["total_ms"] / 1000
                old = chains.get(key, (start, end))
                chains[key] = (min(start, old[0]), max(end, old[1]))
            events = sorted(
                [(a, 1) for a, b in chains.values()] + [(b, -1) for a, b in chains.values()]
            )
            active = peak = 0
            for _, delta in events:
                active += delta
                peak = max(peak, active)
            starts = [a for a, b in chains.values()]
            samples.append(
                {
                    "question_id": str(q.id),
                    "job": row["job"]["id"],
                    "kind": row["job"]["kind"],
                    "plans": len(row["results"]),
                    "total_ms": round((q.completed_at - q.created_at).total_seconds() * 1000),
                    "plan_chain_overlap": peak,
                    "first_call_start_spread_ms": round((max(starts) - min(starts)) * 1000)
                    if starts
                    else None,
                }
            )
        # Slot occupancy is reconstructed from recorded queue and model times.
        intervals = [
            (
                r["started_at"] + r["queue_ms"] / 1000,
                r["started_at"] + (r["queue_ms"] + r["model_ms"]) / 1000,
            )
            for r in calls
            if r["model_ms"]
        ]
        events = sorted([(a, 1) for a, b in intervals] + [(b, -1) for a, b in intervals])
        active = peak = 0
        for _, delta in events:
            active += delta
            peak = max(peak, active)
        first = min(q.created_at.timestamp() for q in questions.values())
        last = max(q.completed_at.timestamp() for q in questions.values())
        answer_rows = [r for row in rows for r in row["results"]]
        output = {
            "run_id": run_id,
            "elapsed_seconds": round(last - first, 3),
            "question_times": {
                str(n): percentiles(
                    [s["total_ms"] for s in samples if s["plans"] == n and s["kind"] == "answer"]
                )
                for n in (3, 5)
            },
            "queue_times": percentiles([r["queue_ms"] for r in calls]),
            "validation_per_answer": percentiles(
                [r["validation_ms"] for r in answer_rows if r.get("validation_ms") is not None]
            ),
            "models": dict(Counter(r["model"] for r in calls)),
            "call_statuses": dict(Counter(r["status"] for r in calls)),
            "relay_peak_from_recorded_intervals": peak,
            "completed_calls_per_minute": round(
                sum(r["status"] == "completed" for r in calls) / (last - first) * 60, 3
            ),
            "plan_answers_per_minute": round(len(answer_rows) / (last - first) * 60, 3),
            "samples": samples,
            "note": "Application elapsed time includes queueing under four concurrent jobs. Relay intervals use millisecond-rounded audit times. This is not an idle-system speed claim.",
        }
        target = (
            Path(settings.BASE_DIR).parent / "output" / ("section16-timings-" + run_id + ".json")
        )
        atomic_json(target, output)
        self.stdout.write(json.dumps({k: v for k, v in output.items() if k != "samples"}))
