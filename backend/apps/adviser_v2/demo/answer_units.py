"""Attach model-selected governing conditions before validating a benefit unit."""

import re

from .answer_scope import question_topic

CONDITIONAL = re.compile(
    r"^\s*(?:if\b|provided\b|subject to\b|however\b|unless\b|in case\b|this benefit is subject)",
    re.I,
)


def conditional_unit(unit):
    return bool(unit.benefit and all(CONDITIONAL.match(r.quote) for r in unit.benefit))


def governing_units(units):
    """A condition-only selection cannot pass independently of its benefit.

    Attach it conservatively to every selected benefit of the same named field
    and scope. This moves original references, never composes new factual text.
    Unmatched conditions remain for explicit rejection by the scope gate.
    """
    output = [u.model_copy(deep=True) for u in units if not conditional_unit(u)]
    for condition in (u for u in units if conditional_unit(u)):
        topics = set(question_topic(" ".join(r.quote for r in condition.benefit)))
        targets = [
            u
            for u in output
            if not conditional_unit(u)
            and u.coverage_scope == condition.coverage_scope
            and topics & set(question_topic(" ".join(r.quote for r in u.benefit)))
        ]
        if not targets:
            output.append(condition)
            continue
        for target in targets:
            target.conditions.extend([*condition.benefit, *condition.conditions])
            target.restrictions.extend(condition.restrictions)
    return output
