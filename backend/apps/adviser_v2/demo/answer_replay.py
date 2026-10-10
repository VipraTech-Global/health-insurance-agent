"""Stored bank answers re-read by the current engine code, without model calls.

A fix to checking, scope, quote boundaries or grouping changes what the same drafted
units give. Replaying the drafts each stored answer kept finds the plan × topic pairs
whose visible answer would change, so only those are asked again. A change to the
packet, prompt, retrieval or draft format can't be replayed: it needs a version bump.
"""

from pydantic import ValidationError

from ..models import DemoTopicAnswer
from .answer_bank import TOPIC_QUESTIONS, current, group, index_bundle
from .answer_scope import ScopedLabels, scope_for
from .answer_units import governing_units
from .answers import DRAFT_VERSION, check_unit, known_variants
from .assembly import EvidenceInsufficient
from .contracts import Answer, ScopedAnswerDraft
from .evaluation import packet_from
from .evidence import Section
from .quotations import QuoteMismatch
from .services import decrypted
from .validation import VALIDATOR_VERSION, validate


class Replay:
    """One plan index's engine gates, set up once for all its stored answers."""

    def __init__(self, index):
        bundle = index_bundle(index)
        self.scope = scope_for(bundle)
        self.sources = [Section.from_payload(s) for s in bundle["sections"]]
        variant = bundle.get("variant", "Default")
        variants = known_variants(bundle, self.scope)
        self.checked = lambda answer, evidence: validate(
            answer, evidence, variant=variant, known_variants=variants
        )

    def result(self, topic, stored):
        """The stored answer as the current code reads its drafts: every drafted unit
        that now passes, against the packet the answer kept. None without a packet."""
        if not stored.get("packet"):
            return None
        packet = packet_from(stored["packet"])
        labels = ScopedLabels(packet, self.scope)
        accepted = []
        for attempt in stored.get("attempts", []):
            try:
                units = governing_units(ScopedAnswerDraft.model_validate(attempt["draft"]).units)
            except (KeyError, ValidationError):
                continue
            for unit in units:
                try:
                    statement, _, verification = check_unit(
                        unit,
                        labels,
                        packet,
                        self.sources,
                        self.scope,
                        TOPIC_QUESTIONS[topic],
                        self.checked,
                    )
                except (EvidenceInsufficient, QuoteMismatch):
                    continue
                if verification.passed and statement not in accepted:
                    accepted.append(statement)
        answer = Answer(plan_id=packet.plan_id, status="answered", statements=accepted[:8])
        return {
            **stored,
            "status": "answered" if accepted else "not_found",
            "answer": answer.model_dump() if accepted else None,
        }


def changed_pairs(indexes, topics, method):
    """(index, topic, stored group, replayed group) for every current stored answer of
    these plan indexes whose drafts now give a different visible answer."""
    changed = []
    for index in indexes:
        replay = None
        rows = DemoTopicAnswer.objects.filter(
            index=index,
            topic__in=[t for t in topics if t in TOPIC_QUESTIONS],
            method=method,
            validator=VALIDATOR_VERSION,
            draft=DRAFT_VERSION,
        ).order_by("topic")
        for row in rows:
            stored = decrypted(row.result_ciphertext, row.id)
            if not current(stored):
                continue
            replay = replay or Replay(index)
            again = replay.result(row.topic, stored)
            if again is None:
                continue
            before = group(stored, row.topic, index.variant)
            after = group(again, row.topic, index.variant)
            if before != after:
                changed.append((index, row.topic, before, after))
    return changed
