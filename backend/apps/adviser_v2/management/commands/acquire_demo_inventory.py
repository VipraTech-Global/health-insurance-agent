"""Global resumable acquisition queue; discovery never becomes executable evidence."""

import hashlib
import json
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.acquisition import acquire, document_role
from apps.adviser_v2.demo.evidence import atomic_json, digest
from apps.adviser_v2.demo.extraction import extract

ROLES = {'base_wording', 'policy_wording', 'prospectus', 'brochure', 'premium_chart', 'customer_information_sheet'}


class Command(BaseCommand):
    help = __doc__

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        inventory = json.loads((root / 'catalogue-inventory.json').read_text())
        directory = root / 'catalogue-acquisition'
        documents = {}
        for entry in inventory['entries']:
            if entry['scope'] != 'review_pending':
                continue
            for doc in entry['documents']:
                if doc['role'] not in ROLES or document_role(doc['url']) == 'excluded':
                    continue
                key = digest(doc['url'])
                row = documents.setdefault(key, {**doc, 'insurer_id': entry['insurer_id'],
                    'source_url': entry['source_url'], 'associations': [], 'applicability': 'unresolved'})
                row['associations'].append({k: entry.get(k) for k in ('name', 'uin', 'edition_status', 'retrieved_at', 'source_sha256')})
        reusable = {}
        for path in (root / 'flagship-candidates.json', root / 'retry-flagship-candidates.json'):
            if path.exists():
                reusable.update({r['url']: r for r in json.loads(path.read_text()) if r['status'] == 'acquired_unreviewed'})

        def download(key, doc):
            path = directory / 'documents' / (key + '.json')
            if path.exists():
                return json.loads(path.read_text())
            old = reusable.get(doc['url'])
            if old and Path(old['path']).exists() and hashlib.sha256(Path(old['path']).read_bytes()).hexdigest() == old['sha256']:
                result = {**old, **doc, 'status': 'acquired_unreviewed', 'acquisition': 'existing_validated_object'}
            else:
                result = acquire(doc, root)
            atomic_json(path, result)
            return result

        def raw(row):
            sha = row['sha256']
            identity = str(uuid.uuid5(uuid.NAMESPACE_URL, 'coverguide-demo-pdf:' + sha))
            pages = extract({**row, 'document_version_id': identity, 'document_key': 'inventory:' + sha}, root)
            return {'sha256': sha, 'physical_pages': len(pages), 'status': 'extracted_unreviewed'}

        results, raw_jobs, seen = [], {}, set()
        with ThreadPoolExecutor(max_workers=6) as downloads, ThreadPoolExecutor(max_workers=2) as extraction:
            jobs = {downloads.submit(download, key, doc): key for key, doc in documents.items()}
            for future in as_completed(jobs):
                row = future.result()
                results.append(row)
                if row['status'] == 'acquired_unreviewed' and row['sha256'] not in seen:
                    seen.add(row['sha256'])
                    raw_jobs[extraction.submit(raw, row)] = row['sha256']
                self.stdout.write(f"{len(results)}/{len(jobs)} {row['insurer_id']} {row['status']}")
                self.stdout.flush()
                atomic_json(directory / 'progress.json', {'total': len(jobs), 'completed': len(results),
                    'statuses': dict(Counter(r['status'] for r in results)), 'executable_evidence': False})
            raw_results = []
            for future in as_completed(raw_jobs):
                try:
                    raw_results.append(future.result())
                except Exception as exc:
                    raw_results.append({'sha256': raw_jobs[future], 'status': 'extraction_failed', 'reason': str(exc)})
                atomic_json(directory / 'extractions.json', raw_results)
        atomic_json(directory / 'result.json', {'documents': results, 'extractions': raw_results, 'executable_evidence': False})
        self.stdout.write(json.dumps(dict(Counter(r['status'] for r in results))))
