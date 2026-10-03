"""Resolve packet-local model selections into indivisible original-source units."""
import json
from dataclasses import replace

from .contracts import Citation, Statement, SupportedText, TableSupport
from .evidence import Packet, Section, pack_sections, reference_covered
from .quotations import clause_bounds, locate, normalized
from .text import token_count

DRAFT_VERSION = 'packet-labels/2'


class EvidenceInsufficient(ValueError):
    pass


class UnknownLabel(EvidenceInsufficient):
    pass


class PacketLabels:
    def __init__(self, packet: Packet):
        self.documents = {}
        self.passages = {f'P{n}': (section, segment) for n, (section, segment) in enumerate(
            ((s, p) for s in packet.sections for p in s.segments), 1)}
        self.tables = {f'T{n}': table for n, table in enumerate(packet.tables, 1)}
        self.cells = {label: {f'C{n}': key for n, key in enumerate(table['cells'], 1)}
                      for label, table in self.tables.items()}

    def payload(self):
        passages = [{'label': label, 'text': segment.text} for label, (_, segment) in self.passages.items()]
        tables = []
        for label, table in self.tables.items():
            cells = []
            for alias, key in self.cells[label].items():
                cell = table['cells'][key]
                cite = cell['citation']
                passage = next((p for p, (s, seg) in self.passages.items()
                                if s.id == cite['section_id'] and seg.page_id == cite['page_id']), None)
                if passage:
                    cells.append({'cell': alias, 'row': cell['row'], 'column': cell['column'],
                                  'passage': passage, 'quote': cite['quote']})
            tables.append({'label': label, 'cells': cells})
        return {'schema_version': 2, 'passages': passages, 'tables': tables}


def document_source(section, all_sections):
    pieces = sorted((p for s in all_sections if s.document_id == section.document_id
                     and s.document_sha256 == section.document_sha256 and s.plan_id == section.plan_id
                     for p in s.segments), key=lambda p: (p.document_start, p.document_end))
    text, cursor = '', 0
    for p in pieces:
        if p.document_start > cursor:
            if p.document_start - cursor != 1:
                raise EvidenceInsufficient('Original document contains an unresolved source gap.')
            text += '\f'
            cursor += 1
        if p.document_end > cursor:
            text += p.text[max(0, cursor - p.document_start):]
            cursor = p.document_end
    return text


def assemble(unit, labels: PacketLabels, packet: Packet, all_sections: list[Section]):
    required = []
    contexts = []

    def resolve(ref, *, complete=True):
        if ref.passage not in labels.passages:
            raise UnknownLabel('Unknown packet passage label: ' + ref.passage)
        section, segment = labels.passages[ref.passage]
        a, b = locate(segment.text, ref.quote, ref.occurrence)
        left, right = segment.document_start + a, segment.document_start + b
        if complete:
            key = (section.plan_id, section.document_id, section.document_sha256)
            if key not in labels.documents:
                labels.documents[key] = document_source(section, all_sections)
            source = labels.documents[key]
            left, right = clause_bounds(source, left, right)
        citations = []
        cursor = left
        for s in sorted(all_sections, key=lambda s: min(p.document_start for p in s.segments)):
            if (s.plan_id, s.document_id, s.document_sha256) != (packet.plan_id, section.document_id, section.document_sha256):
                continue
            for p in s.segments:
                lo, hi = max(cursor, p.document_start), min(right, p.document_end)
                if lo >= hi:
                    continue
                if lo - cursor > 1:
                    raise EvidenceInsufficient('Governing clause has a source gap.')
                quote = p.text[lo - p.document_start:hi - p.document_start]
                if quote.strip():
                    # Repeated wording is located by its original offset, never first-match guessing.
                    occurrence, found = 0, None
                    target_start = lo - p.document_start + normalized(quote)[1][0]
                    while found != target_start:
                        found, _ = locate(p.text, quote, occurrence)
                        if found != target_start:
                            occurrence += 1
                    citations.append(Citation(section_id=s.id, page_id=p.page_id, quote=quote, occurrence=occurrence))
                    contexts.append({'page_span_id': p.page_id, 'start': p.start + lo - p.document_start,
                                     'end': p.start + hi - p.document_start})
                    required.append(s)
                cursor = hi
        if (cursor < right and document_source(section, all_sections)[cursor:right].strip()) or not citations:
            raise EvidenceInsufficient('Complete governing clause cannot be resolved.')
        return citations

    table = None
    if unit.table:
        ref = unit.table
        region = labels.tables.get(ref.table)
        mapping = labels.cells.get(ref.table, {})
        keys = [ref.value, *ref.rows, *ref.columns]
        if region is None or any(key not in mapping for key in keys):
            raise UnknownLabel('Unknown packet table/cell label.')
        table = TableSupport(region_id=region['id'], value_cell_id=mapping[ref.value],
                             row_label_ids=[mapping[k] for k in ref.rows], column_label_ids=[mapping[k] for k in ref.columns])
        main = [Citation.model_validate(region['cells'][mapping[k]]['citation']) for k in [*ref.rows, *ref.columns, ref.value]]
        # Keep complete surrounding source, including table introductions/footnotes,
        # as separate original excerpts. This is conservative, never inferred axes.
        conditions = [c for q in unit.benefit for c in resolve(q)]
    else:
        main = [c for q in unit.benefit for c in resolve(q)]
        conditions = []
    conditions.extend(c for q in unit.conditions for c in resolve(q))
    restrictions = [c for q in unit.restrictions for c in resolve(q)]
    extended = pack_sections(packet.plan_id, [*packet.sections, *required], budget=packet.budget,
                             tables=list(packet.tables))
    if not all(reference_covered(span, extended) for span in contexts):
        raise EvidenceInsufficient('Necessary governing context exceeds the 16000-token packet budget.')
    if table and table.region_id not in {t['id'] for t in extended.tables}:
        raise EvidenceInsufficient('Required table axes exceed the packet budget.')
    extended = replace(extended, omitted_ids=tuple(dict.fromkeys([*packet.omitted_ids, *extended.omitted_ids])))
    actual = token_count(json.dumps(extended.evidence(), ensure_ascii=False))
    if actual > packet.budget:
        raise EvidenceInsufficient('Necessary context and omission metadata exceed the evidence budget.')
    extended = replace(extended, tokens=actual)
    def unique(cites):
        return list({(c.section_id, c.page_id, c.quote, c.occurrence): c for c in cites}.values())
    main = unique(main)
    statement = Statement(text='\n\n'.join(c.quote for c in main), citations=main,
                          excerpts=[c.quote for c in main], heading='Table excerpts' if table else 'Policy excerpt',
                          conditions=[SupportedText(text=c.quote, citations=[c]) for c in unique(conditions)],
                          restrictions=[SupportedText(text=c.quote, citations=[c]) for c in unique(restrictions)], table=table)
    return statement, extended
