"""Resumable paired evaluation; this module never changes the protocol or prompts."""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.db import close_old_connections

from .answers import answer_plan
from .bakeoff import QUESTIONS, Score, complete_cell, freeze, paired_models_match, winner
from .evidence import Packet, Section, atomic_json, reference_covered
from .relay import AUDIT_CONTEXT, ModelChanged, Relay, RelayUnavailable
from .search import search


def packet_from(value: dict) -> Packet:
    return Packet(value['plan_id'], tuple(Section.from_payload(s) for s in value['sections']),
                  tuple(value['omitted_ids']), value['tokens'], tables=tuple(value.get('tables', [])))


def evidence_counts(value: dict) -> tuple[int, int]:
    attempts = value.get('attempts', [])
    rejected = sum(a['validation'].get('rejected_wrong_plan', 0) for a in attempts
                   if not all(a['validation']['checks']))
    displayed = 0
    if value.get('status') == 'answered' and all((value.get('validation') or {}).get('checks', [False])):
        answer = value['answer']
        packet = value['packet']
        selected = {s['id']: s for s in packet['sections']}
        displayed += int(answer['plan_id'] != value['plan_id'])
        for statement in answer['statements']:
            for item in [statement, *statement['conditions'], *statement['restrictions']]:
                for citation in item['citations']:
                    section = selected.get(citation['section_id'])
                    displayed += int(section is None or section['plan_id'] != value['plan_id'])
    return displayed, rejected


def make_jobs(plans: list[dict], queries: list[dict], slots: list[dict]) -> list[dict]:
    by_plan = {p['policy_version_id']: p for p in plans}
    if len(queries) != 39 or len(slots) != 13 or len(QUESTIONS) != 20:
        raise ValueError('Evaluation denominators must be 39 Star cells and 13 x 20 answer cases.')
    jobs = []
    for n, query in enumerate(queries):
        for style in ('fixed', 'customer'):
            jobs.append({'id': f'star-{n:02}-{style}', 'kind': 'star', 'cell': n, 'style': style,
                'plan_id': query['policy_version_id'], 'question': query[style], 'criterion': query['criterion'],
                'table_heavy': query['table_heavy']})
    for slot in slots:
        for key, question, table in QUESTIONS:
            jobs.append({'id': f"answer-{slot['id']}-{key}", 'kind': 'answer', 'slot': slot['id'],
                'plan_id': slot.get('plan_id'), 'question': question, 'question_key': key,
                'table_heavy': table, 'unavailable_reason': slot.get('unavailable_reason')})
    if any(j['plan_id'] and j['plan_id'] not in by_plan for j in jobs):
        raise ValueError('An evaluation slot references a missing bundle.')
    return jobs


def freeze_run(root: Path, plans: list[dict], queries: list[dict], slots: list[dict], repository: Path) -> str:
    directory = Path(__file__).parent
    files = ['answers.py', 'search.py', 'evidence.py', 'validation.py', 'contracts.py', 'bakeoff.py',
             'relay.py', 'evaluation.py', 'vectors.py', 'charts.py']
    sources = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in files}
    fingerprint = freeze(root, {'bundles': plans, 'queries': queries, 'slots': slots,
        'source_hashes': sources, 'questions': [list(q) for q in QUESTIONS],
        'protocol': (repository / 'docs/ten-insurer-bakeoff-protocol.md').read_text(),
        'embedding': {'model': 'BAAI/bge-m3', 'revision': '5617a9f61b028005a4858fdac845db406aefb181',
                      'pooling': 'CLS', 'dimensions': 1024, 'normalization': 'L2', 'profile': 'full-fp32'},
        'packet_tokens': 16000, 'bm25': {'k1': 1.5, 'b': .75}, 'rrf_k': 60})
    path = root / 'frozen.json'
    saved = json.loads(path.read_text())
    if 'source_commit' not in saved:
        saved['source_commit'] = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repository,
                                                check=True, capture_output=True, text=True).stdout.strip()
        atomic_json(path, saved)
    return fingerprint


def run_job(job: dict, bundle: dict | None, root: Path) -> dict:
    path = root / 'pairs' / (job['id'] + '.json')
    if path.exists():
        return json.loads(path.read_text())
    if bundle is None:
        row = {'job': job, 'arms': {m: {'status': 'documents_unavailable', 'models': [],
               'reason': job['unavailable_reason']} for m in ('H', 'P')}, 'split_attempts': []}
        atomic_json(path, row)
        return row
    split_attempts = []
    relay = Relay.configured()
    for pair_attempt in range(12):
        model = relay.state.model()
        if model is None:
            relay.probe_due(deadline=time.monotonic() + 240)
            model = relay.state.model()
        if model is None:
            while model is None:
                atomic_json(root / 'paused' / (job['id'] + '.json'),
                            {'reason': 'Both subscriptions limited; waiting for shared reset/probe.'})
                time.sleep(30)
                relay.probe_due(deadline=time.monotonic() + 60)
                model = relay.state.model()

        def arm(method, model=model, pair_attempt=pair_attempt):
            close_old_connections()
            audit_token = AUDIT_CONTEXT.set({'evaluation_job': job['id'], 'method': method,
                                            'pair_attempt': pair_attempt})
            try:
                if job['kind'] == 'answer':
                    return answer_plan(bundle, job['question'], method=method, priority='background', expected_model=model)
                found = search(bundle=bundle, question=job['question'], method=method, relay=Relay.configured(),
                               priority='background', expected_model=model)
                references = bundle['references'][job['criterion']]
                return {'status': 'retrieved', 'models': [found.model], 'packet': found.packet.evidence(),
                        'search_call_ids': found.call_ids,
                        'covered': [ref['id'] for ref in references if reference_covered(ref, found.packet)]}
            except ModelChanged as exc:
                return {**getattr(exc, 'partial_result', {}), 'status': 'model_changed', 'models': [model]}
            except (RelayUnavailable, ValueError) as exc:
                return {'status': 'temporarily_unavailable', 'models': [model], 'reason': str(exc), 'covered': []}
            finally:
                AUDIT_CONTEXT.reset(audit_token)
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(arm, m): m for m in ('H', 'P')}
            arms = {futures[f]: f.result() for f in as_completed(futures)}
        # Even a completed old-model arm is discarded when its partner switched.
        known_pair = paired_models_match(arms['H'], arms['P'])
        failed_without_output = any(a['status'] == 'temporarily_unavailable' for a in arms.values())
        same_pin = all(set(a.get('models', [])) <= {model} for a in arms.values())
        if any(a['status'] == 'model_changed' for a in arms.values()) or not (known_pair or (failed_without_output and same_pin)):
            split_attempts.append(arms)
            atomic_json(root / 'split-pairs' / f"{job['id']}-{pair_attempt}.json", {'job': job, 'arms': arms})
            continue
        row = {'job': job, 'arms': arms, 'split_attempts': split_attempts}
        atomic_json(path, row)
        return row
    raise RelayUnavailable('Repeated shared model transitions; pair remains unscored and resumable.')


def score_rows(rows: list[dict], queries: list[dict], plans: list[dict]) -> dict:
    if len(rows) != 338 or len({r['job']['id'] for r in rows}) != 338:
        raise ValueError('A complete run needs all 78 Star query pairs and 260 answer pairs.')
    by_plan = {p['policy_version_id']: p for p in plans}
    scores = []
    for method in ('H', 'P'):
        complete = 0
        for n, query in enumerate(queries):
            results = {r['job']['style']: set(r['arms'][method].get('covered', []))
                       for r in rows if r['job']['kind'] == 'star' and r['job']['cell'] == n}
            refs = {ref['id'] for ref in by_plan[query['policy_version_id']]['references'][query['criterion']]}
            complete += complete_cell(refs, results['fixed'], results['customer'])
        answers = [r['arms'][method] for r in rows if r['job']['kind'] == 'answer']
        answered = sum(a['status'] == 'answered' and all((a.get('validation') or {}).get('checks', [False])) for a in answers)
        displayed = rejected = 0
        for row in rows:
            values = [row['arms'][method], *(pair[method] for pair in row['split_attempts'])]
            for position, value in enumerate(values):
                shown, blocked = evidence_counts(value)
                displayed += shown if position == 0 else 0
                rejected += blocked
        scores.append(Score(method, complete, answered, displayed, rejected,
                            sum(a['status'] == 'documents_unavailable' for a in answers)))
    outcome = winner(*scores)
    references = {ref['id'] for p in plans for refs in p['references'].values() for ref in refs}
    outcome['reference_spans'] = len(references)
    outcome['unique_span_recall'] = {}
    for method in ('H', 'P'):
        found = {style: set().union(*(set(r['arms'][method].get('covered', [])) for r in rows
                 if r['job']['kind'] == 'star' and r['job']['style'] == style)) for style in ('fixed', 'customer')}
        outcome['unique_span_recall'][method] = {'fixed': len(found['fixed'] & references),
            'customer': len(found['customer'] & references), 'both': len(found['fixed'] & found['customer'] & references)}
    outcome['map_fallbacks'] = sum(d['status'] == 'fallback' for p in plans for d in p.get('document_status', []))
    return outcome


def write_report(root: Path, repository: Path, rows: list[dict], outcome: dict, slots: list[dict]) -> None:
    atomic_json(root / 'result.json', outcome)
    records = [json.loads(line) for line in (root.parent / 'relay-calls.jsonl').read_text().splitlines()]
    lines = ['# Search bake-off — protocol v2', '', f"Winner: **{outcome['winner']}**. {outcome['reason']}",
             '', f"Map fallbacks: {outcome['map_fallbacks']}. Unique reference spans: {outcome['reference_spans']}.",
             f"Unique-span recall (fixed/customer/both): {outcome['unique_span_recall']}.",
             '', 'Answered means all six deterministic checks passed; it is not expert-verified correctness.',
             'Only displayed wrong-plan quotations disqualify. Rejected attempts are reported separately.', '',
             '| Arm | Complete Star cells /39 | Answered /260 | Score | Displayed wrong-plan | Rejected wrong-plan | Unavailable |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for s in outcome['arms']:
        lines.append(f"| {s['method']} | {s['complete_cells']} | {s['answered']} | {s['score']:.2f} | {s['displayed_wrong_plan']} | {s['rejected_wrong_plan']} | {s['unavailable']} |")
    lines += ['', '## Evaluation slots', '']
    for s in slots:
        lines.append(f"- {s['id']}: {s['name']}. {s.get('unavailable_reason') or s.get('note', 'Available source bundle.')}")
    lines += ['', '## Table-heavy cases', '']
    for method in ('H', 'P'):
        subset = [r['arms'][method] for r in rows if r['job']['kind'] == 'answer' and r['job']['table_heavy']]
        lines.append(f"- {method}: {sum(a['status'] == 'answered' for a in subset)}/{len(subset)} answered.")
    lines += ['', '## Per-question results', '', f'Full packets, omissions, rejected drafts, models and call IDs: `{root / "pairs"}`.',
              f'Per-call queue/model/total timing and token usage: `{root.parent / "relay-calls.jsonl"}`.', '']
    for row in sorted(rows, key=lambda r: r['job']['id']):
        job = row['job']
        lines += [f"### {job['id']}", '', job['question'], '']
        for method in ('H', 'P'):
            value = row['arms'][method]
            lines.append(f"**{method}: {value['status']}**; models={value.get('models', [])}; total_ms={value.get('total_ms', 'see call log')}.")
            calls = [r for r in records if (r.get('scope') or {}).get('evaluation_job') == job['id']
                     and r['scope'].get('method') == method]
            usage = {'input': sum(r.get('usage', {}).get('input_tokens', 0) for r in calls),
                'cached': sum(r.get('usage', {}).get('input_tokens_details', {}).get('cached_tokens', 0) for r in calls),
                'reasoning': sum(r.get('usage', {}).get('output_tokens_details', {}).get('reasoning_tokens', 0) for r in calls),
                'output': sum(r.get('usage', {}).get('output_tokens', 0) for r in calls)}
            lines.append(f"Calls: {len(calls)}; tokens: {usage}; queue_ms={sum(r['queue_ms'] for r in calls)}; model_ms={sum(r['model_ms'] for r in calls)}; transport retries={sum(r.get('transport_retry', 0)>0 for r in calls)}; JSON repairs={sum(r.get('json_retry', 0)>0 for r in calls)}.")
            if job['kind'] == 'star':
                lines.append(f"Covered reference spans: {value.get('covered', [])}.")
            for statement in (value.get('answer') or {}).get('statements', []):
                lines.append('> ' + statement['text'].replace('\n', '\n> '))
            check = value.get('validation') or {}
            lines.append(f"Checks: {check.get('checks', [])}; failures: {check.get('problems', [])}.")
            for anchor in check.get('anchors', []):
                lines.append(f"- {anchor['document_sha256']}, physical page {anchor['page']}, chars {anchor['start']}–{anchor['end']}: {anchor['quote']}")
            lines.append(f"Omitted section IDs: {value.get('omissions', (value.get('packet') or {}).get('omitted_ids', []))}.")
            lines.append('')
    (repository / 'output/search-bakeoff.md').write_text('\n'.join(lines))
