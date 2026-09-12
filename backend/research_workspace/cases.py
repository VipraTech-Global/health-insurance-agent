"""Turn authored scenario designs into explicitly incomplete case records."""

import json
from pathlib import Path

from research_workspace.benchmark import library_report
from research_workspace.contracts import CaseRecord
from research_workspace.storage import write_json

# Information requirements are a starting map, not assertions about any insurer.
INFORMATION = {
    1: ("insured_people", "priorities", "budget", "price_observation", "eligibility"),
    2: ("relationships", "family_composition", "configuration", "shared_limits"),
    3: ("birth_date", "dependency", "addition_dates", "child_eligibility", "endorsements"),
    4: ("insured_age", "medical_disclosures", "underwriting", "copay", "room_limits"),
    5: ("condition", "diagnosis_date", "treatment_history", "waiting_periods", "individual_terms"),
    6: ("medical_history", "underwriting", "exclusions", "continuity", "benefit_conditions"),
    7: ("treatment_purpose", "definitions", "exclusions", "exceptions", "individual_terms"),
    8: ("pregnancy_dates", "maternity_wait", "delivery_limits", "newborn_cover", "add_on"),
    9: ("procedure", "setting", "definitions", "modern_treatment", "limits"),
    10: ("admission_dates", "related_illness", "duration_trigger", "home_care", "opd_conditions"),
    11: ("itemised_bill", "admissible_cost", "deduction_order", "limit_basis", "endorsement"),
    12: ("claim_history", "remaining_limits", "restoration_trigger", "same_illness", "bonus"),
    13: ("existing_schedules", "master_wording", "employment_dates", "coordination", "continuity"),
    14: (
        "deductible_basis",
        "claim_dates",
        "admissible_expenses",
        "policy_years",
        "waiting_periods",
    ),
    15: ("continuity_history", "proposal_state", "renewal_dates", "coverage_increase", "credit"),
    16: ("renewal_dates", "payment_state", "changes", "supersession", "continuity"),
    17: ("hospital_identity", "network_variant", "observation_date", "exclusion_list", "geography"),
    18: ("quote_owner", "configuration", "quote_validity", "underwriting", "price_components"),
    19: ("diagnosis_dates", "advice_dates", "policy_start", "waiting_periods", "existing_cover"),
    20: ("fact_subject", "message_provenance", "corrections", "revision", "ownership", "consent"),
}


def build_drafts(root: Path) -> None:
    """Never upgrade a draft to worked or freeze evaluation as a side effect of generation."""
    blocks = (root / "seeds/scenarios.txt").read_text().split("# ")[1:]
    if len(blocks) != 20:
        raise ValueError("Expected the 20 authored scenario families")
    cases: list[CaseRecord] = []
    for family, block in enumerate(blocks, 1):
        heading, *scenarios = block.strip().splitlines()
        if not heading.startswith(f"{family} ") or len(scenarios) != 20:
            raise ValueError(f"Invalid authored family {family}")
        for index, scenario in enumerate(scenarios):
            evaluation = index >= 10
            case_id = f"{'eval' if evaluation else 'ref'}-{family:02d}-{index % 10 + 1:02d}"
            turns = [scenario]
            if case_id == "ref-20-01":
                turns.append("can you suggest me")
            case = CaseRecord(
                case_id=case_id,
                split="evaluation" if evaluation else "reference",
                family=family,
                title=scenario,
                decision_distinction=scenario,
                factors=(scenario,),
                boundary="Not yet assessed against original policy rules",
                customer_facts={"uninterpreted_synthetic_statement": scenario},
                conversation=tuple(turns),
                known=("Customer statement preserved verbatim",),
                unknown=(
                    "Applicable product configurations and contractual answer not yet established",
                ),
                corrections=(),
                required_information=INFORMATION[family],
                candidate_configurations=(),
                exclusion_reasons=(),
                expected_answer="Unworked. Do not invent a policy answer or mark this case complete.",
                acceptable_alternatives=(),
                evidence=(),
                evidence_requirements=(
                    "Applicable original wording, UIN/version/date and connected definitions/conditions",
                    "All selected add-on and individual endorsement dependencies",
                    "Applicable dated quote/hospital/underwriting evidence when decisive",
                ),
                calculations=(),
                gaps=(
                    "Original evidence, candidate analysis and independently worked answer required",
                    "Decision distinctness, factor count, boundaries and clarification require assessment",
                ),
                information_map=INFORMATION[family],
                pass_criteria=(
                    "All material customer facts belong to the correct insured person",
                    "No unsupported eligibility exclusion or contractual claim",
                    "Every material claim resolves to the applicable original passage",
                    "All essential evidence is present; honest gaps do not count as completion",
                    "Calculations match the independent reference, including units and scope",
                ),
                assessment="draft",
            )
            cases.append(case)
    if len({c.decision_distinction for c in cases}) != 400:
        raise ValueError("Duplicate scenario text")
    for split in ("reference", "evaluation"):
        path = root / split / "drafts.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        content = "".join(c.model_dump_json() + "\n" for c in cases if c.split == split)
        # Draft creation is idempotent but will not erase subsequent case work.
        if path.exists() and path.read_text() != content:
            raise ValueError(f"Refusing to overwrite edited case records: {path}")
        path.write_text(content)
    report = library_report(cases)
    report["evaluation_frozen"] = False
    report["evaluation_independence"] = (
        "Unestablished; drafts are visible in this authoring context"
    )
    write_json(root / "reports/case-library.json", report)
    print(json.dumps({"drafts": len(cases), "worked": 0, "evaluation_frozen": False}))
