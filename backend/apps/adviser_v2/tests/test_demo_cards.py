import pytest

from apps.adviser_v2.demo.cards import CardSources, FieldSource, entry_rules, projected_field
from apps.adviser_v2.demo.charts import ChartLabels, cell_payload
from apps.adviser_v2.demo.contracts import Citation, Statement
from apps.adviser_v2.demo.pricing import TableCell
from apps.adviser_v2.demo.relay import strict_schema


def source(text, field='entry_age'):
    return FieldSource(field=field, status='answered', statements=[Statement(text=text,
        citations=[Citation(section_id='s', page_id='p', quote=text)])])


def test_card_projection_does_not_treat_renewal_as_entry_or_territory_as_purchase_geography():
    assert entry_rules(source('Renewals are allowed at any age.')) == []
    assert entry_rules(source('Maximum age at renewal is 90 years.')) == []
    field = projected_field(source('Treatment is covered in India.', field='geography'))
    assert 'all_india' not in field.labels and not field.exhaustive
    assert not field.numbers


def test_entry_age_includes_completed_upper_year_without_inventing_spouse_rules():
    rules = entry_rules(source('Any person aged between 18 years and 65 years can take this insurance.'))
    assert len(rules) == 1 and rules[0].relationship == 'self'
    assert rules[0].minimum_days == 18*365 and rules[0].maximum_days == 66*365-1


def test_card_and_chart_schemas_are_closed_and_cells_serialize_exactly():
    import json

    import jsonschema
    for schema in [CardSources.model_json_schema(), ChartLabels.model_json_schema()]:
        jsonschema.Draft202012Validator.check_schema(strict_schema(schema))
    c = Citation(section_id='s', page_id='p', quote='1,005')
    cell = TableCell('c', 't', 1, 1, '1,005', c)
    assert json.loads(json.dumps(cell_payload(cell)))['citation']['quote'] == '1,005'
    with pytest.raises(ValueError):
        ChartLabels.model_validate({'prices': [{'value_cell': 'c', 'axes': {}, 'axis_cells': {}, 'heading_cells': []}]})


def test_sum_insured_projection_requires_explicit_new_business_amount_list():
    from apps.adviser_v2.demo.cards import sum_insured_field
    field = sum_insured_field(source('Sum Insured Options: Rs.5,00,000/-, Rs.10,00,000/- and Rs.25,00,000/-', 'sum_insured'))
    assert field.numbers == [500000, 1000000, 2500000] and field.exhaustive
    for text in ['Maternity is limited to Rs.5,00,000/-',
                 'Sum Insured Options: Rs.1,00,000/- available only for renewals',
                 'Sum Insured Options: Rs.5,00,000/- only for ages under 65']:
        assert not sum_insured_field(source(text, 'sum_insured')).numbers
