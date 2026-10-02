from dataclasses import replace

import pytest

from apps.adviser_v2.demo.annual_charts import row_cells
from apps.adviser_v2.demo.pricing import PrintedPrice, TableCell, validate_price
from apps.adviser_v2.demo.validation import locate
from apps.adviser_v2.tests.test_demo_contracts import citation, packet


def test_merged_chart_labels_must_physically_cover_the_amount():
    cells = {key: TableCell(key, 'table', row, column, text, citation(text))
        for key, row, column, text in [('value', 12, 3, '25,799'), ('family', 12, 0, '2A+1C'),
            ('age', 12, 1, '18-35'), ('sum', 1, 3, '10,00,000'), ('term', 0, 0, '1 year'),
            ('tax', 0, 0, 'Excluding Tax'), ('zone', 0, 0, 'Zone A')]}
    cells['family'] = replace(cells['family'], row_end=21)
    for key in ('term', 'tax', 'zone'):
        cells[key] = replace(cells[key], column_end=10)
    axis_ids = {'composition': 'family', 'age': 'age', 'sum_insured': 'sum',
                'term': 'term', 'tax_basis': 'tax', 'zone': 'zone'}
    price = PrintedPrice('value', {name: cells[key].text for name, key in axis_ids.items()}, axis_ids, ('term',))
    assert validate_price(price, cells, set(axis_ids))
    for key, changed in [('family', replace(cells['family'], row=2, row_end=11)),
                         ('zone', replace(cells['zone'], column_end=2)),
                         ('sum', replace(cells['sum'], column=4)),
                         ('zone', replace(cells['zone'], table_id='different-zone-table'))]:
        assert not validate_price(price, {**cells, key: changed}, set(axis_ids))


def test_complete_row_disambiguates_repeated_amounts_and_keeps_highlight_offsets():
    text = '2A\n18-35 10,000 15,000\n36-45 15,000 20,000'
    source = packet(text).sections[0]
    segment = replace(source.segments[0], start=0, end=len(text), text=text)
    source = replace(source, segments=(segment,))
    bundle = {'sections': [source.payload()]}
    raw = {'passage': text, 'evidence_span_id': 'p'}
    cells = row_cells(bundle, raw, 'table', 3, ['36-45', '15,000', '20,000'], 1)
    amount = cells[1].citation
    assert amount.occurrence == 1
    start, end = locate(text, amount.quote, amount.occurrence)
    assert start == text.rindex('15,000') and text[start:end] == '15,000'
    with pytest.raises(ValueError, match='ambiguous'):
        row_cells(bundle, raw, 'table', 3, ['15,000'], 1)
    with pytest.raises(ValueError, match='ambiguous'):
        row_cells(bundle, raw, 'table', 3, ['36-45', '20,000', '15,000'], 1)


def test_chart_title_correction_is_bounded_and_resumes_without_more_calls():
    from types import SimpleNamespace
    from unittest.mock import Mock

    from apps.adviser_v2.demo.annual_charts import EXPECTED_LAYOUT, label_table

    relay = Mock()
    incorrect = EXPECTED_LAYOUT.model_copy(update={'heading_row': 1}).model_dump()
    relay.call.side_effect = [SimpleNamespace(model='gpt-5.6-luna', call_ids=['first'], value=incorrect),
        SimpleNamespace(model='claude-sonnet-5', call_ids=['correction'], value=EXPECTED_LAYOUT.model_dump())]
    saved = label_table([['Premium Chart for 1 year']], 44, relay)
    assert len(saved['attempts']) == relay.call.call_count == 2
    assert saved['attempts'][0]['layout'] == incorrect
    assert saved['model'] == 'claude-sonnet-5'
    assert label_table([], 44, relay, saved) == saved
    assert relay.call.call_count == 2
    saved['layout'] = incorrect
    assert label_table([], 44, relay, saved)['layout'] == incorrect
    assert relay.call.call_count == 2


def test_price_citation_rejects_unaccepted_cells_and_foreign_plan():
    from dataclasses import asdict

    from apps.adviser_v2.demo.charts import cell_payload
    from apps.adviser_v2.demo.citations import price_anchor
    from apps.adviser_v2.tests.test_demo_contracts import price_data

    cells, price = price_data()
    section = packet('Annual premium / Zone A 5 lakh 56–59 15,000/- Unused 99,999').sections[0]
    chart = {'prices': [asdict(price)], 'cells': {key: cell_payload(cell) for key, cell in cells.items()},
             'required_axes': ['age', 'sum']}
    bundle = {'sections': [section.payload()]}
    assert price_anchor(chart, bundle, 'plan', cells['amount'].citation)['quote'] == '15,000/-'
    with pytest.raises(ValueError, match='validated printed price'):
        price_anchor(chart, bundle, 'plan', citation('99,999'))
    with pytest.raises(ValueError, match='plan edition'):
        price_anchor(chart, bundle, 'other', cells['amount'].citation)
