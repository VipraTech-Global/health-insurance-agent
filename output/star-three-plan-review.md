# Star three-plan cited-fact review — Checkpoint 2

Selected variant: **Base policy without optional covers**. Prices and budget remain unavailable.
Comparison support means a source-reviewed plain-English fact with short exact clause quotations. Executable-rule status is separate. No release has been published.
An unknown criterion means source support or independent fact review remains incomplete; a rule encoding failure alone does not make the cell unknown.
Captured manifest SHA-256: `11175393d28fd81b12fb73f6fdeedfb334ce34d1176e6b4b99e2d66d73c939d7`.
Physical PDF pages are used throughout. Character offsets refer to preserved `pdftotext -raw` text and are end-exclusive.

## Validation summary

| Plan | Supported source criteria | Unresolved source criteria | Price |
|---|---:|---:|---|
| Star Comprehensive Insurance Policy | 7/13 | 6/13 | Unavailable |
| Family Health Optima Insurance Plan | Pending | Pending | Unavailable |
| Star Health Assure Insurance Policy | Pending | Pending | Unavailable |

Derived `no_copay` and price are outside the 13-criterion denominator.

## Star Comprehensive Insurance Policy

UIN: `SHAHLIP26044V092526`.

Validation job: `8b7ddada-a4e4-4faa-b82e-612d69729be7` (succeeded). **7/13 supported; 6/13 unresolved.**
Prospectus used for: eligibility, family_floater, sum_insured.
Prospectus gaps reported but not supplemented: none. See the criterion's unknown reasons below.
Timeout calls across retained and resumed processing: 1.

### sum_insured

Status: **unknown**.

Unknown reason: sum_insured_choices: sum_insured: Extraction output still failed validation after one corrective retry: invalid_structured_output.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): sum_insured_choices.coverage.sum_insured_available_new_purchase_amounts

Rule encoding record (does not determine fact support): sum_insured_choices: sum_insured: needs_prospectus: no supplied native document states that the nine Sum Insured amounts in the cited modern-treatment table are the complete amounts available for a new purchase. The cited table uses Sum Insured as an axis for modern-treatment sublimits, not as an available-sum-insured selection schedule; the candidate also invents an identity lookup that grants the selected Sum Insured.

Rule encoding record (does not determine fact support): sum_insured_choices.eligibility.sum_insured_revision_outside_renewal_unavailable: applies_when.arguments[0].members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): sum_insured_choices.eligibility.sum_insured_revision_outside_renewal_unavailable: applies_when.arguments[0].members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): sum_insured_choices.eligibility.sum_insured_revision_outside_renewal_unavailable: applies_when.arguments[1]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): sum_insured_choices.eligibility.sum_insured_reduction_permitted_at_renewal: applies_when.arguments[0]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): sum_insured_choices.eligibility.sum_insured_reduction_permitted_at_renewal: applies_when.arguments[1]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): sum_insured_choices.eligibility.sum_insured_enhancement_subject_to_company_discretion: applies_when.arguments[0]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): sum_insured_choices.eligibility.sum_insured_enhancement_subject_to_company_discretion: applies_when.arguments[1]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): Independent review found additional source-supported rules missing from extraction: sum_insured_choices.definition.sum_insured_basic_amount_opted_and_premium_paid

### room_category

Status: **supported**.

Value: Private Single A/C Room, defined as the hospital's most economical single-occupancy air-conditioned room with an attached wash room and attendant couch; it excludes a Deluxe room or suite. Room, boarding and nursing expenses are covered subject to that category. Hospitalization expenses that vary by the room occupied are considered proportionately against the stated room-rent limit/category or actuals, whichever is less. ICU charges are covered, and proportionate deduction does not apply to ICU charges.

Condition: The permitted room category is a Private Single A/C Room and includes room, boarding and nursing expenses provided by the hospital or nursing home. (quotes 1).

Condition: The room must be the most economical single-occupancy accommodation available in that hospital and must have air conditioning, an attached wash room and an attendant couch; a Deluxe room or suite is not included. (quotes 2).

Condition: Hospitalization expenses that vary according to the room occupied are considered in proportion to the room-rent limit or room category stated in the policy, or actuals, whichever is less. (quotes 3).

Condition: ICU charges are covered under in-patient treatment. (quotes 4).

Condition: Proportionate deduction applies to the specified associated medical expenses, but does not apply to ICU charges. (quotes 5, 6).

Note: No separate numeric room-rent or ICU monetary limit is stated in the supplied base-policy wording for this room category.

Note: The optional Buy Back of Pre-Existing Disease Waiting Period cover is unselected and does not alter this room-category fact.

Note: Coverage remains subject to the policy's other terms, conditions, exclusions and the applicable sum insured.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): rule not executable: intact fact recovered from retained rejected wrapper; no extra extraction call or retry-budget reset.

Rule encoding record (does not determine fact support): room_and_icu_limits.limit.room_category_private_single_ac_room: effects[0].amount must produce a numeric value

Rule encoding record (does not determine fact support): room_and_icu_limits.deduction.room_category_proportionate_associated_expenses

Rule encoding record (does not determine fact support): room_and_icu_limits: room_category: The policy requires proportionate consideration when hospitalization expenses vary by occupied room rent and the policy room-rent limit/category is lower than actuals, but it does not state an insurer-determined deduction amount or a calculation formula. The candidate invents an insurer-determined amount input and omits Medical Practitioner professional fees from the complete associated-medical-expense category.

Rule encoding record (does not determine fact support): room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[2] has an incompatible dimension

Rule encoding record (does not determine fact support): room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[3] has an incompatible dimension

Rule encoding record (does not determine fact support): room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[4] has an incompatible dimension

Rule encoding record (does not determine fact support): room_and_icu_limits.exception.room_category_no_proportionate_deduction_for_excluded_items: applies_when.members[5] has an incompatible dimension

Rule encoding record (does not determine fact support): Independent review found additional source-supported rules missing from extraction: room_and_icu_limits.deduction.room_category_proportionate_deduction_for_room_dependent_expenses

Retained verified rule IDs (partial encodings may not cover the complete fact): `b50ad942-180d-49a8-8dbc-23ce0e59fa9d`, `982476ea-772e-42ec-8420-e82948b5d383`.

Quote 1: [star-comprehensive-base-wording, physical page 9](http://127.0.0.1:3021/evidence/c0bd8f0a-195c-4616-8a9a-a8cc63d5f0de); characters [1688, 1793).

```text
Room (Private Single A/C room),
Boarding and Nursing Expenses as
provided by the Hospital / Nursing
Home.
```

Quote 2: [star-comprehensive-base-wording, physical page 8](http://127.0.0.1:3021/evidence/e778d0fd-6a5e-45f9-b019-ee033de5a2a9); characters [2197, 2528).

```text
Private Single
A/C Room means a single occupancy air-
conditioned room with attached wash room
and a couch for the attendant. The room may
have a television and /or a telephone. Such
room must be the most economical of all
accommodations available in that hospital
as single occupancy. This does not include
Deluxe room or a suite.
```

Quote 3: [star-comprehensive-base-wording, physical page 9](http://127.0.0.1:3021/evidence/d8e5099a-d8c2-401c-b430-f7acdbc2177b); characters [1800, 2043).

```text
Any hospitalization expenses
arising under this Policy, which vary
based on the room rent occupied by
the Insured Person will be considered in
proportion to the room rent limit / room
category stated in the Policy or actuals
whichever is less.
```

Quote 4: [star-comprehensive-base-wording, physical page 9](http://127.0.0.1:3021/evidence/c607dbd3-79eb-4e5a-b2e0-5d9b26584151); characters [2128, 2384).

```text
Anesthesia, blood, oxygen, operation
theatre charges, ICU charges, surgical
appliances, medicines and drugs,
diagnostic materials and X-ray,
diagnostic imaging modalities,
dialysis, chemotherapy, radiotherapy,
cost of pacemaker, stent and similar
expenses.
```

Quote 5: [star-comprehensive-base-wording, physical page 7](http://127.0.0.1:3021/evidence/f5cc690f-a697-4038-8ee1-8f85faa8c989); characters [1922, 2278).

```text
Associated
Medical Expenses means expenses that
shall include the applicable nursing charges,
Operation theatre charges, Professional
fees of Medical Practitioner including
Surgeon/ anesthetist / Physician/Specialist
of the Hospital where the Insured Person
has been admitted and treated and hence
Proportionate deduction will be applicable
on these items.
```

Quote 6: [star-comprehensive-base-wording, physical page 7](http://127.0.0.1:3021/evidence/e4b533a2-eeb5-40bb-ac55-60cbf75ca689); characters [2279, 2506).

```text
“Associated Medical Expenses” does not
include cost of pharmacy and consumables,
cost of implants and medical devices
and cost of diagnostics, ICU charges and
hence proportionate deduction will not be
applicable on these items.
```

### copay

Status: **supported**.

Value: For the selected base policy without optional covers, a mandatory 10% co-payment applies to each and every claim for an Insured Person whose age at entry is 61 years or above, for both fresh and renewal policies. It does not apply to an Insured Person who entered the policy before age 61 and has renewed continuously without any break. The mandatory co-payment applies only to claims under Sections II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8, II.9, II.10, II.11, II.15 and II.25. No voluntary co-payment is selected; that selection does not remove the conditionally applicable mandatory base co-payment.

Condition: The co-payment is 10% of each and every claim amount. (quotes 1, 4).

Condition: It applies to fresh as well as renewal policies when the Insured Person's age at entry is 61 years or above. (quotes 1, 4).

Condition: It does not apply when the Insured Person entered the policy before attaining age 61 and renews continuously without any break. (quotes 2).

Condition: It applies to Sections II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8, II.9, II.10, II.11, II.15 and II.25. (quotes 3).

Condition: The selected variant is the base policy without optional covers; voluntary co-payment is not selected, and this does not negate the mandatory entry-age-based co-payment. (quotes 1, 2, 3, 4).

Note: The age test is based on age at entry, not current age.

Note: Continuous renewal without any break is required for the exception for persons who entered before age 61.

Note: The selected variant excludes optional covers, including any unselected voluntary co-payment; no zero co-payment is inferred from that selection.

Note: All other policy terms, conditions and exclusions remain applicable.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): rule not executable: intact fact recovered from retained rejected wrapper; no extra extraction call or retry-budget reset.

Rule encoding record (does not determine fact support): copay.deduction.copay_entry_age_61_claim_rate: applies_when.arguments[1].members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): copay.deduction.copay_entry_age_61_claim_rate: applies_when.arguments[1].members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): copay.exception.copay_pre_61_continuous_renewal_non_application

Rule encoding record (does not determine fact support): The cited wording supports that co-payment does not apply to a person who entered before age 61 and renewed continuously without a break. However, this exception targets copay.deduction.copay_entry_age_61_claim_rate, whose trigger requires entry age 61 or above. The exception trigger requires entry age below 61, so the two rules can never co-occur and the proposed exception cannot operationally replace the targeted deduction.

Retained verified rule IDs (partial encodings may not cover the complete fact): `78e69c98-31db-4bb8-87c8-73b4f138cf0a`.

Quote 1: [star-comprehensive-base-wording, physical page 39](http://127.0.0.1:3021/evidence/c668c3fd-87ef-4ae1-a52b-453f43d78004); characters [573, 771).

```text
Co-payment: This policy is subject to
co-payment of 10% of each and every
claim amount for fresh as well as renewal
policies for Insured Persons whose age
at the time of entry is 61 years and above.
```

Quote 2: [star-comprehensive-base-wording, physical page 39](http://127.0.0.1:3021/evidence/c9030eae-ba4a-4bf1-935b-f0174afc9d57); characters [772, 942).

```text
This co-payment will not apply for those
insured persons who have entered
the policy before attaining 61 years of
age and renew the policy continuously
without any break.
```

Quote 3: [star-comprehensive-base-wording, physical page 39](http://127.0.0.1:3021/evidence/9c682f5e-f557-4648-a0b4-be43dec3a3ee); characters [943, 1070).

```text
This co-payment is
applicable for Sections II.1, II.2, II.3, II.4, II.5,
II.6, II.7, II.8, II.9, II.10, II.11, II.15 and II.25.
```

Quote 4: [star-comprehensive-customer-information-sheet, physical page 13](http://127.0.0.1:3021/evidence/e6a35708-f502-4128-816b-077980afb7e4); characters [274, 460).

```text
This policy is subject to co-payment of 10% of each and
every claim amount for fresh as well as renewal policies
for Insured Persons whose age at the time of entry is 61
years and above.
```

### deductible

Status: **supported**.

Value: Base-policy deductible: NIL.

Note: Reused accepted extraction and independent review; quotations narrowed to exact clauses.

Executable-rule status: **executable**.

Retained verified rule IDs (partial encodings may not cover the complete fact): `cdeae311-3ff7-48fb-9972-b2c839701e46`.

Quote 1: [star-comprehensive-customer-information-sheet, physical page 13](http://127.0.0.1:3021/evidence/de1d8245-e3e0-4b18-96f1-4bcf01f16583); characters [470, 679).

```text
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
```

### ped_waiting_period

Status: **unknown**.

Unknown reason: missing_material_condition: The candidate states that coverage is unavailable during the 30-day Grace Period without the applicable instalment-payment exception. The policy says that, for premium paid in instalments during the Policy Period, coverage is available during the Grace Period; this exception materially qualifies the candidate’s categorical statement.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): waiting_periods: ped_waiting_period: waiting_periods.eligibility.ped_waiting_period_post_expiry_requires_declaration_and_acceptance: Rule still has unresolved conditions: Final coverage outcome remains dependent on all other applicable policy terms, conditions, exclusions and limits.

Rule encoding record (does not determine fact support): waiting_periods.waiting_period.ped_waiting_period_base_36_month_continuous_coverage_exclusion

Rule encoding record (does not determine fact support): The 36-month exclusion requires continuous coverage, but the candidate does not declare continuous coverage as a required input or explicit applicability condition. Its combination value of "separate" also fails to reflect the wording that, where a specified disease/procedure is also subject to the PED waiting period, the longer waiting period applies.

Rule encoding record (does not determine fact support): waiting_periods.waiting_period.ped_waiting_period_sum_insured_increase_fresh_36_months

Rule encoding record (does not determine fact support): The fresh 36-month condition for an enhanced Basic Sum Insured applies to the PED exclusion, but the candidate applies to every expense within the increased Basic Sum Insured without requiring that the expense relate to a PED or its direct complications. It also omits the required continuous-coverage-without-break condition for the enhanced amount.

Rule encoding record (does not determine fact support): waiting_periods.definition.ped_waiting_period_monthly_instalment_15_day_grace_preserves_credit: applies_when.arguments[0]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): waiting_periods.definition.ped_waiting_period_non_monthly_instalment_30_day_grace_preserves_credit: applies_when.arguments[0].members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): waiting_periods.definition.ped_waiting_period_non_monthly_instalment_30_day_grace_preserves_credit: applies_when.arguments[0].members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): waiting_periods.definition.ped_waiting_period_non_monthly_instalment_30_day_grace_preserves_credit: applies_when.arguments[0].members[2] has an incompatible dimension

Rule encoding record (does not determine fact support): Independent review found additional source-supported rules missing from extraction: waiting_periods.waiting_period.ped_waiting_period_base_continuous_36_month_exclusion, waiting_periods.waiting_period.ped_waiting_period_increased_sum_insured_continuous_36_month_exclusion, waiting_periods.eligibility.ped_waiting_period_post_expiry_requires_declaration_and_acceptance

Retained verified rule IDs (partial encodings may not cover the complete fact): `0e8108a2-77ab-4c95-8b85-dcae81ed4090`, `9a5a2125-9f9a-493e-bf24-393540e4a58a`, `ed0b3728-5f73-49ac-9f38-ae07c81babd9`.

### initial_specific_waiting_periods

Status: **supported**.

Value: For the selected base policy without optional covers, the initial waiting period excludes expenses related to treatment of any illness within 30 days from the first policy commencement date, except covered claims arising due to an accident. It does not apply if the insured person has continuous coverage for more than 12 months, and it applies to an enhanced Sum Insured when a higher Sum Insured is subsequently granted. The specified-disease/procedure waiting period excludes expenses for the listed conditions, surgeries and treatments until expiry of 24 months of continuous coverage from inception of the first policy with the insurer; claims arising due to an accident are excepted. For a Sum Insured enhancement, this exclusion applies afresh to the increase. If a listed disease or procedure is also subject to the pre-existing-disease waiting period, the longer waiting period applies. The specified waiting period applies even if the condition is contracted after policy inception or was declared and accepted without a specific exclusion. Continuous coverage without a break under applicable IRDAI portability norms reduces the waiting period to the extent of prior coverage. The listed scope covers cataract and specified eye diseases; ENT and thyroid diseases; benign breast diseases; specified benign lumps, cysts and similar pathology; tendon, ligament, fascia, bone and joint diseases and interventions, including arthroscopy, arthroplasty and joint replacement other than when caused by accident; degenerative disc, vertebral and musculoskeletal diseases, including prolapsed intervertebral disc other than when caused by accident; hepato-pancreato-biliary diseases, gall bladder and pancreatic calculi, and kidney and genitourinary-tract calculi; all hernias; listed umbilical conditions; listed diseases of the cervix, uterus, fallopian tubes and ovaries, uterine bleeding and pelvic inflammatory diseases; prostate diseases, urethral stricture and obstructive uropathies; benign epididymal tumours, spermatocele, varicocele and hydrocele; fistula, anal fissure, hemorrhoids, pilonidal sinus and fistula, rectal prolapse and stress incontinence; varicose veins and ulcers; all transplants and related surgeries; and congenital internal disease or defect, except to the extent of New Born coverage under Section II.14. The optional Buy Back of Pre-Existing Disease Waiting Period cover, which could reduce the pre-existing-disease waiting period from 36 months to 12 months on payment of additional premium, is unselected and does not alter these base provisions.

Condition: The 30-day initial waiting period runs from the first policy commencement date and applies to expenses related to treatment of illness. (quotes 1).

Condition: Covered claims arising due to an accident are excepted from the initial waiting period. (quotes 1).

Condition: The initial waiting-period exclusion does not apply if the insured person has continuous coverage for more than 12 months. (quotes 2).

Condition: The initial waiting period applies to the enhanced Sum Insured when a higher Sum Insured is subsequently granted. (quotes 2).

Condition: The specified-disease/procedure waiting period is 24 months of continuous coverage from inception of the first policy with the insurer. (quotes 3).

Condition: Claims arising due to an accident are excepted from the specified-disease/procedure waiting period. (quotes 3).

Condition: For a Sum Insured enhancement, the specified waiting-period exclusion applies afresh to the increased amount. (quotes 3).

Condition: If a specified disease or procedure is also subject to the pre-existing-disease waiting period, the longer waiting period applies. (quotes 3).

Condition: The specified waiting period applies even if the listed condition is contracted after policy inception or declared and accepted without a specific exclusion. (quotes 4).

Condition: Continuous coverage without a break under applicable IRDAI portability norms reduces the specified waiting period to the extent of prior coverage. (quotes 4).

Condition: The specified waiting-period scope includes every disease and procedure in the policy list, including the exception for New Born coverage under Section II.14. (quotes 5, 6, 7, 8).

Condition: The Buy Back of Pre-Existing Disease Waiting Period is an optional cover requiring additional premium and is unselected for this variant. (quotes 9).

Note: The wording does not state whether the first policy commencement date itself is counted as day one; no inclusive or exclusive day boundary is inferred.

Note: Coverage after completion of a waiting period remains subject to all other policy terms, conditions and exclusions and any applicable underwriting acceptance.

Note: The optional Buy Back cover is not selected; its 12-month pre-existing-disease waiting period does not apply to the selected base variant.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): waiting_periods.waiting_period.initial_specific_waiting_periods_initial_illness_30_day_wait: applies_when.arguments[0]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): waiting_periods.waiting_period.initial_specific_waiting_periods_initial_illness_30_day_wait: applies_when.arguments[1]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): waiting_periods.waiting_period.initial_specific_waiting_periods_initial_enhancement_at_renewal_30_day_wait: applies_when.arguments[0]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): waiting_periods.waiting_period.initial_specific_waiting_periods_initial_enhancement_at_renewal_30_day_wait: applies_when.arguments[1]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): waiting_periods.exception.initial_specific_waiting_periods_initial_accident_claim_exception: a required dependency was not independently verified.

Rule encoding record (does not determine fact support): waiting_periods.exception.initial_specific_waiting_periods_initial_over_12_month_continuity_exception

Rule encoding record (does not determine fact support): The continuous-coverage-over-twelve-months exception is stated for the Code Excl 03 initial waiting-period exclusion generally. That exclusion is expressly also applied afresh to the enhanced Basic Sum Insured; limiting the exception to only the original-or-continuing sum-insured rule omits the enhanced-sum-insured scope.

Rule encoding record (does not determine fact support): waiting_periods.waiting_period.initial_specific_waiting_periods_listed_condition_continuous_24_month_wait

Rule encoding record (does not determine fact support): The candidate cites an unselected optional-cover passage (07f429f2-ac0c-4265-a1a0-23950acfe0df) and therefore does not safely attribute its rule solely to the selected base variant. In addition, the source makes the 24-month waiting period applicable to every listed condition, including when contracted after inception or declared and accepted without a specific exclusion; the candidate's listed-condition-status restriction is not source-defined as an exhaustive applicability criterion.

Rule encoding record (does not determine fact support): waiting_periods.waiting_period.initial_specific_waiting_periods_listed_condition_enhancement_at_renewal_24_month_wait

Rule encoding record (does not determine fact support): The candidate cites an unselected optional-cover passage (07f429f2-ac0c-4265-a1a0-23950acfe0df), rather than relying only on the selected base-policy wording. It also omits the base-policy portability credit condition for the specified-disease/procedure waiting period.

Rule encoding record (does not determine fact support): waiting_periods.exception.initial_specific_waiting_periods_specific_accident_claim_exception: a required dependency was not independently verified.

Rule encoding record (does not determine fact support): waiting_periods.exception.initial_specific_waiting_periods_specific_ped_overlap_uses_longer_wait: a required dependency was not independently verified.

Rule encoding record (does not determine fact support): waiting_periods.exception.initial_specific_waiting_periods_newborn_congenital_internal_cover_exception: applies_when.arguments[0]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): waiting_periods.exception.initial_specific_waiting_periods_newborn_congenital_internal_cover_exception: applies_when.arguments[1]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): Independent review found additional source-supported rules missing from extraction: waiting_periods.exception.initial_specific_waiting_periods_30_day_continuity_exception, waiting_periods.waiting_period.initial_specific_waiting_periods_listed_condition_base_24_month_wait, waiting_periods.waiting_period.initial_specific_waiting_periods_listed_condition_enhancement_24_month_wait

Quote 1: [star-comprehensive-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/ef5054a6-c796-480b-b4db-55ea9b22117b); characters [969, 1165).

```text
A. Expenses related to the treatment of any illness within
30 days from the first policy commencement date shall
be excluded except claims arising due to an accident,
provided the same are covered
```

Quote 2: [star-comprehensive-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/8d79e37a-f2af-430b-b8e8-5d21864a22ac); characters [1166, 1425).

```text
B. This exclusion shall not, however, apply if the Insured
Person has continuous coverage for more than twelve
months
C. The within referred waiting period is made applicable
to the enhanced Sum Insured in the event of granting
higher Sum Insured subsequently
```

Quote 3: [star-comprehensive-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/884119df-4ac7-49fd-bee0-e12cc90676e8); characters [1555, 2134).

```text
A. Expenses related to the treatment of the following listed
Conditions, surgeries/ treatments shall be excluded
until the expiry of 24 months of continuous coverage
after the date of inception of the first policy with us. This
exclusion shall not be applicable for claims arising due
to an accident
B. In case of enhancement of Sum Insured the exclusion
shall apply afresh to the extent of Sum Insured increase
C. If any of the specified disease/procedure falls under
the waiting period specified for Pre-Existing Diseases,
then the longer of the two waiting periods shall apply
```

Quote 4: [star-comprehensive-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/48d93d69-4fc9-4b82-b11d-d622a954f349); characters [2135, 2503).

```text
D. The waiting period for listed conditions shall apply even
if contracted after the policy or declared and accepted
without a specific exclusion
E. If the Insured Person is continuously covered without any
break as defined under the applicable norms on portability
stipulated by IRDAI, then waiting period for the same
would be reduced to the extent of prior coverage
```

Quote 5: [star-comprehensive-customer-information-sheet, physical page 9](http://127.0.0.1:3021/evidence/a714bb41-4fe6-45ed-9014-616c54c70af6); characters [193, 549).

```text
i. Treatment of Cataract and diseases of the anterior
and posterior chamber of the Eye, Diseases of
ENT, Diseases related to Thyroid, Benign diseases
of the breast
ii. Subcutaneous Benign Lumps, Sebaceous cyst,
Dermoid cyst, Mucous cyst lip / cheek, Carpal Tunnel
Syndrome, Trigger Finger, Lipoma, Neurofibroma,
Fibroadenoma, Ganglion and similar pathology
```

Quote 6: [star-comprehensive-customer-information-sheet, physical page 9](http://127.0.0.1:3021/evidence/97ab8d21-bc17-44ed-b084-f1b232996e24); characters [550, 1028).

```text
iii. All treatments (Conservative, Operative treatment)
and all types of intervention for Diseases related
to Tendon, Ligament, Fascia, Bones and Joint
Including Arthroscopy and Arthroplasty / Joint
Replacement [other than caused by accident]
iv. All types of treatment for Degenerative disc and
Vertebral diseases including Replacement of
bones and joints and Degenerative diseases of the
Musculo-skeletal system, Prolapse of Intervertebral
Disc (other than caused by accident)
```

Quote 7: [star-comprehensive-customer-information-sheet, physical page 9](http://127.0.0.1:3021/evidence/7a888cdb-0542-49b7-bc3b-4248980896d7); characters [1029, 1551).

```text
v. All treatments (conservative, interventional,
laparoscopic and open) related to Hepato-
pancreato-biliary diseases including Gall bladder
and Pancreatic calculi. All types of management
for Kidney and Genitourinary tract calculi
vi. All types of Hernia
vii. Desmoid Tumor, Umbilical Granuloma, Umbilical
Sinus, Umbilical Fistula
viii. All treatments (conservative, interventional,
laparoscopic and open) related to all Diseases of
Cervix, Uterus, Fallopian tubes, Ovaries, Uterine
Bleeding, Pelvic Inflammatory Diseases
```

Quote 8: [star-comprehensive-customer-information-sheet, physical page 9](http://127.0.0.1:3021/evidence/8ef21c1d-376b-460d-b3a2-5c367b8f31af); characters [1552, 2005).

```text
ix. All Diseases of Prostate, Stricture Urethra, all
Obstructive Uropathies,
x. Benign Tumours of Epididymis, Spermatocele,
Varicocele, Hydrocele,
xi. Fistula, Fissure in Ano, Hemorrhoids, Pilonidal Sinus
and Fistula, Rectal Prolapse, Stress Incontinence
xii. Varicose veins and Varicose ulcers
xiii. All types of transplant and related surgeries
xiv. Congenital Internal disease / defect (except to the
extent provided under Section II.14 for New Born)
```

Quote 9: [star-comprehensive-customer-information-sheet, physical page 4](http://127.0.0.1:3021/evidence/68676f5e-3eef-4eb2-882f-4fcbcf8949b3); characters [1827, 2211).

```text
Buy Back of Pre-Existing Disease Waiting Period (Optional
Cover): On payment of additional premium the Insured Person
has the option to opt for reduction of waiting period in respect of
Pre-Existing Diseases from 36 months to 12 months. This option
is available only for the first purchase of this Star Comprehensive
Insurance Policy and also only upto Sum Insured chosen at
that time
```

### maternity

Status: **unknown**.

Unknown reason: Quote 2, star-comprehensive-base-wording, physical page 14: Quotation does not occur word for word on its cited raw page.

Unknown reason: 15000 money lacks quoted numeric support (digits or words).

Unknown reason: 20000 money lacks quoted numeric support (digits or words).

Unknown reason: 750000 money lacks quoted numeric support (digits or words).

Unknown reason: 25000 money lacks quoted numeric support (digits or words).

Unknown reason: 40000 money lacks quoted numeric support (digits or words).

Unknown reason: 1000000 money lacks quoted numeric support (digits or words).

Unknown reason: 30000 money lacks quoted numeric support (digits or words).

Unknown reason: 50000 money lacks quoted numeric support (digits or words).

Unknown reason: 5000000 money lacks quoted numeric support (digits or words).

Unknown reason: 10000000 money lacks quoted numeric support (digits or words).

Unknown reason: 100000 money lacks quoted numeric support (digits or words).

Unknown reason: 200000 money lacks quoted numeric support (digits or words).

Unknown reason: Quotation does not occur word for word on its cited raw page.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): maternity_and_newborn: maternity: maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: Rule still has unresolved conditions: A selected Basic Sum Insured not represented by an original table row produces an unknown lookup result.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 0 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 0 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 1 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 1 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 2 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 2 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 3 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 3 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 4 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 4 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 5 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 5 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 6 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 6 axis delivery_type has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 7 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_delivery_limit_by_sum_insured_and_delivery_type: table cell 7 axis delivery_type has the wrong code namespace.

Rule encoding record (does not determine fact support): maternity_and_newborn: maternity: maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: Rule still has unresolved conditions: A selected Basic Sum Insured not represented by an original table row produces an unknown lookup result.; maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: table cell 0 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: table cell 1 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: table cell 2 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_newborn_treatment_limit_by_sum_insured: table cell 3 axis basic_sum_insured_band has the wrong code namespace.

Rule encoding record (does not determine fact support): maternity_and_newborn: maternity: maternity_and_newborn.coverage.maternity_newborn_vaccination_limit_by_sum_insured: Rule still has unresolved conditions: A selected Basic Sum Insured not represented by an original table row or range produces an unknown lookup result.; maternity_and_newborn.coverage.maternity_newborn_vaccination_limit_by_sum_insured: table cell 0 axis basic_sum_insured_band has the wrong code namespace.; maternity_and_newborn.coverage.maternity_newborn_vaccination_limit_by_sum_insured: table cell 1 axis basic_sum_insured_band has the wrong code namespace.

Rule encoding record (does not determine fact support): maternity_and_newborn: maternity: maternity_and_newborn.waiting_period.maternity_initial_24_month_wait: Rule still has unresolved conditions: The source does not expressly state whether the 24-month completion boundary is inclusive or exclusive.

Rule encoding record (does not determine fact support): maternity_and_newborn: maternity: maternity_and_newborn.waiting_period.maternity_fresh_24_month_wait_after_delivery_claim: Rule still has unresolved conditions: The source states that the waiting period applies afresh following a claim but does not specify whether the anchor is the delivery date, claim submission date, admission date, or claim payment date.; The source does not expressly state whether the 24-month completion boundary is inclusive or exclusive.

Rule encoding record (does not determine fact support): maternity_and_newborn.eligibility.maternity_self_and_spouse_continuity_conditions_met

Rule encoding record (does not determine fact support): Independent verdict: disagree.

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.maternity_miscarriage_not_due_to_accident

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.maternity_lawful_medical_termination_of_pregnancy

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.maternity_pre_post_hospitalization_and_hospital_cash_not_applicable: applies_when.arguments[1].members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.maternity_pre_post_hospitalization_and_hospital_cash_not_applicable: applies_when.arguments[1].members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.maternity_pre_post_hospitalization_and_hospital_cash_not_applicable: applies_when.arguments[1].members[2] has an incompatible dimension

Rule encoding record (does not determine fact support): Independent review found additional source-supported rules missing from extraction: maternity_and_newborn.waiting_period.maternity_initial_delivery_and_newborn_waiting_period, maternity_and_newborn.waiting_period.maternity_waiting_period_restarts_after_delivery_claim, maternity_and_newborn.limit.maternity_delivery_limits_by_sum_insured_and_delivery_type, maternity_and_newborn.limit.maternity_newborn_treatment_limit_by_sum_insured, maternity_and_newborn.limit.maternity_newborn_vaccination_limit_by_sum_insured

Retained verified rule IDs (partial encodings may not cover the complete fact): `95458ce7-188e-4c1d-8178-5336fb6dbdc8`, `e7666e2c-ee93-48b0-97b4-8f8cc025e726`, `7182430e-457e-4abc-8782-fcf4550d0bfb`, `2cd54bf0-bc2b-457a-9794-7aea3ca3c333`.

### newborn

Status: **unknown**.

Unknown reason: Quote 2, star-comprehensive-base-wording, physical page 14: Quotation does not occur word for word on its cited raw page.

Unknown reason: Quotation does not occur word for word on its cited raw page.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): maternity_and_newborn: newborn: Section II.14.C expressly grants newborn vaccination expenses subject to its stated conditions and limits, while Code Excl 31 generally excludes inoculation or vaccination except post-bite treatment and medical treatment for therapeutic reasons; the complete official bundle does not state explicit precedence resolving this decision-critical overlap.

Rule encoding record (does not determine fact support): maternity_and_newborn: newborn: needs_prospectus: the Delivery and New Born table in the core wording and CIS states newborn-cover limits for INR 5,00,000, INR 7,50,000, INR 10,00,000 to INR 25,00,000, and INR 50,00,000 to INR 1,00,00,000, but provides no newborn-cover limit or stated unavailability for Sum Insured values above INR 25,00,000 and below INR 50,00,000.

Rule encoding record (does not determine fact support): maternity_and_newborn: newborn: maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: table cell 0 axis sum_insured_band has the wrong code namespace.; maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: table cell 1 axis sum_insured_band has the wrong code namespace.; maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: table cell 2 axis sum_insured_band has the wrong code namespace.; maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band: table cell 3 axis sum_insured_band has the wrong code namespace.

Rule encoding record (does not determine fact support): maternity_and_newborn: newborn: maternity_and_newborn.limit.newborn_vaccination_limit_by_sum_insured_band: maternity_and_newborn.limit.newborn_vaccination_limit_by_sum_insured_band: table cell 0 axis sum_insured_band has the wrong code namespace.; maternity_and_newborn.limit.newborn_vaccination_limit_by_sum_insured_band: table cell 1 axis sum_insured_band has the wrong code namespace.

Rule encoding record (does not determine fact support): maternity_and_newborn.eligibility.newborn_born_during_policy_and_age_up_to_90_days

Rule encoding record (does not determine fact support): The cited passage defines “New Born Baby”; it does not itself determine eligibility for newborn cover. Eligibility also depends on the Section II.14 conditions, including an admissible delivery claim and the applicable special conditions.

Rule encoding record (does not determine fact support): maternity_and_newborn.eligibility.newborn_parent_coverage_and_continuity_conditions: applies_when.arguments[1].members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): maternity_and_newborn.eligibility.newborn_parent_coverage_and_continuity_conditions: applies_when.arguments[1].members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): maternity_and_newborn.waiting_period.newborn_24_month_wait_and_restart_after_delivery_claim

Rule encoding record (does not determine fact support): The source requires 24 months from first commencement and continuous renewal with the Company. The candidate has no required continuous-renewal/continuous-coverage input or applicability condition, so it can represent the waiting period as satisfied despite a break in renewal.

Rule encoding record (does not determine fact support): maternity_and_newborn.coverage.newborn_hospital_treatment_after_admissible_delivery_claim

Rule encoding record (does not determine fact support): For a policy term exceeding one year, the source restricts newborn treatment expenses to the earlier of policy expiry or the policy anniversary. The candidate tests only that the policy is in force and therefore can grant newborn treatment after the relevant anniversary while a multi-year policy remains in force.

Rule encoding record (does not determine fact support): maternity_and_newborn.coverage.newborn_vaccination_until_one_year_after_admitted_delivery_claim

Rule encoding record (does not determine fact support): The candidate does not require that the baby meets the policy’s New Born Baby definition (born during the Policy Period and aged up to 90 days). It also encodes age as less than or equal to 12 elapsed months, whereas the source says vaccination is payable only until the baby completes one year of age; the inclusive completion-day boundary is not supported.

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.newborn_pre_post_hospitalization_and_cash_not_applicable: effects[0].expense_predicate.members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.newborn_pre_post_hospitalization_and_cash_not_applicable: effects[0].expense_predicate.members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.newborn_pre_post_hospitalization_and_cash_not_applicable: effects[0].expense_predicate.members[2] has an incompatible dimension

Rule encoding record (does not determine fact support): maternity_and_newborn.exclusion.newborn_congenital_conditions_outside_section_ii_14_extent

Rule encoding record (does not determine fact support): The source treats congenital internal disease or defect as a listed condition subject to the specified-disease waiting period, except to the Section II.14 newborn extent. It does not impose a blanket exclusion for internal congenital disease or defect. Only congenital external conditions, defects, or anomalies are stated as an exclusion subject to that exception.

Rule encoding record (does not determine fact support): Independent review found additional source-supported rules missing from extraction: maternity_and_newborn.limit.newborn_treatment_limit_by_sum_insured_band, maternity_and_newborn.limit.newborn_vaccination_limit_by_sum_insured_band, maternity_and_newborn.exclusion.newborn_external_congenital_conditions_outside_section_ii_14, maternity_and_newborn.waiting_period.newborn_internal_congenital_condition_24_month_wait

Retained verified rule IDs (partial encodings may not cover the complete fact): `299aa445-8a68-465f-b6a9-23aa796943d0`, `2cdb360c-7505-4d7a-9efd-837b9492c800`.

### restoration

Status: **supported**.

Value: For the selected base policy without optional covers, the policy automatically restores 100% of the Basic Sum Insured once during the Policy Period, immediately upon exhaustion of the Basic Sum Insured and any accrued Cumulative Bonus. The restored Sum Insured may be used for a subsequent hospitalization, including for the same illness or disease for which an earlier claim was made. Restoration is available only for Sections II.1, II.3, II.5, II.6, II.7, II.8 and II.11. A continuous period of illness, including a relapse within 45 days from the date of the last consultation with the Hospital/Nursing Home where treatment was taken, is considered the same hospitalization under the Any one Illness definition, and any claim under restoration is subject to that definition.

Condition: Restoration is triggered upon exhaustion of the Basic Sum Insured and any accrued Cumulative Bonus. (quotes 1).

Condition: The restoration amount is 100% of the Basic Sum Insured, is restored immediately, and is available once during the Policy Period. (quotes 1).

Condition: The restored Sum Insured may be used for a subsequent hospitalization, including for an illness or disease for which an earlier claim was made. (quotes 2).

Condition: Restoration is available only for Sections II.1, II.3, II.5, II.6, II.7, II.8 and II.11. (quotes 3).

Condition: Hospitalization due to a continuous period of illness, including relapse within 45 days from the last consultation with the Hospital/Nursing Home where treatment was taken, is considered the same hospitalization under the Any one Illness definition. (quotes 4).

Condition: Any claim payable under restoration is subject to the Any one Illness definition. (quotes 5).

Note: Selected variant is the base policy without optional covers; optional covers are unselected.

Note: The restoration benefit remains subject to the policy terms and the Any one Illness definition.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[2] has an incompatible dimension

Rule encoding record (does not determine fact support): restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[3] has an incompatible dimension

Rule encoding record (does not determine fact support): restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[4] has an incompatible dimension

Rule encoding record (does not determine fact support): restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[5] has an incompatible dimension

Rule encoding record (does not determine fact support): restoration.restoration.restoration_subsequent_hospitalization_allows_same_or_different_illness: applies_when.arguments[1].members[6] has an incompatible dimension

Retained verified rule IDs (partial encodings may not cover the complete fact): `b356af29-ba2d-4234-9005-404bc4097320`.

Quote 1: [star-comprehensive-base-wording, physical page 13](http://127.0.0.1:3021/evidence/400e7955-2d2c-4501-91e6-b2cdbb8f1e8a); characters [1837, 2027).

```text
There shall be automatic restoration
of the Basic Sum Insured by 100%
immediately upon exhaustion of
the Basic Sum Insured and accrued
Cumulative Bonus if any, once during the
Policy Period.
```

Quote 2: [star-comprehensive-base-wording, physical page 13](http://127.0.0.1:3021/evidence/14e9720b-70b9-4ab8-b03e-a6b0fe75e77c); characters [2028, 2199).

```text
It is made clear that such restored
Sum Insured can be utilized for the
subsequent hospitalization even for the
illness /disease for which claim/s was /
were already made.
```

Quote 3: [star-comprehensive-base-wording, physical page 13](http://127.0.0.1:3021/evidence/b0bde587-be48-44dd-a418-129f3f5e9c49); characters [2200, 2292).

```text
Such restoration will be available for
Sections II.1, II.3, II.5, II.6, II.7, II.8 and II.11
```

Quote 4: [star-comprehensive-base-wording, physical page 13](http://127.0.0.1:3021/evidence/66dd7df5-a8c3-4e44-884d-902d7691e27f); characters [2293, 2553).

```text
Hospitalization due to continuous period
of illness including its relapse within 45
days from the date of last consultation
with the Hospital/Nursing Home where
treatment was taken will be considered
as same hospitalization as per “Any one
Illness” definition.
```

Quote 5: [star-comprehensive-base-wording, physical page 13](http://127.0.0.1:3021/evidence/33f19c05-d1e7-4d74-be8f-2317494895c7); characters [2554, 2662).

```text
Any claim payable
under this benefit shall be subject to the
definition as provided under “Any one
Illness”.
```

### family_floater

Status: **unknown**.

Unknown reason: Quote 7, star-comprehensive-prospectus, physical page 2: Quotation does not occur word for word on its cited raw page.

Unknown reason: 2 count lacks quoted numeric support (digits or words).

Unknown reason: 3 count lacks quoted numeric support (digits or words).

Unknown reason: 18 year lacks quoted numeric support (digits or words).

Unknown reason: 65 year lacks quoted numeric support (digits or words).

Unknown reason: 91 day lacks quoted numeric support (digits or words).

Unknown reason: Quotation does not occur word for word on its cited raw page.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): family_composition: family_floater: family_composition.eligibility.family_floater_self_spouse_up_to_three_children_subject_to_underwriting: rule.applies_when.arguments[3].right.value: 0 count has no matching quoted number and unit; rule.applies_when.arguments[4].right.value: 3 count has no matching quoted number and unit; Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Rule encoding record (does not determine fact support): family_composition: family_floater: family_composition.eligibility.family_floater_adult_entry_age_subject_to_underwriting: Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Rule encoding record (does not determine fact support): family_composition: family_floater: family_composition.eligibility.family_floater_dependent_child_age_and_dependency_subject_to_underwriting: Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Rule encoding record (does not determine fact support): family_composition.definition.family_floater_shared_sum_insured_among_insured_persons: applies_when: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): Independent review found additional source-supported rules missing from extraction: family_composition.definition.family_floater_dependent_child_definition

### portability

Status: **supported**.

Value: Apply to port the entire policy with all covered family members 30–60 days before renewal. Credits transfer to the extent of the previous sum insured, including no-claim bonus, specific and PED waiting periods, and moratorium.

Condition: The application concerns the entire policy and all covered family members, if any; apply 30–60 days before renewal. (quotes 1).

Condition: Transfer is of credits gained under the previous policy, to the extent of sum insured. (quotes 2).

Note: Application rights and credit transfer do not guarantee underwriting acceptance. Inclusive/exclusive day boundaries are a note.

Note: Reused accepted extraction and independent review; quotations narrowed to exact clauses.

Executable-rule status: **executable**.

Retained verified rule IDs (partial encodings may not cover the complete fact): `a773f2bf-4d94-4b99-9732-ee1a7922f0b4`, `fc935f82-7ae1-4cfe-b67a-70b7ad8975ad`.

Quote 1: [star-comprehensive-customer-information-sheet, physical page 17](http://127.0.0.1:3021/evidence/b0e56bdc-fc1b-4c2d-8d11-28b0ea9dd885); characters [1319, 1638).

```text
The Policyholder has the choice to port his / her policy from one
Insurer to another by applying to such Insurer to port the entire
policy along with all the members of the family, if any, at least
30 days before, but not earlier than 60 days from the policy
renewal date as per IRDAI guidelines related to portability.
```

Quote 2: [star-comprehensive-customer-information-sheet, physical page 17](http://127.0.0.1:3021/evidence/43472171-d92a-4319-9425-8774977f6331); characters [1645, 1920).

```text
The Policyholder is entitled to transfer the credits gained to
the extent of the Sum Insured, No Claim Bonus, Specific
Waiting Periods, Waiting period for Pre-Existing Diseases,
Moratorium period etc. from the existing Insurer to the
Acquiring Insurer in the previous policy.
```

### geography

Status: **supported**.

Value: Health treatments must be taken in India. The personal-accident section has worldwide scope.

Condition: Worldwide scope applies to the personal-accident section, not to the health-treatment territory. (quotes 1, 2).

Note: Reused accepted extraction and independent review; quotations narrowed to exact clauses.

Executable-rule status: **executable**.

Retained verified rule IDs (partial encodings may not cover the complete fact): `b3b53ecb-0dfd-4fc8-83c3-cfc121c903f4`, `8a31bc45-0acd-4447-9489-e19e58e2cbe2`.

Quote 1: [star-comprehensive-base-wording, physical page 44](http://127.0.0.1:3021/evidence/1de6b428-3e4f-4dd2-bd98-34ab62097aca); characters [1258, 1342).

```text
Territorial Limit: All treatments under this
policy shall have to be taken in India.
```

Quote 2: [star-comprehensive-base-wording, physical page 19](http://127.0.0.1:3021/evidence/ce7bc7ec-d1c6-4348-9213-8393795111aa); characters [2566, 2634).

```text
Geographical Scope: The cover under
this Section applies World Wide.
```

### eligibility

Status: **unknown**.

Unknown reason: Quote 9, star-comprehensive-base-wording, physical page 41: Quotation does not occur word for word on its cited raw page.

Unknown reason: Quote 10, star-comprehensive-base-wording, physical page 41: Quotation does not occur word for word on its cited raw page.

Unknown reason: Quotation does not occur word for word on its cited raw page.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_adult_entry_age_and_underwriting_acceptance: applies_when.arguments[2]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[2].members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[2].members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[5]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_renewal_subject_to_product_and_conduct_conditions: applies_when.arguments[0]: comparison requires compatible dimensions

Retained verified rule IDs (partial encodings may not cover the complete fact): `13fe37ff-3ab5-41c2-a816-74d2df971448`.

### no_copay (derived; outside the 13)

Status: **derived**.

Value: No copay is not unconditional. For the selected base policy without optional covers, a mandatory 10% co-payment applies to each and every claim for an Insured Person whose age at entry is 61 years or above, for both fresh and renewal policies. It does not apply to an Insured Person who entered the policy before age 61 and has renewed continuously without any break. The mandatory co-payment applies only to claims under Sections II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8, II.9, II.10, II.11, II.15 and II.25. No voluntary co-payment is selected; that selection does not remove the conditionally applicable mandatory base co-payment.

Condition: The co-payment is 10% of each and every claim amount. (quotes 1, 4).

Condition: It applies to fresh as well as renewal policies when the Insured Person's age at entry is 61 years or above. (quotes 1, 4).

Condition: It does not apply when the Insured Person entered the policy before attaining age 61 and renews continuously without any break. (quotes 2).

Condition: It applies to Sections II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8, II.9, II.10, II.11, II.15 and II.25. (quotes 3).

Condition: The selected variant is the base policy without optional covers; voluntary co-payment is not selected, and this does not negate the mandatory entry-age-based co-payment. (quotes 1, 2, 3, 4).

Executable-rule status: **rule not executable**.

Quote 1: [star-comprehensive-base-wording, physical page 39](http://127.0.0.1:3021/evidence/c668c3fd-87ef-4ae1-a52b-453f43d78004); characters [573, 771).

```text
Co-payment: This policy is subject to
co-payment of 10% of each and every
claim amount for fresh as well as renewal
policies for Insured Persons whose age
at the time of entry is 61 years and above.
```

Quote 2: [star-comprehensive-base-wording, physical page 39](http://127.0.0.1:3021/evidence/c9030eae-ba4a-4bf1-935b-f0174afc9d57); characters [772, 942).

```text
This co-payment will not apply for those
insured persons who have entered
the policy before attaining 61 years of
age and renew the policy continuously
without any break.
```

Quote 3: [star-comprehensive-base-wording, physical page 39](http://127.0.0.1:3021/evidence/9c682f5e-f557-4648-a0b4-be43dec3a3ee); characters [943, 1070).

```text
This co-payment is
applicable for Sections II.1, II.2, II.3, II.4, II.5,
II.6, II.7, II.8, II.9, II.10, II.11, II.15 and II.25.
```

Quote 4: [star-comprehensive-customer-information-sheet, physical page 13](http://127.0.0.1:3021/evidence/e6a35708-f502-4128-816b-077980afb7e4); characters [274, 460).

```text
This policy is subject to co-payment of 10% of each and
every claim amount for fresh as well as renewal policies
for Insured Persons whose age at the time of entry is 61
years and above.
```

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
Brochures and proposal forms remain excluded. Prospectuses remain applicable. Sum insured and eligibility include the complete prospectus on their first call; other criteria add it only when the core evidence lacks the needed definition, table or material information.
