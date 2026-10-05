"""Compile a reviewed annual chart layout with exact merged-cell provenance.

The adapter is limited to the inspected Comprehensive prospectus hash. Luna
labels each table; code verifies its layout and binds every printed amount to
the physical row, column, merged composition and complete chart heading.
There is no inferred Default-variant or coverage-basis axis: this edition's
printed axes are composition, age, sum insured, zone, term and tax basis.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, replace
from pathlib import Path

import pdfplumber
from pydantic import Field

from .contracts import Citation, Closed
from .evidence import Section, atomic_json
from .pricing import PrintedPrice, TableCell, validate_price
from .validation import fold, locate

SOURCE_SHA = '0404693147bd5202e28e39bfdb8fcc87f78e7ee6aa6a6f1032f63cbec63698e1'
VERSION = 'annual-merged-chart/1'
REQUIRED_AXES = {'age', 'sum_insured', 'composition', 'zone', 'term', 'tax_basis'}
TITLE = re.compile(r'Premium Chart for (?P<term>1 year) \((?P<tax_basis>Excluding Tax)\) \(in Rs\.\) (?P<zone>Zone [A-E])')


class Layout(Closed):
    recognized: bool
    heading_row: int = Field(description='Zero-based row of the merged Premium Chart title, not the column labels.')
    sum_insured_row: int
    composition_column: int
    age_column: int
    first_amount_column: int
    last_amount_column: int


EXPECTED_LAYOUT = Layout(recognized=True, heading_row=0, sum_insured_row=1, composition_column=0,
                         age_column=1, first_amount_column=2, last_amount_column=10)


def label_table(grid, page_number, relay, saved=None):
    instructions = ('Identify the printed chart layout. Return zero-based row and column indexes from the original '
        'physical grid. heading_row means the merged Premium Chart title containing term, tax and zone, '
        'not the column-label row. Do not interpret amounts, calculate prices or infer missing labels. '
        'recognized is true only for an annual, tax-excluded age/composition/sum-insured premium chart with a printed zone.')
    messages = [{'role': 'user', 'content': json.dumps({'physical_page': page_number, 'grid': grid})}]
    if saved is None:
        result = relay.call(instructions=instructions, messages=messages, schema=Layout.model_json_schema(),
                            stage='premium_chart', max_tokens=1024, timeout=1800)
        saved = {'version': VERSION, 'sha256': SOURCE_SHA, 'model': result.model,
                 'call_ids': result.call_ids, 'layout': result.value}
    attempts = saved.get('attempts', [{key: saved[key] for key in ('model', 'call_ids', 'layout')}])
    if Layout.model_validate(saved['layout']) != EXPECTED_LAYOUT and len(attempts) == 1:
        messages.extend([{'role': 'assistant', 'content': json.dumps(saved['layout'])},
            {'role': 'user', 'content': 'The labelled layout failed physical-grid validation. Check the original grid '
             'once, particularly the distinction between the merged chart title and the column labels. '
             'Return the complete corrected layout, or recognized=false if this chart cannot be established.'}])
        result = relay.call(instructions=instructions, messages=messages, schema=Layout.model_json_schema(),
                            stage='premium_chart_correction', max_tokens=1024, timeout=1800)
        attempt = {'model': result.model, 'call_ids': result.call_ids, 'layout': result.value}
        attempts.append(attempt)
        saved = {**saved, **attempt}
    return {**saved, 'attempts': attempts}


def source_quote(bundle, raw, start, end) -> Citation:
    """Resolve a known physical-page offset into an original evidence section."""
    quote = raw['passage'][start:end]
    for payload in bundle['sections']:
        section = Section.from_payload(payload)
        for segment in section.segments:
            if (segment.page_id != raw['evidence_span_id'] or start < segment.start or end > segment.end
                    or segment.text[start-segment.start:end-segment.start] != quote):
                continue
            prefix = fold(segment.text[:start-segment.start])
            occurrence = len(list(re.finditer('(?=' + re.escape(fold(quote)) + ')', prefix)))
            if locate(segment.text, quote, occurrence) == (start-segment.start, end-segment.start):
                return Citation(section_id=section.id, page_id=segment.page_id, quote=quote, occurrence=occurrence)
    raise ValueError('Printed cell does not map to a complete original source section.')


def row_cells(bundle, raw, table_id, row, values, first_column, occurrence=0, printed=1):
    """A complete row must occur exactly as often as the page grids print it.

    A row printed more than once (a repeated header) binds to its occurrence in
    reading order; repeated amounts within the row use its offsets.
    """
    joined = ' '.join(values)
    if fold(raw['passage']).count(fold(joined)) != printed:
        raise ValueError('The complete printed table row is ambiguous in original text.')
    start, end = locate(raw['passage'], joined, occurrence)
    positions = [i for i in range(start, end) if not raw['passage'][i].isspace()]
    cells, offset = [], 0
    for column, text in enumerate(values, first_column):
        length = len(fold(text))
        citation = source_quote(bundle, raw, positions[offset], positions[offset+length-1]+1)
        key = f'{table_id}:{row}:{column}'
        cells.append(TableCell(key, table_id, row, column, text, citation))
        offset += length
    return cells


def compile_table(bundle, raw, table, grid, layout):
    if layout != EXPECTED_LAYOUT or len(grid) != 42 or any(len(row) != 11 for row in grid):
        raise ValueError('Labelled layout differs from the reviewed physical chart layout.')
    title = TITLE.fullmatch(grid[0][0] or '')
    if not title or any(grid[0][1:]) or grid[1][:2] != ['Plan type', 'Age band\n(in years)']:
        raise ValueError('Printed chart heading or axis labels changed.')
    table_id = f"{raw['document_sha256']}:{raw['physical_page']}:annual"
    heading = row_cells(bundle, raw, table_id, 0, [grid[0][0]], 0)[0]
    heading = replace(heading, column_end=10)
    cells = {heading.id: heading}
    axes = {}
    heading_start, _ = locate(raw['passage'], heading.text)
    for name in ('term', 'tax_basis', 'zone'):
        text = title[name]
        start, end = locate(raw['passage'][heading_start:], text)
        key = heading.id + ':' + name
        cells[key] = replace(heading, id=key, text=text,
            citation=source_quote(bundle, raw, heading_start+start, heading_start+end))
        axes[name] = key
    headers = row_cells(bundle, raw, table_id, 1, grid[1], 0)
    cells.update({cell.id: cell for cell in headers})
    prices, failures, composition = [], [], None
    for row_number in range(2, len(grid)):
        row = grid[row_number]
        try:
            if not all(row[1:]) or not re.fullmatch(r'(?:\d+m-\d+|\d+-\d+|\d+|Above \d+)', row[1]):
                raise ValueError('Age row or amount cells are incomplete.')
            if row[0]:
                if not re.fullmatch(r'[12]A(?:\+[1-3]C)?', row[0]):
                    raise ValueError('Composition label is outside the inspected grammar.')
                values = row_cells(bundle, raw, table_id, row_number, row, 0)
                composition = None  # Never carry an earlier group into a failed new group.
                bbox = table.rows[row_number].cells[0]
                covered = [n for n in range(row_number, len(grid))
                    if table.rows[n].cells[1] and bbox[1] <= table.rows[n].cells[1][1] + .01
                    and table.rows[n].cells[1][3] <= bbox[3] + .01]
                if not covered or covered != list(range(row_number, row_number+10)):
                    raise ValueError('Composition merged-cell bounds do not cover its ten age rows.')
                composition = replace(values[0], row_end=max(covered))
                values[0] = composition
            else:
                values = row_cells(bundle, raw, table_id, row_number, row[1:], 1)
            cells.update({cell.id: cell for cell in values})
            if composition is None or row_number > composition.row_end:
                raise ValueError('No physically aligned composition cell.')
            age = next(cell for cell in values if cell.column == 1)
            for value in (cell for cell in values if cell.column >= 2):
                axis_ids = {**axes, 'age': age.id, 'composition': composition.id,
                            'sum_insured': headers[value.column].id}
                price = PrintedPrice(value.id, {name: cells[key].text for name, key in axis_ids.items()},
                                     axis_ids, (heading.id, headers[0].id, headers[1].id))
                if not validate_price(price, cells, REQUIRED_AXES):
                    raise ValueError('Printed amount or aligned axes failed validation.')
                prices.append(price)
        except ValueError as exc:
            failures.append({'page': raw['physical_page'], 'row': row_number, 'reason': str(exc)})
    return prices, cells, failures


def parse_annual_chart(bundle: dict, document: dict, root: Path, relay) -> dict:
    directory = root / 'annual-charts' / bundle['index_id']
    prices, cells, failures, models = [], {}, [], set()
    with pdfplumber.open(document['path']) as pdf:
        pages = [p for p in bundle['pages'] if p['document_sha256'] == SOURCE_SHA
                 and 'Premium Chart for 1 year (Excluding Tax)' in p['passage']]
        for raw in pages:
            tables = pdf.pages[raw['physical_page']-1].find_tables()
            if len(tables) != 1:
                failures.append({'page': raw['physical_page'], 'reason': 'Expected one physical chart region.'})
                continue
            table = tables[0]
            grid = table.extract()
            path = directory / f"{raw['physical_page']}.json"
            if path.exists():
                saved = json.loads(path.read_text())
                if saved['version'] != VERSION or saved['sha256'] != SOURCE_SHA:
                    raise ValueError('Annual chart cache identity changed.')
            else:
                saved = None
            saved = label_table(grid, raw['physical_page'], relay, saved)
            atomic_json(path, saved)
            models.update(attempt['model'] for attempt in saved['attempts'])
            try:
                accepted, page_cells, rejected = compile_table(bundle, raw, table, grid, Layout.model_validate(saved['layout']))
                prices.extend(accepted)
                cells.update(page_cells)
                failures.extend(rejected)
            except ValueError as exc:
                failures.append({'page': raw['physical_page'], 'reason': str(exc)})
    result = {'index_id': bundle['index_id'], 'parser_version': VERSION, 'required_axes': sorted(REQUIRED_AXES),
        'prices': [asdict(p) for p in prices], 'cells': {key: asdict(c) | {'citation': c.citation.model_dump()} for key, c in cells.items()},
        'models': sorted(models), 'failures': failures, 'status': 'parsed' if prices else 'invalid_chart',
        'scope': 'Exact printed choices for this prospectus edition. No automatic profile-to-age/zone mapping or quotation.'}
    atomic_json(root / 'premiums' / (bundle['index_id'] + '.json'), result)
    return result
