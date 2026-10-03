"""One bounded second H query, separate from content correction and JSON repair."""

import json
from dataclasses import replace

from .answer_scope import question_topic
from .evidence import pack_sections
from .text import token_count

EXPANSION_VERSION = "second-h-packet/1"
EXPANSION_TERMS = {
    "ped": "pre-existing diseases waiting period Excl01",
    "specified_waiting": "specific disease procedure waiting period Excl02",
    "deductible": "deductible aggregate deductible compulsory voluntary deductible",
    "room": "room rent boarding percentage sum insured per day room category",
    "restoration": "restoration restore recharge reload reinstatement",
    "bonus": "no claim cumulative bonus bonus limit",
    "sum_insured": "base sum insured selectable options eligibility",
    "opd": "outpatient OPD treatment benefit availability exclusions optional cover",
}


def expanded_question(question, bundle):
    terms = " ".join(EXPANSION_TERMS.get(t, t.replace("_", " ")) for t in question_topic(question))
    return (
        question[:1500]
        + "\nFind the governing base cover, explicit exclusion or separately optional cover for "
        + bundle.get("name", "this policy")
        + " / "
        + bundle.get("variant", "Default")
        + ". Include the customer information sheet, coverage/benefit schedule, selected variant table axes, "
        + "and complete policy wording conditions. Search these alternative printed terms too: "
        + terms
    )[:3000]


def expanded_packet(first, second):
    # Preserve the second H result order, then retain earlier independent source
    # sections. No additional lexical/vector scoring or insurer ranking is used.
    tables = {t["id"]: t for p in (second, first) for t in p.tables}
    packet = pack_sections(
        second.plan_id,
        [*second.sections, *first.sections],
        budget=14000,
        tables=list(tables.values()),
    )
    included = {s.id for s in packet.sections} | {"table:" + t["id"] for t in packet.tables}
    omitted = tuple(
        dict.fromkeys(
            x for p in (first, second, packet) for x in p.omitted_ids if x not in included
        )
    )
    packet = replace(packet, budget=16000, omitted_ids=omitted)
    actual = token_count(json.dumps(packet.evidence(), ensure_ascii=False))
    if actual > 16000:
        # Omission metadata is evidence-budget material too. Preserve the audit
        # and fail closed if the bounded union cannot represent it.
        from .assembly import EvidenceInsufficient

        raise EvidenceInsufficient("Expanded packet and omission audit exceed 16000 tokens.")
    return replace(packet, tokens=actual)
