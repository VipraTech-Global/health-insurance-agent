"""Overlap completed-document embeddings with maps still processing elsewhere."""
import json
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.evidence import atomic_json, build_sections, digest
from apps.adviser_v2.demo.search import embed
from apps.adviser_v2.models import DemoSectionVector


class Command(BaseCommand):
    help = 'Fill the shared source-text vector cache as each document map completes, without waiting for an insurer.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true')
        parser.add_argument('--source-root', type=Path)

    def handle(self, **options):
        root = options['source_root'] or Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        corpus = json.loads((root / 'corpus.json').read_text())
        count = 0
        while True:
            pending = 0
            progress_path = root / 'map-progress.json'
            failures = json.loads(progress_path.read_text()).get('failures', {}) if progress_path.exists() else {}
            for plan in corpus['plans']:
                for document in plan['documents']:
                    path = root / 'maps' / (document['sha256'] + '.json')
                    if not path.exists():
                        if failures.get(document['sha256'], {}).get('status') != 'map_failed':
                            pending += 1
                            continue
                        saved = None
                    else:
                        saved = json.loads(path.read_text())
                    pages = [p for p in plan['pages'] if p['document_version_id'] == document['document_version_id']]
                    sections, _, _ = build_sections(plan_id=plan['policy_version_id'], document=document, pages=pages, saved_map=saved)
                    for section in sections:
                        text_hash = digest(section.index_text)
                        cached = root / 'vectors' / (text_hash + '.json')
                        if cached.exists():
                            continue
                        old = DemoSectionVector.objects.filter(text_sha256=text_hash).first()
                        vector = [float(v) for v in old.embedding] if old else embed([section.index_text], priority='background')[0]
                        atomic_json(cached, {'model': 'BAAI/bge-m3', 'revision': '5617a9f61b028005a4858fdac845db406aefb181',
                                            'text_sha256': text_hash, 'vector': vector})
                        count += 1
                    self.stdout.write(f"Cached {count} source vectors; document {document['sha256'][:12]}")
                    self.stdout.flush()
            if not options['loop'] or not pending:
                return
            time.sleep(15)
