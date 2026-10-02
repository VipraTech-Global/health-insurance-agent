"""Report completed application execution without new retrieval or scored calls."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser_v2.demo.evidence import atomic_json
from apps.adviser_v2.models import DemoRelease


class Command(BaseCommand):
    help = __doc__

    def handle(self, **options):
        if settings.DATABASES['default']['NAME'] != 'coverguide_star_slice':
            raise CommandError('Report only the isolated application execution.')
        release = DemoRelease.objects.get(active=True)
        root = Path(settings.COVERGUIDE_REPORT_ROOT) / 'ten-insurer/application-acceptance' / str(release.id)
        if not (root / 'summary.json').exists():
            raise CommandError('The full application acceptance run has not finished.')
        summary = json.loads((root / 'summary.json').read_text())
        state = json.loads((root / 'state.json').read_text())
        rows = [json.loads((root / 'results' / (job['id'] + '.json')).read_text()) for job in state['jobs']]
        cases = [(row, result) for row in rows if row['job']['kind'] == 'answer' for result in row['results']]
        references = [(row, result) for row in rows if row['job']['kind'] == 'star' for result in row['results']]
        if len(cases) != 260 or len(references) != 78:
            raise CommandError('Application denominator or reference queries changed.')
        cells = defaultdict(dict)
        for row, value in references:
            cells[(value['plan_id'], row['job']['criterion'])][row['job']['style']] = {
                'complete': bool(value['required']) and set(value['required']) <= set(value['covered']),
                'required': value['required'], 'covered': value['covered'],
                'missing': sorted(set(value['required']) - set(value['covered']))}
        details = {**summary, 'models': dict(Counter(model for _, r in cases for model in set(r['models']))),
            'table_heavy': dict(Counter(r['status'] for row, r in cases if row['job']['table_heavy'])),
            'reference_details': [{'plan_id': plan, 'criterion': criterion, 'queries': queries,
                'complete': all(queries.get(style, {}).get('complete', False) for style in ('fixed', 'customer'))}
                for (plan, criterion), queries in sorted(cells.items())]}
        repository = Path(settings.BASE_DIR).parent
        atomic_json(repository / 'output/application-acceptance.json', details)
        lines = ['# Winning application answer sheet', '', f'Release: `{release.id}`. Method: {release.method}.', '',
            'Fresh execution through the application service. The five recovered flagships are included here. '
            'These results do not change the frozen bake-off or its unavailable slots.', '',
            f"Answer outcomes / 260: `{summary['outcomes']}`. Complete Star reference cells: "
            f"{summary['complete_reference_cells']}/39, requiring both fixed and customer query packets to contain every reference span.", '',
            f"Table-heavy answer outcomes: `{details['table_heavy']}`. Model usage by answer case: `{details['models']}`.", '',
            'An answered result passed six code checks; this is not expert-verified correctness. '
            'The reference comparison measures packet coverage, not answer completeness.', '']
        for row, value in cases:
            lines.extend([f"## {row['job']['id']} — {value['name']}", '', row['job']['question'], '',
                f"Status: **{value['status']}**. Models: {', '.join(value['models']) or 'No successful model call'}. "
                f"Elapsed including queue: {value['total_ms']} ms. Omitted sections: {len(value['omissions'])}.", '',
                f"Index: `{value['index_version']}`. Validation: `{value['validation']}`.", ''])
            answer = value.get('answer') or {}
            for statement in answer.get('statements', []):
                for item in [statement, *statement.get('conditions', []), *statement.get('restrictions', [])]:
                    lines.append('> ' + item['text'].replace('\n', '\n> '))
                    lines.append('')
            if value['omissions']:
                lines.extend(['Omitted section IDs: ' + ', '.join(f'`{key}`' for key in value['omissions']), ''])
        lines.extend(['## All 39 Star reference cells', '', '| Plan | Criterion | Fixed packet | Customer packet | Complete |',
                      '|---|---|---|---|---|'])
        for cell in details['reference_details']:
            query = cell['queries']
            counts = {style: f"{len(value['covered'])}/{len(value['required'])}" for style, value in query.items()}
            lines.append(f"| {cell['plan_id']} | {cell['criterion']} | {counts['fixed']} | {counts['customer']} | {cell['complete']} |")
        (repository / 'output/application-answer-sheet.md').write_text('\n'.join(lines) + '\n')
        self.stdout.write(json.dumps({key: value for key, value in details.items() if key != 'reference_details'}))
