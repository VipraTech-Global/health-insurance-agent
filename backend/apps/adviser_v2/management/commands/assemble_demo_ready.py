"""Release complete plan bundles from global queues without waiting for slow insurers."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.evidence import atomic_json, cache_matches, digest
from apps.adviser_v2.demo.mapping import SDK_REVISION, assemble_sections


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--source-root", type=Path, required=True)

    def handle(self, **options):
        root = options["source_root"].resolve()
        corpus = json.loads((root / "corpus.json").read_text())
        progress = json.loads((root / "map-progress.json").read_text())
        failures = {k: v for k, v in progress["failures"].items() if v["status"] == "map_failed"}
        completed = set(progress["completed"]) | failures.keys()
        ready = [
            p for p in corpus["plans"] if all(d["sha256"] in completed for d in p["documents"])
        ]
        maps = {}
        for plan in ready:
            for doc in plan["documents"]:
                sha = doc["sha256"]
                if sha in failures or sha in maps:
                    continue
                saved = json.loads((root / "maps" / (sha + ".json")).read_text())
                pages = [
                    p["passage"]
                    for p in plan["pages"]
                    if p["document_version_id"] == doc["document_version_id"]
                ]
                if not cache_matches(
                    saved, pdf_sha=sha, raw_sha=digest(pages), sdk_revision=SDK_REVISION
                ):
                    raise CommandError("A completed map has incompatible provenance: " + sha)
                maps[sha] = saved
        target = root / "ready"
        target.mkdir(exist_ok=True)
        for name in ("maps", "vectors", "tables"):
            (root / name).mkdir(exist_ok=True)
            link = target / name
            if not link.exists():
                link.symlink_to(root / name, target_is_directory=True)
        atomic_json(target / "sections.json", assemble_sections({"plans": ready}, maps, failures))
        self.stdout.write(
            f"{len(ready)} complete plan variants ready; {len(corpus['plans']) - len(ready)} still processing."
        )
