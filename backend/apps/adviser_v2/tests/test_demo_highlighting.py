import pytest

from apps.adviser_v2.demo.highlighting import clause_rectangles
from apps.adviser_v2.demo.quotations import QuoteMismatch, locate


def characters(text):
    return tuple(
        {"text": c, "x0": i * 5, "x1": (i + 1) * 5, "top": 10, "bottom": 20}
        for i, c in enumerate(text)
    )


def test_pdf_hyphen_glyph_mapping_does_not_change_quote_acceptance():
    assert clause_rectangles(characters("in-patient"), "in‐patient") == [[0, 10, 50, 20]]
    with pytest.raises(QuoteMismatch):
        locate("in-patient", "in‐patient")
    with pytest.raises(ValueError):
        clause_rectangles(characters("20-10"), "20−10")
    with pytest.raises(ValueError):
        clause_rectangles(characters("not covered"), "covered.")


def test_repeated_geometry_keeps_the_selected_occurrence():
    assert clause_rectangles(characters("covered covered"), "covered", 1) == [[40, 10, 75, 20]]
    with pytest.raises(ValueError):
        clause_rectangles(characters("covered covered"), "covered", 2)
