"""Audited deletion-only projections of retained descriptive facts.

A projection cannot invent a value, condition, quantity or quote. Its narrowed
candidate must pass the normal exact-source checks and a fresh independent review.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from research_workspace.legacy_v2.processing.cited_facts import CitedFact


def fact_digest(fact: CitedFact) -> str:
    return hashlib.sha256(json.dumps(fact.model_dump(), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def primary_projection(fact: CitedFact, selection: dict[str, Any]) -> CitedFact:
    if selection['source_fact_sha256'] != fact_digest(fact):
        raise ValueError('The retained fact differs from the authorized secondary-statement projection.')
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', fact.value)

    def selected(values: list[Any], key: str) -> list[Any]:
        indexes = selection[key]
        if indexes != sorted(set(indexes)) or any(type(i) is not int or not 0 <= i < len(values) for i in indexes):
            raise ValueError('A projection must select existing items once, in their original order.')
        return [values[i] for i in indexes]

    value = ' '.join(selected(sentences, 'value_sentence_indexes'))
    if not value:
        raise ValueError('A secondary-statement projection cannot remove the complete core value.')
    citations = selected(fact.citations, 'citation_indexes')
    remap = {old: new for new, old in enumerate(selection['citation_indexes'])}

    def references(item: Any) -> dict[str, Any]:
        data = item.model_dump()
        data['citation_indexes'] = [remap[i] for i in data['citation_indexes'] if i in remap]
        if not data['citation_indexes']:
            raise ValueError('Every retained assertion must retain at least one original quotation.')
        return data

    regions = []
    for region in fact.table_regions:
        indexes = [remap[i] for i in region.citation_indexes if i in remap]
        labels = [remap[i] for i in region.label_indexes if i in remap]
        if len(indexes) >= 2 and labels:
            regions.append({'citation_indexes': indexes, 'label_indexes': labels})
    return CitedFact(
        value=value, value_kind=fact.value_kind, citations=citations,
        conditions=[references(c) for c in selected(fact.conditions, 'condition_indexes')],
        quantities=[references(q) for q in selected(fact.quantities, 'quantity_indexes')],
        table_regions=regions, secondary_statements=[],
        notes=[*(selected(fact.notes, 'note_indexes') if 'note_indexes' in selection else fact.notes),
            'Secondary statements omitted from this criterion: ' + selection['reason']],
    )
