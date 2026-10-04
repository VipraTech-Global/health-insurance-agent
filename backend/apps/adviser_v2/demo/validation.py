"""Six statement-level checks against original packet text, without an AI reviewer.

Support is intentionally conservative: publish extractive statements and their
attached conditions. Arbitrary semantic entailment cannot be proved by string checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import Answer, Citation, SupportedText
from .evidence import Packet
from .quantities import quoted_quantities
from .quotations import locate, normalized

VALIDATOR_VERSION = "demo-six-checks/3"
NEUTRAL = re.compile(
    r"\b(?:best|better|recommend(?:ed|ation)?|cheapest|buy|purchase|choose|rank(?:ed|ing)?)\b", re.I
)
RESTRICTIONS = re.compile(
    r"\b(?:optional|variant|add[- ]on|rider|sum insured|subject to|provided that|only if|except|excluding)\b",
    re.I,
)


def fold(text: str) -> str:
    return normalized(text)[0]


@dataclass(frozen=True)
class CheckResult:
    checks: tuple[bool, bool, bool, bool, bool, bool]
    problems: tuple[str, ...]
    anchors: tuple[dict, ...]
    rejected_wrong_plan: int

    @property
    def passed(self) -> bool:
        return all(self.checks)


def validate(
    answer: Answer,
    packet: Packet,
    *,
    variant: str = "Default",
    known_variants: tuple[str, ...] = (),
) -> CheckResult:
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
    tables = {t["id"]: t for t in packet.tables}
    table_quotes = set()
    unit_spans = {}

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
        # BEL is an invisible PDF layout marker that matching skips; treat it
        # like whitespace when deciding where the quotation ends.
        following = re.sub(r"^[\s\x07]+", "", tail)
        next_start = b + len(tail) - len(following)
        continuation_present = any(
            lo <= next_start < hi for lo, hi in unit_spans.get((c.section_id, c.page_id), [])
        )
        # Do not allow a model to turn a conditional clause into an unconditional
        # benefit by stopping immediately before its qualification.
        if not continuation_present and (
            following
            and RESTRICTIONS.match(following)
            or (following and re.match(r"(?:if|when|unless|where|and only|but)\b", following, re.I))
        ):
            fail(2, "A material condition immediately following the quotation was omitted.")
        is_table_cell = (c.section_id, c.page_id, fold(c.quote)) in table_quotes
        preceding = source.text[:a].rstrip()
        if (
            not is_table_cell
            and preceding
            and re.search(r"\b(?:not|no|unless|excluding|except|subject to)\s*$", preceding, re.I)
        ):
            fail(2, "A preceding governing qualification or negation was omitted.")
        if (
            following
            and not continuation_present
            and not is_table_cell
            and re.sub(r"[\s\x07]+$", "", c.quote)[-1:] not in tuple(".;:!?")
            and not re.match(r"[ \t\x07]*[\r\n]", tail)
        ):
            fail(
                2,
                "The quotation stops inside an original clause; include its remaining conditions.",
            )
        anchors.append(
            {
                "section_id": section.id,
                "document_id": section.document_id,
                "document_sha256": section.document_sha256,
                "page_id": source.page_id,
                "page": source.page,
                "start": source.start + a,
                "end": source.start + b,
                "quote": source.text[a:b],
                "method": source.method,
                "role": section.role,
            }
        )
        return source.text[a:b]

    def supported(item: SupportedText, check: int) -> list[str]:
        quotes = [text for c in item.citations if (text := citation(c)) is not None]
        if not quotes:
            fail(
                check, "Every substantive statement and condition requires exact original evidence."
            )
            return []
        # Reject unsupported reformulations instead of treating lexical overlap as entailment.
        target = fold(item.text)
        if not any(target == fold(q) for q in quotes) and target != fold(" ".join(quotes)):
            fail(
                check,
                "Statement must retain its complete quoted wording; paraphrase support cannot be established automatically.",
            )
        quantities = quoted_quantities(item.text)
        support = quoted_quantities(" ".join(quotes))
        if any(not values <= support[unit] for unit, values in quantities.items()):
            fail(
                1, "A statement has a number, amount, duration or unit absent from its quotations."
            )
        # Identifiers/ordinals not classified as quantities still need source support.
        if not set(re.findall(r"\d+(?:[.,]\d+)*", item.text)) <= set(
            re.findall(r"\d+(?:[.,]\d+)*", " ".join(quotes))
        ):
            fail(1, "A numeric identifier is unsupported by this statement's quotations.")
        return quotes

    if answer.status == "not_found":
        if answer.statements:
            fail(3, "An evidence-absent answer cannot include supported statements.")
        return CheckResult(tuple(checks), tuple(problems), (), wrong)
    if not answer.statements:
        fail(3, "An answered result needs a substantive statement.")
    for statement in answer.statements:
        if re.match(
            r"^\s*(?:subject to|provided that|only if|unless)\b", statement.text, re.I
        ) and not re.search(r"\b(?:cover|benefit|pay|indemnif|reimburse)", statement.text, re.I):
            fail(3, "A standalone condition does not answer a benefit question.")
        table_quotes.clear()
        unit_spans.clear()
        for item in [statement, *statement.conditions, *statement.restrictions]:
            for c in item.citations:
                section = sections.get(c.section_id)
                for seg in section.segments if section else ():
                    if seg.page_id == c.page_id:
                        try:
                            unit_spans.setdefault((c.section_id, c.page_id), []).append(
                                locate(seg.text, c.quote, c.occurrence)
                            )
                        except ValueError:
                            pass  # The citation check below reports this exact failure.
        if statement.table:
            support = statement.table
            region = tables.get(support.region_id)
            cells = region.get("cells", {}) if region else {}
            value = cells.get(support.value_cell_id)
            ids = [support.value_cell_id, *support.row_label_ids, *support.column_label_ids]
            if value is None or any(key not in cells for key in ids):
                fail(1, "Table support is outside the supplied original table region.")
            else:
                if any(
                    cells[key]["row"] != value["row"] or cells[key]["column"] >= value["column"]
                    for key in support.row_label_ids
                ):
                    fail(1, "A table row label does not align with its value cell.")
                if any(
                    cells[key]["column"] != value["column"] or cells[key]["row"] >= value["row"]
                    for key in support.column_label_ids
                ):
                    fail(1, "A table column label does not align with its value cell.")
                cited = {(c.section_id, c.page_id, fold(c.quote)) for c in statement.citations}
                for key in ids:
                    original = cells[key]["citation"]
                    identity = (
                        original["section_id"],
                        original["page_id"],
                        fold(original["quote"]),
                    )
                    if identity not in cited:
                        fail(
                            3,
                            "Every selected table label and value requires its separate exact citation.",
                        )
                    table_quotes.add(identity)
        elif re.fullmatch(
            r"\s*(?:(?:Rs\.?|₹)\s*)?\d[\d,.]*\s*(?:(?:lakh|crore|days?|months?|years?|%)\s*)?[.;]?\s*",
            statement.text,
            re.I,
        ):
            fail(3, "An isolated value needs its benefit label and printed table axes.")
        if statement.scope_product is not None and statement.coverage_scope == "base":
            from .answer_scope import optional_cover

            if optional_cover(statement.text):
                fail(
                    4,
                    "An unlabelled optional/add-on/rider statement cannot be shown as base cover.",
                )
        quote_texts = supported(statement, 3)
        for condition in statement.conditions:
            supported(condition, 2)
        for restriction in statement.restrictions:
            supported(restriction, 4)
        attached = " ".join(c.text for c in [*statement.conditions, *statement.restrictions])
        for quote in quote_texts:
            names = "|".join(
                re.escape(name) for name in sorted(known_variants, key=len, reverse=True)
            )
            mentioned = (
                {
                    match.casefold()
                    for match in re.findall(r"(?<!\w)(?:" + names + r")(?!\w)", quote, re.I)
                }
                if names
                else set()
            )
            if mentioned and variant.casefold() not in mentioned:
                fail(4, "Quoted benefit is restricted to a different named variant.")
            if RESTRICTIONS.search(quote) and fold(quote) not in fold(
                statement.text + " " + attached
            ):
                fail(4, "A quoted variant, optional-cover or sum-insured restriction was omitted.")
        # Quoted wording is kept unchanged, including contextual words like 'better
        # treatment'. There is no generated recommendation prose in this contract.
        if (
            NEUTRAL.search(statement.text)
            and fold(statement.text) != fold(" ".join(quote_texts))
            and not any(fold(statement.text) == fold(q) for q in quote_texts)
        ):
            fail(5, "Generated ranking or purchase direction is not allowed.")
        if re.search(
            r"\b(?:you are eligible|your claim (?:is|will)|you will receive)\b",
            statement.text,
            re.I,
        ):
            fail(3, "Personal eligibility and claim calculations need an executable rule.")
        # Named variants explicitly supplied as restrictions may not be silently
        # asserted as the base variant. Display their original restriction text.
        for restriction in statement.restrictions:
            if restriction.text.startswith("variant=") and restriction.text != f"variant={variant}":
                fail(4, "Wrong variant.")
    return CheckResult(tuple(checks), tuple(problems), tuple(anchors), wrong)
