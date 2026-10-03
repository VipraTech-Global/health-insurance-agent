"""Map validated original quotations onto physical PDF characters."""

import unicodedata
from typing import Any


def _normalized(text: str) -> str:
    # The source extractor represents some PDF hyphen glyphs as U+2010/U+2011,
    # while pdfplumber exposes the same glyph as ASCII. Preserve the glyph and
    # every other punctuation mark; this mapping is geometry-only.
    return "".join(
        "-" if c in {"\u2010", "\u2011"} else c
        for c in unicodedata.normalize("NFKC", text)
        if not c.isspace() and unicodedata.category(c) != "Cc"
    )


def clause_rectangles(
    chars: tuple[dict[str, Any], ...], quote: str, occurrence: int = 0
) -> list[list[float]]:
    # NFKC/whitespace folding is for PDF geometry only. Raw quotation validation
    # above remains exact, including original line endings, spelling and punctuation.
    mapped = [(letter, char) for char in chars for letter in _normalized(char["text"])]
    text = "".join(letter for letter, _char in mapped)
    target = _normalized(quote)
    start = -1
    for _ in range(occurrence + 1):
        start = text.find(target, start + 1)
        if start < 0:
            raise ValueError("Exact raw clause has no unambiguous PDF character geometry.")
    rectangles: list[list[float]] = []
    for _letter, char in mapped[start : start + len(target)]:
        box = [float(char[k]) for k in ("x0", "top", "x1", "bottom")]
        if (
            rectangles
            and abs(rectangles[-1][1] - box[1]) < 3
            and -2 <= box[0] - rectangles[-1][2] < 20
        ):
            rectangles[-1][0] = min(rectangles[-1][0], box[0])
            rectangles[-1][2] = max(rectangles[-1][2], box[2])
            rectangles[-1][3] = max(rectangles[-1][3], box[3])
        else:
            rectangles.append(box)
    return rectangles
