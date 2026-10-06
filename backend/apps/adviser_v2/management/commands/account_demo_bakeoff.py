import hashlib
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.evaluation import make_jobs, score_rows, write_report
from apps.adviser_v2.demo.evidence import atomic_json, digest
from apps.adviser_v2.demo.pair_accounting import first_matching_attempt


class Command(BaseCommand):
    help = "Recover earliest same-model saved pairs after missing selector model labels; make no AI calls."

    def handle(self, **options):
        repository = Path(settings.BASE_DIR).parent
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer/bakeoff-v2"
        frozen = json.loads((root / "frozen.json").read_text())
        inputs = frozen["inputs"]
        if digest({"protocol_version": 2, "inputs": inputs}) != frozen["sha256"]:
            raise CommandError("Frozen inputs failed their identity check.")
        source = repository / "research/ten-insurer/protocol-v2-frozen-runtime"
        for name, sha in inputs["source_hashes"].items():
            if hashlib.sha256((source / name).read_bytes()).hexdigest() != sha:
                raise CommandError("Frozen source changed: " + name)
        if (repository / "docs/ten-insurer-bakeoff-protocol.md").read_text() != inputs["protocol"]:
            raise CommandError("Frozen protocol changed.")
        records = [
            json.loads(line)
            for line in (root.parent / "relay-calls.jsonl").read_text().splitlines()
        ]
        rows, audit = [], []
        for job in make_jobs(inputs["bundles"], inputs["queries"], inputs["slots"]):
            final_path = root / "pairs" / (job["id"] + ".json")
            final = json.loads(final_path.read_text()) if final_path.exists() else None
            split_paths = sorted(
                (root / "split-pairs").glob(job["id"] + "-*.json"),
                key=lambda p: int(p.stem.rsplit("-", 1)[1]),
            )
            if [int(p.stem.rsplit("-", 1)[1]) for p in split_paths] != list(
                range(len(split_paths))
            ):
                raise CommandError("Non-contiguous attempt history: " + job["id"])
            candidates = [json.loads(p.read_text())["arms"] for p in split_paths]
            if final:
                candidates.append(final["arms"])
            if not candidates:
                raise CommandError("No saved result for " + job["id"])
            arms, proof = first_matching_attempt(job["id"], candidates, records)
            selected = proof["selected_attempt"]
            row = {
                "job": job,
                "arms": arms,
                "split_attempts": [a for n, a in enumerate(candidates) if n != selected],
                "accounting": proof,
            }
            rows.append(row)
            audit.append(
                {
                    "job": job["id"],
                    **proof,
                    "saved_attempt_hashes": [digest(a) for a in candidates],
                    "selected_raw_attempt_sha256": digest(candidates[selected]),
                }
            )
        for row in rows:
            atomic_json(root / "accounted-pairs" / (row["job"]["id"] + ".json"), row)
        atomic_json(root / "pair-accounting.json", audit)
        outcome = score_rows(rows, inputs["queries"], inputs["bundles"])
        outcome.update(
            frozen_sha256=frozen["sha256"],
            accounting_version="earliest-call-proven-pair/1",
            pairs_directory="accounted-pairs",
            runner_retried_pairs=sum(a["discarded_attempts"] > 0 for a in audit),
            discarded_runner_attempts=sum(a["discarded_attempts"] for a in audit),
            split_pairs=sum(
                any(
                    len(a["models"]) > 1 or a["explicit_transition"]
                    for a in item["examined_attempts"]
                )
                for item in audit
            ),
        )
        outcome["selector_rejections"] = {
            m: sum("selected a section outside" in r["arms"][m].get("reason", "") for r in rows)
            for m in ("H", "P")
        }
        write_report(root, repository, rows, outcome, inputs["slots"])
        report = repository / "output/search-bakeoff.md"
        note = (
            "## Runner accounting correction\n\n"
            "Invalid selected section IDs lost their model label in the answer result. The original runner "
            "mistook this for a model transition and retried. No retrieval, prompt, validator, document or scoring "
            "rule was changed. The earliest call-log-proven same-model attempt is scored uniformly, including "
            "selector failures; later successes do not replace it. Original pairs and all attempts are preserved.\n\n"
            f"Runner-retried pairs: {outcome['runner_retried_pairs']}; discarded extra attempts: {outcome['discarded_runner_attempts']}; "
            f"actual model-split pairs: {outcome['split_pairs']}. Scored packets: `{root / 'accounted-pairs'}`. "
            f"Per-call provenance and attempt hashes: `{root / 'pair-accounting.json'}`.\n\n"
        )
        original = report.read_text()
        report.write_text(original.replace("## Evaluation slots", note + "## Evaluation slots", 1))
        self.stdout.write(json.dumps(outcome, indent=2))
