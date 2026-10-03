"""Exercise the winning application service with synthetic, resumable questions."""

import hashlib
import json
import time
import uuid
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.accounts.models import User
from apps.adviser_v2.demo.bakeoff import QUESTIONS
from apps.adviser_v2.demo.contracts import PersonInput, Profile
from apps.adviser_v2.demo.evaluation import packet_from
from apps.adviser_v2.demo.evidence import atomic_json, digest, reference_covered
from apps.adviser_v2.demo.services import decrypted, run_question, save_profile, submit
from apps.adviser_v2.management.commands.prepare_demo_roster import FLAGSHIPS
from apps.adviser_v2.models import DemoQuestion, DemoRelease, DemoSession


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--workers", type=int, default=2)
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--smoke25", action="store_true")

    def handle(self, **options):
        if settings.DATABASES["default"]["NAME"] != "coverguide_star_slice":
            raise CommandError(
                "Application acceptance is restricted to the isolated demo database."
            )
        release = DemoRelease.objects.filter(active=True).first()
        if not release:
            raise CommandError("Publish the winner and offline cards first.")
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / "ten-insurer"
        frozen = json.loads((root / "bakeoff-v2/frozen.json").read_text())["inputs"]
        available = {row.plan_key for row in release.indexes.all()}
        slots = []
        for slot in frozen["slots"]:
            plan_id = slot.get("plan_id")
            if not plan_id:
                key = FLAGSHIPS[slot["id"].removeprefix("flagship-")][1]
                plan_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "coverguide-demo-unavailable:" + key))
            if plan_id not in available:
                raise CommandError(
                    "The application release is missing evaluation slot " + slot["id"]
                )
            slots.append({**slot, "plan_id": plan_id})
        jobs = []
        for key, question, table in QUESTIONS:
            for n, group in enumerate((slots[:3], slots[3:8], slots[8:])):
                jobs.append(
                    {
                        "id": f"answer-{key}-{n}",
                        "kind": "answer",
                        "question": question,
                        "slots": group,
                        "table_heavy": table,
                    }
                )
        reference_groups = defaultdict(list)
        bundles = {p["policy_version_id"]: p for p in frozen["bundles"]}
        for query in frozen["queries"]:
            for style in ("fixed", "customer"):
                reference_groups[(query["criterion"], style, query[style])].append(query)
        for (criterion, style, question), queries in reference_groups.items():
            if len(queries) != 3:
                raise CommandError("Star reference queries no longer form three-plan comparisons.")
            jobs.append(
                {
                    "id": f"star-{criterion}-{style}",
                    "kind": "star",
                    "question": question,
                    "criterion": criterion,
                    "style": style,
                    "slots": [
                        {"id": q["policy_version_id"], "plan_id": q["policy_version_id"]}
                        for q in queries
                    ],
                }
            )
        if options["smoke25"]:
            sample = {
                "answer-room_rent-0",
                "answer-room_rent-1",
                "answer-room_rent-2",
                "answer-copay-0",
                "answer-ped-0",
                "answer-restoration-0",
                "answer-opd-0",
            }
            jobs = [j for j in jobs if j["id"] in sample]
        run_id = options["run_id"]
        if not run_id.replace("-", "").replace("_", "").isalnum():
            raise CommandError("Use an alphanumeric run ID with hyphens/underscores.")
        directory = root / "application-acceptance" / run_id
        code = Path(__file__).parents[2] / "demo"
        manifest = {
            "run_id": run_id,
            "release_id": str(release.id),
            "method": release.method,
            "indexes": sorted(release.indexes.values_list("id", flat=True)),
            "source_hashes": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in code.glob("*.py")
                if p.stem
                in {
                    "answers",
                    "answer_scope",
                    "answer_retrieval",
                    "assembly",
                    "contracts",
                    "evidence",
                    "evaluation",
                    "search",
                    "validation",
                    "quotations",
                    "relay",
                    "services",
                    "needs",
                    "embeddings",
                    "bakeoff",
                }
            },
            "packet_tokens": 16000,
            "initial_packet_tokens": 12000,
            "draft_schema": 3,
            "scope_contract": "original-scope/1",
            "expanded_packet_tokens": 14000,
            "maximum_h_queries": 2,
            "maximum_content_corrections": 1,
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "jobs_hash": digest(jobs),
        }
        manifest_file = directory / "manifest.json"
        if manifest_file.exists() and json.loads(manifest_file.read_text()) != manifest:
            raise CommandError(
                "Run manifest changed; use a new run ID, never reuse earlier results."
            )
        atomic_json(manifest_file, manifest)
        state_file = directory / "state.json"
        user, _ = User.objects.get_or_create(
            email="ten-insurer-acceptance@example.invalid", defaults={"is_active": True}
        )
        if state_file.exists():
            state = json.loads(state_file.read_text())
            session = DemoSession.objects.get(pk=state["session_id"], owner=user)
        else:
            session = save_profile(
                user,
                Profile(
                    people=[PersonInput(id="self", relationship="self", age_days=35 * 365)],
                    city="Pune",
                    zone=None,
                    sum_insured=1000000,
                    plan_type="medical_indemnity",
                ),
            )
            atomic_json(
                state_file,
                {
                    "session_id": str(session.id),
                    "release_id": str(release.id),
                    "method": release.method,
                    "jobs": jobs,
                },
            )

        def execute(job):
            close_old_connections()
            try:
                path = directory / "results" / (job["id"] + ".json")
                if path.exists():
                    return json.loads(path.read_text())
                pending = directory / "questions" / (job["id"] + ".json")
                if pending.exists():
                    question_id = json.loads(pending.read_text())["id"]
                else:
                    question = submit(
                        user, session.id, job["question"], [s["plan_id"] for s in job["slots"]]
                    )
                    if question.release_id != release.id:
                        raise ValueError(
                            "Active release changed; keep acceptance pinned and resume explicitly."
                        )
                    question_id = str(question.id)
                    atomic_json(pending, {"id": question_id})
                while True:
                    run_question(question_id)
                    question = DemoQuestion.objects.get(pk=question_id, release=release)
                    if question.state == "completed":
                        break
                    if question.state == "cancelled":
                        raise ValueError(
                            "Acceptance question was cancelled; do not silently replace it."
                        )
                    time.sleep(5)
                results = []
                for row in question.answers.select_related("index"):
                    value = decrypted(row.result_ciphertext, row.id)
                    covered, required, displayed = [], [], []
                    if job["kind"] == "star":
                        refs = bundles[row.index.plan_key]["references"][job["criterion"]]
                        required = [r["id"] for r in refs]
                        if value.get("packet"):
                            packet = packet_from(value["packet"])
                            covered = [r["id"] for r in refs if reference_covered(r, packet)]
                            anchors = (value.get("validation") or {}).get("anchors", [])
                            for ref in refs:
                                cursor = ref["start"]
                                for a in sorted(
                                    (a for a in anchors if a["page_id"] == ref["page_span_id"]),
                                    key=lambda a: a["start"],
                                ):
                                    if a["start"] <= cursor:
                                        cursor = max(cursor, a["end"])
                                if cursor >= ref["end"]:
                                    displayed.append(ref["id"])
                    results.append(
                        {
                            "plan_id": row.index.plan_key,
                            "name": row.index.name,
                            "index_version": row.index_id,
                            "status": value["status"],
                            "completeness": value.get("completeness"),
                            "reason": value.get("reason"),
                            "failure_category": value.get("failure_category"),
                            "rejections": value.get("rejections", []),
                            "attempts": value.get("attempts", []),
                            "displayed": displayed,
                            "models": value.get("models", []),
                            "validation": value.get("validation"),
                            "answer": value.get("answer"),
                            "total_ms": value.get("total_ms"),
                            "variant": row.index.variant,
                            "validation_ms": value.get("validation_ms"),
                            "retrieval_attempts": value.get("retrieval_attempts", []),
                            "omissions": value.get("omissions", []),
                            "covered": covered,
                            "required": required,
                        }
                    )
                value = {"job": job, "question_id": question_id, "results": results}
                atomic_json(path, value)
                return value
            finally:
                close_old_connections()

        rows = []
        with ThreadPoolExecutor(max_workers=max(1, min(4, options["workers"]))) as pool:
            for future in as_completed([pool.submit(execute, job) for job in jobs]):
                rows.append(future.result())
                self.stdout.write(f"{len(rows)}/{len(jobs)} {rows[-1]['job']['id']}")
                self.stdout.flush()
        cases = [r for row in rows if row["job"]["kind"] == "answer" for r in row["results"]]
        denominator = 25 if options["smoke25"] else 260
        if len(cases) != denominator:
            raise CommandError("Application answer-sheet denominator changed.")
        cells = defaultdict(dict)
        for row in rows:
            if row["job"]["kind"] == "star":
                for value in row["results"]:
                    cells[(value["plan_id"], row["job"]["criterion"])][row["job"]["style"]] = bool(
                        value["required"]
                    ) and set(value["required"]) <= set(value["covered"])
        summary = {
            "run_id": run_id,
            "manifest": str(manifest_file),
            "release_id": str(release.id),
            "method": release.method,
            "answer_cases": denominator,
            "outcomes": dict(
                Counter(
                    r["completeness"] + "_answer" if r["status"] == "answered" else r["status"]
                    for r in cases
                )
            ),
            "table_heavy": dict(
                Counter(
                    r["completeness"] + "_answer" if r["status"] == "answered" else r["status"]
                    for row in rows
                    if row["job"]["kind"] == "answer" and row["job"]["table_heavy"]
                    for r in row["results"]
                )
            ),
            "rejection_reasons_overlapping": dict(
                Counter(p["category"] for r in cases for p in r["rejections"])
            ),
            "final_not_found_reasons": dict(
                Counter(r["reason"] for r in cases if r["status"] == "not_found")
            ),
            "reference_cells": len(cells),
            "complete_reference_cells": sum(
                v.get("fixed", False) and v.get("customer", False) for v in cells.values()
            ),
            "note": "Fresh application-service execution, not a rerun or adjustment of the frozen bake-off score.",
        }
        atomic_json(directory / "summary.json", summary)
        if options["smoke25"]:
            self.stdout.write(json.dumps(summary))
            return
        atomic_json(
            Path(settings.BASE_DIR).parent / ("output/application-acceptance-" + run_id + ".json"),
            summary,
        )
        # Required immediate progress record: written before any subsequent card work.
        log = Path(settings.BASE_DIR).parent / "output/decisions-log.md"
        with log.open("a") as stream:
            stream.write(
                "\n\n## Section 16 A — fresh application run "
                + run_id
                + "\n\n"
                + "Baseline: 140/260 answered; 23/65 table-heavy answered; 12/39 complete Star packets.\n\n"
                + "Fresh measured results: `"
                + json.dumps(summary, sort_keys=True)
                + "`.\n"
                + "Outcomes are mutually exclusive; rejection reasons overlap. Packet coverage is not displayed evidence or expert verification.\n"
            )
        self.stdout.write(json.dumps(summary))
