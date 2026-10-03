"""Recover bounded hard-field clauses from original H packet passages only.

This is card projection, not a new search method. A retrieved source heading
may complete into the same pinned document; all additions count against the
packet budget. No PageIndex summary is used, and all six checks still apply.
"""

import json
import re
from dataclasses import replace

from .card_assembly import EvidenceInsufficient, PacketLabels, assemble, document_source
from .contracts import Answer, Citation, DraftQuote, DraftUnit, Statement
from .evidence import Packet, Section, pack_sections
from .quotations import locate
from .text import token_count
from .validation import validate

PATTERNS = {
    "opd": r"(?mi)^\s*(?:[a-z]|\d+)[.)]\s*(?:Treatment taken on outpatient basis|Out[ -]Patient treatment)[^\n]*",
    "plan_type": r"(?:Both\s+indemnity\s+and\s+Benefit|(?:Company|We)\s+(?:will|shall)\s+indemnify[^.]{0,160})",
    "geography": r"(?mi)^\s*(?:\d+(?:\.\d+)*\.?\s+)?(?:Premium Tier|Zonal pricing)\s*$",
}


def recover(result, field, bundle):
    data = result.get("packet")
    if field not in PATTERNS or not data:
        return []
    sections = [Section.from_payload(s) for s in bundle["sections"]]
    packet = Packet(
        bundle["policy_version_id"],
        tuple(Section.from_payload(s) for s in data["sections"]),
        tuple(data.get("omitted_ids", [])),
        data["tokens"],
        tables=tuple(data.get("tables", [])),
    )
    labels = PacketLabels(packet)
    recovered, seen = [], set()
    for label, (section, segment) in labels.passages.items():
        for match in re.finditer(PATTERNS[field], segment.text, re.I):
            identity = (section.document_sha256, segment.document_start + match.start())
            if identity in seen:
                continue
            seen.add(identity)
            try:
                if field in {"geography", "opd"}:
                    source = document_source(section, sections)
                    start = segment.document_start + match.start()
                    # This numbered clause ends at its next sibling, not the
                    # page break between the introduction and premium tiers.
                    if field == "geography":
                        number = re.match(r"\s*(\d+(?:\.\d+)*)\.?\s", match[0])
                        if not number:
                            continue
                        prefix = number[1].rsplit(".", 1)[0] + "."
                        end_match = re.search(
                            r"(?m)^\s*" + re.escape(prefix) + r"\d+\.?\s+[A-Z]",
                            source[start + len(match[0]) :],
                        )
                        if not end_match:
                            continue
                        end = start + len(match[0]) + end_match.start()
                        spans = [(start, end)]
                    else:
                        # A list item's base exclusion comes from its enclosing
                        # printed introduction, never an inferred absence.
                        headings = list(
                            re.finditer(
                                r"(?mi)^(?:\d+\.\s*)?(?:Specific Exclusions:|WHAT WE WILL NOT PAY[^\n]*)",
                                source[max(0, start - 15000) : start],
                            )
                        )
                        if not headings:
                            continue
                        head = max(0, start - 15000) + headings[-1].start()
                        following = source[head:start]
                        if re.search(
                            r"(?mi)^\s*(?:SECTION|Optional Covers|General Conditions)\b", following
                        ):
                            continue
                        intro_end = re.search(r"(?mi)^\s*(?:a\.|i\.|i\))\s", following)
                        if not intro_end:
                            continue
                        end = start + len(match[0])
                        spans = [(head, head + intro_end.start()), (start, end)]
                    cites, required = [], []
                    for left, right in spans:
                        cursor = left
                        for s in sorted(
                            sections, key=lambda s: min(p.document_start for p in s.segments)
                        ):
                            if (s.document_id, s.document_sha256) != (
                                section.document_id,
                                section.document_sha256,
                            ):
                                continue
                            for p in s.segments:
                                lo, hi = max(cursor, p.document_start), min(right, p.document_end)
                                if lo >= hi:
                                    continue
                                if lo - cursor > 1:
                                    raise EvidenceInsufficient("Unresolved continuation gap")
                                quote = p.text[lo - p.document_start : hi - p.document_start]
                                occurrence = 0
                                while locate(p.text, quote, occurrence)[
                                    0
                                ] != lo - p.document_start + len(quote) - len(quote.lstrip()):
                                    occurrence += 1
                                cites.append(
                                    Citation(
                                        section_id=s.id,
                                        page_id=p.page_id,
                                        quote=quote,
                                        occurrence=occurrence,
                                    )
                                )
                                required.append(s)
                                cursor = hi
                        if cursor < right:
                            raise EvidenceInsufficient("Unresolved continuation tail")
                    statement = Statement(
                        text="\n\n".join(c.quote for c in cites),
                        citations=cites,
                        excerpts=[c.quote for c in cites],
                    )
                    extended = pack_sections(
                        packet.plan_id, [*required, *packet.sections], budget=16000
                    )
                else:
                    occurrence = len(
                        list(re.finditer(re.escape(match[0]), segment.text[: match.start()]))
                    )
                    unit = DraftUnit(
                        benefit=[DraftQuote(passage=label, quote=match[0], occurrence=occurrence)]
                    )
                    statement, extended = assemble(unit, labels, packet, sections)
            except (EvidenceInsufficient, ValueError) as exc:
                result.setdefault("card_recovery_omissions", []).append(str(exc))
                continue
            extended = replace(
                extended,
                omitted_ids=tuple(dict.fromkeys([*packet.omitted_ids, *extended.omitted_ids])),
            )
            cost = token_count(json.dumps(extended.evidence(), ensure_ascii=False))
            if cost > extended.budget:
                result.setdefault("card_recovery_omissions", []).append(
                    "Continuation and omission metadata exceed the evidence budget."
                )
                continue
            extended = replace(extended, tokens=cost)
            answer = Answer(plan_id=packet.plan_id, status="answered", statements=[statement])
            checks = validate(
                answer,
                extended,
                variant=bundle.get("variant", "Default"),
                known_variants=tuple(bundle.get("variants", [])),
            )
            if not checks.passed:
                result.setdefault("card_recovery_omissions", []).append(list(checks.problems))
                continue
            recovered.append(
                {
                    "status": "answered",
                    "index_version": result.get("index_version"),
                    "answer": answer.model_dump(),
                    "packet": extended.evidence(),
                    "projection_method": "literal_card_clause_recovery",
                    "checks": list(checks.checks),
                    "seed": {
                        "section_id": section.id,
                        "page_id": segment.page_id,
                        "quote": match[0],
                    },
                }
            )
    return recovered
