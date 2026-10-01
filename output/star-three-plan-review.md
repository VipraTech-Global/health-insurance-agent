# Star three-plan cited-fact review — Checkpoint 2

Selected variant: **Base policy without optional covers**. Prices and budget remain unavailable.
Comparison support means a source-reviewed plain-English fact with short exact clause quotations. Executable-rule status is separate. No release has been published.
An unknown criterion means source support or independent fact review remains incomplete; a rule encoding failure alone does not make the cell unknown.
Captured manifest SHA-256: `11175393d28fd81b12fb73f6fdeedfb334ce34d1176e6b4b99e2d66d73c939d7`.
Physical PDF pages are used throughout. Character offsets refer to preserved `pdftotext -raw` text and are end-exclusive.

## Validation summary

| Plan | Supported source criteria | Unresolved source criteria | Price |
|---|---:|---:|---|
| Star Comprehensive Insurance Policy | 13/13 | 0/13 | Unavailable |
| Family Health Optima Insurance Plan | 13/13 | 0/13 | Unavailable |
| Star Health Assure Insurance Policy | 12/13 | 1/13 | Unavailable |

Derived `no_copay` and price are outside the 13-criterion denominator.

## Star Comprehensive Insurance Policy

UIN: `SHAHLIP26044V092526`.

Validation job: `952418fb-46e3-46ec-84c7-59b3eddf7dcc` (succeeded). **13/13 supported; 0/13 unresolved.**
Prospectus used for: eligibility, family_floater, newborn, sum_insured.
Prospectus gaps reported but not supplemented: none. See the criterion's unknown reasons below.
Timeout calls across retained and resumed processing: 1.

### sum_insured

Status: **supported**.

Value: For a new purchase of the selected base policy, the available Sum Insured choices are Rs.5,00,000, Rs.7,50,000, Rs.10,00,000, Rs.15,00,000, Rs.20,00,000, Rs.25,00,000, Rs.50,00,000, Rs.75,00,000 and Rs.1,00,00,000. Adult entry eligibility is 18–65 years and dependent-child eligibility is 91 days–25 years. The insurer may require medical underwriting depending on Sum Insured, medical history, zone and age. Reduction or enhancement of the Basic Sum Insured is not a new-purchase alternative: it is permitted only at renewal; enhancement and its amount are at the insurer's discretion, and waiting periods apply afresh to the increased portion. The optional PED waiting-period buy-back and add-on covers are not part of this selected base variant.

Condition: New-purchase eligibility is 18–65 years for adults and 91 days–25 years for dependent children. (quotes 1).

Condition: The insurer may require medical underwriting based on the selected Sum Insured, medical history, zone and age. (quotes 2).

Condition: A Basic Sum Insured reduction or enhancement may be requested only at renewal; enhancement and its amount remain subject to the insurer's discretion. (quotes 4).

Note: The available choices are the enumerated new-purchase Sum Insured options; amounts between those options are not offered choices.

Note: Medical underwriting may be required, and policy issuance remains subject to insurer acceptance and the other policy terms.

Note: Optional PED waiting-period buy-back and add-on covers were unselected and are excluded from this base-variant fact.

Note: Secondary statements omitted from this criterion: Detailed secondary waiting-period recital removed; every offered sum insured, entry condition, renewal-only revision and increased-portion waiting-period condition remains in the core value with exact quotes. The separate waiting-period criteria retain their own cited facts.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Note: note: Pre-policy medical underwriting may be required based on Sum Insured, medical history, zone, and age; acceptance of an enhancement and its amount are at the insurer's discretion.

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

Quote 1: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/af251711-a9dc-45a2-8098-9faa0233a91a); characters [634, 725).

```text
Eligibility
i. For Adults – 18years – 65 years
ii. For Dependent Child - 91 days – 25 years
```

Quote 2: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/5377d39f-0281-4a51-9e76-ab8c355de790); characters [729, 1010).

```text
Medical Underwriting / Pre-Policy Medical Check-up: The company may ask the
members to be proposed to undergo medical underwriting either through medical
tests or any other medium viz tele underwriting etc. This will vary/depend upon the Sum
Insured/ Medical History/ Zone and Age.
```

Quote 3: [star-comprehensive-prospectus, physical page 3](http://127.0.0.1:3021/evidence/d357a6b7-7ef9-45ad-8a8e-0b430bb59df5); characters [293, 446).

```text
Sum Insured Options:
Rs.5,00,000 ; Rs.7,50,000 ; Rs.10,00,000 ; Rs.15,00,000 ; Rs.20,00,000 ; Rs.25,00,000 ; Rs.50,00,000 ;
Rs.75,00,000 ; Rs.1,00,00,000
```

Quote 4: [star-comprehensive-base-wording, physical page 44](http://127.0.0.1:3021/evidence/5d555ab8-60db-4f4d-8ed0-b57e1f9d050a); characters [2191, 2408).

```text
Revision of Sum Insured: Reduction or
enhancement of Basic Sum Insured is
permissible only at the time of renewal.
The acceptance for enhancement and
the amount of enhancement will be at
the discretion of the Company.
```

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

Status: **supported**.

Value: For the selected base policy without optional covers, treatment of a pre-existing disease and its direct complications has a 36-month waiting period of continuous coverage from inception of the first policy with the insurer. If a condition is also subject to the 24-month specified disease/procedure waiting period, the longer waiting period applies. On a Sum Insured enhancement, the relevant waiting periods apply afresh to the increased portion. Under applicable IRDAI portability norms, qualifying prior continuous coverage reduces the PED and specified waiting periods to the extent of prior coverage. The optional buyback reducing the PED waiting period to 12 months is not selected.

Condition: The 36-month PED waiting period applies to treatment of a pre-existing disease and its direct complications and is measured as continuous coverage after inception of the first policy with the insurer. (quotes 1).

Condition: Coverage after the PED waiting period requires the pre-existing disease to have been declared at application and accepted by the insurer. (quotes 2).

Condition: For an enhanced Sum Insured, the PED waiting-period exclusion applies afresh to the increased portion. (quotes 3).

Condition: Prior qualifying continuous coverage under applicable IRDAI portability norms reduces the PED waiting period to the extent of prior coverage. (quotes 4).

Condition: The specified disease/procedure waiting period is 24 months, does not apply to accident claims, and the longer waiting period applies where a listed condition also falls under the PED waiting period. (quotes 5, 6).

Condition: For an enhanced Sum Insured, the specified disease/procedure waiting-period exclusion applies afresh to the increased portion. (quotes 7).

Condition: Prior qualifying continuous coverage under applicable IRDAI portability norms reduces the specified disease/procedure waiting period to the extent of prior coverage. (quotes 8).

Condition: The 12-month PED waiting-period reduction requires selection of the optional cover and payment of additional premium; it does not apply to the selected base variant. (quotes 9).

Note: Selected variant: Base policy without optional covers. The optional 12-month PED buyback is unselected.

Note: Post-waiting-period PED coverage remains subject to declaration at application and insurer acceptance.

Note: note: Post-waiting-period PED coverage is subject to declaration at application and insurer acceptance.

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

Quote 1: [star-comprehensive-base-wording, physical page 31](http://127.0.0.1:3021/evidence/4a60f92f-185c-4aaa-b562-c7105b8393d3); characters [1438, 1665).

```text
Expenses related to the treatment
of a pre-existing Disease (PED)
and its direct complications shall
be excluded until the expiry of 36
months of continuous coverage
after the date of inception of the first
policy with insurer.
```

Quote 2: [star-comprehensive-base-wording, physical page 31](http://127.0.0.1:3021/evidence/78fca988-9c65-47b8-87f1-aaecd8f0c987); characters [2004, 2179).

```text
Coverage under the policy after the
expiry of 36 months for any pre-
existing disease is subject to the
same being declared at the time of
application and accepted by Insurer.
```

Quote 3: [star-comprehensive-base-wording, physical page 31](http://127.0.0.1:3021/evidence/9b371278-56e6-41f5-b4b5-8ad4f19db7fb); characters [1671, 1773).

```text
IncaseofenhancementofSumInsured
the exclusion shall apply afresh to the
extent of Sum Insured increase
```

Quote 4: [star-comprehensive-base-wording, physical page 31](http://127.0.0.1:3021/evidence/32c72afd-849d-4657-904e-4b667f7fe21b); characters [1779, 1998).

```text
If the Insured Person is continuously
covered without any break as
defined under the applicable norms
on portability stipulated by IRDAI,
then waiting period for the same
would be reduced to the extent of
prior coverage
```

Quote 5: [star-comprehensive-base-wording, physical page 31](http://127.0.0.1:3021/evidence/4302cb1b-a2f9-4851-a7ef-2ac2f06deaab); characters [2248, 2535).

```text
Expenses related to the treatment
of the listed Conditions, surgeries/
treatments shall be excluded until
the expiry of 24 months of continuous
coverage after the date of inception
of the first policy with us. This
exclusion shall not be applicable for
claims arising due to an accident.
```

Quote 6: [star-comprehensive-base-wording, physical page 31](http://127.0.0.1:3021/evidence/bd036fd6-ee83-4665-8cf7-42ee451ee56c); characters [2655, 2821).

```text
If any of the specified disease/
procedure falls under the waiting
period specified for pre-Existing
diseases, then the longer of the two
waiting periods shall apply.
```

Quote 7: [star-comprehensive-base-wording, physical page 31](http://127.0.0.1:3021/evidence/a20358ac-4955-4e8a-b9ee-4b71c21780b3); characters [2541, 2649).

```text
In case of enhancement of Sum Insured
the exclusion shall apply afresh to the
extent of Sum Insured increase
```

Quote 8: [star-comprehensive-base-wording, physical page 32](http://127.0.0.1:3021/evidence/2ff623fc-a1ba-4ee2-900e-046998b5964c); characters [318, 533).

```text
If the Insured Person is continuously
covered without any break as defined
undertheapplicablenormsonportability
stipulated by IRDAI, then waiting period
for the same would be reduced to the
extent of prior coverage.
```

Quote 9: [star-comprehensive-base-wording, physical page 30](http://127.0.0.1:3021/evidence/580d47b7-486d-4b44-98ce-94f17543127b); characters [169, 405).

```text
Optional Cover (Buy Back of Pre-Existing
Disease Waiting Period): On payment of
additional premium the Insured Person
has the option to opt for reduction of
waiting period in respect of Pre-Existing
Diseases from 36 months to 12 months.
```

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

Status: **supported**.

Value: The selected base policy covers delivery, including Caesarean delivery and pre-natal/post-natal expenses, subject to per-delivery limits and a lifetime maximum of two deliveries. A 24-month continuous-coverage waiting period applies and restarts after a delivery claim. Both self and spouse must satisfy the stated coverage requirements. Delivery limits by sum insured are: INR 15,000 normal/INR 20,000 Caesarean at INR 5 lakh; INR 25,000/INR 40,000 at INR 7.5 lakh; INR 30,000/INR 50,000 at INR 10–25 lakh; and INR 50,000/INR 100,000 at INR 50 lakh–1 crore. Pre/post-hospitalization and hospital cash do not apply; claims do not reduce sum insured but affect cumulative bonus. Outside Section II.14, childbirth is excluded except ectopic pregnancy; miscarriage is excluded unless due to accident, and lawful medical termination is excluded.

Condition: Delivery expenses are payable while the policy is in force, per delivery, subject to a maximum of two deliveries during the insured person's lifetime. (quotes 1).

Condition: The benefit has a 24-month waiting period from first commencement with continuous renewal, and a fresh 24-month waiting period applies after a delivery claim. (quotes 7).

Condition: Both self and spouse must be covered on a floater or individual basis, both must have 24 months of continuous coverage under this policy, and the policy covering both must be in force when the benefit becomes payable. (quotes 9, 10).

Condition: Pre-hospitalization, post-hospitalization and hospital cash benefits do not apply to this section. (quotes 8).

Condition: Claims under this section do not reduce the sum insured but affect cumulative bonus. (quotes 11).

Condition: Outside Section II.14, childbirth expenses are excluded except ectopic pregnancy; miscarriage is excluded unless due to accident, and lawful medical termination of pregnancy is excluded. (quotes 12, 13).

Note: The selected variant is the base policy without optional covers; the optional buy-back of the pre-existing-disease waiting period is unselected and does not alter these maternity terms.

Note: The source uses Rs. and /- as rupee formats; normalized money quantities are INR amounts.

Note: The delivery/newborn table offers bands at INR 5 lakh, INR 7.5 lakh, INR 10–25 lakh, and INR 50 lakh–1 crore.

Note: Secondary statements omitted from this criterion: Newborn and vaccination statements belong to the separate newborn criterion; delivery limits, lifetime event limit, continuous waiting period, self/spouse conditions and exclusions remain.

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

Quote 1: [star-comprehensive-base-wording, physical page 13](http://127.0.0.1:3021/evidence/6b284f3f-bb61-4c0e-b7f8-8f2e290a7741); characters [2694, 2988).

```text
Expenses for a Delivery including
Delivery by Caesarean Section
(including pre-natal and post-natal
expenses) up to the limits mentioned
in the table below per Delivery,
subject to a maximum of 2 deliveries
in the entire life time of the Insured
Person are payable while the policy
is in force.
```

Quote 2: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/129db5b0-75d9-42ef-9f5d-3d2c6f0c98bf); characters [577, 717).

```text
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
```

Quote 3: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/48599eb2-b5cc-4640-b334-83209101fb5a); characters [718, 757).

```text
5,00,000/- 15,000/- 20,000/- 1,00,000/-
```

Quote 4: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/9ae112c8-3150-4455-8c21-d1c5c9b52e40); characters [758, 797).

```text
7,50,000/- 25,000/- 40,000/- 1,00,000/-
```

Quote 5: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/0bff6acd-9135-45cb-9f67-8ba4b049acee); characters [798, 853).

```text
10,00,000/-
to
25,00,000/-
30,000/- 50,000/- 1,00,000/-
```

Quote 6: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/e9183b67-5521-4c6a-a507-5c39f318076a); characters [854, 913).

```text
50,00,000/-
to
1,00,00,000/-
50,000/- 1,00,000/- 2,00,000/-
```

Quote 7: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/bebedaca-8cad-42cf-a8c2-b96e363e3449); characters [1417, 1710).

```text
Benefit under this Section is subject to
a waiting period of 24 months from the
date of first commencement of Star
Comprehensive Insurance Policy and
its continuous renewal thereof with the
Company. A waiting period of 24 months
will apply afresh following a claim under
Section II.14.A above.
```

Quote 8: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/f2472395-eeee-4e88-9ef8-04dd6d4c288f); characters [1717, 1833).

```text
Pre-hospitalization and Post Hospitalization
expenses and Hospital Cash Benefit are
not applicable for this Section.
```

Quote 9: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/4a9f9f0a-d74f-477a-9526-6398be348f89); characters [1879, 2106).

```text
both Self and Spouse are covered
under this policy either on floater
basis or on individual basis and both
Self and Spouse should have been
covered for a continuous period of 24
months under Star Comprehensive
Insurance Policy,
```

Quote 10: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/89d7ca0a-c034-40d4-99c9-30a6c5b928de); characters [2112, 2217).

```text
the policy covering the self and
spouse are in force when the benefit
under this Section becomes payable.
```

Quote 11: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/f15b151a-956b-42a1-9ff7-13cd12b954cd); characters [2222, 2316).

```text
Claims under this Section
a. will not reduce the Sum Insured;
b. will affect Cumulative Bonus.
```

Quote 12: [star-comprehensive-base-wording, physical page 34](http://127.0.0.1:3021/evidence/8a108a2e-9f2f-4a1e-8156-21901a5b3137); characters [2035, 2246).

```text
Medical treatment expenses traceable
to childbirth (including complicated
deliveries and caesarean Sections
incurred during hospitalization) except
ectopic pregnancy and to the extent
covered under Section II.14
```

Quote 13: [star-comprehensive-base-wording, physical page 34](http://127.0.0.1:3021/evidence/26261d47-1fd3-4c9f-a12e-a47c4ca61cff); characters [2252, 2377).

```text
Expenses towards miscarriage
(unless due to an accident) and
lawful medical termination of
pregnancy during the Policy Period
```

### newborn

Status: **supported**.

Value: For the selected base policy without optional covers, a New Born Baby is a baby born during the Policy Period and aged up to 90 days. Hospital treatment of the newborn for disease, illness (including congenital disorders), or accidental injury is payable within the applicable newborn-cover limit only when the related delivery claim is admissible and the policy is in force. In a multi-year policy, this treatment cover ends at policy expiry or the policy anniversary, whichever is earlier. The delivery/newborn benefit requires both self and spouse to be covered and continuously insured under this product for 24 months; a fresh 24-month wait applies after a delivery claim. Vaccination is covered until age one and addition at renewal, subject to an admitted delivery claim and the policy remaining in force. General dependent-child eligibility begins at 91 days and ends at 25 years. Maternity is otherwise excluded except for ectopic pregnancy and to the extent covered under Section II.14. Claims under the delivery/newborn section do not reduce the Sum Insured and do affect Cumulative Bonus.

Condition: The baby must be born during the Policy Period and be aged up to 90 days. (quotes 1).

Condition: Newborn hospital treatment is payable only if the related delivery claim under Section II.14.A is admissible and the policy is in force. (quotes 2, 3).

Condition: For a Policy Term longer than one year, newborn treatment expenses are payable only until policy expiry or the policy anniversary, whichever occurs earlier. (quotes 4).

Condition: The delivery benefit supporting newborn cover is limited to two deliveries during the Insured Person's lifetime. (quotes 5).

Condition: The benefit has a 24-month waiting period from first commencement with continuous renewal, and a fresh 24-month waiting period applies after a delivery claim. (quotes 14).

Condition: Both self and spouse must be covered, on a floater or individual basis, and both must have 24 months of continuous coverage under this product. (quotes 15).

Condition: The policy covering self and spouse must be in force when the benefit becomes payable. (quotes 16).

Condition: Vaccination is payable only if the related delivery claim is admitted, while the policy is in force, until the baby completes one year and is added at renewal. (quotes 10).

Condition: Congenital internal disease or defect is in the specified-disease waiting-period list, except to the extent provided for a newborn under Section II.14. (quotes 18).

Condition: Congenital external conditions, defects, or anomalies are excluded except to the extent provided for a newborn under Section II.14. (quotes 19).

Condition: General dependent-child eligibility is from 91 days through 25 years. (quotes 20).

Condition: Midterm inclusion is available for a newborn on payment of proportionate premium; waiting periods apply from inclusion and inclusion is subject to underwriting approval. (quotes 21, 22).

Note: The selected variant is the base policy; the optional PED waiting-period buy-back and add-on covers are unselected.

Note: Newborn-cover limits by offered Basic Sum Insured are INR 100,000 for INR 500,000, INR 750,000, and INR 1,000,000 through INR 2,500,000; and INR 200,000 for INR 5,000,000 through INR 10,000,000. The independently stated offered options confirm there is no offered Sum Insured strictly between INR 2,500,000 and INR 5,000,000.

Note: Vaccination limits are INR 5,000 for Basic Sum Insured INR 500,000 through INR 2,500,000 and INR 10,000 above INR 2,500,000.

Note: Claims under the delivery/newborn section do not reduce the Sum Insured but do affect Cumulative Bonus.

Note: Midterm inclusion is subject to underwriting approval and the policy's other terms.

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

Quote 1: [star-comprehensive-base-wording, physical page 6](http://127.0.0.1:3021/evidence/f697f3a1-c6de-415c-8c19-78428a8da3c5); characters [844, 939).

```text
New Born Baby: New Born Baby means baby
born during the Policy Period and is aged up
to 90 days
```

Quote 2: [star-comprehensive-base-wording, physical page 13](http://127.0.0.1:3021/evidence/0e0fcd39-b6d8-46b0-81fc-3402ed7fa2b7); characters [2989, 3073).

```text
B.	
Expenses up to the limits mentioned in
the table below, incurred in a hospital/
```

Quote 3: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/f5a08a61-e0d8-47b9-a39f-dbb82b537766); characters [164, 403).

```text
nursing home on treatment of the New-
born for any disease, illness (including
any congenital disorders) or accidental
injuries are payable provided there is
an admissible claim under Section II.14.A
above and while the policy is in force.
```

Quote 4: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/81cbe736-fb3a-4881-9a09-77cc0738a86e); characters [404, 554).

```text
In case of Policy Term is more than
one year, such expenses are payable
only till the expiry of the policy or policy
anniversary whichever is earlier.
```

Quote 5: [star-comprehensive-base-wording, physical page 13](http://127.0.0.1:3021/evidence/77b88807-0df4-42ca-addb-a0ed1064545a); characters [2864, 2988).

```text
subject to a maximum of 2 deliveries
in the entire life time of the Insured
Person are payable while the policy
is in force.
```

Quote 6: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/129db5b0-75d9-42ef-9f5d-3d2c6f0c98bf); characters [577, 717).

```text
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
```

Quote 7: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/48599eb2-b5cc-4640-b334-83209101fb5a); characters [718, 757).

```text
5,00,000/- 15,000/- 20,000/- 1,00,000/-
```

Quote 8: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/9ae112c8-3150-4455-8c21-d1c5c9b52e40); characters [758, 797).

```text
7,50,000/- 25,000/- 40,000/- 1,00,000/-
```

Quote 9: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/0bff6acd-9135-45cb-9f67-8ba4b049acee); characters [798, 853).

```text
10,00,000/-
to
25,00,000/-
30,000/- 50,000/- 1,00,000/-
```

Quote 10: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/6ef58a23-43cb-4dc5-8a0f-d94ec8b45973); characters [919, 1234).

```text
Vaccination expenses for the new
born baby are payable up to the limits
mentioned in the table below, until the
new born baby completes one year
of age and is added in the policy on
renewal. Claim under this is admissible
only if claim under Section II.14.A above
has been admitted and while the policy
is in force.
```

Quote 11: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/e9183b67-5521-4c6a-a507-5c39f318076a); characters [854, 913).

```text
50,00,000/-
to
1,00,00,000/-
50,000/- 1,00,000/- 2,00,000/-
```

Quote 12: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/8f3743fe-b7f7-48e7-95ca-1c40cc425374); characters [1258, 1303).

```text
Sum Insured Rs.
Limit per Policy Period
(Rs.)
```

Quote 13: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/cd71208a-b340-49da-82f4-6bf566624a1d); characters [1304, 1364).

```text
5,00,000/- to
25,00,000/-
5,000/-
Above 25,00,000/- 10,000/-
```

Quote 14: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/bebedaca-8cad-42cf-a8c2-b96e363e3449); characters [1417, 1710).

```text
Benefit under this Section is subject to
a waiting period of 24 months from the
date of first commencement of Star
Comprehensive Insurance Policy and
its continuous renewal thereof with the
Company. A waiting period of 24 months
will apply afresh following a claim under
Section II.14.A above.
```

Quote 15: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/4a9f9f0a-d74f-477a-9526-6398be348f89); characters [1879, 2106).

```text
both Self and Spouse are covered
under this policy either on floater
basis or on individual basis and both
Self and Spouse should have been
covered for a continuous period of 24
months under Star Comprehensive
Insurance Policy,
```

Quote 16: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/89d7ca0a-c034-40d4-99c9-30a6c5b928de); characters [2112, 2217).

```text
the policy covering the self and
spouse are in force when the benefit
under this Section becomes payable.
```

Quote 17: [star-comprehensive-base-wording, physical page 14](http://127.0.0.1:3021/evidence/f15b151a-956b-42a1-9ff7-13cd12b954cd); characters [2222, 2316).

```text
Claims under this Section
a. will not reduce the Sum Insured;
b. will affect Cumulative Bonus.
```

Quote 18: [star-comprehensive-base-wording, physical page 32](http://127.0.0.1:3021/evidence/4f8a1bc4-e064-4068-8140-1abc4aa6ef72); characters [2318, 2419).

```text
Congenital Internal disease / defect
(except to the extent provided under
Section II.14 for New Born)
```

Quote 19: [star-comprehensive-base-wording, physical page 34](http://127.0.0.1:3021/evidence/cd0960d6-bb1d-40fa-9813-1624104361fe); characters [2641, 2772).

```text
Congenital External Condition / Defects
/ Anomalies (except to the extent
provided under Section II.14 for New Born)
- Code Excl 20
```

Quote 20: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/3f0ebce5-ed95-4beb-bb1c-3076fd6d71d0); characters [646, 725).

```text
i. For Adults – 18years – 65 years
ii. For Dependent Child - 91 days – 25 years
```

Quote 21: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/2f0f2ec0-40e7-4821-8ea0-3b6021282408); characters [1152, 1294).

```text
Midterm Inclusion Facility: Is available on payment of proportionate premium for Newly
Wedded spouse, New born baby and Legally adopted child.
```

Quote 22: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/121715de-ce0e-45e2-9a59-529555d8d2f9); characters [1295, 1528).

```text
Note:
i.	
Waiting periods as stated in the Policy will be applicable from the date of inclusion of
such newly wedded spouse, new born baby, legally adopted child.
ii. Such midterm inclusion will be subject to underwriter’s approval.
```

Quote 23: [star-comprehensive-prospectus, physical page 3](http://127.0.0.1:3021/evidence/d357a6b7-7ef9-45ad-8a8e-0b430bb59df5); characters [293, 446).

```text
Sum Insured Options:
Rs.5,00,000 ; Rs.7,50,000 ; Rs.10,00,000 ; Rs.15,00,000 ; Rs.20,00,000 ; Rs.25,00,000 ; Rs.50,00,000 ;
Rs.75,00,000 ; Rs.1,00,00,000
```

Quote 24: [star-comprehensive-base-wording, physical page 34](http://127.0.0.1:3021/evidence/8a108a2e-9f2f-4a1e-8156-21901a5b3137); characters [2035, 2246).

```text
Medical treatment expenses traceable
to childbirth (including complicated
deliveries and caesarean Sections
incurred during hospitalization) except
ectopic pregnancy and to the extent
covered under Section II.14
```

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

Status: **supported**.

Value: Family floater cover is available. Under a floater policy, one Basic Sum Insured, cumulative bonus and related benefits are shared among all insured persons. Published floater plan types extend through 2A+3C, where A means Adult and C means Child. Adult entry eligibility is 18–65 years; dependent-child entry eligibility is 91 days–25 years. A dependent child must be a natural or legally adopted child who is financially dependent, has no independent income and is not over age 25. A newly wedded spouse, newborn baby or legally adopted child may be included midterm on proportionate premium; policy waiting periods run from that member's inclusion date and inclusion is subject to underwriting approval.

Condition: Adult entry eligibility is from age 18 through age 65. (quotes 3).

Condition: Dependent-child entry eligibility is from 91 days through age 25. (quotes 3).

Condition: A dependent child must be natural or legally adopted, financially dependent, without an independent source of income, and not over age 25. (quotes 1).

Condition: Midterm inclusion is limited to a newly wedded spouse, newborn baby or legally adopted child, requires proportionate premium and underwriting approval, and applicable waiting periods start from inclusion. (quotes 4, 5, 6).

Condition: On a family floater basis, the shared Basic Sum Insured, cumulative bonus and related benefits float among the insured persons. (quotes 2).

Note: The highest published family-floater plan type shown is 2A+3C, with A defined as Adult and C as Child.

Note: Entry eligibility is distinct from continued renewal at later ages.

Note: Midterm inclusion remains subject to underwriting acceptance and the policy's other terms.

Note: Selected variant is the base policy without optional covers; the optional PED waiting-period buyback and add-on covers are unselected.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): family_composition: family_floater: family_composition.eligibility.family_floater_self_spouse_up_to_three_children_subject_to_underwriting: rule.applies_when.arguments[3].right.value: 0 count has no matching quoted number and unit; rule.applies_when.arguments[4].right.value: 3 count has no matching quoted number and unit; Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Rule encoding record (does not determine fact support): family_composition: family_floater: family_composition.eligibility.family_floater_adult_entry_age_subject_to_underwriting: Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Rule encoding record (does not determine fact support): family_composition: family_floater: family_composition.eligibility.family_floater_dependent_child_age_and_dependency_subject_to_underwriting: Rule still has unresolved conditions: Final eligibility cannot be determined until insurer_underwriting_acceptance is known.

Rule encoding record (does not determine fact support): family_composition.definition.family_floater_shared_sum_insured_among_insured_persons: applies_when: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): Independent review found additional source-supported rules missing from extraction: family_composition.definition.family_floater_dependent_child_definition

Quote 1: [star-comprehensive-base-wording, physical page 7](http://127.0.0.1:3021/evidence/8f2dea70-a925-4447-8a5d-f3f6d47abf16); characters [2741, 2909).

```text
Dependent Child means
a child (natural or legally adopted) who is
financially dependent and does not have his
or her independent source of income and
not over 25 years.
```

Quote 2: [star-comprehensive-base-wording, physical page 45](http://127.0.0.1:3021/evidence/9ed1a8ce-338e-49aa-8915-e6c52799d8ce); characters [1128, 1275).

```text
Where the policy is issued on
floater basis, the Basic Sum Insured,
cumulative bonus and other related
benefits floats amongst the Insured
Persons.
```

Quote 3: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/af251711-a9dc-45a2-8098-9faa0233a91a); characters [634, 725).

```text
Eligibility
i. For Adults – 18years – 65 years
ii. For Dependent Child - 91 days – 25 years
```

Quote 4: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/2f0f2ec0-40e7-4821-8ea0-3b6021282408); characters [1152, 1294).

```text
Midterm Inclusion Facility: Is available on payment of proportionate premium for Newly
Wedded spouse, New born baby and Legally adopted child.
```

Quote 5: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/dda18074-3eb9-437a-88c3-58e5dca47d1a); characters [1306, 1458).

```text
Waiting periods as stated in the Policy will be applicable from the date of inclusion of
such newly wedded spouse, new born baby, legally adopted child.
```

Quote 6: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/462bf0e9-fa51-46b4-be67-f106058c8f7a); characters [1463, 1528).

```text
Such midterm inclusion will be subject to underwriter’s approval.
```

Quote 7: [star-comprehensive-prospectus, physical page 52](http://127.0.0.1:3021/evidence/0165667c-1dc0-4878-930d-cd9f6e2d670a); characters [344, 353).

```text
Plan type
```

Quote 8: [star-comprehensive-prospectus, physical page 52](http://127.0.0.1:3021/evidence/1eaf4639-5d52-48fe-aba4-720b09fdbeb3); characters [464, 466).

```text
2A
```

Quote 9: [star-comprehensive-prospectus, physical page 52](http://127.0.0.1:3021/evidence/daa0cbca-6653-4ea2-81f9-6582a479ef30); characters [1193, 1198).

```text
2A+1C
```

Quote 10: [star-comprehensive-prospectus, physical page 52](http://127.0.0.1:3021/evidence/84af2a32-309f-47d8-9b4c-332766db7e24); characters [1947, 1952).

```text
2A+2C
```

Quote 11: [star-comprehensive-prospectus, physical page 52](http://127.0.0.1:3021/evidence/d1bb62e0-8ff1-4f75-ad05-237034222def); characters [2703, 2708).

```text
2A+3C
```

Quote 12: [star-comprehensive-prospectus, physical page 52](http://127.0.0.1:3021/evidence/e8eff439-735d-488e-a2d4-9caa1564b22c); characters [3469, 3486).

```text
A-Adult | C-Child
```

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

Status: **supported**.

Value: For the selected base policy without optional covers, stated entry eligibility is adults aged 18–65 years and dependent children aged 91 days–25 years. A dependent child must be natural or legally adopted, financially dependent, without an independent source of income, and not over age 25. Age alone does not guarantee acceptance: medical underwriting or pre-policy assessment may be required depending on Sum Insured, medical history, zone and age. Midterm inclusion on proportionate premium is available for a newly wedded spouse, New Born Baby or legally adopted child; a New Born Baby must be born during the Policy Period and be aged up to 90 days. Waiting periods apply from the inclusion date, and midterm inclusion is subject to underwriting approval. Renewal is distinct from entry and is available while the product is not withdrawn, except for established fraud, non-disclosure or misrepresentation. If the product is withdrawn, the policyholder is to be provided suitable migration options under the withdrawal clause.

Condition: Adult entry eligibility is from age 18 through age 65. (quotes 1).

Condition: Dependent-child entry eligibility is from 91 days through age 25, subject to the dependent-child definition. (quotes 1, 2).

Condition: Medical underwriting or a pre-policy medical check may be required depending on Sum Insured, medical history, zone and age; age eligibility alone does not imply acceptance. (quotes 3).

Condition: Midterm inclusion is limited to a newly wedded spouse, New Born Baby or legally adopted child and requires proportionate premium. (quotes 4).

Condition: For midterm inclusion as a New Born Baby, the baby must be born during the Policy Period and be aged up to 90 days. (quotes 5).

Condition: For a person added midterm, policy waiting periods apply from that person's inclusion date. (quotes 6).

Condition: Midterm inclusion is subject to underwriting approval. (quotes 7).

Condition: Renewal is available provided the product is not withdrawn, except in cases of established fraud, non-disclosure or misrepresentation by the policyholder. (quotes 8).

Condition: Applies when the product is withdrawn. (quotes 9).

Note: The stated age ranges are entry eligibility ranges and do not constitute automatic acceptance.

Note: The sources do not state that attaining age 65 after entry ends renewal eligibility; renewal remains subject to the renewal clause and other policy terms.

Note: The selected variant is the base policy without the optional Buy Back of Pre-Existing Disease Waiting Period or other optional/add-on covers.

Note: Underwriting approval and acceptance remain within the insurer's stated discretion.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): rule not executable: model wrapper failed RuleV1; intact cited fact retained for exact quotation checks and independent source review.

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_adult_entry_age_and_underwriting_acceptance: applies_when.arguments[2]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[2].members[0] has an incompatible dimension

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[2].members[1] has an incompatible dimension

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_dependent_child_entry_age_relationship_and_underwriting: applies_when.arguments[5]: comparison requires compatible dimensions

Rule encoding record (does not determine fact support): eligibility.eligibility.eligibility_renewal_subject_to_product_and_conduct_conditions: applies_when.arguments[0]: comparison requires compatible dimensions

Retained verified rule IDs (partial encodings may not cover the complete fact): `13fe37ff-3ab5-41c2-a816-74d2df971448`.

Quote 1: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/af251711-a9dc-45a2-8098-9faa0233a91a); characters [634, 725).

```text
Eligibility
i. For Adults – 18years – 65 years
ii. For Dependent Child - 91 days – 25 years
```

Quote 2: [star-comprehensive-base-wording, physical page 7](http://127.0.0.1:3021/evidence/8f2dea70-a925-4447-8a5d-f3f6d47abf16); characters [2741, 2909).

```text
Dependent Child means
a child (natural or legally adopted) who is
financially dependent and does not have his
or her independent source of income and
not over 25 years.
```

Quote 3: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/5377d39f-0281-4a51-9e76-ab8c355de790); characters [729, 1010).

```text
Medical Underwriting / Pre-Policy Medical Check-up: The company may ask the
members to be proposed to undergo medical underwriting either through medical
tests or any other medium viz tele underwriting etc. This will vary/depend upon the Sum
Insured/ Medical History/ Zone and Age.
```

Quote 4: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/2f0f2ec0-40e7-4821-8ea0-3b6021282408); characters [1152, 1294).

```text
Midterm Inclusion Facility: Is available on payment of proportionate premium for Newly
Wedded spouse, New born baby and Legally adopted child.
```

Quote 5: [star-comprehensive-base-wording, physical page 6](http://127.0.0.1:3021/evidence/f697f3a1-c6de-415c-8c19-78428a8da3c5); characters [844, 939).

```text
New Born Baby: New Born Baby means baby
born during the Policy Period and is aged up
to 90 days
```

Quote 6: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/dda18074-3eb9-437a-88c3-58e5dca47d1a); characters [1306, 1458).

```text
Waiting periods as stated in the Policy will be applicable from the date of inclusion of
such newly wedded spouse, new born baby, legally adopted child.
```

Quote 7: [star-comprehensive-prospectus, physical page 2](http://127.0.0.1:3021/evidence/462bf0e9-fa51-46b4-be67-f106058c8f7a); characters [1463, 1528).

```text
Such midterm inclusion will be subject to underwriter’s approval.
```

Quote 8: [star-comprehensive-base-wording, physical page 41](http://127.0.0.1:3021/evidence/00369f5e-862f-4cf2-8af2-900073c131b1); characters [942, 1125).

```text
Renewal of policy: The policy shall
be renewable provided the product
is not withdrawn, except in case of
established fraud or non-disclosure or
misrepresentation by the Policyholder.
```

Quote 9: [star-comprehensive-base-wording, physical page 41](http://127.0.0.1:3021/evidence/2ce1a514-7817-4623-8e2f-5e3a60a52b0e); characters [1126, 1271).

```text
If
theproductiswithdrawn,thepolicyholder
shall be provided with suitable options
to migrate as per the procedure stated
under “withdrawal clause”
```

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

Validation job: `44849fa0-9f39-4232-b409-83df8fa70161` (succeeded). **13/13 supported; 0/13 unresolved.**
Prospectus used for: eligibility, sum_insured.
Prospectus gaps reported but not supplemented: none. See the criterion's unknown reasons below.
Timeout calls across retained and resumed processing: 0.

### sum_insured

Status: **supported**.

Value: For a new purchase, the available Sum Insured choices are INR 5,00,000, INR 10,00,000, INR 15,00,000, INR 20,00,000 and INR 25,00,000. Sum Insured choices of INR 1,00,000, INR 2,00,000, INR 3,00,000 and INR 4,00,000 are available only for renewals. Entry for a new policy is available to persons aged between 18 and 65 years; beyond 65 years, only renewal is allowed. The policy is offered on a floater basis.

Condition: The new-purchase choices are INR 5,00,000, INR 10,00,000, INR 15,00,000, INR 20,00,000 and INR 25,00,000. (quotes 1).

Condition: INR 1,00,000, INR 2,00,000, INR 3,00,000 and INR 4,00,000 are available only for renewals, not as new-purchase choices. (quotes 2).

Condition: A new policy may be taken by a person aged between 18 and 65 years; beyond 65 years, only renewals are allowed. (quotes 3).

Note: The source describes the entry age as between 18 and 65 years and does not separately specify birthday-boundary treatment.

Note: The lower Sum Insured choices are expressly renewal-only.

Note: Optional covers are unselected for this comparison.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-prospectus, physical page 2](http://127.0.0.1:3021/evidence/4cdeb468-5249-42de-aa54-dc13ba6c118c); characters [1272, 1373).

```text
Sum Insured Options: Rs.5,00,000/-, Rs.10,00,000/-, Rs.15,00,000/-, Rs.20,00,000/- and
Rs.25,00,000/-
```

Quote 2: [star-family-health-optima-prospectus, physical page 2](http://127.0.0.1:3021/evidence/9ce36574-9410-474d-b048-ef8d9b36f476); characters [1375, 1498).

```text
Note: Sum Insured options of Rs.1,00,000/-, Rs.2,00,000/-, Rs.3,00,000/- and Rs.4,00,000/-,
are available only for renewals
```

Quote 3: [star-family-health-optima-prospectus, physical page 2](http://127.0.0.1:3021/evidence/d47d86dc-b52d-4944-b803-fe26df370071); characters [399, 694).

```text
Any person aged between 18 years and 65 years can take this insurance for his/her family
consisting of Self, Spouse / Live in partner / Same Sex partner, dependent children not
exceeding three in number, dependent Parents and dependent Parents-in-law. Beyond 65
years, only renewals are allowed.
```

Quote 4: [star-family-health-optima-prospectus, physical page 2](http://127.0.0.1:3021/evidence/908ec11d-8922-4053-a4da-fbe7574c120f); characters [1244, 1267).

```text
Type of Policy: Floater
```

### room_category

Status: **supported**.

Value: For the selected base policy without optional covers, permitted room, boarding and nursing expenses depend on the opted Sum Insured: Rs.1,00,000 and Rs.2,00,000 permit up to Rs.2,000 per day; Rs.3,00,000 and Rs.4,00,000 permit up to Rs.5,000 per day; and Rs.5,00,000, Rs.10,00,000, Rs.15,00,000, Rs.20,00,000 and Rs.25,00,000 permit a Single Standard A/C Room. A Single Standard A/C Room is a single-occupancy air-conditioned room with attached washroom and attendant couch, may have television and/or telephone, and must be the hospital's most economical single-occupancy accommodation; deluxe rooms and suites are excluded from this category. Associated medical expenses are considered proportionately to the eligible room rent or room category stated in the policy schedule, or actuals, whichever is less. Proportionate deduction does not apply where the hospital does not use differential billing or to expenses not differentially billed by room category. Associated medical expenses include applicable nursing charges, operation-theatre charges and professional fees of the hospital's surgeon, anaesthetist, physician or specialist; they exclude pharmacy and consumables, implants and medical devices, diagnostics and ICU charges, so proportionate deduction does not apply to those excluded items. ICU charges are listed as covered in-patient expenses, but no separate ICU room-category or daily ICU monetary limit is stated in the supplied room-limit table.

Condition: The applicable permitted room limit or category is selected by the opted Sum Insured band. (quotes 1).

Condition: A qualifying Single Standard A/C Room must be the most economical single-occupancy accommodation available in the hospital and cannot be a deluxe room or suite. (quotes 2).

Condition: Associated medical expenses are subject to proportionate consideration based on the eligible room rent or room category stated in the policy schedule, or actuals, whichever is less. (quotes 3).

Condition: Proportionate deductions do not apply where the hospital does not follow differential billing or to expenses for which differential billing is not based on room category. (quotes 3).

Condition: Proportionate deduction applies to the specified associated medical expenses but not to pharmacy and consumables, implants and medical devices, diagnostics or ICU charges. (quotes 4).

Condition: ICU charges are included among covered in-patient medical expenses, subject to the policy's general coverage terms and available Sum Insured. (quotes 5).

Note: The selected variant is the base policy without optional covers; the optional voluntary co-payment cover is unselected and does not alter the room-category fact.

Note: The supplied wording identifies ICU charges as covered and excludes them from room-category proportionate deduction, but does not state a separate ICU daily cap in the room-limit table.

Note: Coverage remains subject to the policy's other terms, conditions, exclusions and available Sum Insured.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-base-wording, physical page 10](http://127.0.0.1:3021/evidence/81da7282-60bc-4c8c-928b-712730445f15); characters [164, 365).

```text
Sum Insured (Rs.) Limit (Rs.)
1,00,000/-
Up to 2,000/- per day
2,00,000/-
3,00,000/-
Up to 5,000/- per day
4,00,000/-
5,00,000/-
Single Standard A/C
Room
10,00,000/-
15,00,000/-
20,00,000/-
25,00,000/-
```

Quote 2: [star-family-health-optima-base-wording, physical page 9](http://127.0.0.1:3021/evidence/a3592ab2-9238-484a-9fa6-6aeb6378d38f); characters [628, 980).

```text
Single Standard A/C Room: Single standard
A/C Room means a single occupancy
air-conditioned room with attached wash
roomandacouchfortheattendant.Theroom
may have a television and / or a telephone.
Such room must be the most economical
of all accommodations available in that
hospital as single occupancy. This does not
include a deluxe room or a suite.
```

Quote 3: [star-family-health-optima-base-wording, physical page 10](http://127.0.0.1:3021/evidence/a1ff0a22-e558-4d39-b62b-77e111f9eb92); characters [366, 764).

```text
Note:ExpensesrelatingtoAssociatedmedical
expenses will be considered in proportion to
the eligible room rent/room category stated
in the policy schedule or actuals whichever
is less. Proportionate deductions are not
applied in respect of the hospitals which
do not follow differential billing or for those
expenses in respect of which differential
billing is not adopted based on the room
category.
```

Quote 4: [star-family-health-optima-base-wording, physical page 8](http://127.0.0.1:3021/evidence/c9178f57-3dac-478a-8a4c-67c7ae4114ba); characters [202, 813).

```text
Associated medical expenses: Associated
Medical Expenses means expenses that shall
include the applicable nursing charges, Operation
theatre charges, Professional fees of Medical
Practitioner including Surgeon/ anaesthetist/
Physician/Specialist of the Hospital where the
Insured Person has been admitted and treated
and hence Proportionate deduction will be
applicable on these items.
Associated Medical Expenses does not
include cost of pharmacy and consumables,
cost of implants and medical devices and
cost of diagnostics, ICU charges and hence
proportionate deduction will not be applicable
on these items.
```

Quote 5: [star-family-health-optima-base-wording, physical page 10](http://127.0.0.1:3021/evidence/f7a7e596-11bf-4b9a-acc8-fbc597eff599); characters [846, 1109).

```text
iii.	Anaesthesia, Blood, Oxygen, Operation theatre
charges, ICU charges, Surgical appliances,
Medicines and Drugs, Diagnostic materials
and X-ray, Diagnostic imaging modalities,
dialysis, chemotherapy, radiotherapy, cost
of pacemaker, stent and similar expenses.
```

### copay

Status: **supported**.

Value: The base policy has a mandatory co-payment of 20% of each and every claim amount, for both fresh and renewal policies, when the insured person's age at entry is 61 years or above. It applies to Coverages II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8, II.9, II.11 and II.13. The separately offered voluntary co-payment optional cover is not selected and therefore is not included in this base-policy comparison fact.

Condition: The insured person's age at entry must be 61 years or above. (quotes 1).

Condition: The mandatory co-payment applies to each and every claim amount. (quotes 1).

Condition: The mandatory co-payment applies to both fresh and renewal policies. (quotes 1).

Condition: The mandatory co-payment applies to Coverages II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8, II.9, II.11 and II.13. (quotes 1).

Condition: Voluntary co-payment is offered as an optional cover; it is unselected for the selected base-policy variant. (quotes 2).

Note: The selected variant is the base policy without optional covers; voluntary co-payment is unselected.

Note: No zero co-payment is inferred for insured persons outside the stated mandatory entry-age condition.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-base-wording, physical page 21](http://127.0.0.1:3021/evidence/c7fb3038-22b6-4113-84b5-570da19031c8); characters [1405, 1716).

```text
28.	
Mandatory Co-payment (Applicable for
Coverages II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8,
II.9, II.11 and II.13):
This policy is subject to co-payment of
20% of each and every claim amount for
fresh as well as renewal policies for Insured
Persons whose age at the time of entry is
61 years and above.
```

Quote 2: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/bc19e01c-180d-4dd1-a7ca-3e24c8160954); characters [165, 313).

```text
30.	
Optional Cover - The following Optional
Cover is available on discount as shown
in the Policy Schedule

Option to choose Voluntary Co-payment
```

### deductible

Status: **supported**.

Value: For the selected base policy without optional covers, the deductible is NIL; no deductible amount applies. Optional covers are unselected. The policy separately identifies voluntary co-payment as an optional cover, but that optional cover is not selected and is distinct from the deductible.

Condition: The NIL deductible applies to the selected base policy without optional covers. (quotes 1).

Condition: The voluntary co-payment is identified as an optional cover and is unselected for this comparison. (quotes 2).

Note: NIL is reported as not applicable rather than converted into an invented monetary deductible.

Note: The optional voluntary co-payment is distinct from a deductible and is excluded because optional covers are unselected.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-customer-information-sheet, physical page 12](http://127.0.0.1:3021/evidence/ed10e2bd-8ebd-46fe-bafe-8685372e8012); characters [964, 1171).

```text
iii.	Deductible (It
is a specified
amount: up
to which an
insurance
company will
not pay any
claim, and
which will
be deducted
from total
claim
amount
(if claim
amount is
more than
the specified
amount)
NIL
```

Quote 2: [star-family-health-optima-customer-information-sheet, physical page 12](http://127.0.0.1:3021/evidence/23662334-31db-48c4-b7f4-cc8bc809c82e); characters [488, 542).

```text
Optional Cover:
Option to choose Voluntary Co-payment:
```

### ped_waiting_period

Status: **supported**.

Value: For the selected base policy without optional covers, expenses for treatment of a pre-existing disease and its direct complications are excluded until 36 months of continuous coverage have expired from inception of the first policy with the insurer. There is no entry-age band stated for this waiting period. If Sum Insured is enhanced, the exclusion applies afresh to the increased portion. Prior continuous coverage recognized under applicable IRDAI portability norms reduces the waiting period to the extent of that prior coverage. After 36 months, coverage for a pre-existing disease remains conditional on its declaration at application and acceptance by the insurer. No optional PED waiting-period buyback applies because optional covers are unselected.

Condition: Treatment expenses for a pre-existing disease and its direct complications are excluded until expiry of 36 months of continuous coverage after inception of the first policy with the insurer; the clause states no entry-age band. (quotes 1).

Condition: If Sum Insured is enhanced, the exclusion applies afresh to the increased portion. (quotes 2).

Condition: Continuous prior coverage recognized under applicable IRDAI portability norms reduces the waiting period to the extent of that prior coverage. (quotes 3).

Condition: Coverage after expiry of 36 months is conditional on the pre-existing disease having been declared at application and accepted by the insurer. (quotes 4).

Note: Secondary statements omitted from this criterion: Omit the secondary grace-period coverage sentence; retain the 36-month continuous-coverage PED core and increased-sum-insured, portability and acceptance conditions.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/e6d9dd21-63cd-4b32-aa6a-bf16099d376d); characters [1355, 1584).

```text
a. Expenses related to the treatment of a pre-existing Disease
(PED) and its direct complications shall be excluded until
the expiry of 36 months of continuous coverage after the
date of inception of the first policy with insurer
```

Quote 2: [star-family-health-optima-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/edafdaff-70f4-46f3-8640-6319a165adb3); characters [1585, 1696).

```text
b. In case of enhancement of Sum Insured the exclusion
shall apply afresh to the extent of Sum Insured increase
```

Quote 3: [star-family-health-optima-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/93fe5c04-c5d3-4053-90da-12169a4c5b0d); characters [1697, 1919).

```text
c. If the Insured Person is continuously covered without
any break as defined under the applicable norms on
portability stipulated by IRDAI, then waiting period
for the same would be reduced to the extent of prior
coverage
```

Quote 4: [star-family-health-optima-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/1340c2bf-38f8-4e51-bd52-b502e7122c91); characters [1920, 2096).

```text
d. Coverage under the policy after the expiry of 36
months for any pre-existing disease is subject to the
same being declared at the time of application and
accepted by Insurer
```

### initial_specific_waiting_periods

Status: **supported**.

Value: For the selected base policy without optional covers, illness treatment is subject to an initial 30-day waiting period from first policy commencement, except covered accident claims. The initial waiting period does not apply after more than 12 months of continuous coverage and applies to an enhanced Sum Insured. Separately, the policy has a 24-month waiting period from inception of the first policy with this insurer for listed diseases, procedures and treatments; accident claims are excepted. The specified list broadly covers identified eye/ENT/thyroid/breast conditions, benign lumps and similar pathology, non-accidental musculoskeletal and spinal conditions, hepatobiliary and urinary calculi, hernia and listed umbilical conditions, gynecological conditions other than cancer, prostate and obstructive uropathies, specified male-genital and anorectal conditions, varicose veins or ulcers, transplants, and congenital internal disease or defects except newborn coverage II.19. On Sum Insured enhancement, both waiting periods apply afresh to the increased portion. For a listed condition also treated as pre-existing disease, the longer waiting period applies. The specified waiting period applies even if the condition is contracted after policy commencement or was declared and accepted without a specific exclusion, and qualifying continuous prior coverage under IRDAI portability norms reduces it by the credited prior coverage.

Condition: The 30-day initial waiting period runs from the first policy commencement date and excludes covered accident claims. (quotes 7).

Condition: The initial waiting-period exclusion does not apply after more than 12 months of continuous coverage. (quotes 8).

Condition: The initial waiting period applies to an enhanced Sum Insured. (quotes 9).

Condition: The 24-month specified-condition waiting period runs from inception of the first policy with this insurer and does not apply to accident claims. (quotes 2).

Condition: On enhancement, the specified waiting period applies afresh to the increased portion of Sum Insured. (quotes 3).

Condition: If a listed disease or procedure is also subject to the pre-existing-disease waiting period, the longer waiting period applies. (quotes 4).

Condition: The specified waiting period applies even when the condition is contracted after policy commencement or declared and accepted without a specific exclusion. (quotes 5).

Condition: Continuous prior coverage qualifying under IRDAI portability norms reduces the specified waiting period to the extent of prior coverage. (quotes 6).

Note: Selected variant is the base policy without optional covers; the voluntary co-payment optional cover is unselected and does not modify these waiting-period clauses.

Note: The source says the initial exclusion ceases after continuous coverage for more than twelve months; this is not restated as an inclusive twelve-month boundary.

Note: The full enumerated disease and procedure list remains governed by policy clause III.2; it is summarized here rather than reproduced in full.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Rule encoding record (does not determine fact support): rule not executable: model wrapper failed RuleV1; intact cited fact retained for exact quotation checks and independent source review.

Quote 1: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/9abcb9f3-de4a-46a4-a146-26fbfd5d6e3c); characters [165, 273).

```text
30.	
Optional Cover - The following Optional
Cover is available on discount as shown
in the Policy Schedule
```

Quote 2: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/d9335d4d-f758-469c-b99a-2f7a8069ad19); characters [1911, 2206).

```text
Expenses related to the treatment of the
following listed Conditions, surgeries/
treatments shall be excluded until
the expiry of 24 months of continuous
coverage after the date of inception
of the ﬁrst policy with us. This exclusion
shall not be applicable for claims arising
due to an accident
```

Quote 3: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/a0e3529d-1208-450b-be23-cd277912085b); characters [1330, 1438).

```text
In case of enhancement of Sum
Insured the exclusion shall apply
afresh to the extent of Sum Insured
increase
```

Quote 4: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/15c90631-cbae-4c68-85bb-e5f61b3c0347); characters [2326, 2489).

```text
If any of the speciﬁed disease/
procedure falls under the waiting
period speciﬁed for pre-existing
diseases, then the longer of the two
waiting periods shall apply
```

Quote 5: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/bf6cb657-ac5b-49aa-9c41-1deb2fab09f4); characters [2494, 2630).

```text
Thewaitingperiodforlistedconditions
shall apply even if contracted after
the policy or declared and accepted
without a speciﬁc exclusion
```

Quote 6: [star-family-health-optima-base-wording, physical page 29](http://127.0.0.1:3021/evidence/3e9141e0-eaa7-4e05-99e6-da80d6164361); characters [170, 388).

```text
If the Insured Person is continuously
covered without any break as deﬁned
under the applicable norms on
portability stipulated by IRDAI, then
waiting period for the same would be
reduced to the extent of prior coverage
```

Quote 7: [star-family-health-optima-base-wording, physical page 29](http://127.0.0.1:3021/evidence/c8dba22a-ea23-4b5f-9de3-9d983c7da032); characters [2291, 2477).

```text
Expenses related to the treatment of any
illness within 30 days from the ﬁrst policy
commencement date shall be excluded
exceptclaimsarisingduetoanaccident,
provided the same are covered
```

Quote 8: [star-family-health-optima-base-wording, physical page 29](http://127.0.0.1:3021/evidence/cca1d842-6b92-49c8-ad65-9a6cbd09ef9a); characters [2483, 2597).

```text
This exclusion shall not, however,
apply if the Insured Person has
continuous coverage for more than
twelve months
```

Quote 9: [star-family-health-optima-base-wording, physical page 29](http://127.0.0.1:3021/evidence/750e187d-ebc8-45d7-b22d-2bd51406ec44); characters [2603, 2741).

```text
The within referred waiting period is
made applicable to the enhanced
Sum Insured in the event of granting
higher Sum Insured subsequently
```

Quote 10: [star-family-health-optima-base-wording, physical page 29](http://127.0.0.1:3021/evidence/de8beb69-1ac2-4d21-8b48-73cfde6496b2); characters [434, 591).

```text
TreatmentofCataractanddiseases
of the anterior and posterior
chamber of the Eye, Diseases of ENT,
Diseases related to Thyroid, Benign
diseases of the breast.
```

Quote 11: [star-family-health-optima-base-wording, physical page 29](http://127.0.0.1:3021/evidence/c785f5ad-89f0-471a-bdc4-bd60701b0607); characters [790, 1028).

```text
All treatments (Conservative,
Operative treatment) and all types
of intervention for Diseases related
to Tendon, Ligament, Fascia, Bones
and Joint Including Arthroscopy and
Arthroplasty / Joint Replacement
[other than caused by accident].
```

Quote 12: [star-family-health-optima-base-wording, physical page 29](http://127.0.0.1:3021/evidence/fe47e0eb-5169-422d-acb9-f921ef7f1561); characters [2125, 2245).

```text
All types of transplant and related
surgeries.
14.	
Congenital Internal disease / defect
- (except for coverage II. 19)
```

### maternity

Status: **supported**.

Value: Selected variant: base policy without optional covers. General maternity cover is excluded: medical treatment expenses traceable to childbirth, including complicated deliveries and caesarean sections incurred during hospitalization, are not covered, except ectopic pregnancy. Expenses for miscarriage are excluded unless due to an accident, and expenses for lawful medical termination of pregnancy during the policy period are excluded. Consequently, no general maternity waiting period, maternity monetary benefit, or covered-delivery event count is provided.

Condition: Medical treatment expenses traceable to childbirth, including complicated deliveries and caesarean sections incurred during hospitalization, are excluded; ectopic pregnancy is excepted. (quotes 1).

Condition: Miscarriage expenses are excluded unless due to an accident, and lawful medical termination of pregnancy during the policy period is excluded. (quotes 2).

Note: Secondary statements omitted from this criterion: Keep maternity exclusion and its ectopic-pregnancy/accidental-miscarriage exceptions; newborn and assisted reproduction are separate benefits, whose secondary recital is omitted.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-base-wording, physical page 31](http://127.0.0.1:3021/evidence/75d26eff-45a4-41a5-a6e5-0dcad1da45e3); characters [2254, 2452).

```text
18. Maternity - Code Excl 18
i.	Medical treatment expenses traceable
to childbirth (including complicated
deliveries and caesarean sections
incurred during hospitalization) except
ectopic pregnancy
```

Quote 2: [star-family-health-optima-base-wording, physical page 31](http://127.0.0.1:3021/evidence/66364ba8-1a6c-4079-af75-ed916b6c6f2c); characters [2453, 2578).

```text
ii.	
Expenses towards miscarriage (unless
duetoanaccident)andlawfulmedical
termination of pregnancy during the
Policy Period
```

### newborn

Status: **supported**.

Value: For the selected base policy without optional covers, a New Born Baby means a baby born during the Policy Period and aged up to 90 days. Hospitalization cover starts from the 16th day after birth and continues until the policy expiry date. The benefit is subject to availability of the Sum Insured and is limited to 10% of the Sum Insured or INR 50,000, whichever is less. The mother must have been continuously insured under the policy for 12 months without a break. The birth must be intimated to the insurer and the policy endorsed before cover commences. The 30-day waiting-period exclusion does not apply to the New Born Baby. For treatment related to congenital internal disease or defects of the newborn, the pre-existing-disease exclusion, specified-disease/procedure waiting-period exclusion, 30-day waiting-period exclusion, and the newborn sublimit do not apply. All other policy terms, conditions and exclusions apply. Maternity remains excluded for medical treatment expenses traceable to childbirth, including complicated and caesarean deliveries during hospitalization, except ectopic pregnancy; expenses for miscarriage, unless due to an accident, and lawful medical termination of pregnancy during the Policy Period are also excluded.

Condition: The baby must be born during the Policy Period and be aged up to 90 days. (quotes 1).

Condition: Hospitalization cover starts from the 16th day after birth and continues until the policy expiry date. (quotes 2).

Condition: The benefit is subject to availability of the Sum Insured and is limited to 10% of the Sum Insured or INR 50,000, whichever is less. (quotes 2).

Condition: The mother must have been insured continuously under the policy for 12 months without a break. (quotes 2).

Condition: The birth must be intimated to the insurer and the policy endorsed before cover commences. (quotes 3).

Condition: The 30-day waiting-period exclusion does not apply to the New Born Baby. (quotes 4).

Condition: For treatment related to congenital internal disease or defects of the newborn, Exclusions 1, 2 and 3 and the newborn sublimit do not apply. (quotes 6).

Condition: All other terms, conditions and exclusions apply to the New Born Baby. (quotes 5).

Condition: Maternity expenses remain excluded subject to the ectopic-pregnancy and accident exceptions stated in the policy. (quotes 7, 8).

Note: Selected variant is the base policy without optional covers; the optional voluntary co-payment cover is unselected.

Note: The wording states that cover starts from the 16th day after birth but does not expressly clarify whether that day is counted inclusively.

Note: The phrase 'till the expiry date of the policy' operates together with the definition limiting a New Born Baby to age up to 90 days.

Note: The congenital-internal-disease exception removes the stated newborn sublimit and specified waiting-period exclusions but does not state a replacement numeric limit; all other applicable policy terms remain in force.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-base-wording, physical page 6](http://127.0.0.1:3021/evidence/71cb07cd-9a5e-40e3-a262-0c063cc1ec0c); characters [1700, 1794).

```text
New Born Baby: Newborn baby means baby
born during the Policy Period and is aged
upto 90 days.
```

Quote 2: [star-family-health-optima-base-wording, physical page 17](http://127.0.0.1:3021/evidence/e041a745-5d16-4c0c-8b2a-1a123a2f9f14); characters [2148, 2495).

```text
The coverage for New
Born Baby starts from the 16th day after
its birth till the expiry date of the policy
and is subject to a limit of 10% of the
Sum Insured or Rupees Fifty thousand,
whichever is less, subject to availability of
the Sum Insured, provided the mother is
insured under the policy for a continuous
period of 12 months without break.
```

Quote 3: [star-family-health-optima-base-wording, physical page 17](http://127.0.0.1:3021/evidence/a8c40883-7942-4cfd-bc8c-edcf40ac3560); characters [2506, 2642).

```text
Intimation about the birth of the New Born
Baby should be given to the company
and policy has to be endorsed for this
cover to commence.
```

Quote 4: [star-family-health-optima-base-wording, physical page 17](http://127.0.0.1:3021/evidence/f5a5043d-aa00-44ef-bfb8-346dac1ec162); characters [2649, 2745).

```text
Exclusion no. 3 (Code Excl 03) as stated
under this policy shall not apply for the
New Born Baby
```

Quote 5: [star-family-health-optima-base-wording, physical page 18](http://127.0.0.1:3021/evidence/2f3316d8-3a14-4454-9871-15c0e753fb08); characters [171, 248).

```text
All other terms, conditions and exclusions
shall apply for the New Born Baby.
```

Quote 6: [star-family-health-optima-base-wording, physical page 18](http://127.0.0.1:3021/evidence/bf8e8e1d-bbc6-4ab9-8394-5417f2e6a050); characters [254, 476).

```text
The Exclusion No.1 (Code Excl 01), Exclusion
No.2 (Code Excl 02), Exclusion No.3 (Code
Excl 03) and the above-mentioned
sublimit will not apply for treatment
related to Congenital Internal disease/
defects for the newborn.
```

Quote 7: [star-family-health-optima-base-wording, physical page 31](http://127.0.0.1:3021/evidence/57f6d07c-5e53-40db-985f-842ffc616f10); characters [2287, 2452).

```text
Medical treatment expenses traceable
to childbirth (including complicated
deliveries and caesarean sections
incurred during hospitalization) except
ectopic pregnancy
```

Quote 8: [star-family-health-optima-base-wording, physical page 31](http://127.0.0.1:3021/evidence/f5886007-d9ef-44da-a81f-37537d1b31a7); characters [2459, 2578).

```text
Expenses towards miscarriage (unless
duetoanaccident)andlawfulmedical
termination of pregnancy during the
Policy Period
```

### restoration

Status: **supported**.

Value: For the selected base policy without optional covers, automatic restoration applies to Coverages II.1, II.2, II.3, II.4, II.6, II.7, II.8, II.9, II.11, II.13 and II.19. It restores 100% of the Sum Insured each time, up to three times during the Policy Period, and is available only for Sum Insured options of Rs.3,00,000/- and above. Restoration occurs immediately upon exhaustion of the Limit of Coverage, defined as Sum Insured plus earned Loyalty Bonus wherever applicable; each restoration operates only after the earlier available cover is exhausted. Restored Sum Insured may be used only for an unrelated illness or disease, not the illness or disease for which the earlier claim was made. Continuous illness, including relapse within 45 days from the last consultation at the treating Hospital/Nursing Home, is treated as the same hospitalization. Unused restoration cannot be carried forward, and restoration is unavailable for Modern Treatment. The optional voluntary co-payment cover is not selected.

Condition: Restoration applies only to Coverages II.1, II.2, II.3, II.4, II.6, II.7, II.8, II.9, II.11, II.13 and II.19. (quotes 2).

Condition: The trigger is immediate exhaustion of the Limit of Coverage, meaning Sum Insured plus earned Loyalty Bonus wherever applicable. (quotes 1, 2).

Condition: Restoration is available three times at 100% each time during the Policy Period, and each restoration operates only after exhaustion of the earlier one. (quotes 3).

Condition: Restored Sum Insured may be used only for an illness or disease unrelated to the illness or disease for which an earlier claim was made. (quotes 4).

Condition: A continuous illness, including relapse within 45 days from the last consultation at the treating Hospital/Nursing Home, is considered the same hospitalization under the Any one Illness definition. (quotes 5).

Condition: Unused restored Sum Insured cannot be carried forward. (quotes 4).

Condition: Restoration is not available for Modern Treatment. (quotes 4).

Condition: Restoration is available only for Sum Insured options of Rs.3,00,000/- and above. (quotes 6).

Condition: The voluntary co-payment optional cover is unselected for the selected base-policy variant. (quotes 7).

Note: The restoration amount is stated as 100% of Sum Insured, normalized as ratio 1.

Note: The selected variant is the base policy without the optional voluntary co-payment cover.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-base-wording, physical page 9](http://127.0.0.1:3021/evidence/b3739119-b9cb-4b94-a890-54f59e6b480f); characters [164, 264).

```text
Limit of Coverage: Limit of Coverage means
Sum Insured plus Loyalty Bonus earned
wherever applicable
```

Quote 2: [star-family-health-optima-base-wording, physical page 14](http://127.0.0.1:3021/evidence/97e40a10-5f7a-4b21-ab8d-ac2b20698d4c); characters [2003, 2274).

```text
Automatic Restoration of Sum Insured
(Applicable for Coverages II.1, II.2, II.3, II.4,
II.6, II.7, II.8, II.9, II.11, II.13 and II.19):
There shall be automatic restoration of the
Sum Insured immediately upon exhaustion
of the Limit of Coverage, during the Policy
Period.
```

Quote 3: [star-family-health-optima-base-wording, physical page 14](http://127.0.0.1:3021/evidence/99423a38-8676-4d84-8d6f-df03f3bfc13f); characters [2275, 2443).

```text
Such Automatic Restoration is available 3
times at 100% each time, during the Policy
Period. Each restoration will operate only
after the exhaustion of the earlier one.
```

Quote 4: [star-family-health-optima-base-wording, physical page 14](http://127.0.0.1:3021/evidence/0af1cb90-e355-439f-8221-fa1f1680f46f); characters [2466, 2720).

```text
such restored Sum
Insured can be utilized only for illness /
disease unrelated to the illness / diseases
for which claim/s was / were made. The
unutilized restored Sum Insured cannot be
carried forward. This Benefit is not available
for Modern Treatment.
```

Quote 5: [star-family-health-optima-base-wording, physical page 14](http://127.0.0.1:3021/evidence/c99d29d7-f1a5-4ac4-aa24-0669cfa25130); characters [2721, 2981).

```text
Hospitalization due to continuous period of
illness including its relapse within 45 days
from the date of last consultation with the
Hospital/Nursing Home where treatment
was taken will be considered as same
hospitalization as per “Any one Illness”
definition.
```

Quote 6: [star-family-health-optima-base-wording, physical page 14](http://127.0.0.1:3021/evidence/c02e2cdd-20d1-4a2d-a853-70d1531ffc47); characters [3091, 3203).

```text
Note: Automatic Restoration of Sum Insured
is available only for Sum Insured options
of Rs.3,00,000/- and above.
```

Quote 7: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/abb1238b-7bd5-4173-839f-5e4260106e9d); characters [171, 313).

```text
Optional Cover - The following Optional
Cover is available on discount as shown
in the Policy Schedule

Option to choose Voluntary Co-payment
```

### family_floater

Status: **supported**.

Value: Family floater cover is available: the Sum Insured, Loyalty Bonus and other related benefits float among the insured members named in the policy schedule. Eligible relationships comprise the insured person; spouse, live-in partner or same-sex partner; dependent natural or legally adopted children aged from 16 days to 25 years, limited to no more than three; and dependent parent(s) or parent(s)-in-law. A dependent child must be financially dependent, have no independent source of income and not be over 25 years. At renewal, a covered dependent child above 25 years is renewed on an individual basis. If all covered adults cease to be insured because of death, covered dependent children may continue on an individual basis, subject to proof of death and the proposer having insurable interest. For a two-adult policy covering self and spouse, live-in partner or same-sex partner, death of one adult or divorce or separation results in renewal on an individual basis, subject to proof and identification of the person continuing. Newborn hospitalization cover starts from the 16th day after birth, requires the mother to have been continuously insured for 12 months without break, and requires birth intimation and policy endorsement. The selected variant is the base policy without optional covers; voluntary co-payment is an available optional cover but is not selected.

Condition: The persons actually insured are the persons named in the policy schedule. (quotes 1).

Condition: Eligible family relationships include the insured person, spouse, live-in partner or same-sex partner, dependent parent(s) or parent(s)-in-law, and no more than three dependent children aged from 16 days to 25 years. (quotes 2, 3).

Condition: A dependent child may be natural or legally adopted and must be financially dependent, have no independent source of income and not be over 25 years. (quotes 4).

Condition: The Sum Insured, Loyalty Bonus and other related benefits float among the insured members. (quotes 5).

Condition: At renewal, a covered dependent child above 25 years is renewed on an individual basis. (quotes 6).

Condition: If covered adults cease to be insured because of death, covered dependent children may be renewed individually, subject to proof of death and the proposer having insurable interest. (quotes 7).

Condition: For a two-adult policy covering self and spouse, live-in partner or same-sex partner, death of one adult or divorce or separation results in individual renewal, subject to proof and specification of the person continuing. (quotes 8).

Condition: Newborn hospitalization cover starts from the 16th day after birth, requires the mother to have 12 months of continuous insurance without break, and commences only after birth intimation and policy endorsement. (quotes 9, 10).

Condition: Voluntary co-payment is an optional cover and is unselected for this base-policy comparison. (quotes 11).

Note: The policy wording does not state a separate overall maximum number of family members beyond the express limit of three dependent children.

Note: The policy schedule determines which eligible persons are actually covered.

Note: The age wording states children are between 16 days and 25 years and separately defines a dependent child as not over 25 years; no further inclusive or exclusive boundary interpretation is added.

Note: Newborn cover is also subject to its stated financial sublimit, availability of Sum Insured and other policy terms.

Note: The selected comparison variant excludes all optional covers.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-base-wording, physical page 8](http://127.0.0.1:3021/evidence/90c25a6c-c8b0-4a1d-b166-137ad7e47de9); characters [2462, 2556).

```text
Insured Person: Insured Person means the
name/s of persons named in the schedule of
the Policy
```

Quote 2: [star-family-health-optima-base-wording, physical page 8](http://127.0.0.1:3021/evidence/b053a313-b6a0-46a0-adf2-115436e36a57); characters [1606, 1772).

```text
Family: Family includes Insured Person, Spouse
/ Live in partner / Same Sex partner, dependent
children between 16 days and 25 years of age
not exceeding 3 in number.
```

Quote 3: [star-family-health-optima-base-wording, physical page 8](http://127.0.0.1:3021/evidence/02ff798b-71d3-42a8-aebc-b4b9446ebfd6); characters [1773, 1807).

```text
Dependent Parent
/ Parents in law.
```

Quote 4: [star-family-health-optima-base-wording, physical page 8](http://127.0.0.1:3021/evidence/5499290a-bec2-4c2d-b892-3fae893dfe53); characters [1176, 1361).

```text
Dependent Child: Dependent child means
a child (natural or legally adopted) who is
financially dependent and does not have his
/ her independent sources of income and
not over 25 years.
```

Quote 5: [star-family-health-optima-base-wording, physical page 41](http://127.0.0.1:3021/evidence/c26dd448-a724-4b92-b8c6-6cb8f83a619e); characters [1093, 1183).

```text
The Sum Insured, Loyalty Bonus and
other related beneﬁts ﬂoats amongst
the insured members
```

Quote 6: [star-family-health-optima-base-wording, physical page 37](http://127.0.0.1:3021/evidence/c34d6bfb-16ef-4242-bf47-a8b417177af5); characters [853, 1018).

```text
At the time of renewal, if the
dependent child covered under the
policy is above 25 years of age, the
policy shall be renewed on Individual
basis for the said child.
```

Quote 7: [star-family-health-optima-base-wording, physical page 37](http://127.0.0.1:3021/evidence/c1a593ca-fa46-41c9-9ee5-4bf99a238a14); characters [1025, 1409).

```text
If at the time of renewal, adult(s)
insured under the policy cease to be
Insured Person on account of death,
then the dependent child or children
if any covered, shall be insured on
Individual basis. Proof of death has
to be submitted for this purpose.
Proposer (at the time of such renewal
and its subsequent renewals) should
have insurable interest to insure such
child or children.
```

Quote 8: [star-family-health-optima-base-wording, physical page 37](http://127.0.0.1:3021/evidence/656eda43-5e88-4ebd-bc16-1b9c19cf5d6b); characters [1415, 1731).

```text
Where the policy is issued for a family
size of 2A (covering Self and Spouse /
Live in Partner / Same Sex Partners),
in the event of death of one of the
adult or divorce or separation of the
partners, the policy shall be renewed
on Individual basis. Proof of death or
separation has to be submitted for
this purpose.
```

Quote 9: [star-family-health-optima-base-wording, physical page 17](http://127.0.0.1:3021/evidence/e041a745-5d16-4c0c-8b2a-1a123a2f9f14); characters [2148, 2495).

```text
The coverage for New
Born Baby starts from the 16th day after
its birth till the expiry date of the policy
and is subject to a limit of 10% of the
Sum Insured or Rupees Fifty thousand,
whichever is less, subject to availability of
the Sum Insured, provided the mother is
insured under the policy for a continuous
period of 12 months without break.
```

Quote 10: [star-family-health-optima-base-wording, physical page 17](http://127.0.0.1:3021/evidence/a8c40883-7942-4cfd-bc8c-edcf40ac3560); characters [2506, 2642).

```text
Intimation about the birth of the New Born
Baby should be given to the company
and policy has to be endorsed for this
cover to commence.
```

Quote 11: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/abb1238b-7bd5-4173-839f-5e4260106e9d); characters [171, 313).

```text
Optional Cover - The following Optional
Cover is available on discount as shown
in the Policy Schedule

Option to choose Voluntary Co-payment
```

### portability

Status: **supported**.

Value: Under the selected base policy without optional covers, portability is the facility for health insurance policyholders, including all members under family cover, to transfer credits for pre-existing diseases and specific waiting periods from one insurer to another. The policyholder may apply to another insurer to port the entire policy together with all covered family members. The application must be made at least 30 days before, but not earlier than 60 days from, the renewal date, in accordance with IRDAI portability guidelines. Credits transferable to the acquiring insurer are stated to include, to the extent of the Sum Insured, No Claim Bonus, specific waiting periods, the waiting period for pre-existing diseases, and the moratorium period. Where the insured person has continuous coverage without a break under applicable IRDAI portability norms, the specified-disease/procedure and pre-existing-disease waiting periods are reduced to the extent of prior coverage. These provisions establish portability application and credit-transfer rights but do not promise acceptance or issuance by the acquiring insurer.

Condition: The policyholder must apply to the other insurer to port the entire policy along with all family members, if any. (quotes 2).

Condition: The portability application must be made at least 30 days before, but not earlier than 60 days from, the policy renewal date, in accordance with IRDAI portability guidelines. (quotes 2).

Condition: Transferable credits are limited to the extent of the Sum Insured and include No Claim Bonus, specific waiting periods, the pre-existing-disease waiting period, and the moratorium period. (quotes 3).

Condition: Reduction of the specified-disease/procedure waiting period for prior coverage requires continuous coverage without a break under applicable IRDAI portability norms. (quotes 4).

Condition: Reduction of the pre-existing-disease waiting period for prior coverage requires continuous coverage without a break under applicable IRDAI portability norms. (quotes 5).

Note: The wording establishes a right to apply for portability and transfer eligible credits; it does not guarantee underwriting acceptance or issuance by the acquiring insurer.

Note: No entry-age condition is stated in the cited portability provisions.

Note: Selected variant is the base policy without optional covers; the optional voluntary co-payment cover is unselected and is not included in this portability comparison fact.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Note: note: The source grants a choice/right to apply for portability and describes transferable credits and timing; it does not state that the acquiring insurer must accept or issue the ported policy.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-base-wording, physical page 7](http://127.0.0.1:3021/evidence/dcc71f0e-afeb-4c8e-beff-fd923e1ed724); characters [1754, 2010).

```text
Portability: Portability means a facility provided
to the health insurance policyholders (including
all members under family cover), to transfer
the credits gained for, pre-existing diseases
and specific waiting periods from one insurer
to another insurer.
```

Quote 2: [star-family-health-optima-base-wording, physical page 36](http://127.0.0.1:3021/evidence/a5f260de-d2c4-43ae-ae11-c9590359391e); characters [2210, 2529).

```text
The Policyholder has the choice to
port his / her policy from one Insurer
to another by applying to such Insurer
to port the entire policy along with all
the members of the family, if any, at
least 30 days before, but not earlier
than 60 days from the policy renewal
date as per IRDAI guidelines related to
portability.
```

Quote 3: [star-family-health-optima-base-wording, physical page 36](http://127.0.0.1:3021/evidence/11584c31-d07f-40cc-991f-1b7abd72d1d7); characters [2536, 2812).

```text
The Policyholder is entitled to transfer
the credits gained to the extent of the
Sum Insured, No Claim Bonus, Specific
Waiting Periods, Waiting period for Pre-
Existing Diseases, Moratorium period
etc. from the existing Insurer to the
Acquiring Insurer in the previous policy.
```

Quote 4: [star-family-health-optima-base-wording, physical page 29](http://127.0.0.1:3021/evidence/3e9141e0-eaa7-4e05-99e6-da80d6164361); characters [170, 388).

```text
If the Insured Person is continuously
covered without any break as deﬁned
under the applicable norms on
portability stipulated by IRDAI, then
waiting period for the same would be
reduced to the extent of prior coverage
```

Quote 5: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/7f9061c3-b697-4a3f-8c30-84f062b42b59); characters [1444, 1662).

```text
If the Insured Person is continuously
covered without any break as deﬁned
under the applicable norms on
portability stipulated by IRDAI, then
waiting period for the same would be
reduced to the extent of prior coverage
```

### geography

Status: **supported**.

Value: Operative coverage is territorial to India: the general hospitalization cover applies where medically necessary in-patient medical or surgical treatment is taken at a nursing home or hospital in India, and all investigations and treatments under the policy must be taken in India. For the air-ambulance benefit, the Insured Person must be in India and the treatment must be in India only. No overseas-treatment exception is stated. This fact applies to the selected base policy without optional covers.

Condition: Hospitalization cover requires medically necessary in-patient medical or surgical treatment at a nursing home or hospital in India. (quotes 1).

Condition: All investigations and treatments under the policy must be taken in India. (quotes 2).

Condition: Air-ambulance coverage requires the Insured Person to be in India and the treatment to be in India only. (quotes 3).

Note: Secondary statements omitted from this criterion: Omit the secondary premium-zone interpretation; retain the independently supported India-only cover and air-ambulance territory condition.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-base-wording, physical page 9](http://127.0.0.1:3021/evidence/06979d97-53f4-4973-ae15-9181667313da); characters [2037, 2311).

```text
if such disease or injury shall
require the Insured Person, upon the advice of
a duly qualified Medical Practitioner to incur
Hospitalization expenses for Medical / Surgical
treatment at any Nursing Home / Hospital in
India as an In-patient for medically necessary
treatment
```

Quote 2: [star-family-health-optima-base-wording, physical page 40](http://127.0.0.1:3021/evidence/9d399bc2-52d4-4f95-b51d-e01e81ffb3be); characters [2271, 2351).

```text
All investigations/treatments
under this policy shall have to be taken in
India.
```

Quote 3: [star-family-health-optima-base-wording, physical page 12](http://127.0.0.1:3021/evidence/d7ce64a8-c771-4c24-a1f8-f693fab14d4d); characters [2105, 2170).

```text
The Insured Person is in India and the
treatment is in India only
```

### eligibility

Status: **supported**.

Value: For the selected base policy without optional covers, a person aged between 18 and 65 years may apply for this family-floater policy for self, spouse, live-in partner or same-sex partner, up to three dependent children, dependent parents and dependent parents-in-law; beyond 65 years, only renewals are allowed. A dependent child may be natural or legally adopted, must be financially dependent, must not have an independent source of income and must not be over 25 years old. Family eligibility states dependent children are between 16 days and 25 years of age, with no more than three dependent children. Child cover begins from the 16th day after birth and continues until policy expiry, subject to applicable policy limits. If a newborn is less than 16 days old when the policy commences, the proposer may include the child by paying the applicable premium in full, but cover begins only from the 16th day after birth. Age and relationship alone do not guarantee acceptance: the insurer may require medical underwriting through medical tests, tele-underwriting or another medium depending on Sum Insured, medical history, zone and age, and issuance remains subject to the insurer accepting the proposal. At renewal, a covered dependent child above 25 years is renewed on an individual basis. If insured adults cease to be insured because of death, covered dependent children are renewed individually, subject to proof of death and the proposer having an insurable interest. For a two-adult policy covering self and spouse, live-in partner or same-sex partner, death of one adult or divorce or separation of the partners results in renewal on an individual basis, subject to proof and specific identification of the person who will continue cover. Optional voluntary co-payment and add-on covers are unselected and do not form part of this eligibility comparison.

Condition: The applicant age stated for taking the insurance is between 18 and 65 years; beyond 65 years, only renewals are allowed. (quotes 1).

Condition: Eligible family relationships are self, spouse, live-in partner, same-sex partner, no more than three dependent children, dependent parents and dependent parents-in-law. (quotes 1, 3).

Condition: A dependent child may be natural or legally adopted, must be financially dependent, must have no independent source of income and must not be over 25 years old. (quotes 2).

Condition: Dependent children within the family definition are between 16 days and 25 years of age and are limited to three. (quotes 3).

Condition: A child under 16 days at policy commencement may be included by paying the applicable premium in full, but coverage begins only from the 16th day after birth. (quotes 4).

Condition: The insurer may require medical underwriting based on Sum Insured, medical history, zone and age, and policy issuance remains subject to acceptance of the proposal. (quotes 5, 6).

Condition: At renewal, a covered dependent child above 25 years is renewed on an individual basis. (quotes 7).

Condition: If insured adults cease to be insured because of death, covered dependent children are renewed individually, subject to proof of death and the proposer's insurable interest. (quotes 8).

Condition: For a two-adult self-and-partner policy, death of one adult or divorce or separation results in individual-basis renewal, subject to proof and naming the person who will continue. (quotes 9).

Note: The phrase 'between 18 years and 65 years' does not separately state whether each endpoint is inclusive; no different boundary interpretation is inferred.

Note: Age and relationship describe who may apply or be covered but do not by themselves imply acceptance; underwriting and proposal-acceptance discretion are preserved.

Note: Child coverage from the 16th day remains subject to the policy's other terms and applicable limits.

Note: The selected variant is the base policy without optional covers; voluntary co-payment and add-on covers are unselected.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Note: note: The cited prospectus states the 18–65 age range and the insurer's ability to require underwriting based on Sum Insured, medical history, zone, and age; proposal acceptance remains conditional on the insurer.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-family-health-optima-prospectus, physical page 2](http://127.0.0.1:3021/evidence/d47d86dc-b52d-4944-b803-fe26df370071); characters [399, 694).

```text
Any person aged between 18 years and 65 years can take this insurance for his/her family
consisting of Self, Spouse / Live in partner / Same Sex partner, dependent children not
exceeding three in number, dependent Parents and dependent Parents-in-law. Beyond 65
years, only renewals are allowed.
```

Quote 2: [star-family-health-optima-base-wording, physical page 8](http://127.0.0.1:3021/evidence/5499290a-bec2-4c2d-b892-3fae893dfe53); characters [1176, 1361).

```text
Dependent Child: Dependent child means
a child (natural or legally adopted) who is
financially dependent and does not have his
/ her independent sources of income and
not over 25 years.
```

Quote 3: [star-family-health-optima-base-wording, physical page 8](http://127.0.0.1:3021/evidence/978bb899-ba5e-4584-99cc-036bfc86a0b8); characters [1606, 1807).

```text
Family: Family includes Insured Person, Spouse
/ Live in partner / Same Sex partner, dependent
children between 16 days and 25 years of age
not exceeding 3 in number. Dependent Parent
/ Parents in law.
```

Quote 4: [star-family-health-optima-prospectus, physical page 2](http://127.0.0.1:3021/evidence/ff380c92-5aaf-4546-a4fe-967350e6e49e); characters [826, 1175).

```text
If, at the commencement
of the policy, the new born child is less than 16 days of age, the proposer can opt to cover
such new born child also in the same policy by paying the applicable premium in full.
However, the cover for such new born child will commence only from the 16th day of its
birth and will continue till the expiry date of the policy.
```

Quote 5: [star-family-health-optima-prospectus, physical page 2](http://127.0.0.1:3021/evidence/4f0c4e68-d1e0-40e1-879c-3d3482133605); characters [1502, 1783).

```text
Medical Underwriting / Pre-Policy Medical Check-up: The company may ask the members
to be proposed to undergo medical underwriting either through medical tests or any other
medium viz tele underwriting etc. This will vary/depend upon the Sum Insured/ Medical
History/ Zone and Age.
```

Quote 6: [star-family-health-optima-prospectus, physical page 2](http://127.0.0.1:3021/evidence/c0b4e87e-76fb-47ee-b0cc-8c89f1787cb4); characters [1784, 1922).

```text
If we accept the proposal, we will reimburse atleast 50% of the costs incurred by the
member undertaking such Pre-Policy medical check-up.
```

Quote 7: [star-family-health-optima-base-wording, physical page 37](http://127.0.0.1:3021/evidence/c34d6bfb-16ef-4242-bf47-a8b417177af5); characters [853, 1018).

```text
At the time of renewal, if the
dependent child covered under the
policy is above 25 years of age, the
policy shall be renewed on Individual
basis for the said child.
```

Quote 8: [star-family-health-optima-base-wording, physical page 37](http://127.0.0.1:3021/evidence/c1a593ca-fa46-41c9-9ee5-4bf99a238a14); characters [1025, 1409).

```text
If at the time of renewal, adult(s)
insured under the policy cease to be
Insured Person on account of death,
then the dependent child or children
if any covered, shall be insured on
Individual basis. Proof of death has
to be submitted for this purpose.
Proposer (at the time of such renewal
and its subsequent renewals) should
have insurable interest to insure such
child or children.
```

Quote 9: [star-family-health-optima-base-wording, physical page 37](http://127.0.0.1:3021/evidence/9839e4c8-db99-452c-8df2-3188b4e250c1); characters [1415, 1849).

```text
Where the policy is issued for a family
size of 2A (covering Self and Spouse /
Live in Partner / Same Sex Partners),
in the event of death of one of the
adult or divorce or separation of the
partners, the policy shall be renewed
on Individual basis. Proof of death or
separation has to be submitted for
this purpose. Name of the person
proposed to continue cover under this
policy has to be specifically stated at
the time of renewal.
```

### no_copay (derived; outside the 13)

Status: **derived**.

Value: No copay is not unconditional. The base policy has a mandatory co-payment of 20% of each and every claim amount, for both fresh and renewal policies, when the insured person's age at entry is 61 years or above. It applies to Coverages II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8, II.9, II.11 and II.13. The separately offered voluntary co-payment optional cover is not selected and therefore is not included in this base-policy comparison fact.

Condition: The insured person's age at entry must be 61 years or above. (quotes 1).

Condition: The mandatory co-payment applies to each and every claim amount. (quotes 1).

Condition: The mandatory co-payment applies to both fresh and renewal policies. (quotes 1).

Condition: The mandatory co-payment applies to Coverages II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8, II.9, II.11 and II.13. (quotes 1).

Condition: Voluntary co-payment is offered as an optional cover; it is unselected for the selected base-policy variant. (quotes 2).

Executable-rule status: **rule not executable**.

Quote 1: [star-family-health-optima-base-wording, physical page 21](http://127.0.0.1:3021/evidence/c7fb3038-22b6-4113-84b5-570da19031c8); characters [1405, 1716).

```text
28.	
Mandatory Co-payment (Applicable for
Coverages II.1, II.2, II.3, II.4, II.5, II.6, II.7, II.8,
II.9, II.11 and II.13):
This policy is subject to co-payment of
20% of each and every claim amount for
fresh as well as renewal policies for Insured
Persons whose age at the time of entry is
61 years and above.
```

Quote 2: [star-family-health-optima-base-wording, physical page 28](http://127.0.0.1:3021/evidence/bc19e01c-180d-4dd1-a7ca-3e24c8160954); characters [165, 313).

```text
30.	
Optional Cover - The following Optional
Cover is available on discount as shown
in the Policy Schedule

Option to choose Voluntary Co-payment
```

### Price and budget (outside the 13)

**Unavailable.** No approved premium table or quote is available for this base variant.

## Star Health Assure Insurance Policy

UIN: `SHAHLIP26048V032526`.

Validation job: `12c472d3-ea57-4b44-9044-95f51e1c1ecc` (succeeded). **12/13 supported; 1/13 unresolved.**
Prospectus used for: eligibility, sum_insured.
Prospectus gaps reported but not supplemented: none. See the criterion's unknown reasons below.
Timeout calls across retained and resumed processing: 0.

### sum_insured

Status: **supported**.

Value: For a new purchase, the available Sum Insured choices are INR 5 lakh, 7.5 lakh, 10 lakh, 15 lakh, 20 lakh, 25 lakh, 50 lakh, 75 lakh, 1 crore and 2 crore, with Individual Sum Insured and Floater Sum Insured policy types. New-entry age is up to 75 years: floater adults enter from 18 years, floater dependent children from 16 days through 25 years, and individual cover from 91 days. The INR 75 lakh, INR 1 crore and INR 2 crore choices are available at inception only for persons aged up to 65. A dependent child reaching age 26 may continue under floater cover at renewal until marriage; this is renewal continuation rather than new-entry eligibility. Sum Insured reduction or enhancement is available only at renewal, with enhancement acceptance and amount at insurer discretion and subject to Exclusions 01, 02 and 03. Medical underwriting or a pre-policy medical check may be required depending on Sum Insured, medical history, zone and age.

Condition: The INR 75 lakh, INR 1 crore and INR 2 crore choices are available only to persons aged up to 65 at policy inception. (quotes 3).

Condition: For floater cover, new-entry ages are 18 through 75 years for adults and 16 days through 25 years for dependent children. (quotes 4).

Condition: For individual cover, new-entry age is 91 days through 75 years. The source also states requirements for a good-health declaration, pediatrician opinion and central medical underwriting routing. (quotes 5).

Condition: A dependent child reaching age 26 may continue under floater cover at renewal until marriage; this is a renewal continuation provision. (quotes 6).

Condition: Reduction or enhancement of Sum Insured is permitted only at renewal; enhancement acceptance and amount are at insurer discretion and subject to Exclusions 01, 02 and 03. (quotes 7).

Condition: Medical underwriting or a pre-policy medical check may be required depending on Sum Insured, medical history, zone and age. (quotes 8).

Note: The stated upper entry ages are inclusive because the source uses 'Up to'.

Note: The policy schedule determines the Sum Insured actually selected for an issued policy.

Note: Enhancement acceptance and amount remain subject to insurer discretion and the cited exclusions.

Note: Premium-table age bands above 75 do not establish new-purchase eligibility beyond the stated maximum entry age; they may apply to continuing or renewal business.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/a2d03ebe-d995-4a18-a1d2-7a15c8bcb8a8); characters [1200, 1263).

```text
Type of Policy: Individual Sum Insured and Floater Sum Insured.
```

Quote 2: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/1d98bef4-b991-41ee-9317-c44f1c56ecab); characters [1287, 1450).

```text
Rs.5,00,000/-, Rs.7,50,000/-, Rs.10,00,000/-, Rs.15,00,000/-, Rs.20,00,000/-, Rs.25,00,000/-,
Rs.50,00,000/-, Rs.75,00,000/-, Rs.1,00,00,000/- and Rs.2,00,00,000/-
```

Quote 3: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/4bc97229-a6f7-4d98-be32-08cba51b6295); characters [1451, 1642).

```text
Note: Rs.75,00,000/- Rs.1,00,00,000/- and Rs.2,00,00,000/- Sum Insured will be available for
persons aged up to 65 years only. This is applicable only at the time of inception of this
policy.
```

Quote 4: [star-health-assure-prospectus, physical page 2](http://127.0.0.1:3021/evidence/27c0babc-f1a1-451f-83cd-9b851c1d3c6e); characters [1799, 1957).

```text
i. Floater Sum Insured:
a. For Adults – Minimum - 18 years & Maximum - Up to 75 years
b. For Dependent Children - Minimum - 16 days & Maximum - Up to 25 years
```

Quote 5: [star-health-assure-prospectus, physical page 2](http://127.0.0.1:3021/evidence/d8c7c235-f5dc-4737-9878-9daa82a621d8); characters [2130, 2347).

```text
ii. Individual Sum Insured:
a. Minimum - 91 days and Maximum up to 75 years.
b.	
Provided Good Health declaration, Pediatrician Opinion and the proposal should
be routed through our Central Medical Underwriting Team.
```

Quote 6: [star-health-assure-prospectus, physical page 2](http://127.0.0.1:3021/evidence/4791a913-f2c3-4a28-a7e1-d1f3c321923c); characters [1958, 2129).

```text
c.	
In case of dependent children, at the time of renewal when they become 26 years of
age, such children can continue under floater Sum Insured till he/she gets married.
```

Quote 7: [star-health-assure-customer-information-sheet, physical page 18](http://127.0.0.1:3021/evidence/bb043259-3f07-4b49-987a-fac12badbcba); characters [1916, 2215).

```text
Revision of Sum Insured: Reduction or enhancement of
Sum Insured is permissible only at the time of renewal.
The acceptance for enhancement and the amount of
enhancement will be at the discretion of the Company and
subject to Exclusion Code Excl 01, Exclusion Code Excl 02 and
Exclusion Code Excl 03
```

Quote 8: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/c84fa49f-7d95-4c06-9611-939815c8f221); characters [1646, 1916).

```text
MedicalUnderwriting/Pre-PolicyMedicalCheck-up:TheCompanymayaskthemembers
to be proposed to undergo medical underwriting either through medical tests or any other
medium viz tele underwriting etc. This will vary/depend upon the Sum Insured/ Medical
History/ Zone and Age.
```

### room_category

Status: **supported**.

Value: For Sum Insured of Rs.5 lakh or Rs.7.5 lakh, room rent is permitted up to 1% of Sum Insured per day. For Rs.10 lakh, Rs.15 lakh, Rs.20 lakh or Rs.25 lakh, any room is permitted except a suite or above category. For Rs.50 lakh, Rs.75 lakh, Rs.1 crore or Rs.2 crore, any room is permitted. ICU and operation-theatre charges are payable at actuals. Room rent includes associated medical expenses. Where associated medical expenses vary with the occupied room, they are considered proportionately against the room-rent entitlement or actual room rent, whichever is lower; proportionate deduction does not apply where the hospital does not use differential billing or where the expense itself is not billed differentially based on room rent.

Condition: The room category or daily room-rent entitlement depends on the selected Sum Insured band. (quotes 1, 2, 3, 4, 5, 6).

Condition: For the Rs.10 lakh to Rs.25 lakh band, suite and above categories are not permitted. (quotes 2, 5).

Condition: Associated medical expenses that vary by occupied room are subject to proportionate consideration against the stated room-rent entitlement or actuals, whichever is lower. (quotes 8, 9).

Condition: Proportionate deduction is not applied where the hospital does not follow differential billing or where differential billing is not adopted for the expense based on room rent. (quotes 9).

Condition: ICU and operation-theatre charges are payable at actuals. (quotes 10, 11).

Note: The selected variant is the base policy without optional covers.

Note: The policy's definition of Room Rent includes associated medical expenses.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-base-wording, physical page 9](http://127.0.0.1:3021/evidence/e843f1b4-7df6-489d-9d40-2bf495e3e44c); characters [2913, 2939).

```text
Sum
Insured
in lakhs
(Rs.)
```

Quote 2: [star-health-assure-base-wording, physical page 9](http://127.0.0.1:3021/evidence/117cd3cb-90e3-4b15-9ed4-5f6fa942933c); characters [2940, 2973).

```text
5/7.5 10/15/20/25
50/75/100
/ 200
```

Quote 3: [star-health-assure-base-wording, physical page 9](http://127.0.0.1:3021/evidence/b43d95b6-c085-4581-84ad-c3b6f1b5a868); characters [2974, 2992).

```text
Room
Rent
Criteria
```

Quote 4: [star-health-assure-base-wording, physical page 9](http://127.0.0.1:3021/evidence/a261e3f7-f716-430d-b4a3-175034772aba); characters [2993, 3024).

```text
Up to 1%
of Sum
Insured
per day
```

Quote 5: [star-health-assure-base-wording, physical page 9](http://127.0.0.1:3021/evidence/9e756468-5f23-4e39-bd10-7a2574960346); characters [3025, 3066).

```text
Any Room
(Except suite
or above
category)
```

Quote 6: [star-health-assure-base-wording, physical page 9](http://127.0.0.1:3021/evidence/2efa0e68-756c-424f-88ce-8c68aaf43c2e); characters [3067, 3075).

```text
Any room
```

Quote 7: [star-health-assure-base-wording, physical page 7](http://127.0.0.1:3021/evidence/36aabaee-4500-4ceb-9b98-40535c310d80); characters [1754, 1899).

```text
Room Rent: Room Rent means the amount
charged by a Hospital towards Room and
Boarding expenses and shall include the
associated medical expenses.
```

Quote 8: [star-health-assure-base-wording, physical page 9](http://127.0.0.1:3021/evidence/b7f4fcf9-d317-4baf-8681-ba7c4f654d57); characters [3076, 3233).

```text
Note: Associated Medical expenses which
vary based on the room occupied by
the Insured Person will be considered in
proportion to the room rent stated in the
```

Quote 9: [star-health-assure-base-wording, physical page 10](http://127.0.0.1:3021/evidence/0cad4cbf-9674-4240-9198-865232b5cb93); characters [163, 420).

```text
policy schedule or actuals whichever is less.
Proportionate deductions are not applied in
respect of the hospitals which do not follow
differential billing or for those expenses in
respect of which differential billing is not
adopted based on the room rent.
```

Quote 10: [star-health-assure-base-wording, physical page 46](http://127.0.0.1:3021/evidence/5b953336-48fe-497a-aa5c-0dd6a4e69beb); characters [418, 447).

```text
ICU/Operation
Theatre Charges
```

Quote 11: [star-health-assure-base-wording, physical page 46](http://127.0.0.1:3021/evidence/49f17ef3-fab7-44ce-b2a1-c4c045d5f604); characters [448, 455).

```text
Actuals
```

### copay

Status: **supported**.

Value: Base policy: a mandatory 10% copayment applies to each and every claim for an insured person whose age at entry is 61 years or above, for both fresh and renewal policies. No voluntary copayment is selected.

Condition: The copayment applies to each and every claim. (quotes 1).

Condition: The copayment applies to both fresh and renewal policies. (quotes 2).

Condition: The insured person's age at entry must be 61 years or above. (quotes 3).

Note: The selected variant is the base policy without optional covers; voluntary copayment is not selected.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-base-wording, physical page 20](http://127.0.0.1:3021/evidence/26486fc4-14c6-499d-9ae4-2a95d171b717); characters [1289, 1363).

```text
This policy is subject to
co-payment of 10% of each and every
claim amount
```

Quote 2: [star-health-assure-base-wording, physical page 20](http://127.0.0.1:3021/evidence/e805caae-9c59-4da0-aae9-ec377c9a888e); characters [1364, 1401).

```text
for fresh as well as renewal
policies
```

Quote 3: [star-health-assure-base-wording, physical page 20](http://127.0.0.1:3021/evidence/76f45dbe-3ea0-4bef-bffa-6357c26e42a1); characters [1402, 1474).

```text
for Insured Person whose age at
the time of entry is 61 years and above.
```

### deductible

Status: **supported**.

Value: No deductible applies to the selected base policy. The only deductible described is an optional aggregate deductible, and all optional covers are unselected. If chosen, the optional deductible applies on an aggregate basis every Policy Year: for Sum Insured up to Rs.20 lakhs, the options are Rs.50,000 with a 45% premium discount or Rs.1,00,000 with a 55% discount; for Sum Insured above Rs.20 lakhs, the options are Rs.50,000 with a 35% discount or Rs.1,00,000 with a 50% discount.

Condition: The deductible is available only as an optional cover chosen by the insured person; the selected base variant excludes optional covers. (quotes 1).

Condition: If chosen, the optional deductible applies on an aggregate basis every Policy Year. (quotes 7).

Note: The selected variant is the base policy without optional covers; therefore the optional aggregate deductible is not applicable. The source does not state a separate numeric zero deductible.

Note: The percentage figures are premium discounts available only when the corresponding optional deductible is chosen.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Note: note: The source characterizes the deductible as an optional cover that applies only if chosen, and states it is aggregate for every Policy Year; no separate numeric zero deductible is stated. Given the selected base variant has no optional covers, the optional deductible is not applicable.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-customer-information-sheet, physical page 14](http://127.0.0.1:3021/evidence/1175f699-2a72-4624-9380-028a8652f143); characters [352, 528).

```text
Optional Cover to choose Deductible:
If the insured person chooses any of the following deductible,
the Company will provide a discount on premium as per the
table given below;
```

Quote 2: [star-health-assure-customer-information-sheet, physical page 14](http://127.0.0.1:3021/evidence/3192a76d-fc6c-49db-8d92-c154b9b3bb87); characters [529, 585).

```text
Sum Insured
Aggregate Deductible
Option
Discount
offered
```

Quote 3: [star-health-assure-customer-information-sheet, physical page 14](http://127.0.0.1:3021/evidence/03f255d7-e8ac-41e8-8edf-c6ab92e0680a); characters [586, 603).

```text
Up to
Rs.20 Lakhs
```

Quote 4: [star-health-assure-customer-information-sheet, physical page 14](http://127.0.0.1:3021/evidence/68493f3a-d67d-4f09-921d-c51a655f2601); characters [604, 639).

```text
Rs. 50,000/- 45%
Rs. 1,00,000/- 55%
```

Quote 5: [star-health-assure-customer-information-sheet, physical page 14](http://127.0.0.1:3021/evidence/db05310c-964e-46ba-920b-4907414124aa); characters [640, 658).

```text
Above
Rs. 20 Lakhs
```

Quote 6: [star-health-assure-customer-information-sheet, physical page 14](http://127.0.0.1:3021/evidence/7834309c-aed9-4483-a663-48348c53c0d0); characters [659, 694).

```text
Rs. 50,000/- 35%
Rs. 1,00,000/- 50%
```

Quote 7: [star-health-assure-customer-information-sheet, physical page 14](http://127.0.0.1:3021/evidence/87cda64a-2c26-4116-83d1-7ff8331b14a3); characters [695, 773).

```text
Note: This deductible is applicable for every Policy Year (on
Aggregate basis)
```

### ped_waiting_period

Status: **unknown**.

Unknown reason: Quote 3, star-health-assure-base-wording, physical page 27: Quotation does not occur word for word on its cited raw page.

Unknown reason: Quote 4, star-health-assure-base-wording, physical page 27: Quotation does not occur word for word on its cited raw page.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

### initial_specific_waiting_periods

Status: **supported**.

Value: The base policy has a 30-day initial waiting period for illness treatment from the first policy commencement date, except covered accident claims. This initial waiting period does not apply after more than 12 months of continuous coverage and applies to subsequently enhanced Sum Insured. Separately, a 24-month specified-disease/procedure waiting period applies to the policy's listed conditions, surgeries and treatments, broadly including listed eye, ENT, thyroid, breast, benign-lump, musculoskeletal, spinal, hepato-pancreato-biliary, urinary-calculus, hernia, reproductive-system, anorectal, varicose-vein, transplant and congenital-internal disease/defect categories. Accident claims are excepted. For Sum Insured enhancement, the specified waiting period applies afresh to the increase. If a listed condition is also subject to the pre-existing-disease waiting period, the longer period applies. The specified waiting period applies even if the condition arose after policy inception or was declared and accepted without a specific exclusion. Eligible continuous prior coverage under IRDAI portability norms reduces it to the extent of prior coverage.

Condition: The initial waiting period applies to illness treatment within 30 days from first policy commencement; covered accident claims are excepted. (quotes 1).

Condition: The initial waiting period does not apply where the Insured Person has continuous coverage for more than 12 months. (quotes 2).

Condition: The initial waiting period applies to an enhanced Sum Insured when a higher Sum Insured is subsequently granted. (quotes 3).

Condition: The specified-disease/procedure waiting period is 24 months of continuous coverage from inception of the first policy with the insurer and does not apply to accident claims. (quotes 4).

Condition: On enhancement of Sum Insured, the specified waiting period applies afresh to the increased amount. (quotes 5).

Condition: If a listed condition also falls under the pre-existing-disease waiting period, the longer waiting period applies. (quotes 6).

Condition: The specified waiting period applies even if the condition is contracted after policy inception or was declared and accepted without a specific exclusion. (quotes 7).

Condition: Continuous coverage without a break under applicable IRDAI portability norms reduces the specified waiting period to the extent of prior coverage. (quotes 8).

Condition: The listed scope includes transplant-related treatment and congenital internal disease or defect, with the stated unborn and newborn coverage exceptions. (quotes 9).

Note: The specified-disease/procedure scope is the policy's enumerated list and is summarized rather than reproduced in full.

Note: The unborn and newborn exceptions apply only to the congenital-internal disease/defect item as stated in the listed scope.

Note: The selected variant is the base policy without optional covers; the optional aggregate deductible cover is unselected.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/8e38456e-d9ca-4a6b-9688-ed90b84208fb); characters [1058, 1251).

```text
Expenses related to the treatment of any illness within
30 days from the first policy commencement date shall
be excluded except claims arising due to an accident,
provided the same are covered
```

Quote 2: [star-health-assure-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/354cfe46-cc2b-47f5-92b0-459af3a7db14); characters [1255, 1369).

```text
This exclusion shall not, however, apply if the Insured Person
has continuous coverage for more than twelve months
```

Quote 3: [star-health-assure-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/fa4dcc47-8e7c-4a9b-a349-26d9a88efba3); characters [1373, 1511).

```text
The within referred waiting period is made applicable to
the enhanced Sum Insured in the event of granting higher
Sum Insured subsequently
```

Quote 4: [star-health-assure-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/25dedb1b-b0c0-4dad-8ca8-dc2164298444); characters [1566, 1852).

```text
Expenses related to the treatment of the listed Conditions,
surgeries/treatments shall be excluded until the expiry
of 24 months of continuous coverage after the date of
inception of the first policy with us. This exclusion shall not
be applicable for claims arising due to an accident.
```

Quote 5: [star-health-assure-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/aa458242-c7cf-4e5e-8245-12e355b83eef); characters [1856, 1965).

```text
In case of enhancement of Sum Insured the exclusion
shall apply afresh to the extent of Sum Insured increase.
```

Quote 6: [star-health-assure-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/c6e371b5-adc8-4246-943b-724bd4d0599b); characters [1969, 2134).

```text
If any of the specified disease/procedure falls under the
waiting period specified for pre-existing diseases, then
the longer of the two waiting periods shall apply.
```

Quote 7: [star-health-assure-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/7d1230a7-8b45-41af-a9fb-91240b6afc4a); characters [2138, 2281).

```text
The waiting period for listed conditions shall apply even
if contracted after the policy or declared and accepted
without a specific exclusion.
```

Quote 8: [star-health-assure-customer-information-sheet, physical page 8](http://127.0.0.1:3021/evidence/9a6a1365-d5e6-4083-8518-4f0b7d026993); characters [2285, 2505).

```text
If the Insured Person is continuously covered without
any break as defined under the applicable norms on
portability stipulated by IRDAI, then waiting period for the
same would be reduced to the extent of prior coverage.
```

Quote 9: [star-health-assure-customer-information-sheet, physical page 10](http://127.0.0.1:3021/evidence/574834f7-1a72-44ab-b6a0-0e987d24e2a7); characters [149, 343).

```text
12. Varicose veins and Varicose ulcers
13. All types of transplant and related surgeries
14. Congenital Internal disease / defect - [except for Unborn
in Coverage 16 and New Born in Coverage 18]
```

### maternity

Status: **supported**.

Value: The selected base policy covers delivery expenses, including caesarean delivery and prenatal and postnatal expenses, up to 10% of the Sum Insured. The first covered delivery requires 24 months of continuous Star Health Assure coverage; both self and spouse must have been covered continuously for 24 months under individual or floater Sum Insured. The benefit is limited to two deliveries during the insured's lifetime under this policy, with no waiting period for a subsequent eligible delivery. Pre-hospitalization and post-hospitalization expenses are not payable under this benefit. Other maternity expenses remain excluded except to the extent of the delivery benefit, subject to the stated ectopic-pregnancy and accident-related miscarriage exceptions. Newborn hospitalization for disease, illness including congenital disorders, or accidental injury is payable from the first day of birth until policy expiry. The limit is INR 200,000 per policy period for Sum Insured options of INR 5, 7.5, 10, 15, 20 or 25 lakh, and INR 400,000 for options of INR 50, 75, 100 or 200 lakh.

Condition: The first delivery benefit requires 24 months from first commencement of Star Health Assure Insurance Policy with continuous renewal. (quotes 2).

Condition: The benefit is available for a maximum of two deliveries during the insured's lifetime under this policy; there is no waiting period for a subsequent eligible delivery. (quotes 2).

Condition: Both self and spouse must be covered continuously for 24 months under individual or floater Sum Insured. (quotes 3).

Condition: Pre-hospitalization and post-hospitalization expenses are not applicable to the delivery benefit. (quotes 4).

Condition: Maternity expenses are excluded except to the extent covered under Coverage 15; childbirth expenses have the stated ectopic-pregnancy exception, and miscarriage expenses have the stated accident exception. (quotes 5).

Condition: A delivery-expenses claim must be paid under the policy, or the mother must have been continuously covered for 12 months without a break. (quotes 7).

Condition: The newborn monetary sublimits do not apply to treatment related to congenital internal disease or defects. (quotes 11).

Note: This fact describes the selected base policy. The optional aggregate-deductible cover is unselected and is not included.

Note: For newborn hospitalization, the monetary sublimits do not apply to treatment related to congenital internal disease or defects.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-base-wording, physical page 14](http://127.0.0.1:3021/evidence/a83a5dc1-b61d-4b9a-adde-f43c8ee42660); characters [548, 747).

```text
15.	Delivery Expenses: Expenses for a Delivery
including Delivery by Caesarean section
(including pre-natal and postnatal
expenses) up to 10% of the Sum Insured
is payable, subject to the following:
```

Quote 2: [star-health-assure-base-wording, physical page 14](http://127.0.0.1:3021/evidence/bc886888-8b3e-432a-be12-ddc2da895b01); characters [748, 1112).

```text
i. 
Benefit under this section is subject
to a waiting period of 24 months from
the date of first commencement of
Star Health Assure Insurance policy
and its continuous renewal thereof
with the Company.
a. 
This benefit is available only for
a maximum of 2 deliveries in the
life time under this Policy.
b.	
There is no waiting period for
subsequent deliveries.
```

Quote 3: [star-health-assure-base-wording, physical page 14](http://127.0.0.1:3021/evidence/a1f6bec6-0979-40a1-a09a-21b01dbf32c6); characters [1113, 1284).

```text
ii. This cover is available only when
a.	
Both self and spouse are covered
under this policy for a continuous
period of 24 months under Individual
or floater Sum Insured.
```

Quote 4: [star-health-assure-base-wording, physical page 14](http://127.0.0.1:3021/evidence/278104ae-cd61-4a20-ab2d-c7445a01ba7b); characters [1285, 1382).

```text
iii.	
Pre-hospitalization and Post
Hospitalization expenses are not
applicable for this section.
```

Quote 5: [star-health-assure-base-wording, physical page 31](http://127.0.0.1:3021/evidence/273d193c-784d-465a-9cf4-09c370a9a71f); characters [1502, 1885).

```text
18.	
Maternity – Code Excl 18 (Except to the
extent covered under Coverage 15)
i.	
Medical treatment expenses traceable
to childbirth (including complicated
deliveries and caesarean sections
incurred during hospitalization) except
ectopic pregnancy;
ii.	
Expenses towards miscarriage (unless
due to an accident) and lawful medical
termination of pregnancy during the
Policy Period
```

Quote 6: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/fae99931-02b3-431c-81b8-8e66c41381bc); characters [775, 1120).

```text
18.	
Hospitalization expenses for treatment
of New Born Baby: Expenses up to the
limit mentioned in the below given table
incurred in a hospital/ nursing home
on treatment of the New born for any
disease, illness (including any congenital
disorders) or accidental injuries are
payable from Day 1 of its birth till the
expiry date of the policy.
```

Quote 7: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/633285b1-f93e-4128-94eb-2300bb1dcf30); characters [1169, 1349).

```text
i.	
This cover is available only If Delivery
Expenses Claim is paid under this
policy or if Mother is covered under
this policy for a continuous period of
12 months without break.
```

Quote 8: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/053f65b1-d6b0-425b-9b33-e4c085038fdb); characters [2004, 2060).

```text
Sum Insured in
Lakhs (Rs.)
Limit Per Policy
Period (Rs.)
```

Quote 9: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/d7a7d175-a409-40ec-8278-b310f8ae7715); characters [2061, 2087).

```text
5/7.5/10/15/20/25 2,00,000
```

Quote 10: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/d0ef5483-59ad-48c6-89aa-038c95f5d2e8); characters [2088, 2110).

```text
50/75/100/200 4,00,000
```

Quote 11: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/d22291fc-918e-4ac4-9e47-ec7f01182a0d); characters [2111, 2242).

```text
Note: The above mentioned sublimits
will not apply for treatment related to
congenital Internal disease / defects for
the new born.
```

### newborn

Status: **supported**.

Value: Under the selected base policy without optional covers, a New Born Baby is a baby born during the Policy Period and aged up to 90 days. Newborn hospitalization cover applies from Day 1 of birth until the policy expiry date for hospital or nursing-home treatment of disease, illness, congenital disorders or accidental injury. The per-Policy-Period limit is INR 200,000 for offered Sum Insured options of INR 500,000, 750,000, 1,000,000, 1,500,000, 2,000,000 and 2,500,000, and INR 400,000 for offered options of INR 5,000,000, 7,500,000, 10,000,000 and 20,000,000; these sublimits do not apply to congenital internal disease or defects in the newborn. Cover requires either payment of a Delivery Expenses claim under this policy or 12 months of the mother's continuous coverage without break, and the birth must be intimated to the insurer. Exclusions 01, 02, 03 and 20 do not apply to this newborn cover. In subsequent years, the child can be covered up to the Sum Insured without underwriting or entry-age criteria if newborn coverage is selected and premium is paid; enhancement remains subject to underwriting approval. The general Family definition separately includes dependent children from 16 days through age 25, while this specific newborn benefit starts on Day 1.

Condition: The baby must be born during the Policy Period and is treated as a New Born Baby only up to 90 days of age. (quotes 1).

Condition: Hospitalization expenses are payable from Day 1 of birth until the policy expiry date for covered disease, illness, congenital disorders or accidental injury. (quotes 2, 3).

Condition: The newborn cover is available only if a Delivery Expenses claim is paid under this policy or the mother has been covered continuously under this policy for 12 months without break. (quotes 4).

Condition: The birth must be intimated to the company for coverage from the first day of birth. (quotes 5).

Condition: Pre-existing disease exclusion (Excl 01), specified disease/procedure waiting-period exclusion (Excl 02), 30-day waiting-period exclusion (Excl 03), and congenital external condition/defect/anomaly exclusion (Excl 20) do not apply to the newborn cover. (quotes 6).

Condition: In subsequent years, coverage up to the Sum Insured without underwriting and entry-age criteria requires the policyholder to opt for newborn coverage and pay the premium. (quotes 7).

Condition: Any enhancement of Sum Insured is subject to underwriting approval. (quotes 8).

Condition: The newborn sublimits do not apply to treatment related to congenital internal disease or defects. (quotes 12).

Condition: The general Family definition includes dependent children from 16 days through age 25, distinct from the newborn benefit that starts on Day 1. (quotes 3, 13).

Note: The wording defines a New Born Baby as aged up to 90 days and separately states that the hospitalization benefit runs from Day 1 until policy expiry; it does not expressly reconcile benefit continuation if the baby exceeds 90 days before that expiry.

Note: The general Family definition begins dependent-child eligibility at 16 days, but the specific newborn benefit expressly begins on Day 1.

Note: The selected variant is the base policy without optional covers; the optional aggregate-deductible cover is unselected.

Note: Subsequent-year Sum Insured enhancement is subject to underwriting acceptance.

Note: Secondary statement omitted after independent review: Inoculation or vaccination is excluded except for post-bite treatment and medical treatment for therapeutic reasons; the newborn-specific exception identifies Excl 01, Excl 02, Excl 03 and Excl 20, not Excl 31.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Note: drop_secondary: {"indexes":[0],"reason":"The vaccination/inoculation exclusion is unrelated to the newborn criterion and is not needed to state the newborn benefit, conditions, limits, or applicable newborn-specific exclusions."}

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-base-wording, physical page 6](http://127.0.0.1:3021/evidence/2bf98336-da84-44a3-8a8e-2c5d79b044a8); characters [1616, 1711).

```text
New Born Baby: Newborn baby means baby
born during the Policy Period and is aged up
to 90 days.
```

Quote 2: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/36f1a4a7-2906-4b78-93c4-6bf6a9dc70bd); characters [898, 1052).

```text
incurred in a hospital/ nursing home
on treatment of the New born for any
disease, illness (including any congenital
disorders) or accidental injuries are
```

Quote 3: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/0f32f0a3-17d6-40a4-b8ce-319f9c91beb7); characters [1053, 1120).

```text
payable from Day 1 of its birth till the
expiry date of the policy.
```

Quote 4: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/ad5f381f-5847-4142-8457-e3fd87e6067d); characters [1174, 1349).

```text
This cover is available only If Delivery
Expenses Claim is paid under this
policy or if Mother is covered under
this policy for a continuous period of
12 months without break.
```

Quote 5: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/50dc9cc7-030c-4b51-a168-3d0b212ac1f7); characters [1356, 1509).

```text
Intimation about the birth of the
New Born should be given to the
company and the coverage will be
given to the New Born from the first
day of its birth.
```

Quote 6: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/b46cdc81-be56-4d92-aa1c-8d538f28b8fd); characters [1517, 1718).

```text
Exclusion no.1, (Code-Excl 01), Exclusion
no.2 (Code-Excl 02), Exclusion no.3 (Code-
Excl 03) and Exclusion no.20 (Code-Excl
20) as stated under this policy shall not
apply for the New Born baby cover.
```

Quote 7: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/7f95af2e-4591-4558-8411-b96710039895); characters [1725, 1934).

```text
In the subsequent years, the New Born
Baby will be covered up to the Sum
Insured (without any underwriting and
the entry age criteria), if the policy holder
opts the coverage for New Born and pays
the premium.
```

Quote 8: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/90983c76-1975-443c-bff2-24194dbc1e5c); characters [1940, 2003).

```text
Enhancement of Sum Insured is subject
to underwriters approval.
```

Quote 9: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/053f65b1-d6b0-425b-9b33-e4c085038fdb); characters [2004, 2060).

```text
Sum Insured in
Lakhs (Rs.)
Limit Per Policy
Period (Rs.)
```

Quote 10: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/d7a7d175-a409-40ec-8278-b310f8ae7715); characters [2061, 2087).

```text
5/7.5/10/15/20/25 2,00,000
```

Quote 11: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/d0ef5483-59ad-48c6-89aa-038c95f5d2e8); characters [2088, 2110).

```text
50/75/100/200 4,00,000
```

Quote 12: [star-health-assure-base-wording, physical page 16](http://127.0.0.1:3021/evidence/d22291fc-918e-4ac4-9e47-ec7f01182a0d); characters [2111, 2242).

```text
Note: The above mentioned sublimits
will not apply for treatment related to
congenital Internal disease / defects for
the new born.
```

Quote 13: [star-health-assure-base-wording, physical page 8](http://127.0.0.1:3021/evidence/01e811eb-357d-49ec-9bbf-c774c94c90e7); characters [1669, 1845).

```text
Family: Family includes Insured Person,
spouse, dependent children between 16
days and 25 years of age not exceeding 3 in
number, Dependent Parent and Dependent
Parents in law.
```

Quote 14: [star-health-assure-base-wording, physical page 32](http://127.0.0.1:3021/evidence/188e5972-eda3-45bf-a2fa-5a5b6eda4ade); characters [890, 1017).

```text
Inoculation or Vaccination (except for post–
bite treatment and for medical treatment
for therapeutic reasons) - Code - Excl 31
```

### restoration

Status: **supported**.

Value: Under the selected base policy, the Sum Insured is automatically restored an unlimited number of times, up to 100% each time. Restoration triggers immediately upon partial or full utilization: partial utilization restores the amount utilized, and full utilization restores 100%. The restored amount is available for all claims, including modern treatment, but only for a subsequent hospitalization, and restoration cannot pay more than the Sum Insured for one claim. A subsequent claim may concern the same or a different illness, but a continuous illness, including relapse within 45 days from the last consultation with the treating Hospital/Nursing Home, is treated as the same hospitalization.

Condition: Restoration can be utilized only for a subsequent hospitalization. (quotes 2, 3, 6).

Condition: Partial utilization restores the extent utilized, while full utilization restores 100% of the Sum Insured. (quotes 4, 5).

Condition: The restored Sum Insured can be used for all claims, including modern treatment. (quotes 6).

Condition: The maximum payable for a single claim under restoration cannot exceed the Sum Insured. (quotes 7).

Condition: Hospitalization for a continuous illness, including relapse within 45 days from the last consultation with the treating Hospital/Nursing Home, is considered the same hospitalization under the Any one Illness definition. (quotes 8).

Condition: The restoration illustration identifies a subsequent claim as potentially being for the same or a different illness, subject to the operative subsequent-hospitalization and Any one Illness conditions. (quotes 9, 10).

Note: The frequency is stated as unlimited rather than as a finite numeric count.

Note: The same-or-different-illness statement appears in the insurer's restoration illustration; operative use remains subject to the subsequent-hospitalization requirement and the Any one Illness definition.

Note: The selected variant is the base policy without optional covers; the optional aggregate-deductible cover is unselected.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Note: note: The operative restoration clause supports unlimited restoration up to 100% each time, immediate triggering after partial/full utilization, partial restoration to the utilized extent, full restoration to 100%, subsequent-hospitalization-only use, all-claims/modern-treatment use, and the single-claim cap. The same/different-illness wording is illustrated in the insurer’s restoration example and is appropriately qualified by the candidate with the operative subsequent-hospitalization and Any one Illness conditions.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/a31d66e0-5630-4fdd-bac4-c2c21cfa9c24); characters [322, 452).

```text
Automatic Restoration of Sum Insured:
The policy provides automatic restoration
of Sum Insured subject to the following
condition;
```

Quote 2: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/4de6a765-7330-4a89-9c1c-4fafd6fd7c3c); characters [458, 602).

```text
Sum Insured will be restored unlimited
number of times and maximum up to
100% each time, which can be utilized
for a subsequent hospitalization.
```

Quote 3: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/f29a066b-7064-4a4b-9e62-7854df121c15); characters [609, 756).

```text
The restoration will trigger immediately
upon partial/ full utilization of the Sum
Insured, which can be utilized for a
subsequent hospitalization.
```

Quote 4: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/df58943d-c9cc-4219-92e7-9573541eff5a); characters [764, 855).

```text
On partial utilization of the Sum
Insured, it will be restored up to
extent of utilization.
```

Quote 5: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/816cf854-ed77-448b-a1c5-4a8fec2b6534); characters [862, 930).

```text
On full utilization of the Sum Insured,
it will be restored to 100%.
```

Quote 6: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/57f17af3-28b5-43a8-9ebb-6ffabc900973); characters [936, 1057).

```text
The Restored Sum Insured can
be used for all claims including
for modern treatment, but for a
subsequent hospitalization.
```

Quote 7: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/06f072b9-b2d8-4420-b566-ea7478fed5b2); characters [1064, 1175).

```text
The maximum payable amount
for a single claim under restoration
benefit shall not be more than the
Sum Insured.
```

Quote 8: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/7c5b48d8-6c9f-4e6c-bc98-17d4a17bc573); characters [1176, 1436).

```text
Hospitalization due to continuous period
of illness including its relapse within 45
days from the date of last consultation
with the Hospital/Nursing Home where
treatment was taken will be considered
as same hospitalization as per “Any one
Illness” definition.
```

Quote 9: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/611fadc5-e976-429b-bd3b-762e9e403339); characters [1739, 1758).

```text
Insured 1 Insured 2
```

Quote 10: [star-health-assure-base-wording, physical page 13](http://127.0.0.1:3021/evidence/3c97202e-35dd-4c7f-a996-3821119d3b6f); characters [2332, 2372).

```text
2nd
Claim
(For Same
/ different
illness)
```

### family_floater

Status: **supported**.

Value: Family floater cover is available under the base policy. On a floater basis, one shared Sum Insured, cumulative bonus and related benefits float among the insured members. The defined family includes the insured person, spouse, dependent children, dependent parent and dependent parents-in-law. No more than 3 dependent children may be included; they must be between 16 days and 25 years old. A dependent child may be natural or legally adopted and must be financially dependent, have no independent source of income and be no older than 25.

Condition: Dependent children included in the defined family must be between 16 days and 25 years of age, with no more than 3 dependent children. (quotes 2).

Condition: A dependent child must be natural or legally adopted, financially dependent, without an independent source of income, and up to 25 years of age. (quotes 1).

Condition: When the policy is issued on a floater basis, the Sum Insured, cumulative bonus and other related benefits are shared among the insured members. (quotes 3).

Note: This fact describes the selected base policy without optional covers; the optional aggregate-deductible cover is unselected.

Note: The supplied documents establish that family floater cover is offered, but the actual coverage basis and enrolled family members depend on the Policy Schedule.

Note: The wording does not state a separate numeric cap for parents or parents-in-law in the cited family definition.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-base-wording, physical page 8](http://127.0.0.1:3021/evidence/284535f8-90eb-47b8-9450-a4c2c10e85c9); characters [1014, 1203).

```text
Dependent Child: Dependent Child means
a child (natural or legally adopted) who is
financially dependent and does not have his
/ her independent sources of income and up
to 25 years of age.
```

Quote 2: [star-health-assure-base-wording, physical page 8](http://127.0.0.1:3021/evidence/01e811eb-357d-49ec-9bbf-c774c94c90e7); characters [1669, 1845).

```text
Family: Family includes Insured Person,
spouse, dependent children between 16
days and 25 years of age not exceeding 3 in
number, Dependent Parent and Dependent
Parents in law.
```

Quote 3: [star-health-assure-base-wording, physical page 40](http://127.0.0.1:3021/evidence/053e7f99-7c82-4f49-9e02-f9dda47ed730); characters [1131, 1272).

```text
Where the policy is issued on floater
basis, The Sum Insured, cumulative
bonus and other related benefits floats
amongst the insured members.
```

### portability

Status: **supported**.

Value: Portability is the facility to transfer eligible continuity credits when moving a health insurance policy from one insurer to another. The policyholder may apply to port the entire policy, including all family members, to another insurer between 60 and 30 days before renewal. Transferable credits include, to the extent of the Sum Insured, No Claim Bonus, specific waiting periods, the pre-existing-disease waiting period and the moratorium period. Prior-coverage reduction of pre-existing-disease and specified-disease/procedure waiting periods requires continuous coverage without a break under applicable IRDAI portability norms.

Condition: The portability request is for the entire policy together with all family members, if any. (quotes 2).

Condition: The application must be made at least 30 days before, but not earlier than 60 days before, the policy renewal date, in accordance with IRDAI portability guidelines. (quotes 2).

Condition: Credits are transferable only to the extent stated in the policy, including the Sum Insured, No Claim Bonus, specific waiting periods, pre-existing-disease waiting period and moratorium period. (quotes 3).

Condition: Reduction of the pre-existing-disease waiting period for prior coverage requires continuous coverage without a break as defined under applicable IRDAI portability norms. (quotes 4).

Condition: Reduction of the specified-disease/procedure waiting period for prior coverage requires continuous coverage without a break as defined under applicable IRDAI portability norms. (quotes 5).

Note: The wording describes a right to apply for portability and transfer eligible credits; it does not promise acceptance by the acquiring insurer.

Note: The selected variant is the base policy without the optional aggregate deductible cover.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-base-wording, physical page 7](http://127.0.0.1:3021/evidence/75f1bc46-8e3f-4182-99cd-5ce7efb29b25); characters [271, 522).

```text
Portability: Portability means a facility
providedtothehealthinsurancepolicyholders
(including all members under family cover),
to transfer the credits gained for, pre-existing
diseases and specific waiting periods from
one insurer to another insurer.
```

Quote 2: [star-health-assure-base-wording, physical page 36](http://127.0.0.1:3021/evidence/8bef6bf5-eee8-424f-82b7-901cf036ef68); characters [1494, 1813).

```text
The Policyholder has the choice to
port his / her policy from one Insurer
to another by applying to such
Insurer to port the entire policy along
with all the members of the family, if
any, at least 30 days before, but not
earlier than 60 days from the policy
renewal date as per IRDAI guidelines
related to portability.
```

Quote 3: [star-health-assure-base-wording, physical page 36](http://127.0.0.1:3021/evidence/881b740f-6ff9-43e9-b5ec-06e1f78491ec); characters [1819, 2094).

```text
The Policyholder is entitled to transfer
the credits gained to the extent of
the Sum Insured, No Claim Bonus,
Specific Waiting Periods, Waiting
period for Pre-Existing Diseases,
Moratorium period etc. from the
existing Insurer to the Acquiring
Insurer in the previous policy.
```

Quote 4: [star-health-assure-base-wording, physical page 27](http://127.0.0.1:3021/evidence/a89aef2a-49c9-4e59-9dc0-db40a2914413); characters [2080, 2300).

```text
If the Insured Person is continuously
covered without any break as
defined under the applicable norms
on portability stipulated by IRDAI,
then waiting period for the same
would be reduced to the extent of
prior coverage.
```

Quote 5: [star-health-assure-base-wording, physical page 28](http://127.0.0.1:3021/evidence/d93726ad-f885-4ac0-98ca-7fb62b45cd8a); characters [946, 1166).

```text
If the Insured Person is continuously
covered without any break as
defined under the applicable norms
on portability stipulated by IRDAI,
then waiting period for the same
would be reduced to the extent of
prior coverage.
```

### geography

Status: **supported**.

Value: Operative coverage is territorial to India: all investigations and treatments under the base policy must be taken in India. The general hospitalization cover applies to medically necessary inpatient treatment at a nursing home or hospital in India. Air-ambulance cover additionally requires the insured person to be in India and the treatment to be in India. Premium zones are not territorial coverage bands.

Condition: All investigations and treatments under the policy must be taken in India. (quotes 1).

Condition: General hospitalization indemnity applies where medically necessary medical or surgical inpatient treatment is incurred at a nursing home or hospital in India. (quotes 2).

Condition: For air-ambulance expenses, the insured person must be in India and the treatment must be in India. (quotes 3).

Note: The policy's Zone A, Zone B, Zone C and Zone D classifications are premium zones and do not alter the India-only territorial limit.

Note: The selected variant is the base policy without optional covers.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-base-wording, physical page 39](http://127.0.0.1:3021/evidence/12d92a98-e9af-4be8-8781-7a6ee965ac34); characters [2242, 2346).

```text
22.	Territorial Limit: All investigations/treatments
under this policy shall have to be taken
in India.
```

Quote 2: [star-health-assure-base-wording, physical page 9](http://127.0.0.1:3021/evidence/1a4dc433-cd2b-4a9e-a25b-8d5a44362f21); characters [2164, 2312).

```text
Hospitalization expenses for Medical / Surgical
treatment at any Nursing Home / Hospital in
India as an In-patient for medically necessary
treatment
```

Quote 3: [star-health-assure-base-wording, physical page 11](http://127.0.0.1:3021/evidence/587bb852-bbfb-4fff-ae1e-1b99bdb3992b); characters [1226, 1298).

```text
iv.	
The Insured Person is in India and the
treatment is in India only.
```

### eligibility

Status: **supported**.

Value: For the selected base policy without optional covers, floater entry ages are 18 through 75 years for adults and 16 days through 25 years for dependent children. A floater dependent child reaching age 26 at renewal may continue until marriage. Eligible family relationships are self, spouse, children, parents and parents-in-law. The stated maximum floater family size is 6 adults plus 3 children, with a stated possibility of 9 adults when children retained under the floater are above 25. Sum-insured choices are INR 5 lakh, 7.5 lakh, 10 lakh, 15 lakh, 20 lakh, 25 lakh, 50 lakh, 75 lakh, 1 crore and 2 crore; the INR 75 lakh, 1 crore and 2 crore options are available only to persons aged up to 65 at policy inception. Age within a stated band does not by itself establish acceptance: the insurer may require medical underwriting depending on sum insured, medical history, zone and age. Midterm inclusion is available for a newly wedded spouse, newborn baby or legally adopted child on proportionate premium, subject to underwriting approval, with policy waiting periods running from that member's inclusion date.

Condition: Floater adult entry is from age 18 through age 75; floater dependent-child entry is from 16 days through age 25. (quotes 1).

Condition: At renewal, a dependent child who becomes 26 may remain under the floater until marriage. (quotes 2).

Condition: Individual-cover entry is from 91 days through age 75, and the stated pediatric documentation and central medical-underwriting requirements apply. (quotes 3).

Condition: Family eligibility extends to self, spouse, children, parents and parents-in-law. (quotes 4).

Condition: The maximum stated floater composition is 6 adults plus 3 children; the source also permits a family size of 9 adults when children retained under the floater are above age 25. (quotes 5).

Condition: The highest three offered sum-insured choices—INR 75 lakh, INR 1 crore and INR 2 crore—are restricted at inception to persons aged up to 65. (quotes 6).

Condition: The insurer may require medical underwriting based on sum insured, medical history, zone and age; entry-band eligibility therefore remains subject to insurer acceptance. (quotes 7).

Condition: Midterm addition of a newly wedded spouse, newborn baby or legally adopted child requires proportionate premium and underwriting approval, and waiting periods apply from the inclusion date. (quotes 8, 9).

Note: The selected variant is the base policy without optional covers; optional deductible and add-on covers are not selected and do not alter this eligibility summary.

Note: All stated entry ages remain subject to proposal acceptance, applicable underwriting and the other policy terms; age alone does not imply acceptance.

Note: The source states age limits as minimum/maximum or up to limits; the quoted boundaries are retained as inclusive eligibility endpoints.

Note: The continuation of a dependent child after age 25 is expressly a renewal distinction and is not stated as a new-entry entitlement.

Note: Pre-policy medical-check-up reimbursement applies only if the insurer accepts the proposal.

Note: Secondary statements omitted from this criterion: Remove the secondary sentence that incorrectly narrows pediatric documentation and central medical-underwriting requirements to young children. The individual entry age and the source-stated general documentation requirement remain explicitly in condition 3 and its exact quotation; all other eligibility conditions and underwriting notes are retained.

Note: rule_not_executable: Independent fact agreement did not include a rule body.

Executable-rule status: **rule not executable**.

Rule encoding record (does not determine fact support): The descriptive fact does not establish an executable encoding; prior verified partial rules remain separate.

Quote 1: [star-health-assure-prospectus, physical page 2](http://127.0.0.1:3021/evidence/27c0babc-f1a1-451f-83cd-9b851c1d3c6e); characters [1799, 1957).

```text
i. Floater Sum Insured:
a. For Adults – Minimum - 18 years & Maximum - Up to 75 years
b. For Dependent Children - Minimum - 16 days & Maximum - Up to 25 years
```

Quote 2: [star-health-assure-prospectus, physical page 2](http://127.0.0.1:3021/evidence/4791a913-f2c3-4a28-a7e1-d1f3c321923c); characters [1958, 2129).

```text
c.	
In case of dependent children, at the time of renewal when they become 26 years of
age, such children can continue under floater Sum Insured till he/she gets married.
```

Quote 3: [star-health-assure-prospectus, physical page 2](http://127.0.0.1:3021/evidence/d8c7c235-f5dc-4737-9878-9daa82a621d8); characters [2130, 2347).

```text
ii. Individual Sum Insured:
a. Minimum - 91 days and Maximum up to 75 years.
b.	
Provided Good Health declaration, Pediatrician Opinion and the proposal should
be routed through our Central Medical Underwriting Team.
```

Quote 4: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/75c98da2-656f-4bff-ba8c-9a9f56191d46); characters [293, 364).

```text
Family Definition: Self + Spouse + Children + Parents + Parents-in-law.
```

Quote 5: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/e8c4b7aa-b476-443f-a81a-7690a841a3f2); characters [369, 609).

```text
Maximum Family Size Covered under Floater Sum Insured: 6 Adults + 3 Children (6 Adults
= Self + Spouse + Parents + Parents-in-law) and the family size can be 9 Adults, if children
covered under floater Sum Insured are above 25 years of age.
```

Quote 6: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/f4511abc-a1d5-4b6c-b168-c1920756ee46); characters [1266, 1642).

```text
Sum Insured Options:
Rs.5,00,000/-, Rs.7,50,000/-, Rs.10,00,000/-, Rs.15,00,000/-, Rs.20,00,000/-, Rs.25,00,000/-,
Rs.50,00,000/-, Rs.75,00,000/-, Rs.1,00,00,000/- and Rs.2,00,00,000/-
Note: Rs.75,00,000/- Rs.1,00,00,000/- and Rs.2,00,00,000/- Sum Insured will be available for
persons aged up to 65 years only. This is applicable only at the time of inception of this
policy.
```

Quote 7: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/02ce906d-5686-4d68-a164-6635cdc453a8); characters [1646, 2056).

```text
MedicalUnderwriting/Pre-PolicyMedicalCheck-up:TheCompanymayaskthemembers
to be proposed to undergo medical underwriting either through medical tests or any other
medium viz tele underwriting etc. This will vary/depend upon the Sum Insured/ Medical
History/ Zone and Age. If we accept the proposal, we will reimburse at least 50% of the
costs incurred by the member undertaking such Pre-Policy medical check-up.
```

Quote 8: [star-health-assure-prospectus, physical page 3](http://127.0.0.1:3021/evidence/9b4088d8-20de-4c66-9b55-cc7752fa69ea); characters [2390, 2532).

```text
Midterm Inclusion Facility: Is available on payment of proportionate premium for Newly
Wedded spouse, New born baby and Legally adopted child.
```

Quote 9: [star-health-assure-prospectus, physical page 4](http://127.0.0.1:3021/evidence/7dafbf76-b26b-4aae-99e9-6f8f21943f62); characters [298, 525).

```text
i.	
Waiting periods as stated in the policy will be applicable from the date of inclusion of
such newly wedded spouse, new born baby, legally adopted child.
ii. Such midterm inclusion will be subject to underwriter’s approval.
```

### no_copay (derived; outside the 13)

Status: **derived**.

Value: No copay is not unconditional. Base policy: a mandatory 10% copayment applies to each and every claim for an insured person whose age at entry is 61 years or above, for both fresh and renewal policies. No voluntary copayment is selected.

Condition: The copayment applies to each and every claim. (quotes 1).

Condition: The copayment applies to both fresh and renewal policies. (quotes 2).

Condition: The insured person's age at entry must be 61 years or above. (quotes 3).

Executable-rule status: **rule not executable**.

Quote 1: [star-health-assure-base-wording, physical page 20](http://127.0.0.1:3021/evidence/26486fc4-14c6-499d-9ae4-2a95d171b717); characters [1289, 1363).

```text
This policy is subject to
co-payment of 10% of each and every
claim amount
```

Quote 2: [star-health-assure-base-wording, physical page 20](http://127.0.0.1:3021/evidence/e805caae-9c59-4da0-aae9-ec377c9a888e); characters [1364, 1401).

```text
for fresh as well as renewal
policies
```

Quote 3: [star-health-assure-base-wording, physical page 20](http://127.0.0.1:3021/evidence/76f45dbe-3ea0-4bef-bffa-6357c26e42a1); characters [1402, 1474).

```text
for Insured Person whose age at
the time of entry is 61 years and above.
```

### Price and budget (outside the 13)

**Unavailable.** No approved premium table or quote is available for this base variant.

## Approved document decisions and remaining scope limits

All optional covers remain unselected: Comprehensive PED buyback; Optima voluntary copayment; Assure aggregate deductible.
Comprehensive's captured 2025 document codes versus its 2026 UIN remain the accepted edition mismatch.
Assure consumables use wording clause 27 (physical page 20, printed page 19) and the wording's List I (physical page 44, printed page 43). This approved document decision is separate from the 13 extracted criteria above.
The separate Assure expense sheet remains reference only. Its 68 item descriptions match wording List I after case, whitespace and punctuation normalization. Differences are the title, presentation and column break (wording left column ends at item 35; separate sheet at 34). It cannot support executable rules.
Brochures and proposal forms remain excluded. Prospectuses remain applicable. Sum insured and eligibility include the complete prospectus on their first call; other criteria add it only when the core evidence lacks the needed definition, table or material information.
