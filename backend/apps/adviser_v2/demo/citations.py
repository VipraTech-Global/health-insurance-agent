"""Resolve published card quotations back to immutable original source spans."""

from .contracts import Citation
from .evidence import Section
from .validation import locate


def published_citations(value):
    if isinstance(value, dict):
        if {'section_id', 'page_id', 'quote'} <= value.keys():
            yield Citation.model_validate(value)
        else:
            for child in value.values():
                yield from published_citations(child)
    elif isinstance(value, list):
        for child in value:
            yield from published_citations(child)


def card_anchor(card: dict, bundle: dict, citation: Citation) -> dict:
    if citation not in list(published_citations(card)):
        raise ValueError('The quotation is not in this published plan card.')
    sections = [Section.from_payload(s) for s in bundle['sections'] if s['id'] == citation.section_id]
    if len(sections) != 1 or sections[0].plan_id != card['plan_id']:
        raise ValueError('The quotation is outside this plan edition.')
    section = sections[0]
    segments = [s for s in section.segments if s.page_id == citation.page_id]
    if len(segments) != 1:
        raise ValueError('The quotation is outside the cited physical page.')
    source = segments[0]
    start, end = locate(source.text, citation.quote, citation.occurrence)
    return {'section_id': section.id, 'document_id': section.document_id,
        'document_sha256': section.document_sha256, 'page_id': source.page_id,
        'page': source.page, 'start': source.start + start, 'end': source.start + end,
        'quote': source.text[start:end], 'method': source.method, 'role': section.role}


def price_anchor(chart: dict, bundle: dict, plan_id: str, citation: Citation) -> dict:
    from .charts import load_prices
    from .pricing import validate_price
    prices, cells = load_prices(chart)
    if not prices or any(not validate_price(price, cells, set(chart['required_axes'])) for price in prices):
        raise ValueError('This chart has no fully validated printed prices.')
    published = {key for price in prices for key in
                 [price.value_cell, *price.axis_cells.values(), *price.heading_cells]}
    if citation not in [cells[key].citation for key in published]:
        raise ValueError('The quotation is not in a validated printed price.')
    return card_anchor({'plan_id': plan_id, 'citations': [citation.model_dump()]}, bundle, citation)
