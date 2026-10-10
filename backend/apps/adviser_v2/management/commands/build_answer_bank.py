from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from apps.adviser_v2.demo.answer_bank import (
    QUESTION_TOPICS,
    TOPIC_QUESTIONS,
    TOPICS,
    current,
    group,
    lookup,
    remember,
)
from apps.adviser_v2.demo.answer_replay import changed_pairs
from apps.adviser_v2.demo.answers import answer_plan
from apps.adviser_v2.demo.services import bundle_for, decrypted
from apps.adviser_v2.models import DemoQuestion, DemoRelease


class Command(BaseCommand):
    help = (
        "Fill the shared answer bank: the engine's validated answer to every canonical "
        "topic question for every plan in a release. Imports stored answers into missing "
        "pairs first, then answers only the missing or out-of-date pairs at background "
        "priority. After a change to checking, scope, quote boundaries or grouping, "
        "--refresh-changed also re-asks the pairs whose stored drafts now give a "
        "different answer; a packet, prompt, retrieval or draft change needs a version bump."
    )

    def add_arguments(self, parser):
        parser.add_argument("--release", help="Release ID (default: the active release).")
        parser.add_argument("--topics", nargs="*", choices=TOPICS, default=list(TOPICS))
        parser.add_argument("--workers", type=int, default=5)
        parser.add_argument("--dry-run", action="store_true", help="Report coverage only.")
        parser.add_argument(
            "--import-only", action="store_true", help="Import stored answers; run nothing."
        )
        parser.add_argument(
            "--retry-rejected",
            action="store_true",
            help="Also re-ask pairs whose every drafted unit failed validation.",
        )
        parser.add_argument(
            "--refresh-changed",
            action="store_true",
            help="Also re-ask pairs whose stored drafts, checked again by the current code "
            "without model calls, give a different answer.",
        )

    def handle(self, **options):
        release = (
            DemoRelease.objects.filter(pk=options["release"]).first()
            if options["release"]
            else DemoRelease.objects.filter(active=True).first()
        )
        if release is None:
            raise CommandError("No such release.")
        indexes = list(release.indexes.filter(revoked_at__isnull=True))
        by_id = {i.id: i for i in indexes}
        topics = options["topics"]
        if not options["dry_run"]:
            imported = self.import_stored(release, by_id)
            self.stdout.write(f"Imported {imported} stored answers.")
        gaps = self.report(release, indexes, topics, options["retry_rejected"])
        if options["refresh_changed"]:
            changed = changed_pairs(indexes, topics, release.method)
            self.stdout.write(f"{len(changed)} stored answers read differently by this code:")
            for index, topic, before, after in changed:
                self.stdout.write(f"  {index.name} ({index.variant}) · {topic}: {before} → {after}")
            gaps += [(i, t) for i, t, _, _ in changed if (i, t) not in gaps]
        if options["dry_run"] or options["import_only"] or not gaps:
            return
        self.stdout.write(f"Answering {len(gaps)} plan × topic pairs…")
        failures = Counter()

        def one(pair):
            index, topic = pair
            close_old_connections()
            try:
                result = answer_plan(
                    bundle_for(index),
                    TOPIC_QUESTIONS[topic],
                    method=release.method,
                    priority="background",
                )
                kept = remember(index, topic, release.method, result)
                return index, topic, result, kept
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=max(1, options["workers"])) as pool:
            jobs = [pool.submit(one, pair) for pair in gaps]
            for n, job in enumerate(as_completed(jobs), 1):
                try:
                    index, topic, result, kept = job.result()
                except Exception as exc:  # One plan's failure must not stop the others.
                    failures["error"] += 1
                    self.stderr.write(f"[{n}/{len(gaps)}] failed: {exc}")
                    continue
                if not kept:
                    failures[result.get("status")] += 1
                self.stdout.write(
                    f"[{n}/{len(gaps)}] {index.name} ({index.variant}) · {topic}: "
                    f"{result.get('status')} → "
                    f"{group(result, topic, index.variant) if kept else 'not kept'}"
                    f" in {result.get('total_ms', 0) / 1000:.0f}s"
                )
        if failures:
            self.stdout.write(f"Not kept (retry later): {dict(failures)}")
        self.report(release, indexes, topics)

    def import_stored(self, release, by_id):
        """Reuse current engine answers to canonical questions for the pairs the bank
        lacks. A current bank row is kept: live answers reach the bank as they finish, and
        one re-asked by --refresh-changed must not be put back by an older chat."""
        imported = 0
        have = {
            (index_id, topic)
            for topic in TOPICS
            for index_id in lookup(list(by_id.values()), topic, release.method)
        }
        questions = DemoQuestion.objects.filter(answers__index__in=list(by_id)).distinct()
        for question in questions.order_by("created_at"):
            try:
                text = decrypted(question.input_ciphertext, question.id)["question"]
            except (ValueError, KeyError):
                continue
            topic = QUESTION_TOPICS.get(text)
            if topic is None:
                continue
            for row in question.answers.exclude(result_ciphertext=None):
                if row.index_id not in by_id or (row.index_id, topic) in have:
                    continue
                result = decrypted(row.result_ciphertext, row.id)
                if (
                    current(result)
                    and result.get("method", release.method) == release.method
                    and remember(by_id[row.index_id], topic, release.method, result)
                ):
                    imported += 1
        return imported

    def report(self, release, indexes, topics, retry_rejected=False):
        gaps = []
        self.stdout.write(f"{'topic':18} answered not_found missing  base addon excluded")
        for topic in topics:
            found = lookup(indexes, topic, release.method)
            groups = Counter(group(found[i.id], topic, i.variant) for i in indexes if i.id in found)
            missing = [i for i in indexes if i.id not in found]
            gaps += [(i, topic) for i in missing]
            if retry_rejected:
                gaps += [
                    (i, topic)
                    for i in indexes
                    if i.id in found
                    and found[i.id]["status"] == "not_found"
                    and str(found[i.id].get("reason", "")).startswith("all_units_rejected")
                ]
            statuses = Counter(r["status"] for r in found.values())
            self.stdout.write(
                f"{topic:18} {statuses['answered']:8} {statuses['not_found']:9} "
                f"{len(missing):7}  {groups['base']:4} {groups['addon']:5} {groups['excluded']:8}"
            )
        return gaps
