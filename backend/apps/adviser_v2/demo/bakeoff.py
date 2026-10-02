"""Mechanical protocol-v2 accounting; never use observed outcomes to change inputs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .evidence import atomic_json, digest
from .relay import MODELS

PROTOCOL_VERSION = 2
STAR_CELLS = 39
ANSWER_CASES = 260
EVALUATION_SLOTS = 13
QUESTIONS = (
    ("room_rent", "What room rent limits and room-category conditions apply?", True),
    ("icu", "What ICU charges are covered and what limits apply?", True),
    ("ped", "What waiting period applies to pre-existing diseases?", False),
    ("specified_waiting", "What waiting periods apply to specified diseases or procedures?", False),
    ("maternity", "What maternity cover, limits and conditions apply?", True),
    ("newborn", "What newborn cover, limits and conditions apply?", True),
    ("copay", "What co-pay applies, including age and zone conditions?", False),
    ("deductible", "What deductible applies to the base plan?", False),
    ("restoration", "How is cover restored and what conditions apply?", False),
    ("no_claim_bonus", "How does the no-claim bonus work and what limits apply?", False),
    ("pre_post", "How many pre- and post-hospitalisation days are covered?", False),
    ("day_care", "What day-care treatments are covered and on what conditions?", False),
    ("road_ambulance", "What road ambulance expenses are covered?", False),
    ("air_ambulance", "What air ambulance expenses are covered?", False),
    ("ayush", "What AYUSH treatment is covered and what conditions apply?", False),
    ("organ_donor", "What organ donor expenses are covered and excluded?", False),
    ("home_care", "What domiciliary or home-care treatment is covered?", False),
    ("health_check", "What health check-up benefit is available?", False),
    ("opd", "What outpatient or OPD expenses are covered?", False),
    ("cataract", "What cataract treatment limits and conditions apply?", True),
)


@dataclass(frozen=True)
class Score:
    method: str
    complete_cells: int
    answered: int
    displayed_wrong_plan: int
    rejected_wrong_plan: int
    unavailable: int = 0

    def __post_init__(self):
        if self.method not in {"H", "P"}:
            raise ValueError("Only H and P are admissible methods.")
        if not 0 <= self.complete_cells <= STAR_CELLS or not 0 <= self.answered <= ANSWER_CASES:
            raise ValueError("Fixed scoring denominator exceeded.")
        if min(self.displayed_wrong_plan, self.rejected_wrong_plan, self.unavailable) < 0:
            raise ValueError("Counts cannot be negative.")
        if self.answered + self.unavailable > ANSWER_CASES:
            raise ValueError("Unavailable cases cannot also count as answered.")

    @property
    def score(self) -> float:
        return self.complete_cells + self.answered / ANSWER_CASES * STAR_CELLS

    @property
    def disqualified(self) -> bool:
        return self.displayed_wrong_plan > 0


def winner(hybrid: Score, pageindex: Score) -> dict:
    if (hybrid.method, pageindex.method) != ("H", "P"):
        raise ValueError("Expected H followed by P.")
    if hybrid.disqualified != pageindex.disqualified:
        chosen = pageindex if hybrid.disqualified else hybrid
        reason = "Only one arm has no displayed wrong-plan quotations."
    elif hybrid.disqualified and pageindex.disqualified:
        chosen = hybrid if hybrid.score > pageindex.score else pageindex
        reason = "Both arms disqualified; user-directed higher-score selection (exact tie P)."
    elif abs(hybrid.score - pageindex.score) <= 2:
        chosen, reason = pageindex, "P wins when eligible scores differ by no more than two points."
    else:
        chosen = hybrid if hybrid.score > pageindex.score else pageindex
        reason = "Higher eligible score."
    return {"protocol_version": PROTOCOL_VERSION, "winner": chosen.method, "reason": reason,
            "both_disqualified": hybrid.disqualified and pageindex.disqualified,
            "live_enabled": True, "denominators": {"star_cells": 39, "answer_cases": 260, "slots": 13},
            "arms": [{**asdict(s), "score": s.score, "disqualified": s.disqualified} for s in (hybrid, pageindex)]}


def complete_cell(reference_ids: set[str], fixed: set[str], customer: set[str]) -> bool:
    if not reference_ids:
        raise ValueError("A reference cell cannot be vacuously complete.")
    return reference_ids <= fixed and reference_ids <= customer


def paired_models_match(hybrid: dict, pageindex: dict) -> bool:
    """Both retrieval and answer must stay on one allowed model within a pair."""
    identities = set(hybrid.get("models", [])) | set(pageindex.get("models", []))
    return (bool(hybrid.get("models")) and bool(pageindex.get("models"))
            and len(identities) == 1 and identities <= set(MODELS))


def freeze(root: Path, inputs: dict) -> str:
    """Resume is allowed only with byte-identical inputs, including validators."""
    fingerprint = digest({"protocol_version": PROTOCOL_VERSION, "inputs": inputs})
    path = root / "frozen.json"
    if path.exists():
        saved = json.loads(path.read_text())
        if saved["sha256"] != fingerprint or saved["inputs"] != inputs:
            raise ValueError("Frozen bake-off inputs changed; do not resume or tune this run.")
    else:
        atomic_json(path, {"protocol_version": PROTOCOL_VERSION, "inputs": inputs, "sha256": fingerprint})
    return fingerprint
