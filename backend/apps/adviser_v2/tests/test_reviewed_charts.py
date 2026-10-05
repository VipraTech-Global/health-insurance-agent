from dataclasses import replace
from types import SimpleNamespace

from apps.adviser_v2.demo.reviewed_charts import STAR_ASSURE, compile_table
from apps.adviser_v2.demo.validation import locate
from apps.adviser_v2.tests.test_demo_contracts import packet

TITLE = "Premium Chart for 1 Year (in Rs.) (Excluding GST) | Zone D | A-Adult, C-Child"
ADAPTER = replace(STAR_ASSURE, width=4, bands={"*": ("18-35", "36-45")})
GRID = [
    [TITLE, None, None, None],
    ["Plan Type", "Age Band / SI", "5,00,000", "10,00,000"],
    ["Individual", "18-35", "6,054", "8,309"],
    [None, "36-45", "7,210", "9,902"],
    ["2A", "18-35", "10,010", "13,420"],
    [None, "36-45", "11,520", "15,330"],
]


def source(grid=GRID):
    text = "\n".join(" ".join(c for c in row if c) for row in grid)
    section = packet(text).sections[0]
    segment = replace(section.segments[0], start=0, end=len(text), text=text)
    bundle = {"sections": [replace(section, segments=(segment,)).payload()]}
    return bundle, {"passage": text, "evidence_span_id": "p", "physical_page": 44}


def table(spans):
    """A physical table whose first column merges rows first..end per span."""
    rows = []
    for n in range(len(GRID)):
        first = next((a for a, b in spans if a <= n < b), None)
        cell0 = (0, 10 * n, 5, 10 * next(b for a, b in spans if a == n)) if first == n else None
        rows.append(SimpleNamespace(cells=[cell0, (5, 10 * n, 9, 10 * n + 10), None, None]))
    return SimpleNamespace(rows=rows)


def test_reviewed_chart_binds_every_amount_to_its_printed_axes():
    bundle, raw = source()
    prices, cells, failures = compile_table(
        bundle, raw, table([(2, 4), (4, 6)]), GRID, "t", ADAPTER
    )
    assert failures == [] and len(prices) == 8
    price = next(p for p in prices if cells[p.value_cell].text == "8,309")
    assert price.axes == {
        "term": "1 Year",
        "tax_basis": "Excluding GST",
        "zone": "Zone D",
        "age": "18-35",
        "composition": "Individual",
        "sum_insured": "10,00,000",
    }
    late = next(p for p in prices if cells[p.value_cell].text == "15,330")
    assert late.axes["composition"] == "2A" and late.axes["age"] == "36-45"
    quote = cells[price.value_cell].citation
    start, end = locate(raw["passage"], quote.quote, quote.occurrence)
    assert raw["passage"][start:end] == "8,309"


def test_reviewed_chart_reports_rather_than_guesses_a_differing_group():
    bundle, raw = source()
    # The plan-type cell merges only its first age row: the second is unbound.
    prices, _, failures = compile_table(bundle, raw, table([(2, 3), (4, 6)]), GRID, "t", ADAPTER)
    assert {p.axes["composition"] for p in prices} == {"2A"}
    assert failures[0]["reason"].startswith("Plan-type merged-cell bounds")
    # Age bands printed out of the reviewed order.
    swapped = [*GRID[:2], ["Individual", *GRID[3][1:]], [None, *GRID[2][1:]], *GRID[4:]]
    bundle, raw = source(swapped)
    prices, _, failures = compile_table(bundle, raw, table([(2, 4), (4, 6)]), swapped, "t", ADAPTER)
    assert len(prices) == 4 and "Age bands differ" in failures[0]["reason"]


def test_a_new_card_version_pins_the_current_chart_by_content(tmp_path, settings):
    import hashlib

    import pytest

    from apps.adviser_v2.demo.fact_cards_v3 import freeze_prices

    settings.COVERGUIDE_REPORT_ROOT = str(tmp_path)
    run = tmp_path / "run"
    run.mkdir()
    assert freeze_prices("index", run) == {}
    chart = tmp_path / "ten-insurer/premiums/index.json"
    chart.parent.mkdir(parents=True)
    chart.write_text('{"status": "parsed"}')
    pinned = freeze_prices("index", run)
    assert pinned["pricing_sha256"] == hashlib.sha256(chart.read_bytes()).hexdigest()
    # Re-parsing the live chart never alters an already pinned copy.
    chart.write_text('{"status": "invalid_chart"}')
    assert (run / "prices" / (pinned["pricing_sha256"] + ".json")).read_text() == (
        '{"status": "parsed"}'
    )
    assert freeze_prices("index", run)["pricing_sha256"] != pinned["pricing_sha256"]
    (run / "prices" / (pinned["pricing_sha256"] + ".json")).write_text("tampered")
    chart.write_text('{"status": "parsed"}')
    with pytest.raises(ValueError, match="collision"):
        freeze_prices("index", run)
