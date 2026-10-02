import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.adviser_v2.demo.acquisition import INSURERS
from apps.adviser_v2.demo.catalogue import register_rows, scope
from apps.adviser_v2.demo.evidence import atomic_json


class Command(BaseCommand):
    help = 'Inventory official register entries with visible scope/currentness uncertainty; no automatic evidence admission.'

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        all_rows, summaries = [], []
        for key, name, url in INSURERS:
            candidates = list(root.rglob(key + '-discovery.json'))
            rows = []
            if candidates:
                source = json.loads(candidates[0].read_text())
                if source.get('source_sha256'):
                    html = candidates[0].parent / (source['source_sha256'] + '.html')
                    rows = register_rows(key, html.read_text(), source)
            rendered = root.parent / (key + '-rendered-register.json')
            if rendered.exists():
                captured = json.loads(rendered.read_text())
                html = captured['html']
                source = {'source_url': captured['source_url'],
                          'source_sha256': hashlib.sha256(html.encode()).hexdigest(),
                          'retrieved_at': datetime.fromtimestamp(rendered.stat().st_mtime, UTC).isoformat()}
                rows = register_rows(key, html, source)
            # The prior official Care register is retained explicitly as historical
            # metadata when its latest page cannot be fetched. It is not current proof.
            if key == 'care':
                prior = Path('/home/akhilesh/Projects/coverguide-star-pilot-data/three-insurer/care-roster.json')
                if prior.exists():
                    saved = json.loads(prior.read_text())
                    for item in saved['products']:
                        status, reason = scope(item['name_as_listed'], item.get('uin', ''))
                        if item.get('roster_section') == 'withdrawn':
                            status, reason = 'excluded', 'Listed as withdrawn in the preserved official register.'
                        rows.append({'insurer_id': key, 'name': item['name_as_listed'], 'uin': item.get('uin', ''),
                            'scope': status, 'reason': reason, 'edition_status': 'historical_register_only',
                            'variant_status': 'unresolved', 'source_url': saved['source_url'],
                            'source_sha256': saved['source_sha256'], 'retrieved_at': saved['captured_at'],
                            'documents': [], 'source_row': item['source_row']})
            if key == 'star':
                prior = Path('/home/akhilesh/Projects/coverguide-star-pilot-data/star/source-snapshot.json')
                if prior.exists():
                    saved = json.loads(prior.read_text())
                    source = saved['sources']['products']
                    for item in saved['products']:
                        status, reason = scope(item['name'], item.get('uin', ''))
                        documents = [d for d in saved['documents'] if item['uin'] in d.get('candidate_product_uins', [])]
                        rows.append({'insurer_id': key, 'name': item['name'], 'uin': item.get('uin', ''),
                            'scope': status, 'reason': reason, 'edition_status': 'historical_register_only',
                            'variant_status': 'unresolved', 'source_url': source['url'],
                            'source_sha256': source['sha256'], 'retrieved_at': saved['source_captured_at'],
                            'documents': documents, 'source_row': item['source_row']})
            supplement = root / 'catalogue-supplements' / (key + '.json')
            if supplement.exists():
                rows.extend(json.loads(supplement.read_text()))
            for row in rows:
                row['insurer'] = name
            all_rows.extend(rows)
            summaries.append({'insurer_id': key, 'insurer': name, 'source_url': url,
                'register_entries': len(rows), 'scope_counts': dict(Counter(r['scope'] for r in rows)),
                'verified_current_plan_count': None, 'catalogue_complete': False,
                'limitation': 'Current edition and complete retail scope are not established.' if rows else
                              'Official catalogue unavailable or requires further discovery; count is unknown.'})
        payload = {'schema_version': 1, 'selection_basis': 'demo_sample', 'insurers': summaries,
                   'entries': all_rows, 'executable_evidence': False}
        atomic_json(root / 'catalogue-inventory.json', payload)
        repository = Path(settings.BASE_DIR).parent
        atomic_json(repository / 'output/catalogue-inventory.json', payload)
        self.stdout.write(json.dumps(summaries, indent=2))
