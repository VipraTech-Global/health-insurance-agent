from apps.adviser_v2.demo.evaluation import evidence_counts, make_jobs, score_rows


def fixtures():
    queries = [{'policy_version_id': 'p', 'criterion': str(n), 'fixed': 'f', 'customer': 'c', 'table_heavy': False} for n in range(39)]
    plans = [{'policy_version_id': 'p', 'references': {str(n): [{'id': str(n)}] for n in range(39)}}]
    slots = [{'id': str(n), 'plan_id': 'p' if n < 8 else None, 'unavailable_reason': 'official PDF unavailable'} for n in range(13)]
    return plans, queries, slots


def test_fixed_jobs_and_missing_sources_remain_in_denominator():
    plans, queries, slots = fixtures()
    jobs = make_jobs(plans, queries, slots)
    assert len(jobs) == 338
    assert sum(j['plan_id'] is None for j in jobs) == 100
    rows = []
    for job in jobs:
        result = {'status': 'retrieved', 'covered': [str(job['cell'])]} if job['kind'] == 'star' else {
            'status': 'not_found' if job['plan_id'] else 'documents_unavailable'}
        rows.append({'job': job, 'arms': {'H': result, 'P': result}, 'split_attempts': []})
    outcome = score_rows(rows, queries, plans)
    assert outcome['winner'] == 'P'
    assert all(arm['complete_cells'] == 39 and arm['answered'] == 0 and arm['unavailable'] == 100 for arm in outcome['arms'])


def test_rejected_attempt_is_counted_but_not_displayed():
    draft = {'validation': {'checks': [False, True, True, True, True, True], 'rejected_wrong_plan': 2}}
    assert evidence_counts({'status': 'not_found', 'attempts': [draft]}) == (0, 2)


def test_independent_display_identity_audit():
    value = {'status': 'answered', 'plan_id': 'p', 'validation': {'checks': [True]*6},
        'packet': {'sections': []}, 'answer': {'plan_id': 'foreign', 'statements': [
            {'citations': [{'section_id': 'foreign'}], 'conditions': [], 'restrictions': []}]}}
    assert evidence_counts(value) == (2, 0)
