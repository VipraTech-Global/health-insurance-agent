"""Exact PDF-artifact matching with offsets back into the unchanged source."""
import re
from functools import lru_cache


class QuoteMismatch(ValueError):
    pass


@lru_cache(maxsize=128)
def normalized(text: str, *, dewrap: bool = False) -> tuple[str, tuple[int, ...]]:
    # PDF extraction can emit BEL as an invisible layout marker; it is not punctuation.
    # Preserve lexical hyphens. A printed line-wrap may insert whitespace after
    # the hyphen (air-\nconditioned); soft hyphens are explicitly discretionary.
    discretionary = {m.start() + 1 for m in re.finditer(r'[A-Za-z]-[ \t]*\n[ \t]*(?=[A-Za-z])', text)} if dewrap else set()
    positions = [i for i, char in enumerate(text) if not char.isspace() and char not in {'\u00ad', '\x07'} and i not in discretionary]
    return ''.join(text[i] for i in positions), tuple(positions)


def locate(text: str, quote: str, occurrence: int = 0) -> tuple[int, int]:
    if not normalized(quote)[0] or occurrence < 0:
        raise QuoteMismatch('An exact quote cannot be empty.')
    for dewrap in (False, True):
        original, positions = normalized(text, dewrap=dewrap)
        target, _ = normalized(quote, dewrap=dewrap)
        start = -1
        for _ in range(occurrence + 1):
            start = original.find(target, start + 1)
            if start < 0:
                break
        if start >= 0:
            return positions[start], positions[start + len(target) - 1] + 1
    raise QuoteMismatch('Quotation does not match original wording and punctuation.')


def clause_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    """Complete both ends; newlines alone are never sentence boundaries.

    A list stays with its introduction until the next blank paragraph. Include
    adjacent qualification sentences rather than allowing a cropped exception.
    Ambiguous section boundaries are handled by the caller, never guessed.
    """
    boundaries, headings = boundaries_for(text)
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


def enumeration_end(text: str, end: int) -> bool:
    """Equivalent to the anchored enumeration regex, without scanning its prefix."""
    if end < 2 or text[end-1] != '.':
        return False
    start = end-2
    while start >= 0 and (text[start].isalnum() or text[start] == '_'):
        start -= 1
    token = text[start+1:end-1]
    return bool(token) and (token.isdecimal() or len(token) == 1 and 'A' <= token <= 'Z')


@lru_cache(maxsize=64)
def boundaries_for(text: str):
    sentence_ends = [m.end() for m in re.finditer(r'(?<=[.!?])\s+(?=[A-Z])|\n[ \t]*\n', text)
                     if not enumeration_end(text, m.start())]
    headings = [m.end() for m in re.finditer(
        r'\n[ \t]*(?=(?:\d+\.[\s\x07]*[A-Z]|\d+\.\d+(?:\.\d+)*[ \t]+[A-Z]|\([ivx]+\)[ \t]*Benefit:))', text)]
    # Printed title-case headings are source boundaries, unlike ordinary wrapped
    # prose. Require at least two title words to avoid one-word wrapped lines.
    headings.extend(m.start() for m in re.finditer(
        r'(?m)^[ \t]*[A-Z][A-Za-z/-]*(?:[ \t]+(?:[A-Z][A-Za-z/-]*|of|and|for|in|the|to|under)){1,9}:?[ \t]*$', text))
    boundaries = sorted(set([0, *sentence_ends, *headings, len(text)]))
    return tuple(boundaries), frozenset(headings)
