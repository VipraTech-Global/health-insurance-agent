import hashlib
import json
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.demo.extraction import extract


class Command(BaseCommand):
    help = 'Extract reviewed browser recoveries into an app-only corpus, preserving the frozen evaluation.'

    def add_arguments(self, parser):
        parser.add_argument('--manifest', required=True, type=Path)

    def handle(self, **options):
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer'
        manifest = json.loads(options['manifest'].read_text())
        if manifest.get('scope') != 'application_only_after_frozen_bakeoff':
            raise CommandError('An explicit application-only admission manifest is required.')
        plans, excluded, pages_by_sha = [], [], {}
        for product in manifest['products']:
            documents, pages = [], []
            for row in product['documents']:
                if row['evidence_use'] != 'executable':
                    excluded.append(row)
                    continue
                path = root / 'objects' / (row['sha256'] + '.pdf')
                if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
                    raise CommandError('Missing or changed approved PDF: ' + row['sha256'])
                doc = {**row, 'path': str(path), 'status': 'acquired',
                    'document_key': product['key'] + ':' + row['role'] + ':' + row['sha256'][:12],
                    'document_version_id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'coverguide-demo-pdf:' + row['sha256']))}
                documents.append(doc)
                if row['sha256'] not in pages_by_sha:
                    pages_by_sha[row['sha256']] = extract(doc, root)
                pages.extend(pages_by_sha[row['sha256']])
            if not any(d['role'] == 'base_wording' for d in documents):
                raise CommandError('No applicable wording for ' + product['key'])
            for n, variant in enumerate(product['variants']):
                key = product['key'] if n == 0 else product['key'] + '-' + variant.casefold().replace(' ', '-')
                # The primary variant supersedes its unavailable picker placeholder.
                identity = 'coverguide-demo-unavailable:' + key if n == 0 else 'coverguide-demo-plan:' + key
                plans.append({k: v for k, v in product.items() if k != 'documents'} | {
                    'plan': key, 'policy_version_id': str(uuid.uuid5(uuid.NAMESPACE_URL, identity)),
                    'variant': variant, 'documents': documents, 'pages': pages, 'references': {}, 'chunks': []})
        target = root / 'app-catalogue'
        atomic_json(target / 'corpus.json', {'plans': plans, 'excluded_documents': excluded,
                    'scope': manifest['scope'], 'frozen_evaluation_modified': False})
        self.stdout.write(f'{len(plans)} app-only plan variants; {len(pages_by_sha)} physical PDFs; {len(excluded)} reference-only records.')
