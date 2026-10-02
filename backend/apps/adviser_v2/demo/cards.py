"""Winner-based offline cards; typed projections use narrow source grammars.

Exact quotations remain visible even when a complex rule cannot be executed.
Unsupported numbers, family combinations and purchase geography stay not stated.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import Literal

from django.db import close_old_connections
from pydantic import Field

from .answers import ANSWER_PROMPT
from .contracts import AgeRule, Answer, CardField, Closed, PlanCard, Statement
from .relay import Relay
from .search import search
from .validation import validate

FIELDS = ('entry_age', 'renewal_age', 'family', 'sum_insured', 'geography', 'copay',
          'room_limit', 'ped_waiting', 'maternity', 'opd', 'icu', 'specified_waiting', 'newborn',
          'deductible', 'restoration', 'no_claim_bonus', 'pre_post', 'day_care', 'road_ambulance',
          'air_ambulance', 'ayush', 'organ_donor', 'home_care', 'health_check', 'cataract')


class FieldSource(Closed):
    field: Literal[*FIELDS]
    status: Literal['answered', 'not_found']
    statements: list[Statement] = Field(max_length=3)


class CardSources(Closed):
    fields: list[FieldSource] = Field(max_length=25)


def projected_field(source: FieldSource | None) -> CardField:
    if source is None or source.status != 'answered' or not source.statements:
        return CardField(state='not_stated')
    statements = source.statements
    citations = [c for s in statements for c in s.citations]
    # The complete clause is retained as a condition. A complex clause remains
    # unresolved for matching until a supported executable projection exists.
    return CardField(state='stated', labels=[s.text for s in statements],
        citations=citations, conditions=[condition for s in statements for condition in [*s.conditions, *s.restrictions]])


def entry_rules(source: FieldSource | None) -> list[AgeRule]:
    if not source or source.status != 'answered':
        return []
    for statement in source.statements:
        for citation in statement.citations:
            raw = ' '.join(citation.quote.split())
            pattern = r'(?:Any person|Persons?|Adults?)\s+(?:aged\s+)?between\s+(\d+)\s+years\s+and\s+(\d+)\s+years\s+(?:can take|can apply|are eligible)'
            match = re.search(pattern, raw, re.I)
            if match and not statement.conditions and not statement.restrictions:
                minimum, maximum = map(int, match.groups())
                if 0 <= minimum <= maximum <= 120:
                    # Completed years: an upper age of 65 includes the 65th year.
                    return [AgeRule(relationship='self', minimum_days=minimum * 365,
                        maximum_days=(maximum + 1) * 365 - 1, citations=[citation])]
    return []


def extract_fields(bundle: dict, original: PlanCard, method: str, fields: tuple[str, ...], relay):
    query = ('Find complete original clauses for these fields: ' + ', '.join(fields) +
             '. Distinguish new-application entry from renewal ages, and floater from individual basis. '
             'For family, include every permitted relationship and composition restriction. '
             'For sum insured, include all new-business choices and any age/variant restrictions. '
             'Geography means purchase eligibility, not treatment territory. Include all conditions.')
    found = search(bundle=bundle, question=query, method=method, relay=relay, priority='background')
    packet = found.packet
    messages = [{'role': 'user', 'content': json.dumps(packet.evidence(), ensure_ascii=False)},
        {'role': 'user', 'content': json.dumps({'fields': fields, 'selected_variant': original.variant,
            'task': 'Extract exact cited clauses for every requested field; not_found for missing fields.'})}]
    attempts, accepted, models = [], {}, {found.model}
    for correction in range(2):
        result = relay.call(instructions=ANSWER_PROMPT + ' Return the requested fields contract instead of a single answer.',
            messages=messages, schema=CardSources.model_json_schema(), stage='plan_card', max_tokens=8192)
        models.add(result.model)
        sources = CardSources.model_validate(result.value)
        names = [f.field for f in sources.fields]
        problems = []
        if len(set(names)) != len(names) or set(names) != set(fields):
            problems.append('Return each requested field exactly once and no other fields.')
        else:
            for source in sources.fields:
                checked = validate(Answer(plan_id=original.plan_id, status=source.status, statements=source.statements), packet,
                                   variant=original.variant, known_variants=tuple(bundle.get('variants', [])))
                attempts.append({'field': source.field, 'model': result.model, 'source': source.model_dump(),
                                 'validation': asdict(checked), 'correction': correction, 'call_ids': result.call_ids})
                if checked.passed:
                    accepted[source.field] = source
                else:
                    problems.extend(source.field + ': ' + p for p in checked.problems)
        if not problems:
            break
        messages.extend([{'role': 'assistant', 'content': sources.model_dump_json()},
                         {'role': 'user', 'content': 'Correct once: ' + json.dumps(problems)}])
    return accepted, {'fields': fields, 'models': sorted(models), 'attempts': attempts,
                     'omissions': list(packet.omitted_ids), 'packet': packet.evidence()}


def sum_insured_field(source: FieldSource | None) -> CardField:
    field = projected_field(source)
    if source is None or field.conditions:
        return field
    for statement in source.statements:
        for citation in statement.citations:
            # Only a labelled list of rupee amounts is executable. Benefit limits,
            # renewal-only choices, ranges and mixed age/variant clauses stay text.
            raw = ' '.join(citation.quote.split())
            match = re.fullmatch(r'Sum Insured Options?:\s*((?:Rs\.?\s*[\d,]+/-[\s,]*(?:and\s*)?)+)[.;]?', raw, re.I)
            if match:
                numbers = [int(n.replace(',', '')) for n in re.findall(r'Rs\.?\s*([\d,]+)/-', match[1], re.I)]
                if numbers and all(n > 0 for n in numbers):
                    return field.model_copy(update={'numbers': sorted(set(numbers)), 'exhaustive': True,
                                                     'citations': [citation]})
    return field


def build_card(bundle: dict, original: PlanCard, method: str, relay=None) -> tuple[PlanCard, dict]:
    relay = relay or Relay.configured()
    # Small independent field groups prevent a 25-field response from exhausting
    # its output budget and retrieve clauses omitted by one broad query.
    groups = [FIELDS[n:n + 5] for n in range(0, len(FIELDS), 5)]
    def group(fields):
        close_old_connections()
        try:
            return extract_fields(bundle, original, method, fields, relay)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(group, groups))
    accepted = {name: value for fields, _ in results for name, value in fields.items()}
    models = sorted({model for _, audit in results for model in audit['models']})
    updates = {name: projected_field(accepted.get(name)) for name in
               ('geography', 'copay', 'room_limit', 'ped_waiting', 'maternity', 'opd')}
    updates['sum_insured'] = sum_insured_field(accepted.get('sum_insured'))
    # Complex or basis-dependent rules remain unresolved until a supported
    # executable projection exists; source quotations are still shown in full.
    updates.update(entry_ages=entry_rules(accepted.get('entry_age')), renewal_ages=[], family_rule=None,
                   model=models[-1] if len(models) == 1 else None, status='partial',
                   common_needs=[{'field': name, 'value': projected_field(accepted.get(name)).model_dump()} for name in FIELDS])
    card = PlanCard.model_validate({**original.model_dump(), **updates})
    return card, {'method': method, 'models': models, 'groups': [audit for _, audit in results]}
