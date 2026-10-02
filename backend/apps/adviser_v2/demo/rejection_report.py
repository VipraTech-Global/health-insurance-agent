"""Post-score diagnostics only: never modify scoring, validation or frozen pairs."""

PARAPHRASE = 'Statement must retain its complete quoted wording; paraphrase support cannot be established automatically.'


def paraphrase_only(validation: dict | None) -> bool:
    value = validation or {}
    checks = value.get('checks', [])
    return (len(checks) == 6 and not all(checks)
            and bool(value.get('problems')) and set(value['problems']) == {PARAPHRASE}
            and not value.get('rejected_wrong_plan', 0))


def summarize_rejections(rows: list[dict]) -> dict:
    result = {}
    for method in ('H', 'P'):
        counts = {'answer_cases': 0, 'rejected_attempts': 0, 'paraphrase_only_attempts': 0,
                  'final_unanswered_only_paraphrase': 0, 'split_pair_paraphrase_only_attempts': 0}
        cases = []
        for row in rows:
            if row['job']['kind'] != 'answer':
                continue
            counts['answer_cases'] += 1
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
    return {'definition': 'The only reported failure is complete-quotation/paraphrase support. '
            'This does not establish semantic correctness or readability.', 'arms': result}
