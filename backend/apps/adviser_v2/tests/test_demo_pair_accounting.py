from copy import deepcopy

import pytest

from apps.adviser_v2.demo.pair_accounting import first_matching_attempt
from apps.adviser_v2.demo.relay import LUNA, SONNET


def record(method, model=LUNA, number=0):
    return {'call_id': method + str(number), 'model': model, 'observed_model': model,
            'stage': 'section_selection', 'scope': {'evaluation_job': 'j', 'method': method, 'pair_attempt': number}}


def test_selector_rejection_keeps_first_failure_not_later_success():
    first = {'H': {'status': 'not_found', 'models': [], 'reason': 'Invalid section.'},
             'P': {'status': 'answered', 'models': [LUNA]}}
    later = {m: {'status': 'answered', 'models': [LUNA]} for m in ('H', 'P')}
    preserved = deepcopy(first)
    arms, proof = first_matching_attempt('j', [first, later], [record('H'), record('P')])
    assert first == preserved
    assert arms['H']['status'] == 'not_found' and arms['H']['models'] == [LUNA]
    assert proof['selected_attempt'] == 0 and proof['discarded_attempts'] == 1
    with pytest.raises(ValueError, match='No same-model'):
        first_matching_attempt('j', [first], [])


def test_real_model_split_requires_later_matching_pair():
    first = {'H': {'status': 'answered', 'models': [LUNA]}, 'P': {'status': 'answered', 'models': [SONNET]}}
    later = {m: {'status': 'not_found', 'models': [SONNET]} for m in ('H', 'P')}
    records = [record('H'), record('P', SONNET), record('H', SONNET, 1), record('P', SONNET, 1)]
    arms, proof = first_matching_attempt('j', [first, later], records)
    assert proof['selected_attempt'] == 1
    assert arms['H']['status'] == 'not_found'
    with pytest.raises(ValueError, match='No same-model'):
        first_matching_attempt('j', [first], records)


def test_unavailable_slots_need_no_model_call():
    arms = {m: {'status': 'documents_unavailable', 'models': []} for m in ('H', 'P')}
    assert first_matching_attempt('j', [arms], [])[0] == arms
