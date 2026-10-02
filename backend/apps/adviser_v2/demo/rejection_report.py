"""Post-score diagnostics only: never modify scoring, validation or frozen pairs."""

PARAPHRASE = 'Statement must retain its complete quoted wording; paraphrase support cannot be established automatically.'


def paraphrase_only(validation: dict | None) -> bool:
    value = validation or {}
    checks = value.get('checks', [])
    return (len(checks) == 6 and not all(checks)
            and bool(value.get('problems')) and set(value['problems']) == {PARAPHRASE}
            and not value.get('rejected_wrong_plan', 0))


def arm_counts(rows: list[dict], case_label: str) -> dict:
    result = {}
    for method in ('H', 'P'):
        counts = {case_label: 0, 'rejected_attempts': 0, 'paraphrase_only_attempts': 0,
                  'final_unanswered_only_paraphrase': 0, 'split_pair_paraphrase_only_attempts': 0}
        cases = []
        for row in rows:
            counts[case_label] += 1
            arm = row['arms'][method]
            attempts = arm.get('attempts', [])
            counts['rejected_attempts'] += sum(not all(a['validation']['checks']) for a in attempts)
            counts['paraphrase_only_attempts'] += sum(paraphrase_only(a['validation']) for a in attempts)
            if arm['status'] == 'not_found' and paraphrase_only(arm.get('validation')):
                counts['final_unanswered_only_paraphrase'] += 1
                cases.append(row['job']['id'])
            for split in row.get('split_attempts', []):
                counts['split_pair_paraphrase_only_attempts'] += sum(
                    paraphrase_only(a['validation']) for a in split[method].get('attempts', []))
        result[method] = {**counts, 'case_ids': cases}
    return result


def summarize_rejections(rows: list[dict]) -> dict:
    return {'definition': 'The only reported failure is complete-quotation/paraphrase support. '
            'This does not establish semantic correctness or readability.',
            'arms': arm_counts([r for r in rows if r['job']['kind'] == 'answer'], 'answer_cases'),
            'star_query_arms': arm_counts([r for r in rows if r['job']['kind'] == 'star'], 'query_cases'),
            'all_query_arms': arm_counts(rows, 'query_cases')}
