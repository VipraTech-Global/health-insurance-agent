"""Exact PDF-artifact matching with offsets back into the unchanged source."""
import re


class QuoteMismatch(ValueError):
    pass


def normalized(text: str) -> tuple[str, list[int]]:
    # Preserve lexical hyphens. A printed line-wrap may insert whitespace after
    # the hyphen (air-\nconditioned); soft hyphens are explicitly discretionary.
    positions = [i for i, char in enumerate(text) if not char.isspace() and char != '\u00ad']
    return ''.join(text[i] for i in positions), positions


def locate(text: str, quote: str, occurrence: int = 0) -> tuple[int, int]:
    original, positions = normalized(text)
    target, _ = normalized(quote)
    if not target or occurrence < 0:
        raise QuoteMismatch('An exact quote cannot be empty.')
    start = -1
    for _ in range(occurrence + 1):
        start = original.find(target, start + 1)
        if start < 0:
            raise QuoteMismatch('Quotation does not match original wording and punctuation.')
    return positions[start], positions[start + len(target) - 1] + 1


def clause_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    """Complete both ends; newlines alone are never sentence boundaries.

    A list stays with its introduction until the next blank paragraph. Include
    adjacent qualification sentences rather than allowing a cropped exception.
    Ambiguous section boundaries are handled by the caller, never guessed.
    """
    sentence_ends = [m.end() for m in re.finditer(r'(?<=[.!?])\s+(?=[A-Z])|\n[ \t]*\n', text)
                     if not re.search(r'(?:\b[A-Z]|\b\d+)\.$', text[:m.start()])]
    headings = [m.end() for m in re.finditer(r'\n(?=\d+\.[\t\x07 ]+[A-Z])', text)]
    boundaries = sorted(set([0, *sentence_ends, *headings, len(text)]))
    left = max(b for b in boundaries if b <= start)
    right = min(b for b in boundaries if b >= end)
    # An exception/qualification immediately preceding the selected sentence is
    # part of the same validation unit, including negative governing language.
    qualifiers = r'(?:subject to|provided|however|except|excluding|only|unless|note|notwithstanding|no |not |this .*?not )'
    before = max((b for b in boundaries if b < left), default=0)
    if re.match(r'\s*' + qualifiers, text[before:left], re.I):
        left = before
    # Lists have no independent meaning without their introduction. Retain the
    # entire enclosing source block rather than selecting one favourable item.
    prefix = text[left:start]
    if re.search(r'(?:^|\n)\s*(?:\(?[a-zivx0-9]+[.)]|[•*-])\s', prefix, re.I):
        introduction = text.rfind(':', max(0, left - 4000), start)
        if introduction >= 0:
            left = max(b for b in boundaries if b <= introduction)
    while right < len(text):
        if right in headings:
            break
        after = min(b for b in boundaries if b > right)
        following = text[right:after]
        if not (re.match(r'\s*(?:' + qualifiers + r'|\(?[a-zivx0-9]+[.)]\s|[•*])', following, re.I)
                or re.search(r'\b(?:subject to|provided|with regard|will|shall|must|required|only|except|excluded|not|condition|limit)\b', following, re.I)):
            break
        right = after
    return left, right
