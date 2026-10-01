# Star three-plan rule review — Checkpoint 2

Selected variant: **Base policy without optional covers**. Prices and budget remain unavailable.
This file reports validated source rules, their conditions and exact quotations. It does not rank or choose a policy.
An unresolved criterion means the current extraction, review or rule validation is incomplete; it does not establish that the policy excludes the benefit.
Captured manifest SHA-256: `11175393d28fd81b12fb73f6fdeedfb334ce34d1176e6b4b99e2d66d73c939d7`.
Physical PDF pages are used throughout. Character offsets refer to preserved `pdftotext -raw` text and are end-exclusive.

## Validation summary

| Plan | Supported source criteria | Unresolved source criteria | Price |
|---|---:|---:|---|
| Star Comprehensive Insurance Policy | 3/13 | 10/13 | Unavailable |
| Family Health Optima Insurance Plan | Pending | Pending | Unavailable |
| Star Health Assure Insurance Policy | Pending | Pending | Unavailable |

Derived `no_copay` and price are outside the 13-criterion denominator.
Processing stopped at the seven-unresolved-criteria guard. Other pending plans retain their completed calls but have not reached final validation.

## Star Comprehensive Insurance Policy

UIN: `SHAHLIP26044V092526`.

Validation job: `bd953f59-9135-4a59-a63a-10c695acdb47` (blocked). **3/13 supported; 10/13 unresolved.**
Prospectus used for: eligibility, family_floater.
Prospectus gaps reported but not supplemented: sum_insured, newborn. See the criterion's unknown reasons below.
Timeout calls across retained and resumed processing: 1.

**STOP: the plan's seven-unresolved-criteria threshold has been reached. This is not approval to publish or continue processing.**

### sum_insured

Status: **unknown**.

Unknown reason: sum_insured_choices.coverage.sum_insured_available_new_purchase_amounts

Unknown reason: sum_insured_choices: sum_insured: needs_prospectus: no supplied native document states that the nine Sum Insured amounts in the cited modern-treatment table are the complete amounts available for a new purchase. The cited table uses Sum Insured as an axis for modern-treatment sublimits, not as an available-sum-insured selection schedule; the candidate also invents an identity lookup that grants the selected Sum Insured.

Unknown reason: sum_insured_choices.eligibility.sum_insured_revision_outside_renewal_unavailable: applies_when.arguments[0].members[0] has an incompatible dimension

Unknown reason: sum_insured_choices.eligibility.sum_insured_revision_outside_renewal_unavailable: applies_when.arguments[0].members[1] has an incompatible dimension

Unknown reason: sum_insured_choices.eligibility.sum_insured_revision_outside_renewal_unavailable: applies_when.arguments[1]: comparison requires compatible dimensions

Unknown reason: sum_insured_choices.eligibility.sum_insured_reduction_permitted_at_renewal: applies_when.arguments[0]: comparison requires compatible dimensions

Unknown reason: sum_insured_choices.eligibility.sum_insured_reduction_permitted_at_renewal: applies_when.arguments[1]: comparison requires compatible dimensions

Unknown reason: sum_insured_choices.eligibility.sum_insured_enhancement_subject_to_company_discretion: applies_when.arguments[0]: comparison requires compatible dimensions

Unknown reason: sum_insured_choices.eligibility.sum_insured_enhancement_subject_to_company_discretion: applies_when.arguments[1]: comparison requires compatible dimensions

Unknown reason: Independent review found additional source-supported rules missing from extraction: sum_insured_choices.definition.sum_insured_basic_amount_opted_and_premium_paid

### room_category

Status: **unknown**.

Unknown reason: room_and_icu_limits.limit.room_category_private_single_ac_room: effects[0].amount must produce a numeric value

Unknown reason: room_and_icu_limits.deduction.room_category_proportionate_associated_expenses

Unknown reason: room_and_icu_limits: room_category: The policy requires proportionate consideration when hospitalization expenses vary by occupied room rent and the policy room-rent limit/category is lower than actuals, but it does not state an insurer-determined deduction amount or a calculation formula. The candidate invents an insurer-determined amount input and omits Medical Practitioner professional fees from the complete associated-medical-expense category.

Unknown reason: room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[0] has an incompatible dimension

Unknown reason: room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[1] has an incompatible dimension

Unknown reason: room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[2] has an incompatible dimension

Unknown reason: room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[3] has an incompatible dimension

Unknown reason: room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[4] has an incompatible dimension

Unknown reason: room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[5] has an incompatible dimension

Unknown reason: Independent review found additional source-supported rules missing from extraction: room_and_icu_limits.deduction.room_category_proportionate_deduction_for_room_dependent_expenses

Rule: `room_and_icu_limits.definition.room_category_private_single_ac_room_meaning` (`b50ad942-180d-49a8-8dbc-23ce0e59fa9d`).

Condition: Applies within the stated scope.

Value — `permitted_room_category`: A single occupancy air-conditioned room with attached wash room and a couch for the attendant; the room may have a television and/or telephone; it must be the most economical of all single-occupancy accommodations available in that hospital and does not include a Deluxe room or suite..

Scope: {"benefit_keys": ["in_patient_treatment", "room_boarding_nursing_expenses"], "period": "per_event", "reset": "new_event", "subject": "admission", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "new_event",
        "period": "per_event",
        "subject": "admission",
        "subject_ids": [],
        "benefit_keys": [
          "in_patient_treatment",
          "room_boarding_nursing_expenses"
        ]
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "text",
          "value": "A single occupancy air-conditioned room with attached wash room and a couch for the attendant; the room may have a television and/or telephone; it must be the most economical of all single-occupancy accommodations available in that hospital and does not include a Deluxe room or suite."
        }
      },
      "term_key": "private_single_ac_room",
      "target_key": "permitted_room_category"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "b9a87d61-3798-4bf1-a45b-cf2fc80e038e"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 8](#citation-b9a87d61-3798-4bf1-a45b-cf2fc80e038e); characters [0, 3084).

Rule: `room_and_icu_limits.limit.room_category_icu_charges_within_sum_insured` (`982476ea-772e-42ec-8420-e82948b5d383`).

Condition: Applies within the stated scope.

Value — `icu_charges`: sum insured (input).

Scope: {"benefit_keys": ["in_patient_treatment", "icu_charges"], "period": "policy_year", "reset": "anniversary", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "sum_insured",
      "unit": "money",
      "required": true,
      "value_kind": "quantity",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "limit",
      "scope": {
        "reset": "anniversary",
        "period": "policy_year",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": [
          "in_patient_treatment",
          "icu_charges"
        ]
      },
      "amount": {
        "key": "sum_insured",
        "node": "input"
      },
      "target_key": "icu_charges",
      "percentage_base_key": null,
      "inclusive_categories": [
        "icu_bed",
        "general_medical_support_services_for_icu_patient",
        "monitoring_devices",
        "critical_care_nursing",
        "intensivist_charges"
      ]
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "20ff97c6-7758-4a9d-a36b-847bb468e9af",
    "7654a150-0751-4523-a24f-2b6ad2179743"
  ],
  "mandatory_rule_keys": []
}
```

Citation (restricts): [star-comprehensive-base-wording, physical page 5](#citation-7654a150-0751-4523-a24f-2b6ad2179743); characters [0, 3260).

Citation (restricts): [star-comprehensive-base-wording, physical page 9](#citation-20ff97c6-7758-4a9d-a36b-847bb468e9af); characters [0, 3330).

### copay

Status: **unknown**.

Unknown reason: copay.deduction.copay_entry_age_61_claim_rate: applies_when.arguments[1].members[0] has an incompatible dimension

Unknown reason: copay.deduction.copay_entry_age_61_claim_rate: applies_when.arguments[1].members[1] has an incompatible dimension

Unknown reason: copay.exception.copay_pre_61_continuous_renewal_non_application

Unknown reason: The cited wording supports that co-payment does not apply to a person who entered before age 61 and renewed continuously without a break. However, this exception targets copay.deduction.copay_entry_age_61_claim_rate, whose trigger requires entry age 61 or above. The exception trigger requires entry age below 61, so the two rules can never co-occur and the proposed exception cannot operationally replace the targeted deduction.

Rule: `copay.definition.copay_cost_sharing_percentage` (`78e69c98-31db-4bb8-87c8-73b4f138cf0a`).

Condition: Applies within the stated scope.

Value — `copay_definition`: A cost-sharing requirement under which the policyholder or insured bears a specified percentage of the admissible claim amount; a co-payment does not reduce the Sum Insured..

Scope: {"benefit_keys": [], "period": "policy_term", "reset": "never", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "never",
        "period": "policy_term",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": []
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "text",
          "value": "A cost-sharing requirement under which the policyholder or insured bears a specified percentage of the admissible claim amount; a co-payment does not reduce the Sum Insured."
        }
      },
      "term_key": "co_payment",
      "target_key": "copay_definition"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "6fa98415-3c81-4a4a-a3c3-9c2944e07c2a"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 3](#citation-6fa98415-3c81-4a4a-a3c3-9c2944e07c2a); characters [0, 3173).

### deductible

Status: **supported**.

Rule: `deductible.definition.deductible_nil_base_policy` (`cdeae311-3ff7-48fb-9972-b2c839701e46`).

Condition: Applies within the stated scope.

Value — `base_deductible`: Not applicable: The Customer Information Sheet explicitly states that the deductible is NIL..

Scope: {"benefit_keys": [], "period": "unknown", "reset": "unknown", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "unknown",
        "period": "unknown",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": []
      },
      "value": {
        "node": "literal",
        "value": {
          "state": "not_applicable",
          "reason": "The Customer Information Sheet explicitly states that the deductible is NIL.",
          "basis_span_ids": [
            "e12bc2fb-0918-44e3-9170-f74085362c0d"
          ]
        }
      },
      "term_key": "base_deductible",
      "target_key": "base_deductible"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "e12bc2fb-0918-44e3-9170-f74085362c0d"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-customer-information-sheet, physical page 13](#citation-e12bc2fb-0918-44e3-9170-f74085362c0d); characters [0, 724).

### ped_waiting_period

Status: **unknown**.

Unknown reason: waiting_periods: ped_waiting_period: waiting_periods.eligibility.ped_waiting_period_post_expiry_requires_declaration_and_acceptance: Rule still has unresolved conditions: Final coverage outcome remains dependent on all other applicable policy terms, conditions, exclusions and limits.

Unknown reason: waiting_periods.waiting_period.ped_waiting_period_base_36_month_continuous_coverage_exclusion

Unknown reason: The 36-month exclusion requires continuous coverage, but the candidate does not declare continuous coverage as a required input or explicit applicability condition. Its combination value of "separate" also fails to reflect the wording that, where a specified disease/procedure is also subject to the PED waiting period, the longer waiting period applies.

Unknown reason: waiting_periods.waiting_period.ped_waiting_period_sum_insured_increase_fresh_36_months

Unknown reason: The fresh 36-month condition for an enhanced Basic Sum Insured applies to the PED exclusion, but the candidate applies to every expense within the increased Basic Sum Insured without requiring that the expense relate to a PED or its direct complications. It also omits the required continuous-coverage-without-break condition for the enhanced amount.

Unknown reason: waiting_periods.definition.ped_waiting_period_monthly_instalment_15_day_grace_preserves_credit: applies_when.arguments[0]: comparison requires compatible dimensions

Unknown reason: waiting_periods.definition.ped_waiting_period_non_monthly_instalment_30_day_grace_preserves_credit: applies_when.arguments[0].members[0] has an incompatible dimension

Unknown reason: waiting_periods.definition.ped_waiting_period_non_monthly_instalment_30_day_grace_preserves_credit: applies_when.arguments[0].members[1] has an incompatible dimension

Unknown reason: waiting_periods.definition.ped_waiting_period_non_monthly_instalment_30_day_grace_preserves_credit: applies_when.arguments[0].members[2] has an incompatible dimension

Unknown reason: Independent review found additional source-supported rules missing from extraction: waiting_periods.waiting_period.ped_waiting_period_base_continuous_36_month_exclusion, waiting_periods.waiting_period.ped_waiting_period_increased_sum_insured_continuous_36_month_exclusion, waiting_periods.eligibility.ped_waiting_period_post_expiry_requires_declaration_and_acceptance

Rule: `waiting_periods.definition.ped_waiting_period_portability_credit_within_transferred_sum_insured` (`0e8108a2-77ab-4c95-8b85-dcae81ed4090`).

Condition: (portability under applicable irdai norms (input) = True) AND (continuous coverage without break for portability (input) = True) AND (expense is within sum insured extent transferred by portability (input) = True) AND (prior ped waiting period coverage duration must be provided) AND (sum insured extent transferred by portability must be provided).

Value — `ped_waiting_period_credit_within_ported_sum_insured_extent`: prior ped waiting period coverage duration (input).

Scope: {"benefit_keys": ["pre_existing_disease_waiting_period", "sum_insured_extent_transferred_by_portability"], "period": "unknown", "reset": "never", "subject": "person", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "portability_under_applicable_irdai_norms",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "continuous_coverage_without_break_for_portability",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "expense_is_within_sum_insured_extent_transferred_by_portability",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "prior_ped_waiting_period_coverage_duration",
      "unit": "calendar_month",
      "required": true,
      "value_kind": "duration",
      "provenance_required": true
    },
    {
      "key": "sum_insured_extent_transferred_by_portability",
      "unit": "money",
      "required": true,
      "value_kind": "quantity",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "never",
        "period": "unknown",
        "subject": "person",
        "subject_ids": [],
        "benefit_keys": [
          "pre_existing_disease_waiting_period",
          "sum_insured_extent_transferred_by_portability"
        ]
      },
      "value": {
        "key": "prior_ped_waiting_period_coverage_duration",
        "node": "input"
      },
      "term_key": "applicable_ped_waiting_period_credit_duration",
      "target_key": "ped_waiting_period_credit_within_ported_sum_insured_extent"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "all",
    "arguments": [
      {
        "left": {
          "key": "portability_under_applicable_irdai_norms",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": true
          }
        },
        "operator": "eq"
      },
      {
        "left": {
          "key": "continuous_coverage_without_break_for_portability",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": true
          }
        },
        "operator": "eq"
      },
      {
        "left": {
          "key": "expense_is_within_sum_insured_extent_transferred_by_portability",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": true
          }
        },
        "operator": "eq"
      },
      {
        "node": "present",
        "input_key": "prior_ped_waiting_period_coverage_duration"
      },
      {
        "node": "present",
        "input_key": "sum_insured_extent_transferred_by_portability"
      }
    ]
  },
  "schema_version": 1,
  "source_span_ids": [
    "07f429f2-ac0c-4265-a1a0-23950acfe0df",
    "1fe34c5d-d0aa-48ea-81c2-9f59e3903527",
    "bb3b7a47-7ab6-4625-8095-cada2e8c3dc0",
    "6d8cc600-33aa-45a8-9af0-82466a4f5939"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-customer-information-sheet, physical page 17](#citation-6d8cc600-33aa-45a8-9af0-82466a4f5939); characters [0, 2545).

Citation (defines): [star-comprehensive-customer-information-sheet, physical page 10](#citation-bb3b7a47-7ab6-4625-8095-cada2e8c3dc0); characters [0, 2475).

Citation (defines): [star-comprehensive-base-wording, physical page 31](#citation-07f429f2-ac0c-4265-a1a0-23950acfe0df); characters [0, 2822).

Citation (defines): [star-comprehensive-base-wording, physical page 41](#citation-1fe34c5d-d0aa-48ea-81c2-9f59e3903527); characters [0, 3038).

Rule: `waiting_periods.definition.ped_waiting_period_migration_credit_within_transferred_sum_insured` (`9a5a2125-9f9a-493e-bf24-393540e4a58a`).

Condition: (migration to another policy with same insurer (input) = True) AND (expense is within sum insured extent transferred by migration (input) = True) AND (prior policy ped waiting period credit duration must be provided) AND (sum insured extent transferred by migration must be provided).

Value — `ped_waiting_period_credit_within_migrated_sum_insured_extent`: prior policy ped waiting period credit duration (input).

Scope: {"benefit_keys": ["pre_existing_disease_waiting_period", "sum_insured_extent_transferred_by_migration"], "period": "unknown", "reset": "never", "subject": "person", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "migration_to_another_policy_with_same_insurer",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "expense_is_within_sum_insured_extent_transferred_by_migration",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "prior_policy_ped_waiting_period_credit_duration",
      "unit": "calendar_month",
      "required": true,
      "value_kind": "duration",
      "provenance_required": true
    },
    {
      "key": "sum_insured_extent_transferred_by_migration",
      "unit": "money",
      "required": true,
      "value_kind": "quantity",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "never",
        "period": "unknown",
        "subject": "person",
        "subject_ids": [],
        "benefit_keys": [
          "pre_existing_disease_waiting_period",
          "sum_insured_extent_transferred_by_migration"
        ]
      },
      "value": {
        "key": "prior_policy_ped_waiting_period_credit_duration",
        "node": "input"
      },
      "term_key": "applicable_ped_waiting_period_credit_duration",
      "target_key": "ped_waiting_period_credit_within_migrated_sum_insured_extent"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "all",
    "arguments": [
      {
        "left": {
          "key": "migration_to_another_policy_with_same_insurer",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": true
          }
        },
        "operator": "eq"
      },
      {
        "left": {
          "key": "expense_is_within_sum_insured_extent_transferred_by_migration",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": true
          }
        },
        "operator": "eq"
      },
      {
        "node": "present",
        "input_key": "prior_policy_ped_waiting_period_credit_duration"
      },
      {
        "node": "present",
        "input_key": "sum_insured_extent_transferred_by_migration"
      }
    ]
  },
  "schema_version": 1,
  "source_span_ids": [
    "904832d2-8071-44dd-bea5-198b553b1bcc",
    "1fe34c5d-d0aa-48ea-81c2-9f59e3903527",
    "6d8cc600-33aa-45a8-9af0-82466a4f5939"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-customer-information-sheet, physical page 17](#citation-6d8cc600-33aa-45a8-9af0-82466a4f5939); characters [0, 2545).

Citation (defines): [star-comprehensive-base-wording, physical page 41](#citation-1fe34c5d-d0aa-48ea-81c2-9f59e3903527); characters [0, 3038).

Citation (defines): [star-comprehensive-base-wording, physical page 40](#citation-904832d2-8071-44dd-bea5-198b553b1bcc); characters [0, 3080).

Rule: `waiting_periods.definition.ped_waiting_period_renewal_within_30_day_grace_preserves_credit` (`ed0b3728-5f73-49ac-9f38-ae07c81babd9`).

Condition: policy renewed within 30 day grace period (input) = True.

Value — `ped_waiting_period_credit_preservation_on_renewal`: True.

Scope: {"benefit_keys": ["pre_existing_disease_waiting_period_credit"], "period": "policy_term", "reset": "never", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "policy_renewed_within_30_day_grace_period",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "never",
        "period": "policy_term",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": [
          "pre_existing_disease_waiting_period_credit"
        ]
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "boolean",
          "value": true
        }
      },
      "term_key": "ped_waiting_period_credit_preserved",
      "target_key": "ped_waiting_period_credit_preservation_on_renewal"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "left": {
      "key": "policy_renewed_within_30_day_grace_period",
      "node": "input"
    },
    "node": "compare",
    "right": {
      "node": "literal",
      "value": {
        "kind": "boolean",
        "value": true
      }
    },
    "operator": "eq"
  },
  "schema_version": 1,
  "source_span_ids": [
    "1fe34c5d-d0aa-48ea-81c2-9f59e3903527",
    "6d8cc600-33aa-45a8-9af0-82466a4f5939"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 41](#citation-1fe34c5d-d0aa-48ea-81c2-9f59e3903527); characters [0, 3038).

Citation (defines): [star-comprehensive-customer-information-sheet, physical page 17](#citation-6d8cc600-33aa-45a8-9af0-82466a4f5939); characters [0, 2545).

### initial_specific_waiting_periods

Status: **unknown**.

Unknown reason: waiting_periods.waiting_period.initial_specific_waiting_periods_initial_illness_30_day_wait: applies_when.arguments[0]: comparison requires compatible dimensions

Unknown reason: waiting_periods.waiting_period.initial_specific_waiting_periods_initial_illness_30_day_wait: applies_when.arguments[1]: comparison requires compatible dimensions

Unknown reason: waiting_periods.waiting_period.initial_specific_waiting_periods_initial_enhancement_at_renewal_30_day_wait: applies_when.arguments[0]: comparison requires compatible dimensions

Unknown reason: waiting_periods.waiting_period.initial_specific_waiting_periods_initial_enhancement_at_renewal_30_day_wait: applies_when.arguments[1]: comparison requires compatible dimensions

Unknown reason: waiting_periods.exception.initial_specific_waiting_periods_initial_accident_claim_exception: a required dependency was not independently verified.

Unknown reason: waiting_periods.exception.initial_specific_waiting_periods_initial_over_12_month_continuity_exception

Unknown reason: The continuous-coverage-over-twelve-months exception is stated for the Code Excl 03 initial waiting-period exclusion generally. That exclusion is expressly also applied afresh to the enhanced Basic Sum Insured; limiting the exception to only the original-or-continuing sum-insured rule omits the enhanced-sum-insured scope.

Unknown reason: waiting_periods.waiting_period.initial_specific_waiting_periods_listed_condition_continuous_24_month_wait

Unknown reason: The candidate cites an unselected optional-cover passage (07f429f2-ac0c-4265-a1a0-23950acfe0df) and therefore does not safely attribute its rule solely to the selected base variant. In addition, the source makes the 24-month waiting period applicable to every listed condition, including when contracted after inception or declared and accepted without a specific exclusion; the candidate's listed-condition-status restriction is not source-defined as an exhaustive applicability criterion.

Unknown reason: waiting_periods.waiting_period.initial_specific_waiting_periods_listed_condition_enhancement_at_renewal_24_month_wait

Unknown reason: The candidate cites an unselected optional-cover passage (07f429f2-ac0c-4265-a1a0-23950acfe0df), rather than relying only on the selected base-policy wording. It also omits the base-policy portability credit condition for the specified-disease/procedure waiting period.

Unknown reason: waiting_periods.exception.initial_specific_waiting_periods_specific_accident_claim_exception: a required dependency was not independently verified.

Unknown reason: waiting_periods.exception.initial_specific_waiting_periods_specific_ped_overlap_uses_longer_wait: a required dependency was not independently verified.

Unknown reason: waiting_periods.exception.initial_specific_waiting_periods_newborn_congenital_internal_cover_exception: applies_when.arguments[0]: comparison requires compatible dimensions

Unknown reason: waiting_periods.exception.initial_specific_waiting_periods_newborn_congenital_internal_cover_exception: applies_when.arguments[1]: comparison requires compatible dimensions

Unknown reason: Independent review found additional source-supported rules missing from extraction: waiting_periods.exception.initial_specific_waiting_periods_30_day_continuity_exception, waiting_periods.waiting_period.initial_specific_waiting_periods_listed_condition_base_24_month_wait, waiting_periods.waiting_period.initial_specific_waiting_periods_listed_condition_enhancement_24_month_wait

### maternity

Status: **unknown**.

Unknown reason: maternity_and_newborn: maternity: maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: Rule still has unresolved conditions: A selected Basic Sum Insured not represented by an original table row produces an unknown lookup result.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 0 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 0 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 1 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 1 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 2 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 2 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 3 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 3 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 4 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 4 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 5 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 5 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 6 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 6 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 7 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 7 axis delivery_type has the wrong code namespace.

Unknown reason: maternity_and_newborn: maternity: maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: Rule still has unresolved conditions: A selected Basic Sum Insured not represented by an original table row produces an unknown lookup result.; maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: table cell 0 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: table cell 1 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: table cell 2 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: table cell 3 axis basic_sum_insured_band has the wrong code namespace.

Unknown reason: maternity_and_newborn: maternity: maternity_and_newborn.coverage.maternity_newborn_vaccination_limit_by_sum_insured: Rule still has unresolved conditions: A selected Basic Sum Insured not represented by an original table row or range produces an unknown lookup result.; maternity_and_newborn.coverage.maternity_newborn_vaccination_limit_by_sum_insured: table cell 0 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_newborn_vaccination_limit_by_sum_insured: table cell 1 axis basic_sum_insured_band has the wrong code namespace.

Unknown reason: maternity_and_newborn: maternity: maternity_and_newborn.waiting_period.maternity_initial_24_month_wait: Rule still has unresolved conditions: The source does not expressly state whether the 24-month completion boundary is inclusive or exclusive.

Unknown reason: maternity_and_newborn: maternity: maternity_and_newborn.waiting_period.maternity_fresh_24_month_wait_after_delivery_claim: Rule still has unresolved conditions: The source states that the waiting period applies afresh following a claim but does not specify whether the anchor is the delivery date, claim submission date, admission date, or claim payment date.; The source does not expressly state whether the 24-month completion boundary is inclusive or exclusive.

Unknown reason: maternity_and_newborn.eligibility.maternity_self_and_spouse_continuity_conditions_met

Unknown reason: Independent verdict: disagree.

Unknown reason: maternity_and_newborn.exclusion.maternity_miscarriage_not_due_to_accident

Unknown reason: maternity_and_newborn.exclusion.maternity_lawful_medical_termination_of_pregnancy

Unknown reason: maternity_and_newborn.exclusion.maternity_pre_post_hospitalization_and_hospital_cash_not_applicable: applies_when.arguments[1].members[0] has an incompatible dimension

Unknown reason: maternity_and_newborn.exclusion.maternity_pre_post_hospitalization_and_hospital_cash_not_applicable: applies_when.arguments[1].members[1] has an incompatible dimension

Unknown reason: maternity_and_newborn.exclusion.maternity_pre_post_hospitalization_and_hospital_cash_not_applicable: applies_when.arguments[1].members[2] has an incompatible dimension

Unknown reason: Independent review found additional source-supported rules missing from extraction: maternity_and_newborn.waiting_period.maternity_initial_delivery_and_newborn_waiting_period, maternity_and_newborn.waiting_period.maternity_waiting_period_restarts_after_delivery_claim, maternity_and_newborn.limit.maternity_delivery_limits_by_sum_insured_and_delivery_type, maternity_and_newborn.limit.maternity_newborn_treatment_limit_by_sum_insured, maternity_and_newborn.limit.maternity_newborn_vaccination_limit_by_sum_insured

Rule: `maternity_and_newborn.definition.maternity_new_born_baby_age_and_birth_status` (`95458ce7-188e-4c1d-8178-5336fb6dbdc8`).

Condition: Applies within the stated scope.

Value — `new_born_baby_definition`: Baby born during the Policy Period and aged up to 90 days.

Scope: {"benefit_keys": ["delivery_and_new_born"], "period": "unknown", "reset": "unknown", "subject": "person", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "unknown",
        "period": "unknown",
        "subject": "person",
        "subject_ids": [],
        "benefit_keys": [
          "delivery_and_new_born"
        ]
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "text",
          "value": "Baby born during the Policy Period and aged up to 90 days"
        }
      },
      "term_key": "new_born_baby",
      "target_key": "new_born_baby_definition"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "f1e37045-2e50-44d4-8f97-79af60cc483a"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 6](#citation-f1e37045-2e50-44d4-8f97-79af60cc483a); characters [0, 3205).

Rule: `maternity_and_newborn.limit.maternity_maximum_two_lifetime_deliveries` (`e7666e2c-ee93-48b0-97b4-8f8cc025e726`).

Condition: Applies within the stated scope.

Value — `covered_delivery_event_count`: 2 count.

Scope: {"benefit_keys": ["delivery_and_new_born"], "period": "lifetime", "reset": "never", "subject": "person", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [],
  "effects": [
    {
      "kind": "limit",
      "scope": {
        "reset": "never",
        "period": "lifetime",
        "subject": "person",
        "subject_ids": [],
        "benefit_keys": [
          "delivery_and_new_born"
        ]
      },
      "amount": {
        "node": "literal",
        "value": {
          "unit": "count",
          "state": "finite",
          "value": "2"
        }
      },
      "target_key": "covered_delivery_event_count",
      "percentage_base_key": null,
      "inclusive_categories": [
        "normal_delivery",
        "caesarean_section"
      ]
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "832fe413-0802-4639-9e14-f26eb385afeb"
  ],
  "mandatory_rule_keys": []
}
```

Citation (restricts): [star-comprehensive-base-wording, physical page 13](#citation-832fe413-0802-4639-9e14-f26eb385afeb); characters [0, 3074).

Rule: `maternity_and_newborn.eligibility.maternity_self_or_spouse_conditions_not_met` (`7182430e-457e-4abc-8782-fcf4550d0bfb`).

Condition: (both self and spouse covered under policy (input) = False) OR (both self and spouse continuously covered for 24 months (input) = False) OR (policy covering self and spouse in force when benefit payable (input) = False).

Value — `section_ii_14_maternity_cover_availability`: "ineligible".

Scope: {"benefit_keys": ["delivery_and_new_born", "delivery_and_new_born_vaccination"], "period": "unknown", "reset": "unknown", "subject": "family", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "both_self_and_spouse_covered_under_policy",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "both_self_and_spouse_continuously_covered_for_24_months",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "policy_covering_self_and_spouse_in_force_when_benefit_payable",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "eligibility",
      "scope": {
        "reset": "unknown",
        "period": "unknown",
        "subject": "family",
        "subject_ids": [],
        "benefit_keys": [
          "delivery_and_new_born",
          "delivery_and_new_born_vaccination"
        ]
      },
      "reason": "Section II.14 is available only when both Self and Spouse are covered under the policy, both have been continuously covered for 24 months, and the policy covering Self and Spouse is in force when the benefit becomes payable.",
      "decision": "ineligible",
      "target_key": "section_ii_14_maternity_cover_availability"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "any",
    "arguments": [
      {
        "left": {
          "key": "both_self_and_spouse_covered_under_policy",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": false
          }
        },
        "operator": "eq"
      },
      {
        "left": {
          "key": "both_self_and_spouse_continuously_covered_for_24_months",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": false
          }
        },
        "operator": "eq"
      },
      {
        "left": {
          "key": "policy_covering_self_and_spouse_in_force_when_benefit_payable",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": false
          }
        },
        "operator": "eq"
      }
    ]
  },
  "schema_version": 1,
  "source_span_ids": [
    "6845e8f4-0e08-47d8-af93-ee594a0cc94d"
  ],
  "mandatory_rule_keys": []
}
```

Citation (restricts): [star-comprehensive-base-wording, physical page 14](#citation-6845e8f4-0e08-47d8-af93-ee594a0cc94d); characters [0, 2659).

Rule: `maternity_and_newborn.exclusion.maternity_childbirth_outside_ectopic_or_section_ii_14_cover` (`2cd54bf0-bc2b-457a-9794-7aea3ca3c333`).

Condition: (expense traceable to childbirth (input) = True) AND (ectopic pregnancy (input) = False) AND (expense covered under section ii 14 (input) = False).

Value — `childbirth_expenses_exclusion`: "Medical treatment expenses traceable to childbirth, including complicated deliveries and caesarean sections incurred during hospitalization, are excluded except ectopic pregnancy and to the extent covered under Section II.14.".

Scope: {"benefit_keys": ["maternity"], "period": "per_event", "reset": "new_event", "subject": "claim", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "expense_traceable_to_childbirth",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "ectopic_pregnancy",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "expense_covered_under_section_ii_14",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "exclusion",
      "scope": {
        "reset": "new_event",
        "period": "per_event",
        "subject": "claim",
        "subject_ids": [],
        "benefit_keys": [
          "maternity"
        ]
      },
      "reason": "Medical treatment expenses traceable to childbirth, including complicated deliveries and caesarean sections incurred during hospitalization, are excluded except ectopic pregnancy and to the extent covered under Section II.14.",
      "target_key": "childbirth_expenses_exclusion",
      "expense_predicate": {
        "node": "constant",
        "value": "true"
      }
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "all",
    "arguments": [
      {
        "left": {
          "key": "expense_traceable_to_childbirth",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": true
          }
        },
        "operator": "eq"
      },
      {
        "left": {
          "key": "ectopic_pregnancy",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": false
          }
        },
        "operator": "eq"
      },
      {
        "left": {
          "key": "expense_covered_under_section_ii_14",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "kind": "boolean",
            "value": false
          }
        },
        "operator": "eq"
      }
    ]
  },
  "schema_version": 1,
  "source_span_ids": [
    "94711633-5762-412f-8b4e-f74c1c3f9fe5",
    "af639b61-6d94-4429-b111-f85ca27b3fcc"
  ],
  "mandatory_rule_keys": []
}
```

Citation (restricts): [star-comprehensive-base-wording, physical page 34](#citation-94711633-5762-412f-8b4e-f74c1c3f9fe5); characters [0, 2921).

Citation (restricts): [star-comprehensive-customer-information-sheet, physical page 5](#citation-af639b61-6d94-4429-b111-f85ca27b3fcc); characters [0, 2395).

### newborn

Status: **unknown**.

Unknown reason: maternity_and_newborn: newborn: Section II.14.C expressly grants newborn vaccination expenses subject to its stated conditions and limits, while Code Excl 31 generally excludes inoculation or vaccination except post-bite treatment and medical treatment for therapeutic reasons; the complete official bundle does not state explicit precedence resolving this decision-critical overlap.

Unknown reason: maternity_and_newborn: newborn: needs_prospectus: the Delivery and New Born table in the core wording and CIS states newborn-cover limits for INR 5,00,000, INR 7,50,000, INR 10,00,000 to INR 25,00,000, and INR 50,00,000 to INR 1,00,00,000, but provides no newborn-cover limit or stated unavailability for Sum Insured values above INR 25,00,000 and below INR 50,00,000.

Unknown reason: maternity_and_newborn: newborn: maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: table cell 0 axis sum_insured_band has the wrong code namespace.; maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: table cell 1 axis sum_insured_band has the wrong code namespace.; maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: table cell 2 axis sum_insured_band has the wrong code namespace.; maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: table cell 3 axis sum_insured_band has the wrong code namespace.

Unknown reason: maternity_and_newborn: newborn: maternity_and_newborn.limit.newborn_vaccination_limit_by_sum_insured_band: maternity_and_newborn.limit.newborn_vaccination_limit_by_sum_insured_band: table cell 0 axis sum_insured_band has the wrong code namespace.; maternity_and_newborn.limit.newborn_vaccination_limit_by_sum_insured_band: table cell 1 axis sum_insured_band has the wrong code namespace.

Unknown reason: maternity_and_newborn.eligibility.newborn_born_during_policy_and_age_up_to_90_days

Unknown reason: The cited passage defines “New Born Baby”; it does not itself determine eligibility for newborn cover. Eligibility also depends on the Section II.14 conditions, including an admissible delivery claim and the applicable special conditions.

Unknown reason: maternity_and_newborn.eligibility.newborn_parent_coverage_and_continuity_conditions: applies_when.arguments[1].members[0] has an incompatible dimension

Unknown reason: maternity_and_newborn.eligibility.newborn_parent_coverage_and_continuity_conditions: applies_when.arguments[1].members[1] has an incompatible dimension

Unknown reason: maternity_and_newborn.waiting_period.newborn_24_month_wait_and_restart_after_delivery_claim

Unknown reason: The source requires 24 months from first commencement and continuous renewal with the Company. The candidate has no required continuous-renewal/continuous-coverage input or applicability condition, so it can represent the waiting period as satisfied despite a break in renewal.

Unknown reason: maternity_and_newborn.coverage.newborn_hospital_treatment_after_admissible_delivery_claim

Unknown reason: For a policy term exceeding one year, the source restricts newborn treatment expenses to the earlier of policy expiry or the policy anniversary. The candidate tests only that the policy is in force and therefore can grant newborn treatment after the relevant anniversary while a multi-year policy remains in force.

Unknown reason: maternity_and_newborn.coverage.newborn_vaccination_until_one_year_after_admitted_delivery_claim

Unknown reason: The candidate does not require that the baby meets the policy’s New Born Baby definition (born during the Policy Period and aged up to 90 days). It also encodes age as less than or equal to 12 elapsed months, whereas the source says vaccination is payable only until the baby completes one year of age; the inclusive completion-day boundary is not supported.

Unknown reason: maternity_and_newborn.exclusion.newborn_pre_post_hospitalization_and_cash_not_applicable: effects[0].expense_predicate.members[0] has an incompatible dimension

Unknown reason: maternity_and_newborn.exclusion.newborn_pre_post_hospitalization_and_cash_not_applicable: effects[0].expense_predicate.members[1] has an incompatible dimension

Unknown reason: maternity_and_newborn.exclusion.newborn_pre_post_hospitalization_and_cash_not_applicable: effects[0].expense_predicate.members[2] has an incompatible dimension

Unknown reason: maternity_and_newborn.exclusion.newborn_congenital_conditions_outside_section_ii_14_extent

Unknown reason: The source treats congenital internal disease or defect as a listed condition subject to the specified-disease waiting period, except to the Section II.14 newborn extent. It does not impose a blanket exclusion for internal congenital disease or defect. Only congenital external conditions, defects, or anomalies are stated as an exclusion subject to that exception.

Unknown reason: Independent review found additional source-supported rules missing from extraction: maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band, maternity_and_newborn.limit.newborn_vaccination_limit_by_sum_insured_band, maternity_and_newborn.exclusion.newborn_external_congenital_conditions_outside_section_ii_14, maternity_and_newborn.waiting_period.newborn_internal_congenital_condition_24_month_wait

Rule: `maternity_and_newborn.definition.newborn_multiyear_cover_ends_at_expiry_or_anniversary` (`299aa445-8a68-465f-b6a9-23aa796943d0`).

Condition: policy term more than one year (input) = True.

Value — `newborn_cover_end_date`: {"node": "conditional", "otherwise": {"key": "next_policy_anniversary_date", "node": "input"}, "then": {"key": "policy_expiry_date", "node": "input"}, "when": {"left": {"key": "policy_expiry_date", "node": "input"}, "node": "compare", "operator": "lte", "right": {"key": "next_policy_anniversary_date", "node": "input"}}}.

Scope: {"benefit_keys": ["newborn_cover"], "period": "unknown", "reset": "unknown", "subject": "person", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "policy_term_more_than_one_year",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "policy_expiry_date",
      "unit": "date",
      "required": true,
      "value_kind": "date",
      "provenance_required": true
    },
    {
      "key": "next_policy_anniversary_date",
      "unit": "date",
      "required": true,
      "value_kind": "date",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "unknown",
        "period": "unknown",
        "subject": "person",
        "subject_ids": [],
        "benefit_keys": [
          "newborn_cover"
        ]
      },
      "value": {
        "node": "conditional",
        "then": {
          "key": "policy_expiry_date",
          "node": "input"
        },
        "when": {
          "left": {
            "key": "policy_expiry_date",
            "node": "input"
          },
          "node": "compare",
          "right": {
            "key": "next_policy_anniversary_date",
            "node": "input"
          },
          "operator": "lte"
        },
        "otherwise": {
          "key": "next_policy_anniversary_date",
          "node": "input"
        }
      },
      "term_key": "newborn_cover_end_date_for_policy_term_over_one_year",
      "target_key": "newborn_cover_end_date"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "left": {
      "key": "policy_term_more_than_one_year",
      "node": "input"
    },
    "node": "compare",
    "right": {
      "node": "literal",
      "value": {
        "kind": "boolean",
        "value": true
      }
    },
    "operator": "eq"
  },
  "schema_version": 1,
  "source_span_ids": [
    "6845e8f4-0e08-47d8-af93-ee594a0cc94d"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 14](#citation-6845e8f4-0e08-47d8-af93-ee594a0cc94d); characters [0, 2659).

Rule: `maternity_and_newborn.definition.newborn_claim_sum_insured_and_bonus_effects` (`2cdb360c-7505-4d7a-9efd-837b9492c800`).

Condition: claim under section ii 14 (input) = True.

Value — `newborn_claim_reduces_sum_insured`: False.

Scope: {"benefit_keys": ["newborn_cover", "newborn_vaccination"], "period": "per_event", "reset": "new_event", "subject": "claim", "subject_ids": []}.

Value — `newborn_claim_affects_cumulative_bonus`: True.

Scope: {"benefit_keys": ["newborn_cover", "newborn_vaccination"], "period": "per_event", "reset": "new_event", "subject": "claim", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "claim_under_section_ii_14",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "new_event",
        "period": "per_event",
        "subject": "claim",
        "subject_ids": [],
        "benefit_keys": [
          "newborn_cover",
          "newborn_vaccination"
        ]
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "boolean",
          "value": false
        }
      },
      "term_key": "reduces_sum_insured",
      "target_key": "newborn_claim_reduces_sum_insured"
    },
    {
      "kind": "definition",
      "scope": {
        "reset": "new_event",
        "period": "per_event",
        "subject": "claim",
        "subject_ids": [],
        "benefit_keys": [
          "newborn_cover",
          "newborn_vaccination"
        ]
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "boolean",
          "value": true
        }
      },
      "term_key": "affects_cumulative_bonus",
      "target_key": "newborn_claim_affects_cumulative_bonus"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "left": {
      "key": "claim_under_section_ii_14",
      "node": "input"
    },
    "node": "compare",
    "right": {
      "node": "literal",
      "value": {
        "kind": "boolean",
        "value": true
      }
    },
    "operator": "eq"
  },
  "schema_version": 1,
  "source_span_ids": [
    "6845e8f4-0e08-47d8-af93-ee594a0cc94d"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 14](#citation-6845e8f4-0e08-47d8-af93-ee594a0cc94d); characters [0, 2659).

### restoration

Status: **unknown**.

Unknown reason: restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[0] has an incompatible dimension

Unknown reason: restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[1] has an incompatible dimension

Unknown reason: restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[2] has an incompatible dimension

Unknown reason: restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[3] has an incompatible dimension

Unknown reason: restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[4] has an incompatible dimension

Unknown reason: restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[5] has an incompatible dimension

Unknown reason: restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[6] has an incompatible dimension

Rule: `restoration.restoration.restoration_exhaustion_restores_basic_sum_insured_once_each_policy_year` (`b356af29-ba2d-4234-9005-404bc4097320`).

Condition: basic sum insured and accrued cumulative bonus exhausted (input) = True.

Value — `restored_sum_insured`: basic sum insured (input).

Scope: {"benefit_keys": ["sections_ii_1_ii_3_ii_5_ii_6_ii_7_ii_8_ii_11"], "period": "policy_year", "reset": "anniversary", "subject": "policy", "subject_ids": []}.

Value — `restoration_frequency`: Once during the Policy Period; where the policy is issued for more than 1 year, automatic restoration is available for each year without carry over..

Scope: {"benefit_keys": ["restored_sum_insured"], "period": "policy_year", "reset": "anniversary", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "basic_sum_insured_and_accrued_cumulative_bonus_exhausted",
      "unit": "truth",
      "required": true,
      "value_kind": "boolean",
      "provenance_required": true
    },
    {
      "key": "basic_sum_insured",
      "unit": "money",
      "required": true,
      "value_kind": "quantity",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "accumulation",
      "scope": {
        "reset": "anniversary",
        "period": "policy_year",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": [
          "sections_ii_1_ii_3_ii_5_ii_6_ii_7_ii_8_ii_11"
        ]
      },
      "amount": {
        "key": "basic_sum_insured",
        "node": "input"
      },
      "membership": {
        "node": "constant",
        "value": "true"
      },
      "target_key": "restored_sum_insured",
      "accounting_role": "reserve"
    },
    {
      "kind": "definition",
      "scope": {
        "reset": "anniversary",
        "period": "policy_year",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": [
          "restored_sum_insured"
        ]
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "text",
          "value": "Once during the Policy Period; where the policy is issued for more than 1 year, automatic restoration is available for each year without carry over."
        }
      },
      "term_key": "automatic_restoration_frequency",
      "target_key": "restoration_frequency"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "left": {
      "key": "basic_sum_insured_and_accrued_cumulative_bonus_exhausted",
      "node": "input"
    },
    "node": "compare",
    "right": {
      "node": "literal",
      "value": {
        "kind": "boolean",
        "value": true
      }
    },
    "operator": "eq"
  },
  "schema_version": 1,
  "source_span_ids": [
    "832fe413-0802-4639-9e14-f26eb385afeb",
    "0b9e14a9-91d2-42ba-bc1a-d6a55ab36ca6"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 45](#citation-0b9e14a9-91d2-42ba-bc1a-d6a55ab36ca6); characters [0, 3368).

Citation (defines): [star-comprehensive-base-wording, physical page 13](#citation-832fe413-0802-4639-9e14-f26eb385afeb); characters [0, 3074).

### family_floater

Status: **unknown**.

Unknown reason: family_composition: family_floater: family_composition.eligibility.family_floater_self_spouse_up_to_three_children_subject_to_underwriting: rule.applies_when.arguments[3].right.value: 0 count has no matching quoted number and unit; rule.applies_when.arguments[4].right.value: 3 count has no matching quoted number and unit; Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Unknown reason: family_composition: family_floater: family_composition.eligibility.family_floater_adult_entry_age_subject_to_underwriting: Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Unknown reason: family_composition: family_floater: family_composition.eligibility.family_floater_dependent_child_age_and_dependency_subject_to_underwriting: Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Unknown reason: family_composition.definition.family_floater_shared_sum_insured_among_insured_persons: applies_when: comparison requires compatible dimensions

Unknown reason: Independent review found additional source-supported rules missing from extraction: family_composition.definition.family_floater_dependent_child_definition

### portability

Status: **supported**.

Rule: `portability.operational_right.portability_apply_within_renewal_window` (`a773f2bf-4d94-4b99-9732-ee1a7922f0b4`).

Condition: (days before policy renewal date (input) >= 30 day) AND (days before policy renewal date (input) <= 60 day).

Value — `portability_application`: {"action": "Apply to another insurer to port the entire policy together with all covered family members, if any; this is an application right and does not promise acceptance by the acquiring insurer.", "deadline": {"node": "literal", "value": {"kind": "duration", "value": {"anchor_event": "before the policy renewal date", "boundary": "inclusive", "state": "known", "unit": "elapsed_day", "value": 30}}}, "kind": "right", "scope": {"benefit_keys": [], "period": "policy_term", "reset": "never", "subject": "policy", "subject_ids": []}, "target_key": "portability_application", "trigger_input": "days_before_policy_renewal_date"}.

Scope: {"benefit_keys": [], "period": "policy_term", "reset": "never", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "days_before_policy_renewal_date",
      "unit": "day",
      "required": true,
      "value_kind": "quantity",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "right",
      "scope": {
        "reset": "never",
        "period": "policy_term",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": []
      },
      "action": "Apply to another insurer to port the entire policy together with all covered family members, if any; this is an application right and does not promise acceptance by the acquiring insurer.",
      "deadline": {
        "node": "literal",
        "value": {
          "kind": "duration",
          "value": {
            "unit": "elapsed_day",
            "state": "known",
            "value": 30,
            "boundary": "inclusive",
            "anchor_event": "before the policy renewal date"
          }
        }
      },
      "target_key": "portability_application",
      "trigger_input": "days_before_policy_renewal_date"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "all",
    "arguments": [
      {
        "left": {
          "key": "days_before_policy_renewal_date",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "unit": "day",
            "state": "finite",
            "value": "30"
          }
        },
        "operator": "gte"
      },
      {
        "left": {
          "key": "days_before_policy_renewal_date",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "unit": "day",
            "state": "finite",
            "value": "60"
          }
        },
        "operator": "lte"
      }
    ]
  },
  "schema_version": 1,
  "source_span_ids": [
    "1fe34c5d-d0aa-48ea-81c2-9f59e3903527",
    "6d8cc600-33aa-45a8-9af0-82466a4f5939"
  ],
  "mandatory_rule_keys": []
}
```

Citation (supports): [star-comprehensive-base-wording, physical page 41](#citation-1fe34c5d-d0aa-48ea-81c2-9f59e3903527); characters [0, 3038).

Citation (supports): [star-comprehensive-customer-information-sheet, physical page 17](#citation-6d8cc600-33aa-45a8-9af0-82466a4f5939); characters [0, 2545).

Rule: `portability.operational_right.portability_transfer_prior_coverage_credits` (`fc935f82-7ae1-4cfe-b67a-70b7ad8975ad`).

Condition: (days before policy renewal date (input) >= 30 day) AND (days before policy renewal date (input) <= 60 day).

Value — `portability_prior_coverage_credits`: {"action": "Transfer to the acquiring insurer the credits gained under the previous policy, to the extent of the Sum Insured, including No Claim Bonus, Specific Waiting Periods, the waiting period for Pre-Existing Diseases, and the Moratorium Period; this credit-transfer entitlement does not promise acceptance of the portability application.", "deadline": {"node": "literal", "value": {"kind": "duration", "value": {"anchor_event": "before the policy renewal date", "boundary": "inclusive", "state": "known", "unit": "elapsed_day", "value": 30}}}, "kind": "right", "scope": {"benefit_keys": ["sum_insured_credit", "no_claim_bonus_credit", "specific_waiting_period_credit", "pre_existing_disease_waiting_period_credit", "moratorium_period_credit"], "period": "policy_term", "reset": "never", "subject": "policy", "subject_ids": []}, "target_key": "portability_prior_coverage_credits", "trigger_input": "days_before_policy_renewal_date"}.

Scope: {"benefit_keys": ["sum_insured_credit", "no_claim_bonus_credit", "specific_waiting_period_credit", "pre_existing_disease_waiting_period_credit", "moratorium_period_credit"], "period": "policy_term", "reset": "never", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [
    {
      "key": "days_before_policy_renewal_date",
      "unit": "day",
      "required": true,
      "value_kind": "quantity",
      "provenance_required": true
    }
  ],
  "effects": [
    {
      "kind": "right",
      "scope": {
        "reset": "never",
        "period": "policy_term",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": [
          "sum_insured_credit",
          "no_claim_bonus_credit",
          "specific_waiting_period_credit",
          "pre_existing_disease_waiting_period_credit",
          "moratorium_period_credit"
        ]
      },
      "action": "Transfer to the acquiring insurer the credits gained under the previous policy, to the extent of the Sum Insured, including No Claim Bonus, Specific Waiting Periods, the waiting period for Pre-Existing Diseases, and the Moratorium Period; this credit-transfer entitlement does not promise acceptance of the portability application.",
      "deadline": {
        "node": "literal",
        "value": {
          "kind": "duration",
          "value": {
            "unit": "elapsed_day",
            "state": "known",
            "value": 30,
            "boundary": "inclusive",
            "anchor_event": "before the policy renewal date"
          }
        }
      },
      "target_key": "portability_prior_coverage_credits",
      "trigger_input": "days_before_policy_renewal_date"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "all",
    "arguments": [
      {
        "left": {
          "key": "days_before_policy_renewal_date",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "unit": "day",
            "state": "finite",
            "value": "30"
          }
        },
        "operator": "gte"
      },
      {
        "left": {
          "key": "days_before_policy_renewal_date",
          "node": "input"
        },
        "node": "compare",
        "right": {
          "node": "literal",
          "value": {
            "unit": "day",
            "state": "finite",
            "value": "60"
          }
        },
        "operator": "lte"
      }
    ]
  },
  "schema_version": 1,
  "source_span_ids": [
    "1fe34c5d-d0aa-48ea-81c2-9f59e3903527",
    "6d8cc600-33aa-45a8-9af0-82466a4f5939"
  ],
  "mandatory_rule_keys": [
    "portability.operational_right.portability_apply_within_renewal_window"
  ]
}
```

Citation (supports): [star-comprehensive-base-wording, physical page 41](#citation-1fe34c5d-d0aa-48ea-81c2-9f59e3903527); characters [0, 3038).

Citation (supports): [star-comprehensive-customer-information-sheet, physical page 17](#citation-6d8cc600-33aa-45a8-9af0-82466a4f5939); characters [0, 2545).

### geography

Status: **supported**.

Rule: `geography.definition.geography_treatment_territory_india` (`b3b53ecb-0dfd-4fc8-83c3-cfc121c903f4`).

Condition: Applies within the stated scope.

Value — `treatment_territory`: India.

Scope: {"benefit_keys": ["health_treatments"], "period": "policy_term", "reset": "never", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "never",
        "period": "policy_term",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": [
          "health_treatments"
        ]
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "text",
          "value": "India"
        }
      },
      "term_key": "operative_treatment_territory",
      "target_key": "treatment_territory"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "7740dd5a-4799-425e-91bd-72d3edc93283"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 44](#citation-7740dd5a-4799-425e-91bd-72d3edc93283); characters [0, 3135).

Rule: `geography.definition.geography_personal_accident_worldwide` (`8a31bc45-0acd-4447-9489-e19e58e2cbe2`).

Condition: Applies within the stated scope.

Value — `personal_accident_territory`: Worldwide.

Scope: {"benefit_keys": ["section_ii_23_accidental_death_and_permanent_total_disablement"], "period": "policy_term", "reset": "never", "subject": "policy", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "never",
        "period": "policy_term",
        "subject": "policy",
        "subject_ids": [],
        "benefit_keys": [
          "section_ii_23_accidental_death_and_permanent_total_disablement"
        ]
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "text",
          "value": "Worldwide"
        }
      },
      "term_key": "operative_personal_accident_territory",
      "target_key": "personal_accident_territory"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "4f6fefbe-0340-4aaf-9b4b-40169ccca324"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 19](#citation-4f6fefbe-0340-4aaf-9b4b-40169ccca324); characters [0, 2635).

### eligibility

Status: **unknown**.

Unknown reason: eligibility.eligibility.eligibility_adult_entry_age_and_underwriting_acceptance: applies_when.arguments[2]: comparison requires compatible dimensions

Unknown reason: eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[2].members[0] has an incompatible dimension

Unknown reason: eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[2].members[1] has an incompatible dimension

Unknown reason: eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[5]: comparison requires compatible dimensions

Unknown reason: eligibility.eligibility.eligibility_renewal_subject_to_product_and_conduct_conditions: applies_when.arguments[0]: comparison requires compatible dimensions

Rule: `eligibility.definition.eligibility_dependent_child_relationship_definition` (`13fe37ff-3ab5-41c2-a816-74d2df971448`).

Condition: Applies within the stated scope.

Value — `dependent_child_relationship`: A natural or legally adopted child who is financially dependent, has no independent source of income, and is not over 25 years of age..

Scope: {"benefit_keys": [], "period": "policy_term", "reset": "never", "subject": "person", "subject_ids": []}.

Conditions, scope and dependencies (complete validated contract):

```json
{
  "table": null,
  "inputs": [],
  "effects": [
    {
      "kind": "definition",
      "scope": {
        "reset": "never",
        "period": "policy_term",
        "subject": "person",
        "subject_ids": [],
        "benefit_keys": []
      },
      "value": {
        "node": "literal",
        "value": {
          "kind": "text",
          "value": "A natural or legally adopted child who is financially dependent, has no independent source of income, and is not over 25 years of age."
        }
      },
      "term_key": "dependent_child",
      "target_key": "dependent_child_relationship"
    }
  ],
  "rounding": {
    "mode": "none",
    "scale": 0,
    "authority_span_ids": []
  },
  "unresolved": [],
  "applies_when": {
    "node": "constant",
    "value": "true"
  },
  "schema_version": 1,
  "source_span_ids": [
    "5b320602-24ee-4fdb-b173-1f0001230353"
  ],
  "mandatory_rule_keys": []
}
```

Citation (defines): [star-comprehensive-base-wording, physical page 7](#citation-5b320602-24ee-4fdb-b173-1f0001230353); characters [0, 3502).

### no_copay (derived; outside the 13)

Status: **unknown**.

Unknown reason: Copay remains unresolved; no_copay cannot be inferred from missing evidence.

### Price and budget (outside the 13)

**Unavailable.** No approved premium table or quote is available for this base variant.

## Family Health Optima Insurance Plan

UIN: `SHAHLIP26046V092526`.

**Pending:** no completed criterion-validation artifact is available. No source criterion is reported as supported.

## Star Health Assure Insurance Policy

UIN: `SHAHLIP26048V032526`.

**Pending:** no completed criterion-validation artifact is available. No source criterion is reported as supported.

## Approved document decisions and remaining scope limits

All optional covers remain unselected: Comprehensive PED buyback; Optima voluntary copayment; Assure aggregate deductible.
Comprehensive's captured 2025 document codes versus its 2026 UIN remain the accepted edition mismatch.
Assure consumables use wording clause 27 (physical page 20, printed page 19) and the wording's List I (physical page 44, printed page 43). This approved document decision is separate from the 13 extracted criteria above.
The separate Assure expense sheet remains reference only. Its 68 item descriptions match wording List I after case, whitespace and punctuation normalization. Differences are the title, presentation and column break (wording left column ends at item 35; separate sheet at 34). It cannot support executable rules.
Brochures and proposal forms remain excluded. Prospectuses remain applicable; a criterion prompt adds the complete prospectus only when core evidence is insufficient or a cited definition/table requires it.

## Verbatim citation pages

<a id="citation-6fa98415-3c81-4a4a-a3c3-9c2944e07c2a"></a>
### star-comprehensive-base-wording — physical page 3

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3173); document characters [2850, 6023).

```text
2 / 47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
a. Having at least 5 in-patient beds;
b. 
Having qualified AYUSH Medical Practitioner
in charge round the clock;
c.	
Having dedicated AYUSH therapy Sections
asrequiredand/orhasequippedoperation
theatre where surgical procedures are to
be carried out;
d.	
Maintaining daily records of the
patients and making them accessible
to the insurance company’s authorized
representative.
AYUSH Treatment: AYUSH Treatment refers
to the medical and / or hospitalization
treatments given under Ayurveda, Yoga and
Naturopathy, Unani, Siddha and Homeopathy
systems.
Break in Policy: Break in Policy means the
period of gap that occurs at the end of the
existing Policy Term/instalment premium
due date, when the premium due for renewal
on a given policy or instalment premium due
is not paid on or before the premium renewal
date or grace period.
Cashless Facility: Cashless Facility means a
facility extended by the insurer to the insured
where the payments, of the cost of treatment
undergone by the insured in accordance with
the Policy Terms and conditions, are directly
made to the network provider by the insurer
to the extent pre-authorization approved.
Condition Precedent: Condition Precedent
means a Policy Term or condition upon
which the insurer’s liability under the policy is
conditional upon.
Congenital Anomaly: Congenital Anomaly
means a condition which is present since
birth, and which is abnormal with reference
to form, structure or position.
i.	
Internal Congenital Anomaly: Congenital
anomaly which is not in the visible and
accessible parts of the body
ii.	
External Congenital Anomaly: Congenital
anomaly which is in the visible and
accessible parts of the body
Co-payment: Co-payment means a cost-
sharingrequirementunderahealthinsurance
policy that provides that the policyholder/
insured will bear a specified percentage of
the admissible claim amount. A co-payment
does not reduce the Sum Insured.
CumulativeBonus:CumulativeBonusmeans
any increase or addition in the Sum Insured
granted by the insurer without an associated
increase in premium.
Day Care Centre: A day care centre means
any institution established for day care
treatment of illness and / or injuries or
a medical set up within a hospital and
which has been registered with the local
authorities, wherever applicable and is under
the supervision of a registered and qualified
Medical Practitioner AND must comply with
all minimum criteria as under :-
i. 
has qualified nursing staff under its
employment;
ii. 
has qualified medical practitioner/s in
charge;
iii.	
has a fully equipment operation theatre
of its own where surgical procedures are
carried out;
iv.	
maintains daily records of patients
and will make these accessible to
the insurance company’s authorized
personnel.
Day Care treatment: Day Care treatment
means medical treatment and/or surgical
procedure which is;
i.	
Undertaken under General or Local
Anesthesia in a hospital/day care
centre in less than 24 hrs because of
technological advancement, and

```

<a id="citation-7654a150-0751-4523-a24f-2b6ad2179743"></a>
### star-comprehensive-base-wording — physical page 5

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3260); document characters [9502, 12762).

```text
4 / 47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
ii.	Chronic condition - A chronic condition
is defined as a disease, illness, or injury
that has one or more of the following
characteristics:
a.	
it needs ongoing or long-term
monitoring through consultations,
examinations, check-ups, and /or tests
b.	
it needs ongoing or long-term
control or relief of symptoms
c.	
it requires rehabilitation for the
patient or for the patient to be
specially trained to cope with it
d. it continues indefinitely
e. it recurs or is likely to recur
Injury: Injury means accidental physical
bodily harm excluding illness or disease
solely and directly caused by external, violent,
visible and evident means which is verified
and certified by a Medical Practitioner.
Intensive Care Unit: Intensive Care Unit means
an identified Section, ward or wing of a hospital
which is under the constant supervision of a
dedicated medical practitioner(s), and which
is specially equipped for the continuous
monitoring and treatment of patients who are
in a critical condition, or require life support
facilities and where the level of care and
supervision is considerably more sophisticated
and intensive than in the ordinary and other
wards.
ICU Charges: ICU (Intensive Care Unit)
Charges means the amount charged by a
Hospital towards ICU expenses which shall
include the expenses for ICU bed, general
medical support services provided to any
ICU patient including monitoring devices,
critical care nursing and intensivist charges.
Maternity Expenses: Maternity expenses
means
i.	
Medical treatment expenses traceable
to childbirth (including complicated
deliveries and caesarean Sections
incurred during Hospitalization).
ii.	
expenses towards the lawful medical
termination of pregnancy during the
Policy Period.
Medical Advice: Medical Advice means
any consultation or advice from a Medical
Practitioner including the issue of any
prescription or follow-up prescription.
Medical Expenses: Medical expenses means
those expenses that an Insured Person has
necessarily and actually incurred for medical
treatmentonaccountofIllnessorAccidenton
the advice of a Medical Practitioner, as long
as these are no more than would have been
payable if the Insured Person had not been
insured and no more than other hospitals
or doctors in the same locality would have
charged for the same medical treatment.
Medical Practitioner: Medical Practitioner
is a person who holds a valid registration
from the Medical Council of any State or
Medical Council of India or Council for Indian
Medicine or for Homeopathy set up by the
Government of India or a State Government
and is thereby entitled to practice medicine
within its jurisdiction; and is acting within the
scope and jurisdiction of licence.
Medically Necessary Treatment: Medically
necessary treatment means any treatment,
tests, medication or stay in hospital or part of
a stay in a hospital which
i.	isrequiredforthemedicalmanagementof
the illness or injury suffered by the Insured
ii.	
must not exceed the level of care
necessary to provide safe, adequate
and appropriate medical care in scope,
duration or intensity

```

<a id="citation-f1e37045-2e50-44d4-8f97-79af60cc483a"></a>
### star-comprehensive-base-wording — physical page 6

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3205); document characters [12763, 15968).

```text
5 / 47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
iii.	
must have been prescribed by a Medical
Practitioner
iv.	
must conform to the professional
standards widely accepted in
international medical practice or by the
medical community in India.
Migration: Migration means a facility
provided to policyholders (including all
members under family cover and group
policies), to transfer the credits gained for
pre-existing diseases and specific waiting
periods from one health insurance policy to
another with the same insurer.
Network Provider: Network Provider means
hospitals or health care providers enlisted by
an insurer, TPA or jointly by an Insurer and TPA
to provide medical services to an insured by
a cashless facility.
New Born Baby: New Born Baby means baby
born during the Policy Period and is aged up
to 90 days
Non-Network Provider: Non-Network means
any hospital, day care center or other
provider that is not part of the network.
Notification of Claim: Notification of Claim
means the process of intimating a claim
to the insurer or TPA through any of the
recognized modes of communication.
OPD treatment: OPD treatment means the
oneinwhichtheInsuredvisitsaclinic/hospital
or associated facility like a consultation room
for diagnosis and treatment based on the
advice of a Medial Practitioner. The insured
is not admitted as a day care or in-patient.
Pre-Existing Disease: Pre-Existing Disease
(PED) means any condition, ailment, injury or
disease:
i.	
that is/are diagnosed by a physician not
more than 36 months prior to the date of
commencement of the policy issued by
the insurer;
or
ii.	
for which medical advice or treatment
was recommended by, or received from,
a physician, not more than 36 months
prior to the date of commencement of
the policy.
Pre-Hospitalization Medical Expenses: Pre-
Hospitalization Medical Expenses means medical
expenses incurred during pre-defined number
of days preceding the hospitalization of the
Insured Person, provided that:
i.	
Such medical expenses are incurred for
the same condition for which the Insured
Person’s hospitalization was required
and
ii.	
The inpatient hospitalization claim for
such hospitalization is admissible by the
insurance company.
Portability: Portability means a facility
providedtothehealthinsurancepolicyholders
(including all members under family cover),
to transfer the credits gained for, pre-existing
diseases and specific waiting periods from
one insurer to another insurer.
Post-Hospitalization Medical Expenses:
Post-hospitalization Medical Expenses means
medical expenses incurred during pre-defined
number of days immediately after the Insured
Person is discharged from the hospital provided
that:
i.	
Such medical expenses are incurred for
the same condition for which the Insured
Person’s hospitalization was required
and
ii.	
The inpatient hospitalization claim for
such hospitalization is admissible by the
insurance company.
Qualified Nurse: Qualified Nurse means a
person who holds a valid registration from
the Nursing Council of India or the Nursing
Council of any state in India.

```

<a id="citation-5b320602-24ee-4fdb-b173-1f0001230353"></a>
### star-comprehensive-base-wording — physical page 7

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3502); document characters [15969, 19471).

```text
6 / 47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
Reasonable and Customary charges:
Reasonable and Customary charges means
the charges for services or supplies, which are
the standard charges for the specific provider
and consistent with the prevailing charges in
the geographical area for identical or similar
services, taking into account the nature of
the illness / injury involved.
Renewal: Renewal means the terms on which
the contract of insurance can be renewed
on mutual consent with a provision of grace
period for treating the renewal continuous for
the purpose of gaining credit for pre-existing
diseases, time-bound exclusions and for all
waiting periods.
Room Rent: Room Rent means the amount
charged by a Hospital towards Room and
Boarding expenses and shall include the
associated medical expenses.
Specific Waiting Period: Specific Waiting Period
means a period up to 36 months from the
commencement of a health insurance policy
during which period specified diseases/treatments
(except due to an Accident) are not covered. On
completion of the period, diseases/treatments
shall be covered provided the policy has been
continuously renewed without any break.
Surgery or Surgical Procedure: Surgery or
Surgical Procedure means manual and
/ or operative procedure(s) required for
treatment of an illness or injury, correction
of deformities and defects, diagnosis and
cure of diseases, relief from suffering and
prolongation of life, performed in a hospital
or day care centre by a medical practitioner.
Unproven/Experimental treatment: Unproven/
Experimental treatment means the treatment
including drug experimental therapy which is
not based on established medical practice in
India, is treatment experimental or unproven.
S P E C I F I C D E F I N I T I O N S
Associated medical expenses: Associated
Medical Expenses means expenses that
shall include the applicable nursing charges,
Operation theatre charges, Professional
fees of Medical Practitioner including
Surgeon/ anesthetist / Physician/Specialist
of the Hospital where the Insured Person
has been admitted and treated and hence
Proportionate deduction will be applicable
on these items.
“Associated Medical Expenses” does not
include cost of pharmacy and consumables,
cost of implants and medical devices
and cost of diagnostics, ICU charges and
hence proportionate deduction will not be
applicable on these items.
Basic Sum Insured: Basic Sum Insured means
the Sum Insured opted for and for which the
premium is paid.
Company / Insurer / We / Us: Company /
Insurer / We / Us means Star Health and
Allied Insurance Company Limited.
Dependent Child: Dependent Child means
a child (natural or legally adopted) who is
financially dependent and does not have his
or her independent source of income and
not over 25 years.
Diagnosis: Diagnosis means Diagnosis by a
registered medical practitioner, supported by
clinical, radiological and histological, histo-
pathological and laboratory evidence and
also surgical evidence wherever applicable,
acceptable to the Company.
Hazardous Sport / Hazardous Activities:
Hazardous Sport / Hazardous Activities
means engaging whether professionally or
otherwise in any sport or activity, which is
potentially dangerous to the Insured Person
(whether trained, or not). Such Sport/Activity
including but not limited to Winter sports,
Ice hockey, Skiing, Skydiving, Parachuting,

```

<a id="citation-b9a87d61-3798-4bf1-a45b-cf2fc80e038e"></a>
### star-comprehensive-base-wording — physical page 8

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3084); document characters [19472, 22556).

```text
7 / 47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
Ballooning, Scuba Diving, Bungee Jumping,
Mountain Climbing, Riding or Driving in Races
or Rallies, caving or pot holing, hunting or
equestrian activities, diving or under-water
activity, rafting or canoeing involving rapid
waters, yachting or boating outside coastal
waters, jockeys, horseback, Polo, Circus
personnel, army/navy/air force personnel
and policemen whilst on duty, persons
working in underground mines, explosives,
magazines, workers whilst involved in
electrical installation with high-tension
supply, nuclear installations, handling
hazardous chemicals.
Home: Home means the Insured Person’s
place of residence.
Home Care Treatment: Home Care
Treatment means treatment availed by the
Insured Person at home, which in normal
course would require care and treatment
at a hospital but is actually taken at home
provided that:
i.	TheMedicalpractitioneradvicestheInsured
person to undergo treatment at home
ii.	
There is a continuous active line of
treatment with monitoring of the health
status by a medical practitioner for each
day through the duration of the home
care treatment
iii.	
Daily monitoring chart including records
of treatment administered duly signed
by the treating doctor is maintained.
Insured Person: Insured Person means the
name/s of person/s shown in the schedule
of the Policy.
Instalment: Instalment means premium
amount paid through Monthly / Quarterly
/ Half-yearly / Yearly mode by the Policy
Holder/ Insured.
In-Patient means an Insured Person who
is admitted to Hospital and stays there for
a minimum period of 24 hours for the sole
purpose of receiving treatment.
Limit of Coverage: Limit of Coverage means
Basic Sum Insured plus the Cumulative Bonus
earned plus Restored Sum Insured, wherever
applicable.
Policy Period/Policy Year: Policy Period
/ Policy Year means a year following the
commencement date and its subsequent
annual anniversary.
Policy Term: Policy Term means the period
between the commencement date and
expiry date specified in the schedule.
Private Single A/C Room: Private Single
A/C Room means a single occupancy air-
conditioned room with attached wash room
and a couch for the attendant. The room may
have a television and /or a telephone. Such
room must be the most economical of all
accommodations available in that hospital
as single occupancy. This does not include
Deluxe room or a suite.
Sum Insured: Sum Insured wherever it
appears shall mean Basic Sum Insured,
except otherwise expressed.
Zone A: Delhi, New Delhi, Faridabad, Gurugram,
Shahdara, Gautam Buddha Nagar, Ghaziabad,
Mewat, Alwar, Baghpat, Bharatpur, Bhiwani,
Bulandshahar, Fatehabad, Hisar, Jhajjar, Jind,
Kaithal, Karnal, Kurukshetra, Mahendragarh,
Meerut, Muzaffar Nagar, Palwal, Panchsheel Nagar
(Hapur), Panipat, Rewari, Rohtak, Saharanpur,
Sirsa, Sonipat, Charkhi Dadri, Gujarat, Daman and
Diu, Dadra and Nagar Haveli, Mumbai (including
suburban), Thane, Palghar and Raigad

```

<a id="citation-20ff97c6-7758-4a9d-a36b-847bb468e9af"></a>
### star-comprehensive-base-wording — physical page 9

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3330); document characters [22557, 25887).

```text
8 / 47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
Zone B: Telangana, Ernakulam, Kollam,
Wayanad, Thiruvananthapuram, Mathura,
Aligarh, Pune, Nashik and Ahmed Nagar
Zone C: Chennai, Bengaluru, Chengalpattu,
Kanchipuram, Tiruvallur, Indore and Gwalior
Zone D: Rest of Uttar Pradesh, Rest of Tamil
Nadu, Rest of Kerala, Rest of Maharashtra,
Rest of Haryana, Rest of Madhya Pradesh,
Rest of Karnataka, Rest of Rajasthan, Andhra
Pradesh, Punjab, Kolkata, North 24 Parganas
and Paschim Bardhaman
Zone E: Rest Of India
II - COVERAGE
In consideration of the premium paid, subject
to the terms, conditions, exclusions and
definitions contained herein the Company
agrees as under.
If during the period stated in the Policy Schedule
the insured person sustains bodily injury or
contracts any disease or suffer from any illness
and if such disease or injury shall require the
Insured person, upon the advice of a duly qualified
Medical Practitioner to incur Hospitalization
expenses for Medical / Surgical treatment at
any Nursing Home / Hospital in India as an
In-patient for medically necessary treatment,
the Company will indemnify the Insured Person
such expenses as are reasonably and necessarily
incurred under the Coverage but not exceeding
the sum insured/ annual sum insured/ appropriate
benefit stated in the Policy schedule.
1.	In-patient Treatment: We will cover the
following Medical Expenses incurred in
respect of Hospitalization of the Insured
Person during the Policy Period, up to
the Sum Insured specified in the Policy
ScheduleagainstthisIn-Patienttreatment:
i.	
Room (Private Single A/C room),
Boarding and Nursing Expenses as
provided by the Hospital / Nursing
Home.
Note: Any hospitalization expenses
arising under this Policy, which vary
based on the room rent occupied by
the Insured Person will be considered in
proportion to the room rent limit / room
category stated in the Policy or actuals
whichever is less.
ii.	
Surgeon,Anesthetist,MedicalPractitioner,
Consultants, Specialist Fees.
iii.	
Anesthesia, blood, oxygen, operation
theatre charges, ICU charges, surgical
appliances, medicines and drugs,
diagnostic materials and X-ray,
diagnostic imaging modalities,
dialysis, chemotherapy, radiotherapy,
cost of pacemaker, stent and similar
expenses. With regard to coronary
stenting, medicines, Implants and
such other similar items, the Company
will pay cost of stent as per the Drug
Price Control Order (DPCO) / National
Pharmaceuticals Pricing Authority
(NPPA) Capping.
2.	
Day Care Treatment: We will cover the
Medical Expenses incurred in respect of
All Day Care Treatments of the Insured
Person during the Policy Period up to the
Sum Insured as specified in the Policy
Schedule if such Day Care treatment
requires hospitalization as an in‑patient
for less than 24 hours. Applicable for
Sections II.3, II.4, II.9, II.14, II.15 and II.25.
3.	AYUSH Treatment: Medical expenses
for Inpatient Hospitalization incurred
on treatment under Ayurveda, Yoga
and Naturopathy, Unani, Siddha and
Homeopathy systems of medicines in a
AYUSH Hospital is payable up to the Sum
Insured.
Note: Claims under Yoga and Naturopathy
system of treatment will be payable subject
to prior approval from the company

```

<a id="citation-832fe413-0802-4639-9e14-f26eb385afeb"></a>
### star-comprehensive-base-wording — physical page 13

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3074); document characters [34214, 37288).

```text
12/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
Where the Sum Insured under the policy
is Rs.7,50,000/-or above, the Insured
Person would be entitled to the benefit
of Cumulative Bonus calculated at 100%
of the Basic Sum Insured under this
policy following a claim free year. The
maximum benefit of cumulative bonus
is 100% of the Basic Sum Insured.
Claims under Sections II.1, II.2, II.3, II.4, II.5,
II.6, II.7, II.8, II.9, II.10, II.11, II.14, II.15 and II.25 will
impact the eligibility and accumulation
of Cumulative Bonus.
Special Conditions for Cumulative Bonus
i.	
The Cumulative Bonus will be calculated
on the expiring Basic Sum Insured.
ii.	
If the insured opts to reduce the Basic
Sum Insured at the subsequent renewal,
the limit of indemnity by way of such
Cumulative Bonus shall not exceed such
reduced Basic Sum Insured.
iii. In the event of a claim resulting in
a.	
Partial utilization of Basic Sum
Insured, such cumulative bonus so
granted will be reduced at the same
rate at which it has accrued
b.	
Full utilization of Basic Sum Insured
and nil utilization of cumulative
bonus accrued, such cumulative
bonus so granted will be reduced
at the same rate at which it has
accrued
c.	
Full utilization of Basic Sum Insured
and partial utilization of cumulative
bonus accrued, the cumulative
bonus granted on renewal will be the
balance cumulative bonus available
and after the reduction at the same
rate at which it has accrued. At any
point of time, the cumulative bonus
will not be less than “zero”
d.	
Full utilization of Basic Sum Insured
and full utilization of cumulative
bonus accrued, the cumulative
bonus granted on renewal will be
“nil” or “zero”
13.	
Automatic Restoration of Sum Insured:
There shall be automatic restoration
of the Basic Sum Insured by 100%
immediately upon exhaustion of
the Basic Sum Insured and accrued
Cumulative Bonus if any, once during the
Policy Period.
It is made clear that such restored
Sum Insured can be utilized for the
subsequent hospitalization even for the
illness /disease for which claim/s was /
were already made.
Such restoration will be available for
Sections II.1, II.3, II.5, II.6, II.7, II.8 and II.11
Hospitalization due to continuous period
of illness including its relapse within 45
days from the date of last consultation
with the Hospital/Nursing Home where
treatment was taken will be considered
as same hospitalization as per “Any one
Illness” definition. Any claim payable
under this benefit shall be subject to the
definition as provided under “Any one
Illness”.
14. Delivery and New Born
A.	
Expenses for a Delivery including
Delivery by Caesarean Section
(including pre-natal and post-natal
expenses) up to the limits mentioned
in the table below per Delivery,
subject to a maximum of 2 deliveries
in the entire life time of the Insured
Person are payable while the policy
is in force.
B.	
Expenses up to the limits mentioned in
the table below, incurred in a hospital/

```

<a id="citation-6845e8f4-0e08-47d8-af93-ee594a0cc94d"></a>
### star-comprehensive-base-wording — physical page 14

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 2659); document characters [37289, 39948).

```text
13/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
nursing home on treatment of the New-
born for any disease, illness (including
any congenital disorders) or accidental
injuries are payable provided there is
an admissible claim under Section II.14.A
above and while the policy is in force.
In case of Policy Term is more than
one year, such expenses are payable
only till the expiry of the policy or policy
anniversary whichever is earlier.
Delivery and New Born
Sum
Insured Rs.
Limit for Delivery Limit of
Company’s
liability for
New Born
Cover Rs.
Normal
Delivery
Rs.
Delivery by
Ceasarean
Section Rs.
5,00,000/- 15,000/- 20,000/- 1,00,000/-
7,50,000/- 25,000/- 40,000/- 1,00,000/-
10,00,000/-
to
25,00,000/-
30,000/- 50,000/- 1,00,000/-
50,00,000/-
to
1,00,00,000/-
50,000/- 1,00,000/- 2,00,000/-
C.	
Vaccination expenses for the new
born baby are payable up to the limits
mentioned in the table below, until the
new born baby completes one year
of age and is added in the policy on
renewal. Claim under this is admissible
only if claim under Section II.14.A above
has been admitted and while the policy
is in force.
Limits for Vaccination
Sum Insured Rs.
Limit per Policy Period
(Rs.)
5,00,000/- to
25,00,000/-
5,000/-
Above 25,00,000/- 10,000/-
Special Conditions applicable for this
Section
i. 
Benefit under this Section is subject to
a waiting period of 24 months from the
date of first commencement of Star
Comprehensive Insurance Policy and
its continuous renewal thereof with the
Company. A waiting period of 24 months
will apply afresh following a claim under
Section II.14.A above.
ii.	
Pre-hospitalization and Post Hospitalization
expenses and Hospital Cash Benefit are
not applicable for this Section.
iii. This cover is available only when;
a.	
both Self and Spouse are covered
under this policy either on floater
basis or on individual basis and both
Self and Spouse should have been
covered for a continuous period of 24
months under Star Comprehensive
Insurance Policy,
b.	
the policy covering the self and
spouse are in force when the benefit
under this Section becomes payable.
iv. Claims under this Section
a. will not reduce the Sum Insured;
b. will affect Cumulative Bonus.
15.	Bariatric Surgery: Expenses incurred
on hospitalization for bariatric surgical
procedure and its complications
thereof are payable subject to limits
mentioned in the table given below,
during the Policy Period. This maximum
limit of Rs.2,50,000/- and Rs.5,00,000/-
are inclusive of pre-hospitalization and
post-hospitalization expenses.

```

<a id="citation-4f6fefbe-0340-4aaf-9b4b-40169ccca324"></a>
### star-comprehensive-base-wording — physical page 19

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 2635); document characters [50594, 53229).

```text
18/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
a.	
The disablement occurs within
12 Calendar months from the
date of the Accident.
b. 
The disablement is confirmed
and claimed for, prior to
the expiry of a period of 60
days since occurrence of the
disablement.
Special Conditions
i. I
f the Accident affects any physical
function, which was already impaired
prior to the accident, a deduction as per
“Table – B2” will be made in respect of
this prior disablement.
ii.	
In the event of Permanent Total
Disablement, the Insured Person will be
under obligation:
a.	
To have himself/herself examined by
doctors appointed by the Company
/ and the Company will pay the costs
involved thereof.
b.	
To authorize doctors providing
treatments or giving expert opinion
and any other authority to supply the
Company any information that may
be required. If the obligations are not
met with due to whatsoever reason,
the Company may be relieved of its
liability to pay.
iii.	
This Section is applicable for the person
specifically mentioned in the Schedule.
iv.	
The Sum Insured for this Section is equal
to the Sum Insured opted for Health
Section.
v.	
Where a claim has been paid during the
Policy Period the cover under this Section
ceases until the expiry of the policy. Upon
renewal the cover applies to the person
specifically chosen again. However even
if the Sum Insured under this Section is
exhausted by way of claim, the coverage
under health Section will continue until
expiry of the Policy Period.
vi.	
At any point of time, only one person
will be eligible to be covered under
this Section. Dependent Children and
persons above 70 years can be covered
under this Section up to the Sum Insured
of Rs.10,00,000/-.
vii.	
Any claim under health portion will not
affect the Sum Insured under this Section.
viii.	
Where there is an admissible claim
for Accidental Death during the Policy
Period, the health cover will continue for
the remaining Insured Persons.
ix.	
Where there is an admissible claim for
Permanent Total Disability during the
Policy Period, the health cover would
continue until the expiry of the policy for
all the Insured Persons covered including
the person who has made a claim for
Permanent Total Disability and renewal
thereof.
x.	
Where there is an admissible claim
under this Section, during the Policy
Period, the personal accident cover will
be applicable for another person chosen
at the time of renewal.
xi.	
Geographical Scope: The cover under
this Section applies World Wide.

```

<a id="citation-07f429f2-ac0c-4265-a1a0-23950acfe0df"></a>
### star-comprehensive-base-wording — physical page 31

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 2822); document characters [77217, 80039).

```text
30/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
v.	
All treatments (conservative,
interventional, laparoscopic and
open) related to Hepato-pancreato-
biliary diseases including Gall bladder
and Pancreatic calculi. All types
of management for Kidney and
Genitourinary tract calculi
vi. All types of Hernia
vii.	
Desmoid Tumor, Umbilical Granuloma,
Umbilical Sinus, Umbilical Fistula,
viii.	
All treatments (conservative,
interventional, laparoscopic and open)
related to all Diseases of Cervix, Uterus,
Fallopian tubes, Ovaries, Uterine Bleeding,
Pelvic Inflammatory Diseases
ix.	
All Diseases of Prostate, Stricture
Urethra, all Obstructive Uropathies,
x.	
Benign Tumours of Epididymis,
Spermatocele,Varicocele,Hydrocele,
xi.	
Fistula, Fissure in Ano, Hemorrhoids,
Pilonidal Sinus and Fistula, Rectal
Prolapse, Stress Incontinence
xii. Varicose veins and Varicose ulcers
xiii.	
All types of transplant and related
surgeries
xiv.	
Congenital Internal disease / defect
(except to the extent provided under
Section II.14 for New Born)
III - EXCLUSIONS
S T A N D A R D E X C L U S I O N S
A.	
The Company shall not be liable to make
any payments under this policy in respect
of any expenses what so ever incurred
by the Insured Person in connection with
or in respect of;
1. Pre-Existing Diseases – Code Excl 01
A.	
Expenses related to the treatment
of a pre-existing Disease (PED)
and its direct complications shall
be excluded until the expiry of 36
months of continuous coverage
after the date of inception of the first
policy with insurer.
B.	
IncaseofenhancementofSumInsured
the exclusion shall apply afresh to the
extent of Sum Insured increase
C.	
If the Insured Person is continuously
covered without any break as
defined under the applicable norms
on portability stipulated by IRDAI,
then waiting period for the same
would be reduced to the extent of
prior coverage
D.	
Coverage under the policy after the
expiry of 36 months for any pre-
existing disease is subject to the
same being declared at the time of
application and accepted by Insurer.
2.	
Specified disease/procedure waiting
period – Code Excl 02
A.	
Expenses related to the treatment
of the listed Conditions, surgeries/
treatments shall be excluded until
the expiry of 24 months of continuous
coverage after the date of inception
of the first policy with us. This
exclusion shall not be applicable for
claims arising due to an accident.
B.	
In case of enhancement of Sum Insured
the exclusion shall apply afresh to the
extent of Sum Insured increase
C. 
If any of the specified disease/
procedure falls under the waiting
period specified for pre-Existing
diseases, then the longer of the two
waiting periods shall apply.

```

<a id="citation-94711633-5762-412f-8b4e-f74c1c3f9fe5"></a>
### star-comprehensive-base-wording — physical page 34

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 2921); document characters [85694, 88615).

```text
33/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
11.	
Excluded Providers – Code Excl 11:
Expenses incurred towards treatment in
anyhospitalorbyanyMedicalPractitioner
or any other provider specifically
excluded by the Insurer and disclosed in
its website / notified to the policyholders
are not admissible. However, in case of
life threatening situations or following
an accident, expenses up to the stage
of stabilization are payable but not the
complete claim.
12.	
Treatment for Alcoholism, drug or
substance abuse or any addictive
condition and consequences thereof –
Code Excl 12
13.	
Treatments received in health hydros,
nature cure clinics, spas or similar
establishmentsorprivatebedsregistered
as a nursing home attached to such
establishments or where admission is
arranged wholly or partly for domestic
reasons – Code Excl 13
14.	Dietarysupplementsandsubstancesthat
can be purchased without prescription,
including but not limited to Vitamins,
minerals and organic substances unless
prescribed by a medical practitioner as
part of hospitalization claim or day care
procedure – Code Excl 14
15.	
Refractive Error – Code Excl 15: Expenses
related to the treatment for correction of
eye sight due to refractive error less than
7.5 dioptres.
16.	
Unproven Treatments – Code Excl
16: Expenses related to any unproven
treatment, services and supplies for
or in connection with any treatment.
Unproven treatments are treatments,
procedures or supplies that lack
significant medical documentation to
support their effectiveness.
17.	
Sterility and Infertility – Code Excl 17:
Expenses related to sterility and infertility.
This includes;
a.	
Any type of contraception,
sterilization
b.	
Assisted Reproduction services
including artificial insemination and
advanced reproductive technologies
such as IVF, ZIFT, GIFT, ICSI
c. Gestational Surrogacy
d. Reversal of sterilization
18. Maternity – Code Excl 18
a.	
Medical treatment expenses traceable
to childbirth (including complicated
deliveries and caesarean Sections
incurred during hospitalization) except
ectopic pregnancy and to the extent
covered under Section II.14
b.	
Expenses towards miscarriage
(unless due to an accident) and
lawful medical termination of
pregnancy during the Policy Period
S P E C I F I C E X C L U S I O N S
19.	
Circumcision (unless necessary for
treatment of a disease not excluded
under this policy or necessitated
due to an accident), Preputioplasty,
Frenuloplasty, Preputial Dilatation and
Removal of SMEGMA - Code Excl 19
20.	
Congenital External Condition / Defects
/ Anomalies (except to the extent
provided under Section II.14 for New Born)
- Code Excl 20
21.	
Convalescence, general debility, run-
down condition, Nutritional deficiency
states - Code Excl 21
22. Intentional self injury - Code Excl 22

```

<a id="citation-904832d2-8071-44dd-bea5-198b553b1bcc"></a>
### star-comprehensive-base-wording — physical page 40

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3080); document characters [103271, 106351).

```text
39/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
policies and / or having multiple policies that
exceeds the maximum Sum Insured filed as
per the Product.
5.	Fraud: lf any claim made by the Insured
Person, is in any respect fraudulent, or
if any false statement, or declaration is
made or used in support thereof, or if any
fraudulent means or devices are used by
the Insured Person or anyone acting on
his/her behalf to obtain any benefit under
this policy, all benefits under this policy
and the premium paid shall be forfeited.
Any amount already paid against claims
made under this policy but which are
found fraudulent later shall be repaid by
all recipient(s)/policyholder(s), who has
made that particular claim, who shall
be jointly and severally liable for such
repayment to the insurer.
For the purpose of this clause, the
expression “fraud” means any of the
following acts committed by the Insured
Person or by his agent or the hospital/
doctor/any other party acting on behalf
of the Insured Person, with intent to
deceive the insurer or to induce the
insurer to issue an insurance policy:
i.	
the suggestion, as a fact of that which
is not true and which the Insured Person
does not believe to be true;
ii.	
the active concealment of a fact by the
Insured Person having knowledge or
belief of the fact;
iii. any other act fitted to deceive; and
iv.	
any such act or omission as the law
specially declares to be fraudulent
The Company shall not repudiate the claim
and / or forfeit the policy benefits on the
ground of Fraud, if the Insured Person /
beneficiary can prove that the misstatement
was true to the best of his knowledge and
there was no deliberate intention to suppress
the fact or that such misstatement of or
suppression of material fact are within the
knowledge of the insurer.
6. Cancellation
i.	
The Policy Holder may cancel his policy
any time during the term by giving 7
days written notice. In such an event, The
Company shall
a.	
refund proportionate premium for
unexpired Policy Period, if Policy Term
upto one year and there is no claim
(s) made during the Policy Period.
b.	
refund premium for the unexpired
Policy Period, in respect of policies
with Policy Term more than 1 year
and risk coverage for such Policy
Years has not commenced.
ii.	
The Company may cancel the policy at
anytimeongroundsofmisrepresentation,
non-disclosure of material facts, fraud
by the Insured Person by giving 15 days’
written notice. There would be no refund
of premium on cancellation on grounds
of misrepresentation, non-disclosure of
material facts or fraud.
Note: Incase of long term policies the
refund will be given after adjusting
the long term discount availed by the
insured/ policyholder.
7.	Migration: In case of migration of one
policy to another with the same insurer,
the Policyholder (including all members
under family cover and group insurance
policies) can transfer the credits gained
to the extent of the Sum Insured, No

```

<a id="citation-1fe34c5d-d0aa-48ea-81c2-9f59e3903527"></a>
### star-comprehensive-base-wording — physical page 41

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3038); document characters [106352, 109390).

```text
40/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
Claim Bonus, Specific Waiting Periods,
Waiting period for Pre-Existing Diseases,
Moratorium period etc. in the previous
policy to the migrated policy.
8. Portability:
i.	
The Policyholder has the choice to
port his / her policy from one Insurer
to another by applying to such
Insurer to port the entire policy along
with all the members of the family, if
any, at least 30 days before, but not
earlier than 60 days from the policy
renewal date as per IRDAI guidelines
related to portability.
ii.	The Policyholder is entitled to transfer
the credits gained to the extent of
the Sum Insured, No Claim Bonus,
Specific Waiting Periods, Waiting
period for Pre-Existing Diseases,
Moratorium period etc. from the
existing Insurer to the Acquiring
Insurer in the previous policy.
9.	
Renewal of policy: The policy shall
be renewable provided the product
is not withdrawn, except in case of
established fraud or non-disclosure or
misrepresentation by the Policyholder. If
theproductiswithdrawn,thepolicyholder
shall be provided with suitable options
to migrate as per the procedure stated
under “withdrawal clause”
i.	
AttheendofthePolicyPeriod,thepolicy
shall terminate and can be renewed
within the Grace Period of 30 days.
ii.	
While coverage is not available
during the Grace Period, if the
policy is renewed during the Grace
Period, all the credits (Sum Insured,
No Claim Bonus, Specific Waiting
Periods, Waiting period for Pre-
Existing Diseases, Moratorium period
etc.) accrued under the policy shall
be protected.
10. Withdrawal of policy:
In the likelihood of this product being
withdrawn in future, the Company will
intimate the Policyholder about the same
90 days prior to expiry of the policy.
i.	
A one-time option to renew the
existing product, if renewal falls
within the 90 days from the date of
withdrawal of the product, or
ii.	
Policyholder will have the option to
migrate to similar health insurance
product available with the Company
at the time of renewal. Policyholder
can transfer the credits gained (to
the extent of Sum Insured, No Claim
Bonus, Specific Waiting Periods,
Waiting period for Pre-Existing
Diseases, Moratorium period etc.) in
the previous policy to the migrated
policy, provided the policy has been
maintained without a break.
11.	Moratorium Period: After completion
of sixty continuous months of coverage
(including portability and migration)
in health insurance policy, no policy
and claim shall be contestable by the
insurer on grounds of non-disclosure,
misrepresentation, except on grounds
of established fraud. This period of
sixty continuous months is called as
moratorium period. The moratorium
would be applicable for the Sums Insured
of the first policy. Wherever, the Sum
Insured is enhanced, completion of sixty
continuous months would be applicable
from the date of enhancement of Sums
Insured only on the enhanced limits.

```

<a id="citation-7740dd5a-4799-425e-91bd-72d3edc93283"></a>
### star-comprehensive-base-wording — physical page 44

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3135); document characters [115606, 118741).

```text
43/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
21. Notice and Communication:
i.	
Any direction or instruction given
under this Policy shall be in writing
and delivered by hand, post, or email
to Star Health and Allied Insurance
Company Limited, Registered Office:
No. 1, New Tank Street, Valluvar
Kottam High Road, Nungambakkam,
Chennai - 600 034/Corporate Office:
No. 148, Acropolis, Dr. Radha Krishnan
Salai, Mylapore, Chennai - 600 004.
Customer Care No. 044-69006900
or Toll-Free No. 1800 425 2255
e-mail: support@starhealth.in
ii.	
Any legal notice under this policy
shall be in writing and delivered
by hand, post, or email to Claims
Department, 4th Floor, Balaji
Complex, No.15, Whites Lane, Whites
Road, Royapettah, Chennai- 600014;
a.	
e-mail for Consumer Matter:
claims.legal@starhealth.in
b.	
e-mail for Ombudsman:
claims.ombudsman@starhealth.in
Notices and instructions will be
deemed served 7 days after posting
or immediately upon receipt in the
case of hand delivery or e-mail.
If notices or communications are not
sent to the addresses or email IDs
mentioned above, the Company will
not be able to respond promptly.
22.	Territorial Limit: All treatments under this
policy shall have to be taken in India.
23.	Automatic Expiry: The insurance under
this policy with respect to each relevant
Insured Person shall expire immediately
on the earlier of the following events.
i.	
Upon the death of the Insured
Person. This also means that in case
of family floater policy, cover for
the other surviving members of the
family will continue, subject to other
terms of the policy
ii.	
Upon exhaustion of the Limit of
Coverage
24.	
Policy disputes: Any dispute concerning
theinterpretationoftheterms,conditions,
limitations and/or exclusions contained
herein is understood and agreed to by
both the Insured and the Company to be
subject to Indian Law.
25.	
Excluded Hospitals (providers): Insured
can refer the company website using the
following link to get the list of excluded
hospitals.
https://www.starhealth.in/lookup/
hospital/#excluded-hospital
26.	
Revision of Sum Insured: Reduction or
enhancement of Basic Sum Insured is
permissible only at the time of renewal.
The acceptance for enhancement and
the amount of enhancement will be at
the discretion of the Company. Where
the Basic Sum Insured is enhanced, the
amount of such additional Basic Sum
Insuredincludingtherespectivesublimits
shall be subject to the following terms.
Exclusion as under shall apply afresh
from the date of such enhancement for
the increase in the Basic Sum Insured,
that is, the difference between the
expiring policy Basic Sum Insured and
the increased current Basic Sum Insured.
i.	
First 30 days as per exclusion - Code
Excl 03
ii.	24 months with continuous coverage
without break (with grace period) in
respect of diseases / treatments as
per exclusion - Code Excl 02
iii.	
36 months of continuous coverage
without break (with grace period) in
respect of Pre-Existing diseases as
per exclusion - Code Excl 01

```

<a id="citation-0b9e14a9-91d2-42ba-bc1a-d6a55ab36ca6"></a>
### star-comprehensive-base-wording — physical page 45

PDF SHA-256: `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`. Page characters [0, 3368); document characters [118742, 122110).

```text
44/47
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | POLICY WORDINGS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | POL / COMP / V.24 / 2025
iv.	
36 months of continuous coverage
without break (with grace period) for
diseases / conditions diagnosed /
treated irrespective of whether any
claimismadeornotintheimmediately
preceding three Policy Periods
v.	
The above applies to each relevant
Insured Person
27.	ReliefunderSection80-D:InsuredPerson
is eligible for relief under Section 80-D of
the IT Act in respect of the premium paid
by any mode other than cash
28. Important Note
i.	
Where the policy is issued for more
than 1 year, the Basic Sum Insured
including sublimits, cumulative
bonus (if applicable), automatic
restoration benefit (if applicable) is
for each of the year, without any carry
over benefit thereof. The said benefits
/ covers available for the 2nd year or
3rd year cannot be utilized in the 1st
year itself. The terms conditions and
exceptions that appear in the Policy
or in any Endorsement are part of
the contract, must be complied with
and applies to each Policy Year.
ii.	
Where the policy is issued on
floater basis, the Basic Sum Insured,
cumulative bonus and other related
benefits floats amongst the Insured
Persons.
iii.	
The Policy Schedule and any
Endorsement are to be read together
and any word or such meaning
wherever it appears shall have the
meaning as stated in the Act / Indian
Laws.
iv.	
The terms, conditions and exceptions
that appear in the Policy or in any
Endorsement are part of the contract,
must be complied with and applies to
each relevant Insured Person. Failure
to comply with may result in the claim
being denied.
v.	
The attention of the policy holder
is drawn to our website www.
starhealth.in for anti-fraud policy
of the company for necessary
compliance by all stake holders.
29.	Customer Service: If at any time the
Insured Person requires any clarification
or assistance, the insured may contact
Star Health and Allied Insurance Company
Limited, “Balaji Complex, No.15, Whites
Lane, Whites Road, Royapettah, Chennai-
600014”, during normal business hours.
31.	Third-Party Claims: Only the authorized
Third-Party Administrator (TPA), legal
heirs, Proposer, or approved Insurance
Intermediaries have the right to make
or follow up on reimbursement claims
underthispolicy.Theclaimswillbesettled
directly to the Proposer’s account. In case
of the Proposer’s death, the settlement
will be made to the nominee’s account
as the case may be.
Claims by unauthorized third party will
not be entertained, and the Company
reserves the right to reject such claims.
This rejection does not breach the terms
of the policy.
32.	Professional Conduct: The Company shall
ensure that its staff and representatives
shall conduct themselves in courteous
and professional manner in all their
interactions with the insured/proposer,
whether in person, through email, telephone
or any other online or offline platforms.
The insured/proposer hereby irrevocably
agrees to conduct themselves in courteous
and professional manner in all interactions
with the Company. Any unprofessional or
inappropriate behaviour by the insured/
proposer may result in strict action by the
Company, including without limitation, legal
action under the Bharatiya Nyaya Sanhita,
Act 2023, as amended from time to time.

```

<a id="citation-af639b61-6d94-4429-b111-f85ca27b3fcc"></a>
### star-comprehensive-customer-information-sheet — physical page 5

PDF SHA-256: `afe91f7446ed4dfc6090d3ce746386cf182ab5b094c9c6ae1b5af81a1375e665`. Page characters [0, 2395); document characters [6901, 9296).

```text
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | CIS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | CIS / COMP / V.5 / 2025 4 / 19
6
Exclusions:
(What the
policy does
not cover?
Investigation & Evaluation Excl 04
Rest Cure, rehabilitation and respite care Excl 05
Obesity / Weight Control Excl 06
Change-of-Gender treatments Excl 07
Cosmetic or plastic Surgery Excl 08
Hazardous or Adventure sport Excl 09
Breach of law Excl 10
Excluded Providers Excl 11
Treatment for Alcoholism, drug or substance abuse or any
addictive condition and consequences thereof
Excl 12
Treatments received in health hydros, nature cure clinics,
spas or similar establishments or private beds registered as
a nursing home attached to such establishments or where
admission is arranged wholly or partly for domestic reasons
Excl 13
Dietary supplements and substances that can be purchased
without prescription, including but not limited to Vitamins,
minerals and organic substances unless prescribed by a
medical practitioner as part of hospitalization claim or day
care procedure
Excl 14
Refractive Error: Expenses related to the treatment for
correction of eye sight due to refractive error less than 7.5 dioptres
Excl 15
Unproven Treatments: Expenses related to any unproven
treatment, services and supplies for or in connection with any
treatment. Unproven treatments are treatments, procedures
or supplies that lack significant medical documentation to
support their effectiveness
Excl 16
Sterility and Infertility: Expenses related to sterility and
infertility. This includes; a. Any type of contraception,
sterilization b. Assisted Reproduction services including
artificial insemination and advanced reproductive technologies
such as IVF, ZIFT, GIFT, ICSI c. Gestational Surrogacy d.
Reversal of sterilization
Excl 17
Maternity
i. Medical treatment expenses traceable to childbirth
(including complicated deliveries and caesarean sections
incurred during hospitalization) except ectopic pregnancy
and to the extent covered under Section II.14
ii. Expenses towards miscarriage (unless due to an accident)
and lawful medical termination of pregnancy during the
Policy Period
Excl 18
Circumcision (unless necessary for treatment of a disease
not excluded under this policy or necessitated due to an
accident), Preputioplasty, Frenuloplasty, Preputial Dilatation
and Removal of SMEGMA
Excl 19

```

<a id="citation-bb3b7a47-7ab6-4625-8095-cada2e8c3dc0"></a>
### star-comprehensive-customer-information-sheet — physical page 10

PDF SHA-256: `afe91f7446ed4dfc6090d3ce746386cf182ab5b094c9c6ae1b5af81a1375e665`. Page characters [0, 2475); document characters [18801, 21276).

```text
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | CIS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | CIS / COMP / V.5 / 2025 9 / 19
Pre-Existing Diseases
A. Expenses related to the treatment of a pre-existing Disease
(PED) and its direct complications shall be excluded until
the expiry of 36 months of continuous coverage after the
date of inception of the first policy with insurer
B. In case of enhancement of Sum Insured the exclusion
shall apply afresh to the extent of Sum Insured increase
C. If the Insured Person is continuously covered without
any break as defined under the applicable norms on
portability stipulated by IRDAI, then waiting period for the
same would be reduced to the extent of prior coverage
D. Coverage under the policy after the expiry of 36
months for any pre-existing disease is subject to the
same being declared at the time of application and
accepted by Insurer
III A(1) Excl
01
8
The policy will pay only up to the limits specified hereunder for
the following diseases/procedures:
Sublimits
1. Room category: Private Single A/C room
II(1)(i)
Financial
limits of
coverage
i. Sub-limit
(It is a pre-
defined
limit
and the
insurance
company
will not pay
any amount
in excess
of this limit)
2. Coverage for Modern Treatments:
Sum Insured
(Rs.)
Uterine artey
Embolization &
HIFU
Ballon
Sinuplasty
Deep Brain
Stimulation
Limits in Rs.
5,00,000/- 1,25,000/- 50,000/- 2,50,000/-
7,50,000/- 1,25,000/- 50,000/- 2,50,000/-
10,00,000/- 1,50,000/- 1,00,000/- 3,00,000/-
15,00,000/- 1,75,000/- 1,25,000/- 4,00,000/-
20,00,000/- 2,00,000/- 1,50,000/- 4,50,000/-
25,00,000/- 2,00,000/- 1,50,000/- 5,00,000/-
50,00,000/- 2,25,000/- 1,75,000/- 6,00,000/-
75,00,000/- 2,50,000/- 2,00,000/- 7,00,000/-
1,00,00,000/- 3,00,000/- 2,00,000/- 7,50,000/-
Sum Insured
(Rs.)
Oral
Chemotherapy*
(Sublimits
including
Pre and Post
Hospitalization)
Immunotheraphy
– Monoclonal
injection
Intra vitreal
Injections
Limits in Rs.
5,00,000/- 1,25,000/- 2,50,000/- 50,000/-
7,50,000/- 1,25,000/- 2,75,000/- 60,000/-
10,00,000/- 2,00,000/- 4,00,000/- 75,000/-
15,00,000/- 2,50,000/- 5,00,000/- 1,00,000/-
20,00,000/- 2,75,000/- 5,50,000/- 1,25,000/-
25,00,000/- 3,00,000/- 6,00,000/- 1,50,000/-
50,00,000/- 4,00,000/- 7,50,000/- 1,75,000/-
75,00,000/- 5,00,000/- 9,00,000/- 2,00,000/-
1,00,00,000/- 6,00,000/- 10,00,000/- 2,00,000/-
* Sublimitsareallinclusivewithorwithouthospitalizationwherever
hospitalization includes pre and post hospitalization.
II(4)

```

<a id="citation-e12bc2fb-0918-44e3-9170-f74085362c0d"></a>
### star-comprehensive-customer-information-sheet — physical page 13

PDF SHA-256: `afe91f7446ed4dfc6090d3ce746386cf182ab5b094c9c6ae1b5af81a1375e665`. Page characters [0, 724); document characters [23970, 24694).

```text
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | CIS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | CIS / COMP / V.5 / 2025 12/19
ii) 
Co-payment
(It is a
specified
amount/
percentage
of the
admissible
claim amount
to be paid by
policy holder/
insured
This policy is subject to co-payment of 10% of each and
every claim amount for fresh as well as renewal policies
for Insured Persons whose age at the time of entry is 61
years and above.
IV(2)(I)
iii) Deductible
(It is a
specified
amount: up
to which an
insurance
company
will not pay
any claim,
and which
will be
deducted
from total
claim
amount
(if claim
amount
is more
than the
specified
amount)
NIL -
iv) Any other
limit ( as
applicable)
NIL -

```

<a id="citation-6d8cc600-33aa-45a8-9af0-82466a4f5939"></a>
### star-comprehensive-customer-information-sheet — physical page 17

PDF SHA-256: `afe91f7446ed4dfc6090d3ce746386cf182ab5b094c9c6ae1b5af81a1375e665`. Page characters [0, 2545); document characters [31395, 33940).

```text
STAR HEALTH AND ALLIED INSURANCE COMPANY LIMITED | CIS
Star Comprehensive Insurance Policy | UIN : SHAHLIP26044V092526 | CIS / COMP / V.5 / 2025 16/19
Policy renewal: The policy shall be renewable provided the
product is not withdrawn, except in case of established fraud
or non-disclosure or misrepresentation by the Policyholder. If
the product is withdrawn, the policyholder shall be provided
with suitable options to migrate as per the procedure stated
under “withdrawal clause”
i. 
At the end of the Policy Period, the policy shall terminate and
can be renewed within the Grace Period of 30 days.
ii. 
While coverage is not available during the Grace Period, if
the policy is renewed during the Grace Period, all the credits
(Sum Insured, No Claim Bonus, Specific Waiting Periods,
Waiting period for Pre-Existing Diseases, Moratorium period
etc.) accrued under the policy shall be protected.
IV(9)
Migration: In case of migration of one policy to another with
the same insurer, the Policyholder (including all members
under family cover and group insurance policies) can transfer
the credits gained to the extent of the Sum Insured, No Claim
Bonus, Specific Waiting Periods, Waiting period for Pre-
Existing Diseases, Moratorium period etc. in the previous
policy to the migrated policy.
IV(7)
Portability:
i. 
The Policyholder has the choice to port his / her policy from one
Insurer to another by applying to such Insurer to port the entire
policy along with all the members of the family, if any, at least
30 days before, but not earlier than 60 days from the policy
renewal date as per IRDAI guidelines related to portability.
ii. 
The Policyholder is entitled to transfer the credits gained to
the extent of the Sum Insured, No Claim Bonus, Specific
Waiting Periods, Waiting period for Pre-Existing Diseases,
Moratorium period etc. from the existing Insurer to the
Acquiring Insurer in the previous policy.
IV(8)
Change in Sum Insured: Reduction or enhancement of Basic
Sum Insured is permissible only at the time of renewal. The
acceptance for enhancement and the amount of enhancement
will be at the discretion of the Company. Where the basic
sum insured is enhanced, the amount of such additional
basic sum insured including the respective sublimits shall be
subject to the following terms. Exclusion as under shall apply
afresh from the date of such enhancement for the increase
in the Basic Sum Insured, that is, the difference between the
expiring policy Basic Sum Insured and the increased current
Basic Sum Insured.
IV(26)

```
