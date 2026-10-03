"""Complete a currency bullet list inside its pinned source passage and budget."""

import re

from .contracts import Answer, Citation, Statement
from .evidence import Packet, Section
from .quotations import locate
from .validation import validate


def complete_sum_list(result, bundle, statement):
    if statement.get("table") or not result.get("packet"):
        return statement
    for cite in statement["citations"]:
        section = next((s for s in bundle["sections"] if s["id"] == cite["section_id"]), None)
        if not section:
            continue
        segment = next(s for s in section["segments"] if s["page_id"] == cite["page_id"])
        origin, stop = locate(segment["text"], cite["quote"], cite.get("occurrence", 0))
        head = re.search(
            r"(?im)^[^\n]*sum\s*insured\s*(?:options?|choices?)[^\n]*\n",
            segment["text"][origin:stop],
        )
        if not head:
            continue
        start = origin + head.start()
        cursor = origin + head.end()
        found, terminated = 0, False
        for line in segment["text"][cursor:].splitlines(keepends=True):
            value = re.sub(r"^[\s•▪➢*-]+", "", line).strip()
            if not value:
                cursor += len(line)
                continue
            if re.fullmatch(
                r"(?:(?:Rs\.?|INR|₹)\s*)?[\d,.]+(?:\s*(?:Lakhs?|Lacs?|Crores?|Cr\.?))?(?:\s*[/,;&]\s*(?:(?:Rs\.?|INR|₹)\s*)?[\d,.]+(?:\s*(?:Lakhs?|Lacs?|Crores?|Cr\.?))?)*(?:\s*/-)?\s*",
                value,
                re.I,
            ):
                found += 1
                cursor += len(line)
            else:
                terminated = True
                break
        if found < 2 or not terminated or re.search(r"\d", head[0]):
            continue  # A page end is not proof that the list is complete.
        leading = len(segment["text"][start:cursor]) - len(segment["text"][start:cursor].lstrip())
        start += leading
        selected = segment["text"][start:cursor].strip()
        occurrence = 0
        while locate(segment["text"], selected, occurrence)[0] != start:
            occurrence += 1
        new_cite = Citation(**{**cite, "quote": selected, "occurrence": occurrence})
        candidate = Statement.model_validate(
            {
                **statement,
                "citations": [new_cite.model_dump()],
                "excerpts": [selected],
                "text": selected,
            }
        )
        data = result["packet"]
        packet = Packet(
            bundle["policy_version_id"],
            tuple(Section.from_payload(s) for s in data["sections"]),
            tuple(data.get("omitted_ids", [])),
            data["tokens"],
            tables=tuple(data.get("tables", [])),
        )
        check = validate(
            Answer(plan_id=packet.plan_id, status="answered", statements=[candidate]),
            packet,
            variant=bundle.get("variant", "Default"),
            known_variants=tuple(bundle.get("variants", [])),
        )
        result.setdefault("list_projection_audit", []).append(
            {
                "page_id": cite["page_id"],
                "items": found,
                "checks": list(check.checks),
                "passed": check.passed,
                "problems": check.problems,
                "tokens": packet.tokens,
            }
        )
        if check.passed and packet.tokens <= packet.budget:
            return {**candidate.model_dump(), "complete_options": True}
    return statement
