"""Six statement-level checks against original packet text, without an AI reviewer.

Support is intentionally conservative: publish extractive statements and their
attached conditions. Arbitrary semantic entailment cannot be proved by string checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..processing.criterion_evidence import quoted_quantities
from .contracts import Answer, Citation, SupportedText
from .evidence import Packet

VALIDATOR_VERSION = "demo-six-checks/1"
NEUTRAL = re.compile(r"\b(?:best|better|recommend(?:ed|ation)?|cheapest|buy|purchase|choose|rank(?:ed|ing)?)\b", re.I)
RESTRICTIONS = re.compile(r"\b(?:optional|variant|add[- ]on|rider|sum insured|subject to|provided that|only if|except|excluding)\b", re.I)


def fold(text: str) -> str:
    return "".join(char for char in text if not char.isspace())


def locate(text: str, quote: str, occurrence: int = 0) -> tuple[int, int]:
    positions = [i for i, char in enumerate(text) if not char.isspace()]
    original, target = "".join(text[i] for i in positions), fold(quote)
    if not target or occurrence < 0:
        raise ValueError("An exact quote cannot be empty.")
    start = -1
    for _ in range(occurrence + 1):
        start = original.find(target, start + 1)
        if start < 0:
            raise ValueError("Quotation is not exact under whitespace-only normalization.")
    return positions[start], positions[start + len(target) - 1] + 1


@dataclass(frozen=True)
class CheckResult:
    checks: tuple[bool, bool, bool, bool, bool, bool]
    problems: tuple[str, ...]
    anchors: tuple[dict, ...]
    rejected_wrong_plan: int

    @property
    def passed(self) -> bool:
        return all(self.checks)


def validate(answer: Answer, packet: Packet, *, variant: str = "Default", known_variants: tuple[str, ...] = ()) -> CheckResult:
    checks, problems, anchors = [True] * 6, [], []
    wrong = 0

    def fail(index, message):
        checks[index] = False
        if message not in problems:
            problems.append(message)

    if answer.plan_id != packet.plan_id:
        wrong += 1
        fail(0, "Wrong-plan answer identity.")
    sections = {s.id: s for s in packet.sections}

    def citation(c: Citation) -> str | None:
        nonlocal wrong
        section = sections.get(c.section_id)
        if section is None or section.plan_id != packet.plan_id:
            wrong += 1
            fail(0, "Quotation cites a section outside the selected plan edition and packet.")
            return None
        segments = [s for s in section.segments if s.page_id == c.page_id]
        if len(segments) != 1:
            fail(0, "Quotation page is outside its selected section.")
            return None
        source = segments[0]
        try:
            a, b = locate(source.text, c.quote, c.occurrence)
        except ValueError as exc:
            fail(0, str(exc))
            return None
        tail = source.text[b:]
        # Do not allow a model to turn a conditional clause into an unconditional
        # benefit by stopping immediately before its qualification.
        following = tail.lstrip()
        if (following and RESTRICTIONS.match(following)
                or (following and re.match(r"(?:if|when|unless|where|and only|but)\b", following, re.I))):
            fail(2, "A material condition immediately following the quotation was omitted.")
        if following and c.quote.rstrip()[-1] not in ".;:!?" and not tail.startswith(("\n", "\r")):
            fail(2, "The quotation stops inside an original clause; include its remaining conditions.")
        anchors.append({"section_id": section.id, "document_id": section.document_id,
            "document_sha256": section.document_sha256, "page_id": source.page_id,
            "page": source.page, "start": source.start + a, "end": source.start + b,
            "quote": source.text[a:b], "method": source.method, "role": section.role})
        return source.text[a:b]

    def supported(item: SupportedText, check: int) -> list[str]:
        quotes = [text for c in item.citations if (text := citation(c)) is not None]
        if not quotes:
            fail(check, "Every substantive statement and condition requires exact original evidence.")
            return []
        # Reject unsupported reformulations instead of treating lexical overlap as entailment.
        target = fold(item.text)
        if not any(target == fold(q) for q in quotes) and target != fold(" ".join(quotes)):
            fail(check, "Statement must retain its complete quoted wording; paraphrase support cannot be established automatically.")
        quantities = quoted_quantities(item.text)
        support = quoted_quantities(" ".join(quotes))
        if any(not values <= support[unit] for unit, values in quantities.items()):
            fail(1, "A statement has a number, amount, duration or unit absent from its quotations.")
        # Identifiers/ordinals not classified as quantities still need source support.
        if not set(re.findall(r"\d+(?:[.,]\d+)*", item.text)) <= set(re.findall(r"\d+(?:[.,]\d+)*", " ".join(quotes))):
            fail(1, "A numeric identifier is unsupported by this statement's quotations.")
        return quotes

    if answer.status == "not_found":
        if answer.statements:
            fail(3, "An evidence-absent answer cannot include supported statements.")
        return CheckResult(tuple(checks), tuple(problems), (), wrong)
    if not answer.statements:
        fail(3, "An answered result needs a substantive statement.")
    for statement in answer.statements:
        quote_texts = supported(statement, 3)
        for condition in statement.conditions:
            supported(condition, 2)
        for restriction in statement.restrictions:
            supported(restriction, 4)
        attached = " ".join(c.text for c in [*statement.conditions, *statement.restrictions])
        for quote in quote_texts:
            mentioned = {name for name in known_variants if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", quote, re.I)}
            if mentioned and variant not in mentioned:
                fail(4, "Quoted benefit is restricted to a different named variant.")
            if RESTRICTIONS.search(quote) and fold(quote) not in fold(statement.text + " " + attached):
                fail(4, "A quoted variant, optional-cover or sum-insured restriction was omitted.")
        # Quoted wording is kept unchanged, including contextual words like 'better
        # treatment'. There is no generated recommendation prose in this contract.
        if NEUTRAL.search(statement.text) and not any(fold(statement.text) == fold(q) for q in quote_texts):
            fail(5, "Generated ranking or purchase direction is not allowed.")
        if re.search(r"\b(?:you are eligible|your claim (?:is|will)|you will receive)\b", statement.text, re.I):
            fail(3, "Personal eligibility and claim calculations need an executable rule.")
        # Named variants explicitly supplied as restrictions may not be silently
        # asserted as the base variant. Display their original restriction text.
        for restriction in statement.restrictions:
            if restriction.text.startswith("variant=") and restriction.text != f"variant={variant}":
                fail(4, "Wrong variant.")
    return CheckResult(tuple(checks), tuple(problems), tuple(anchors), wrong)
