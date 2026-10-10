"""Grid extents and printed fields of extracted table cells.

The table reader stores a merged cell once, at its first row and column, with the
inclusive ``row_end``/``column_end`` it covers; every other cell covers one slot.
"""

import re

# A cell may print several fields, each under its own label at the start of a line:
# "Road Ambulance: INR 2000 per Hospitalization\nAir Ambulance: NA".
FIELD = re.compile(r"^[ \t]*([A-Za-z][^:\n]{0,40}):", re.M)


def extent(cell, axis):
    """The first and last slot a cell covers along "row" or "column"."""
    end = cell.get(f"{axis}_end")
    return cell[axis], cell[axis] if end is None else end


def slots(cell, axis):
    first, last = extent(cell, axis)
    return range(first, last + 1)


def covers(cell, axis, wanted):
    """Whether a cell covers any of these rows (or columns)."""
    return not set(wanted).isdisjoint(slots(cell, axis))


def shares(a, b, axis):
    """Whether two cells cover a common slot along this axis."""
    a_first, a_last = extent(a, axis)
    b_first, b_last = extent(b, axis)
    return a_first <= b_last and b_first <= a_last


def aligned(label, value, axis):
    """Whether a label heads this value: a row label ("row") shares one of its rows
    and ends left of it; a column label ("column") shares one of its columns and
    ends above it. A value printed across several columns is each one's value."""
    across = "column" if axis == "row" else "row"
    return shares(label, value, axis) and extent(label, across)[1] < value[across]


def spans(cell):
    """The span fields a merged cell sets; none for a single-slot cell."""
    return {k: cell[k] for k in ("row_end", "column_end") if cell.get(k) is not None}


def fields(text):
    """The entries a cell prints under its own field labels, by label; none when no
    line starts with a label."""
    marks = list(FIELD.finditer(text))
    ends = [m.start() for m in marks[1:]] + [len(text)] * bool(marks)
    return {
        " ".join(m.group(1).split()): " ".join(text[m.end() : end].split())
        for m, end in zip(marks, ends, strict=True)
    }
