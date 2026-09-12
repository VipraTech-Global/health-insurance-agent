# Reference family 14

Ten cases in the fixed reference set. Missing originals, configuration or customer evidence cannot count as successful insurance advice.

## ref-14-01 — I want a per-claim top-up compared with an aggregate super top-up.

**Decision tested:** Same product name can have variants with different aggregation rules.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 35; insured people: Nisha(self,35); fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; deductible: 300000; sum insured: 1000000; admissions: 2026-03-02:200000;2026-07-03:250000; basis: Compare stipulated Silver and Gold, otherwise admissible inpatient expenses, no pre/post, no room deduction, no prior usage

**Conversation:**

1. I want a per-claim top-up compared with an aggregate super top-up.
2. Are you comparing separate-hospitalisation or annual thresholds, and can your savings fund the threshold?
3. I can fund 300000. Both claims are otherwise admissible and fall in the same calendar-year policy. I have no premium quotes.
4. Conditional arithmetic: Silver pays zero toward these hospitalisation expenses because neither admission exceeds 300000. Gold aggregate 450000 crosses 300000 by 150000. This alone cannot select the better purchase: price, room terms, waits and threshold funding still differ.

**Expected assessment:** Conditional arithmetic: Silver pays zero toward these hospitalisation expenses because neither admission exceeds 300000. Gold aggregate 450000 crosses 300000 by 150000. This alone cannot select the better purchase: price, room terms, waits and threshold funding still differ.

**Missing evidence and effect:** Complete comparable quotes and underwriting offers absent; suitability comparison remains unfinished.

**Calculations:**

- label: Gold defined-limit excess; inputs: first admission: 200000; second admission: 250000; defined limit: 300000; zero: 0; expected: 150000; assumptions: INR amounts; input values and dates explicitly stipulated in customer_facts and conversation.; Result is threshold excess before any otherwise applicable contractual deductions; not a real insurer settlement.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, II operative grant; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, II.A; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 3, III.A; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note4; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note5; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, IV.1A

**Judging criteria:**

- Do not call Gold universally better without price and suitability evidence.
- Preserve that Silver and Gold are configurations in the same original.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-14-02 — Can a rejected base-insurer bill still count toward Gold's threshold when Gold accepts the expense?

**Decision tested:** Base-policy refusal and Gold threshold membership are independently assessed; not just arithmetic on two paid claims.

**Customer and facts:** authored stipulations: Buyer-insured Nisha35; Gold defined limit300000; same policy year; first hospital expense200000 was rejected by base insurer solely because base cover expired; Gold membership/period and expense admissibility are explicitly stipulated satisfied; second Gold-admissible expense250000; no Gold prior payout.; follow up statement: Only base insurer rejected it; for this arithmetic Gold independently admits both hospital expenses.

**Conversation:**

1. customer: Can a rejected base-insurer bill still count toward Gold's threshold when Gold accepts the expense?
2. adviser: Did Gold reject the first expense under its own terms, or did only the base insurer reject it?
3. customer: Only base insurer rejected it; for this arithmetic Gold independently admits both hospital expenses.
4. adviser: Gold's threshold depends on its admissible hospitalization expense, not whether a different base policy paid. Under the explicit Gold-admissibility stipulation, the200000 can contribute with250000, producing150000 threshold excess. A base rejection alone would not prove Gold admissibility; this script supplies that premise and tests its independent treatment.

**Expected assessment:** Gold's threshold depends on its admissible hospitalization expense, not whether a different base policy paid. Under the explicit Gold-admissibility stipulation, the200000 can contribute with250000, producing150000 threshold excess. A base rejection alone would not prove Gold admissibility; this script supplies that premise and tests its independent treatment.

**Missing evidence and effect:** This bounded calculation assumes Gold admissibility; actual claim facts and other-policy recoveries still govern a real settlement.

**Calculations:**

- label: Gold-admitted base-refused expense accumulation; inputs: first gold admitted: 200000; second gold admitted: 250000; threshold: 300000; result unit: INR; reference expression: max(first_gold_admitted+second_gold_admitted-threshold,0); expected: 150000; assumptions: Gold independently admits both expenses by explicit stipulation; base refusal alone does not supply that premise.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, Specific definitions: Defined Limit; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 6, V.4ii

**Judging criteria:**

- Base-policy refusal and Gold threshold membership are independently assessed; not just arithmetic on two paid claims.
- Reach this bounded assessment: Gold's threshold depends on its admissible hospitalization expense, not whether a different base policy paid. Under the explicit Gold-admissibility stipulation, the200000 can contribute with250000, producing150000 threshold excess. A base rejection alone would not prove Gold admissibility; this script supplies that premise and tests its independent treatment.
- Preserve this unresolved effect: This bounded calculation assumes Gold admissibility; actual claim facts and other-policy recoveries still govern a real settlement.
- Do not convert hypothetical inputs into issuer evidence or adviser acceptance success.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-14-03 — My employer cover is lower than the proposed super top-up deductible.

**Decision tested:** The uncovered gap between employer limit and deductible needs explicit funding.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 35; insured people: Nisha(self,35); fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; variant: Gold; employer available limit: 200000; defined limit: 300000; sum insured: 1000000; admissible hospitalisation: 700000; basis: Employer payment of200000 is stipulated for arithmetic; no assertion about unknown employer wording

**Conversation:**

1. My employer cover is lower than the proposed super top-up deductible.
2. How much has the employer insurer actually accepted, and can you fund any gap to the defined limit?
3. Assume it accepts 200000 of this 700000 bill. I cannot fund the remaining 100000 below the top-up threshold.
4. The stipulated Gold excess is 400000. Employer 200000 plus Gold 400000 leaves 100000 of the 700000 eligible bill unfunded. A 200000 employer limit does not align with a 300000 defined limit. Actual coordination needs both policies and settlement evidence.

**Expected assessment:** The stipulated Gold excess is 400000. Employer 200000 plus Gold 400000 leaves 100000 of the 700000 eligible bill unfunded. A 200000 employer limit does not align with a 300000 defined limit. Actual coordination needs both policies and settlement evidence.

**Missing evidence and effect:** Employer master wording, actual settlement, cashless observations and funded alternative absent.

**Calculations:**

- label: Gold defined-limit excess; inputs: admissible hospitalisation: 700000; defined limit: 300000; zero: 0; expected: 400000; assumptions: INR amounts; input values and dates explicitly stipulated in customer_facts and conversation.; Result is threshold excess before any otherwise applicable contractual deductions; not a real insurer settlement.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, Specific definitions: Defined Limit; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 6, V.2G; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 6, V.4ii

**Judging criteria:**

- Expose the 100000 gap and inability to fund it.
- Do not lower the defined limit to the base-policy limit.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-14-04 — I have no base policy but can personally fund the deductible.

**Decision tested:** Do not invent a mandatory base policy or assume it is never required.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 35; insured people: Nisha(self,35); fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; variant: Gold; has base policy: False; accessible savings: 400000; defined limit: 300000; sum insured: 1000000; admissible hospitalisation: 500000

**Conversation:**

1. I have no base policy but can personally fund the deductible.
2. Are your savings accessible during admission, and is the hospitalisation otherwise admissible under this contract?
3. I can access 400000. Use a hypothetical admissible 500000 hospital bill and no other claim this policy year.
4. The original threshold is admissible expenses, not a required payment by a base insurer: stipulated excess is 200000 and 300000 must be funded below threshold. Savings can fund that illustration, but this wording reading alone does not establish proposal acceptance, price or cashless access without a base policy.

**Expected assessment:** The original threshold is admissible expenses, not a required payment by a base insurer: stipulated excess is 200000 and 300000 must be funded below threshold. Savings can fund that illustration, but this wording reading alone does not establish proposal acceptance, price or cashless access without a base policy.

**Missing evidence and effect:** Proposal/prospectus acceptance conditions, quote and network availability need original confirmation.

**Calculations:**

- label: Gold defined-limit excess; inputs: admissible hospitalisation: 500000; defined limit: 300000; zero: 0; expected: 200000; assumptions: INR amounts; input values and dates explicitly stipulated in customer_facts and conversation.; Result is threshold excess before any otherwise applicable contractual deductions; not a real insurer settlement.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, Specific definitions: Defined Limit; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 6, V.2G; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 6, V.4ii

**Judging criteria:**

- Do not invent a requirement that a base insurer must pay the threshold.
- Do not promise issuance from absence of a base-policy requirement in the threshold clause.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-14-05 — My base policy and super top-up renew on different dates.

**Decision tested:** Do not use base renewal to reset a differently dated top-up accumulator.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 35; insured people: Nisha(self,35); fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; variant: Gold; defined limit: 300000; sum insured: 1000000; topup year one: 2025-07-01 to2026-06-30; topup year two: 2026-07-01 to2027-06-30; employer year: 2026-01-01 to2026-12-31; admissions: 2026-06-10:200000;2026-08-10:250000; expense basis: Both individually admissible; no pre/post, other usage or change to original terms; asks only top-up period allocation

**Conversation:**

1. My base policy and super top-up renew on different dates.
2. What are the top-up dates rather than just the employer renewal date?
3. The top-up renews 1 July. Employer cover renews 1 January. The eligible admissions are June 200000 and August 250000.
4. The top-up puts 200000 in its year ending 30 June and 250000 in its year beginning 1 July. Neither crosses 300000, so its threshold excess is zero in each year. Combining them using the employer year would wrongly produce 150000.

**Expected assessment:** The top-up puts 200000 in its year ending 30 June and 250000 in its year beginning 1 July. Neither crosses 300000, so its threshold excess is zero in each year. Combining them using the employer year would wrongly produce 150000.

**Missing evidence and effect:** 

**Calculations:**

- label: Gold excess across two separate policy years; inputs: first policy year admission: 200000; second policy year admission: 250000; defined limit: 300000; zero: 0; expected: 0; assumptions: INR amounts; input values and dates explicitly stipulated in customer_facts and conversation.; Result is threshold excess before any otherwise applicable contractual deductions; not a real insurer settlement.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note4; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note5

**Judging criteria:**

- Allocate to the top-up policy year, not calendar or employer year.
- Do not carry 250000 or 200000 unused threshold across renewal.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.

**Status:** `bounded_threshold_scope_complete`; no adviser attempt or acceptance pass.

## ref-14-06 — My family shares an aggregate deductible and both spouses made claims.

**Decision tested:** Aggregate family and per-person deductibles require different ledgers.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 35; insured people: Nisha(self,35); Arun(spouse,37), both stipulated insured under one Gold floater; fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; variant: Gold; defined limit: 300000; sum insured: 1000000; policy year: 2026-01-01 to2026-12-31; admissions: Nisha2026-02-10:180000; Arun2026-07-10:220000; expense basis: Both admissions otherwise admissible, no pre/post, prior usage or other deductions; asks shared-threshold arithmetic

**Conversation:**

1. My family shares an aggregate deductible and both spouses made claims.
2. Are you both named on one floater and do the claims fall in its same policy year?
3. Yes, one Gold floater for both of us. My eligible claim 180000 is followed by his 220000.
4. One Gold policy aggregates the stipulated 400000 across both insured members. The first claim leaves 120000 threshold; the second exceeds that remaining threshold by 100000. There is no separate 300000 deductible for each spouse in this illustration.

**Expected assessment:** One Gold policy aggregates the stipulated 400000 across both insured members. The first claim leaves 120000 threshold; the second exceeds that remaining threshold by 100000. There is no separate 300000 deductible for each spouse in this illustration.

**Missing evidence and effect:** 

**Calculations:**

- label: Gold defined-limit excess; inputs: self admission: 180000; spouse admission: 220000; defined limit: 300000; zero: 0; expected: 100000; assumptions: INR amounts; input values and dates explicitly stipulated in customer_facts and conversation.; Result is threshold excess before any otherwise applicable contractual deductions; not a real insurer settlement.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, Specific definitions: Family; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, Specific definitions: Defined Limit; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note4; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note7

**Judging criteria:**

- Attribute each admission to its person while sharing policy-period accumulation.
- Recompute if membership correction removes a person.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.

**Status:** `bounded_threshold_scope_complete`; no adviser attempt or acceptance pass.

## ref-14-07 — A non-admissible expense should not automatically count toward the deductible.

**Decision tested:** Gross billed amounts cannot automatically satisfy an admissible-expense deductible.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 35; insured people: Nisha(self,35), stipulated named insured on the selected Gold floater; fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; variant: Gold; defined limit: 300000; sum insured: 1000000; policy year: 2026-01-01 to2026-12-31; gross bill: 320000; excluded items: 40000; admissible inpatient: 280000; pre hospital: 15000; post hospital: 10000; basis: Exclusion/admissibility of each amount is expressly stipulated; only threshold membership is being assessed; admission date: 2026-08-10; prior policy year admissible usage: 0; prior policy year paid excess: 0

**Conversation:**

1. A non-admissible expense should not automatically count toward the deductible.
2. Does 320000 mean eligible inpatient expense, or does it include denied items and pre/post costs?
3. Correction: it is gross inpatient 320000 including 40000 ineligible items. Separately I paid 15000 before and 10000 after admission. This is my only admission in the policy year, on 10 August 2026; I am named on the Gold policy and there is no earlier admissible usage or paid excess.
4. Only 280000 contributes to the Gold defined limit. The 40000 excluded items and 25000 pre/post expenses do not move it toward 300000. Threshold excess is zero and 20000 of threshold remains. Whether pre/post benefits themselves are payable is a separate linked-grant question and is not calculated here.

**Expected assessment:** Only 280000 contributes to the Gold defined limit. The 40000 excluded items and 25000 pre/post expenses do not move it toward 300000. Threshold excess is zero and 20000 of threshold remains. Whether pre/post benefits themselves are payable is a separate linked-grant question and is not calculated here.

**Missing evidence and effect:** 

**Calculations:**

- label: Gold defined-limit excess; inputs: gross inpatient: 320000; excluded inpatient: 40000; defined limit: 300000; zero: 0; prior admissible usage: 0; expected: 0; assumptions: INR amounts; input values and dates explicitly stipulated in customer_facts and conversation.; Result is threshold excess before any otherwise applicable contractual deductions; not a real insurer settlement.; Named insured admission10August2026 is within stipulated calendar-year policy. No prior admissible expenses or paid excess; result would change if prior usage were supplied.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, Specific definitions: Defined Limit; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note4

**Judging criteria:**

- Correct the gross/admissible distinction before answering.
- Do not add 25000 pre/post expenses to cross the defined limit.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.
- If a correction adds 50000 of earlier admissible hospitalisation expenses, revise cumulative excess to 30000 rather than retaining zero.

**Status:** `bounded_threshold_scope_complete`; no adviser attempt or acceptance pass.

## ref-14-08 — I want to reduce the deductible after a major diagnosis.

**Decision tested:** A requested lower deductible is not an accepted contractual change.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 50; insured people: Nisha(self,50); Arun(spouse,52); fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; variant: Gold; defined limit: 500000; proposed limit: 300000; first entry age: 47; continuous years: 3; new diagnosis: cancer,2026-08-20; request date: 2026-09-10

**Conversation:**

1. I want to reduce the deductible after a major diagnosis.
2. Are you requesting a reduced defined limit at renewal, or the separate pathway to a policy with no defined limit?
3. I mean lower 500000 to 300000 now. We have held this policy three years and have a recent diagnosis.
4. Do not promise a midterm reduction. The originalV.29 pathway concerns a different indemnity policy without defined limit from the sixth year, subject to underwriting and further five-year/no-claim/all-member conditions. It does not establish a general right to reduce 500000 to 300000 after diagnosis. Obtain the applicable change provision and underwriting decision.

**Expected assessment:** Do not promise a midterm reduction. The originalV.29 pathway concerns a different indemnity policy without defined limit from the sixth year, subject to underwriting and further five-year/no-claim/all-member conditions. It does not establish a general right to reduce 500000 to 300000 after diagnosis. Obtain the applicable change provision and underwriting decision.

**Missing evidence and effect:** No original provision establishing requested defined-limit reduction or insurer offer/acceptance supplied.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 8, V.26; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 8, V.29

**Judging criteria:**

- Keep defined-limit change distinct from sum-insured change.
- Do not repurpose the six-year conversion clause to approve a three-year midterm request.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-14-09 — A single claim exceeds both the base cover and top-up deductible.

**Decision tested:** Prevent double recovery while distinguishing threshold from base payout.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 35; insured people: Nisha(self,35); fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; variant: Gold; defined limit: 300000; sum insured: 1000000; admissible hospitalisation: 800000; base accepted payment: 400000; basis: No other episodes, pre/post or deductions. Base400000 payment is stipulated, not inferred from a cover limit.

**Conversation:**

1. A single claim exceeds both the base cover and top-up deductible.
2. How much of the 800000 eligible bill has the base insurer paid, and has either insurer already paid the same expense?
3. Base paid 400000. I have not received any top-up payment.
4. The Gold standalone excess calculation is 500000, but only 400000 of the 800000 bill remains after base payment. Do not add both full amounts and pay 900000 against 800000 of indemnity loss. Coordination must identify overlapping bill items and the applicable settlement basis before stating Star final payment.

**Expected assessment:** The Gold standalone excess calculation is 500000, but only 400000 of the 800000 bill remains after base payment. Do not add both full amounts and pay 900000 against 800000 of indemnity loss. Coordination must identify overlapping bill items and the applicable settlement basis before stating Star final payment.

**Missing evidence and effect:** Item-level base settlement and insurer coordination/adjudication evidence missing; no final payment established.

**Calculations:**

- label: Gold defined-limit excess; inputs: admissible hospitalisation: 800000; defined limit: 300000; zero: 0; expected: 500000; assumptions: INR amounts; input values and dates explicitly stipulated in customer_facts and conversation.; Result is threshold excess before any otherwise applicable contractual deductions; not a real insurer settlement.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 6, V.4ii; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 6, V.4iv

**Judging criteria:**

- Show standalone excess separately from unpaid eligible balance 400000.
- Forbid duplicate indemnification; do not report standalone 500000 as final Star payment.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-14-10 — My top-up has its own waiting periods despite long-standing base cover.

**Decision tested:** A base policy's age does not automatically waive a new top-up's waits.

**Customer and facts:** buyer id: buyer-nisha; buyer age: 35; insured people: Nisha(self,35); fact provenance: Individually authored hypothetical customer statements. Contract wording is a preserved insurer original; the selected configuration and admissible expenses are explicit case stipulations, not fabricated insurer documents.; wording: Star Super Surplus Floater SHAHLIP22034V062122 POL SSF V18/2025; currency: INR; as of: 2026-09-10; variant: Gold; old base start: 2022-01-01; new topup start: 2026-07-01; new topup proposal type: fresh purchase, not accepted port/migration; planned admission: 2026-09-01; condition: Diabetes diagnosed2020; ongoing physician-prescribed treatment with consultation15June2026, within36months before newtopup1July2026; disclosed and synthetically accepted without permanent exclusion; defined limit: 300000; sum insured: 1000000

**Conversation:**

1. My top-up has its own waiting periods despite long-standing base cover.
2. Was the new top-up issued with documented continuity credit or simply bought alongside the old policy?
3. It was a new purchase with no credited waiting period. I expected the old base policy to remove the wait. My physician continued diabetes treatment at consultation 15 June 2026.
4. Longstanding base cover alone does not prove transferred credit. The selected Gold wording has 12 months PED waiting, unlike Silver 36 months. With new commencement 1 July and no credited continuity, a 1 September diabetes-related admission is within Gold PED waiting, subject to exact accepted terms. The deductible being crossed would not remove that wait.

**Expected assessment:** Longstanding base cover alone does not prove transferred credit. The selected Gold wording has 12 months PED waiting, unlike Silver 36 months. With new commencement 1 July and no credited continuity, a 1 September diabetes-related admission is within Gold PED waiting, subject to exact accepted terms. The deductible being crossed would not remove that wait.

**Missing evidence and effect:** Complete current application/endorsement bundle and treatment-to-PED relationship require review before an actual eligibility conclusion.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, IV.1A; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 5, IV.2C

**Judging criteria:**

- Use Gold 12 months rather than Silver 36 months.
- Keep eligibility waiting and deductible arithmetic as separate mandatory checks.
- Cite the exact selected original and keep the result within the explicitly assessed question.
- A worked reference calculation is not an adviser acceptance attempt.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

