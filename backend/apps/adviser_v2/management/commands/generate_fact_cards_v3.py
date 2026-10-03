import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.demo.fact_cards_v3 import CARD_FIELDS, build
from apps.adviser_v2.models import DemoFactCard, DemoRelease


class Command(BaseCommand):
    help = "Generate immutable cards with the fresh answer method; flagship/Star plans first."

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--answer-run", required=True)
        parser.add_argument("--workers", type=int, default=3)

    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError("Isolated demo only.")
        reports = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        source = reports / "application-acceptance" / options["answer_run"]
        summary = json.loads((source / "summary.json").read_text())
        release = DemoRelease.objects.get(pk=summary["release_id"])
        indexes = list(release.indexes.order_by("insurer", "name", "variant"))
        indexes.sort(
            key=lambda i: (
                0 if i.insurer.startswith(("Star", "HDFC", "Bajaj")) else 1,
                i.insurer,
                i.name,
                i.variant,
            )
        )
        root = reports / "fact-card-runs" / options["run_id"]
        root.mkdir(parents=True, exist_ok=True)
        code = Path(__file__).resolve().parents[2] / "demo"
        relevant = [
            "answers.py",
            "assembly.py",
            "contracts.py",
            "evidence.py",
            "quotations.py",
            "search.py",
            "validation.py",
            "relay.py",
            "fact_cards_v3.py",
            "fact_rules_v3.py",
            "card_answers.py",
            "card_assembly.py",
            "card_clauses.py",
            "cards.py",
        ]
        manifest = {
            "schema_version": 3,
            "run_id": options["run_id"],
            "answer_run": options["answer_run"],
            "indexes": [i.id for i in indexes],
            "method": "H",
            "fields": list(CARD_FIELDS),
            "code": {n: hashlib.sha256((code / n).read_bytes()).hexdigest() for n in relevant},
            "packet_budget": 16000,
            "primary": "gpt-5.6-luna",
            "fallback": "claude-sonnet-5",
        }
        if (root / "manifest.json").exists() and json.loads(
            (root / "manifest.json").read_text()
        ) != manifest:
            raise CommandError("Pinned card generation code changed; use a new run ID.")
        atomic_json(root / "manifest.json", manifest)
        accepted = {}
        questions = {}
        priority = set()
        for path in sorted((source / "results").glob("*.json")):
            row = json.loads(path.read_text())
            job = row["job"]
            if job["kind"] != "answer":
                continue
            field = job["id"].removeprefix("answer-").rsplit("-", 1)[0]
            field = {"room_rent": "room_limit", "ped": "ped_waiting"}.get(field, field)
            questions[field] = job["question"]
            for result in row["results"]:
                priority.add(result["index_version"])
                accepted.setdefault(
                    (result["index_version"], field),
                    {
                        "result": result,
                        "provenance": {
                            "method": "fresh_application_answer",
                            "run": options["answer_run"],
                            "case": job["id"],
                            "question_id": row["question_id"],
                            "index": result["index_version"],
                        },
                    },
                )
        close_old_connections()
        completed = []
        failures = []

        def one(index):
            close_old_connections()
            try:
                identity, card, audit = build(index, root, accepted, questions)
                row, _ = DemoFactCard.objects.get_or_create(
                    id=identity, defaults={"index": index, "card": card, "audit_path": str(audit)}
                )
                return {
                    "id": row.id,
                    "index": index.id,
                    "name": index.name,
                    "variant": index.variant,
                    "quoted": sum(card["field_coverage"].values()),
                    "executable": sum(card["rule_coverage"].values()),
                    "total": len(CARD_FIELDS),
                }
            finally:
                close_old_connections()

        for name, rows in [
            ("priority", [i for i in indexes if i.id in priority]),
            ("remaining", [i for i in indexes if i.id not in priority]),
        ]:
            self.stdout.write(f"Starting {name}: {len(rows)} plan variants")
            self.stdout.flush()
            with ThreadPoolExecutor(max_workers=max(1, min(4, options["workers"]))) as pool:
                futures = {pool.submit(one, i): i for i in rows}
                for future in as_completed(futures):
                    index = futures[future]
                    try:
                        result = future.result()
                    except (RuntimeError, ValueError, OSError) as exc:
                        failures.append({"index": index.id, "error": str(exc)})
                        self.stderr.write(str(exc))
                    else:
                        completed.append(result)
                        self.stdout.write(json.dumps(result))
                    atomic_json(
                        root / "progress.json", {"completed": completed, "failures": failures}
                    )
                    self.stdout.flush()
            atomic_json(
                root / (name + ".json"),
                {
                    "cards": [r for r in completed if r["index"] in {i.id for i in rows}],
                    "failures": failures,
                },
            )
        if failures:
            raise CommandError(f"{len(failures)} cards pending; successful fields are cached.")
        atomic_json(root / "complete.json", {"cards": completed, "manifest": manifest})
