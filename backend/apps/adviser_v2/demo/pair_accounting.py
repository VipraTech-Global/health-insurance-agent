"""Recover model provenance, never retrieval or answers, from immutable call logs."""

from copy import deepcopy

from .relay import MODELS


def first_matching_attempt(job_id: str, candidates: list[dict], records: list[dict]) -> tuple[dict, dict]:
    """Use the earliest same-model attempt, including rejected selector outputs.

    The original runner mistook a missing result model label for a transition.
    Audit records retain the actual model even when source-ID validation raises.
    This rule is applied uniformly without looking at an arm's answer quality.
    """
    examined = []
    for number, original in enumerate(candidates):
        arms = deepcopy(original)
        identities, proof = set(), {}
        for method in ('H', 'P'):
            calls = [r for r in records if (r.get('scope') or {}).get('evaluation_job') == job_id
                     and r['scope'].get('method') == method and r['scope'].get('pair_attempt') == number]
            observed = {r['observed_model'] for r in calls if r.get('observed_model')}
            requested = {r['model'] for r in calls if r.get('model')}
            declared = set(arms[method].get('models', []))
            identities.update(observed | requested | declared)
            proof[method] = {'observed_models': sorted(observed), 'requested_models': sorted(requested),
                             'call_ids': [r['call_id'] for r in calls]}
            if not declared and observed:
                arms[method]['models'] = sorted(observed)
                arms[method]['model_provenance'] = 'Recovered from immutable relay call log after selector rejection.'
                arms[method]['search_call_ids'] = [r['call_id'] for r in calls if r['stage'] == 'section_selection']
        changed = any(a.get('status') == 'model_changed' for a in arms.values())
        proven = all(proof[m]['observed_models'] or arms[m].get('models')
                     or arms[m].get('status') in {'documents_unavailable', 'temporarily_unavailable'}
                     for m in ('H', 'P'))
        same = len(identities) <= 1 and identities <= set(MODELS) and proven
        examined.append({'attempt': number, 'models': sorted(identities), 'explicit_transition': changed})
        if same and not changed:
            return arms, {'selected_attempt': number, 'proof': proof, 'examined_attempts': examined,
                          'discarded_attempts': len(candidates) - 1}
    raise ValueError('No same-model saved pair is established for ' + job_id)
