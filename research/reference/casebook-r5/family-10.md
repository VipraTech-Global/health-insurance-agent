# Reference family 10

Ten cases in the fixed reference set. Missing originals, configuration or customer evidence cannot count as successful insurance advice.

## ref-10-01 — I need regular medicines without any hospital admission.

**Decision tested:** A medical prescription does not create outpatient cover under an inpatient policy.

**Customer and facts:** authored stipulations: Buyer-insured Farah 41; recurring prescription medicines 1500/month; New India AS; no hospitalisation.; follow up statement: Routine; no admission.

**Conversation:**

1. customer: I need regular medicines without any hospital admission.
2. adviser: Are these routine standalone medicines or related to an admissible hospital episode?
3. customer: Routine; no admission.
4. adviser: The original OPD exclusion prevents treating all prescribed medicine as covered hospital expense. The 18000 annual spend estimate belongs to a separate outpatient requirement. Search only original-backed OPD grants/options for that need; do not manufacture a pre/post link or claim it is paid under the hospital grant.

**Expected assessment:** The original OPD exclusion prevents treating all prescribed medicine as covered hospital expense. The 18000 annual spend estimate belongs to a separate outpatient requirement. Search only original-backed OPD grants/options for that need; do not manufacture a pre/post link or claim it is paid under the hospital grant.

**Missing evidence and effect:** Suitable OPD alternative and actual quote absent; no reimbursement from the chosen hospital clause established.

**Calculations:**

- label: Annual recurring expenditure; inputs: monthly: 1500; annual extra: 0; result unit: INR; reference expression: monthly*12+annual_extra; expected: 18000; assumptions: Annual budget arithmetic only; no OPD entitlement inferred.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 13, 7.18; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.42; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.43

**Judging criteria:**

- Preserve the decision boundary: A medical prescription does not create outpatient cover under an inpatient policy.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: The original OPD exclusion prevents treating all prescribed medicine as covered hospital expense. The 18000 annual spend estimate belongs to a separate outpatient requirement. Search only original-backed OPD grants/options for that need; do not manufacture a pre/post link or claim it is paid under the hospital grant.
- Retain the material limitation: Suitable OPD alternative and actual quote absent; no reimbursement from the chosen hospital clause established.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-02 — My tests occurred before admission and may fall within the pre-hospitalisation window.

**Decision tested:** A test inside the date window can still fail the related-condition requirement.

**Customer and facts:** authored stipulations: Buyer-insured Farah 41; admission 10 Aug 2026 for fracture; thyroid test 20 Jul; fracture X-ray 5 Aug; New India AS.; follow up statement: The X-ray relates to the fracture; the thyroid test is routine and unrelated.

**Conversation:**

1. customer: My tests occurred before admission and may fall within the pre-hospitalisation window.
2. adviser: Which tests relate to the condition that caused the admissible admission?
3. customer: The X-ray relates to the fracture; the thyroid test is routine and unrelated.
4. adviser: Both dates can fall inside a 30-day window, but timing alone is insufficient. The original requires related expenses and an admissible main admission. The fracture X-ray may satisfy relationship under the fixture; unrelated thyroid testing does not become pre-hospitalisation merely by date. Other exclusions/admissibility still apply.

**Expected assessment:** Both dates can fall inside a 30-day window, but timing alone is insufficient. The original requires related expenses and an admissible main admission. The fracture X-ray may satisfy relationship under the fixture; unrelated thyroid testing does not become pre-hospitalisation merely by date. Other exclusions/admissibility still apply.

**Missing evidence and effect:** Actual accepted admission, itemized bills and relationship evidence missing; no final claim amount.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.42; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.4-4.5; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 13, 7.18

**Judging criteria:**

- Preserve the decision boundary: A test inside the date window can still fail the related-condition requirement.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Both dates can fall inside a 30-day window, but timing alone is insufficient. The original requires related expenses and an admissible main admission. The fracture X-ray may satisfy relationship under the fixture; unrelated thyroid testing does not become pre-hospitalisation merely by date. Other exclusions/admissibility still apply.
- Retain the material limitation: Actual accepted admission, itemized bills and relationship evidence missing; no final claim amount.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-03 — My follow-up bill is on the last day of the post-hospitalisation period.

**Decision tested:** Compare exact last eligible day and following day with calendar arithmetic.

**Customer and facts:** authored stipulations: Buyer-insured Farah, 41; discharged 1 Jul 2026; related follow-up on 30 Aug and 31 Aug; New India AS has a stated 60-day post-hospitalisation window; main claim acceptance is stipulated.; follow up statement: The supplied wording says 60 days from discharge; the inclusive-day convention has not been clarified.

**Conversation:**

1. customer: My follow-up bill is on the last day of the post-hospitalisation period.
2. adviser: Does the wording count discharge day and which date/time anchor defines the last day?
3. customer: The supplied wording says 60 days from discharge; the inclusive-day convention has not been clarified.
4. adviser: Elapsed-calendar arithmetic gives 30 August as 60 days after 1 July and 31 August as 61 days. Preserve the unresolved inclusive-day convention rather than silently using an off-by-one rule. Relationship and other follow-up conditions still apply; acceptance of the main claim does not resolve every follow-up bill.

**Expected assessment:** Elapsed-calendar arithmetic gives 30 August as 60 days after 1 July and 31 August as 61 days. Preserve the unresolved inclusive-day convention rather than silently using an off-by-one rule. Relationship and other follow-up conditions still apply; acceptance of the main claim does not resolve every follow-up bill.

**Missing evidence and effect:** Exact inclusive boundary interpretation and service-specific admissibility unresolved; report date arithmetic separately from benefit eligibility.

**Calculations:**

- label: Post-discharge date60elapsed days; inputs: discharge: 2026-07-01; days: 60; result unit: date; reference expression: discharge + days; expected: 2026-08-30; assumptions: Original inclusion of discharge day versus elapsed boundary remains unresolved; this date arithmetic does not decide coverage.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.43; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.4-4.5

**Judging criteria:**

- Preserve the decision boundary: Compare exact last eligible day and following day with calendar arithmetic.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Elapsed-calendar arithmetic gives 30 August as 60 days after 1 July and 31 August as 61 days. Preserve the unresolved inclusive-day convention rather than silently using an off-by-one rule. Relationship and other follow-up conditions still apply; acceptance of the main claim does not resolve every follow-up bill.
- Retain the material limitation: Exact inclusive boundary interpretation and service-specific admissibility unresolved; report date arithmetic separately from benefit eligibility.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-04 — I need treatment at home because no hospital bed was available.

**Decision tested:** The domiciliary definition is not itself a benefit grant.

**Customer and facts:** authored stipulations: Buyer-insured Farah 41; physician ordered home treatment because beds unavailable; New India AS; no confirmed other policy.; follow up statement: No grant found; only definition.

**Conversation:**

1. customer: I need treatment at home because no hospital bed was available.
2. adviser: Does the selected product actually grant domiciliary cover, beyond defining it?
3. customer: No grant found; only definition.
4. adviser: New India's 7.18 expressly excludes domiciliary hospitalisation and OPD. A qualifying reason for home care does not override that selected product exclusion. Do not infer a grant from a definition; search another original-backed product if home treatment is required, preserving its trigger/facility conditions.

**Expected assessment:** New India's 7.18 expressly excludes domiciliary hospitalisation and OPD. A qualifying reason for home care does not override that selected product exclusion. Do not infer a grant from a definition; search another original-backed product if home treatment is required, preserving its trigger/facility conditions.

**Missing evidence and effect:** No alternative applicable home-treatment grant supplied; selected original does not support this benefit.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 13, 7.18; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: The domiciliary definition is not itself a benefit grant.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: New India's 7.18 expressly excludes domiciliary hospitalisation and OPD. A qualifying reason for home care does not override that selected product exclusion. Do not infer a grant from a definition; search another original-backed product if home treatment is required, preserving its trigger/facility conditions.
- Retain the material limitation: No alternative applicable home-treatment grant supplied; selected original does not support this benefit.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-05 — I prefer treatment at home for convenience and want domiciliary cover checked.

**Decision tested:** Convenience is distinct from the contract's qualifying home-treatment trigger.

**Customer and facts:** authored stipulations: Buyer-insured Farah 41; home treatment preferred for convenience; hospital bed available; generic domiciliary benefit advertised.; follow up statement: Neither; home is just preferred.

**Conversation:**

1. customer: I prefer treatment at home for convenience and want domiciliary cover checked.
2. adviser: What qualifying trigger does the actual product require and has a doctor documented inability to move or bed shortage?
3. customer: Neither; home is just preferred.
4. adviser: Convenience must not be substituted for a contractual home-treatment trigger. The candidate's exact grant and conditions are needed; New India's explicit domiciliary exclusion demonstrates that terminology alone is insufficient. Preserve customer preference separately from clinically or contractually required facts.

**Expected assessment:** Convenience must not be substituted for a contractual home-treatment trigger. The candidate's exact grant and conditions are needed; New India's explicit domiciliary exclusion demonstrates that terminology alone is insufficient. Preserve customer preference separately from clinically or contractually required facts.

**Missing evidence and effect:** Authentic domiciliary grant/trigger and clinical evidence absent; no home-treatment eligibility.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 13, 7.18; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: Convenience is distinct from the contract's qualifying home-treatment trigger.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Convenience must not be substituted for a contractual home-treatment trigger. The candidate's exact grant and conditions are needed; New India's explicit domiciliary exclusion demonstrates that terminology alone is insufficient. Preserve customer preference separately from clinically or contractually required facts.
- Retain the material limitation: Authentic domiciliary grant/trigger and clinical evidence absent; no home-treatment eligibility.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-06 — My outpatient benefit has a yearly cap and a network-only condition.

**Decision tested:** An eligible treatment at an ineligible provider can have a different outcome.

**Customer and facts:** authored stipulations: Buyer-insured Farah 41; OPD option reportedly cap 10000/year network only; spent 8000; new visit 3000 at non-network clinic.; follow up statement: Stipulate 8000 eligible usage; new provider outside option network; clause missing.

**Conversation:**

1. customer: My outpatient benefit has a yearly cap and a network-only condition.
2. adviser: Is the provider/network condition mandatory and are the 8000 earlier costs eligible paid usage?
3. customer: Stipulate 8000 eligible usage; new provider outside option network; clause missing.
4. adviser: The arithmetic remaining cap is 2000, but that does not make a non-network visit payable. Verify the original provider condition and any reimbursement exception first. Store cap usage, provider eligibility and booking/access state separately; unknown exception is not unlimited reimbursement.

**Expected assessment:** The arithmetic remaining cap is 2000, but that does not make a non-network visit payable. Verify the original provider condition and any reimbursement exception first. Store cap usage, provider eligibility and booking/access state separately; unknown exception is not unlimited reimbursement.

**Missing evidence and effect:** Exact OPD rider/network exceptions and actual accepted usage evidence missing; 2000 is only remaining-cap arithmetic.

**Calculations:**

- label: Hypothetical OPD cap remaining; inputs: annual cap: 10000; used: 8000; result unit: INR; reference expression: annual_cap-used; expected: 2000; assumptions: A stipulated limit balance does not establish network/provider eligibility.

**Original anchors:** ce59f6f9785af314739a4b9a1b7bce63880793e5923d8d39ed20c91053312b48 physical page 26, II.A.I.5a; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 20, 10.20; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: An eligible treatment at an ineligible provider can have a different outcome.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: The arithmetic remaining cap is 2000, but that does not make a non-network visit payable. Verify the original provider condition and any reimbursement exception first. Store cap usage, provider eligibility and booking/access state separately; unknown exception is not unlimited reimbursement.
- Retain the material limitation: Exact OPD rider/network exceptions and actual accepted usage evidence missing; 2000 is only remaining-cap arithmetic.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-07 — I need physiotherapy after discharge and the hospitalisation claim was accepted.

**Decision tested:** Accepted hospitalisation does not automatically cover every follow-up service.

**Customer and facts:** authored stipulations: Buyer-insured Farah 41; accepted fracture admission; physiotherapy 20 days after discharge; New India AS.; follow up statement: Prescribed for fracture; bill and therapy setting not verified.

**Conversation:**

1. customer: I need physiotherapy after discharge and the hospitalisation claim was accepted.
2. adviser: Is therapy for the same condition, within the window and a covered service rather than custodial care?
3. customer: Prescribed for fracture; bill and therapy setting not verified.
4. adviser: An accepted main admission supplies one dependency, not blanket approval of every later service. Check related condition, 60-day window, service admissibility, setting and exclusions. Keep prescribed physiotherapy distinct from help with daily living or unrelated outpatient treatment.

**Expected assessment:** An accepted main admission supplies one dependency, not blanket approval of every later service. Check related condition, 60-day window, service admissibility, setting and exclusions. Keep prescribed physiotherapy distinct from help with daily living or unrelated outpatient treatment.

**Missing evidence and effect:** Bill/service-setting and exact grant/exclusion interaction need review; no automatic follow-up payment.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.43; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.4-4.5; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 11, 7.2; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 13, 7.18

**Judging criteria:**

- Preserve the decision boundary: Accepted hospitalisation does not automatically cover every follow-up service.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: An accepted main admission supplies one dependency, not blanket approval of every later service. Check related condition, 60-day window, service admissibility, setting and exclusions. Keep prescribed physiotherapy distinct from help with daily living or unrelated outpatient treatment.
- Retain the material limitation: Bill/service-setting and exact grant/exclusion interaction need review; no automatic follow-up payment.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-08 — Does the included doctor chat reimburse my diabetes medicines or provide a repeat prescription?

**Decision tested:** Distinguish an included service, its prohibited function and an unevidenced financial benefit.

**Customer and facts:** authored stipulations: Buyer-insured Kavita40; Star Gold policy stipulated; diabetes medicine2000/month; requests repeat prescription and reimbursement through Star Health app online chat; no selected OPD indemnity benefit evidenced.; follow up statement: All three; I assumed an included doctor chat meant medicine expenses were insured.

**Conversation:**

1. customer: Does the included doctor chat reimburse my diabetes medicines or provide a repeat prescription?
2. adviser: Are you asking for wellness chat advice, a prescription, or reimbursement of medicine bills?
3. customer: All three; I assumed an included doctor chat meant medicine expenses were insured.
4. adviser: The original M.1 service provides advice and quick consultations through the app, and expressly says it does not prescribe medications or diagnose health issues. That service does not establish medicine-bill reimbursement. Explain the supported chat function and its prescription restriction; investigate a separately evidenced OPD grant before any expense-cover claim. Routine annual spend is not the decisive test here.

**Expected assessment:** The original M.1 service provides advice and quick consultations through the app, and expressly says it does not prescribe medications or diagnose health issues. That service does not establish medicine-bill reimbursement. Explain the supported chat function and its prescription restriction; investigate a separately evidenced OPD grant before any expense-cover claim. Routine annual spend is not the decisive test here.

**Missing evidence and effect:** Any separate prescription service or OPD reimbursement option needs its own selected terms; do not claim all Star services prohibit prescriptions.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, M.1 online doctor chat, bottom left column

**Judging criteria:**

- Distinguish an included service, its prohibited function and an unevidenced financial benefit.
- Reach this bounded assessment: The original M.1 service provides advice and quick consultations through the app, and expressly says it does not prescribe medications or diagnose health issues. That service does not establish medicine-bill reimbursement. Explain the supported chat function and its prescription restriction; investigate a separately evidenced OPD grant before any expense-cover claim. Routine annual spend is not the decisive test here.
- Preserve this unresolved effect: Any separate prescription service or OPD reimbursement option needs its own selected terms; do not claim all Star services prohibit prescriptions.
- Do not convert hypothetical inputs into issuer evidence or adviser acceptance success.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-09 — My outpatient add-on requires app booking but I used a walk-in clinic.

**Decision tested:** Availability of a service does not prove that its required access method was followed.

**Customer and facts:** authored stipulations: Buyer-insured Farah 41; claimed OPD add-on requires app booking; used walk-in clinic 5 Sep; no booking confirmation.; follow up statement: Only app requirement is known from summary; no exception located.

**Conversation:**

1. customer: My outpatient add-on requires app booking but I used a walk-in clinic.
2. adviser: What does the rider say about booking exceptions and is this provider otherwise eligible?
3. customer: Only app requirement is known from summary; no exception located.
4. adviser: Treat booking as a separate potentially mandatory condition, not merely a UI detail. A service being covered in principle does not prove an unbooked visit qualifies. Obtain exact rider/access rules and any exception before approving or denying; do not invent a retrospective booking.

**Expected assessment:** Treat booking as a separate potentially mandatory condition, not merely a UI detail. A service being covered in principle does not prove an unbooked visit qualifies. Obtain exact rider/access rules and any exception before approving or denying; do not invent a retrospective booking.

**Missing evidence and effect:** Original access condition, selected rider, provider evidence and exception details missing.

**Original anchors:** ce59f6f9785af314739a4b9a1b7bce63880793e5923d8d39ed20c91053312b48 physical page 20, I.1b; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 20, 10.20; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: Availability of a service does not prove that its required access method was followed.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Treat booking as a separate potentially mandatory condition, not merely a UI detail. A service being covered in principle does not prove an unbooked visit qualifies. Obtain exact rider/access rules and any exception before approving or denying; do not invent a retrospective booking.
- Retain the material limitation: Original access condition, selected rider, provider evidence and exception details missing.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-10-10 — I need nursing at home after surgery and separate consumable supplies.

**Decision tested:** Separate skilled treatment from custodial support and supplies.

**Customer and facts:** authored stipulations: Buyer-insured Farah 41; after surgery needs nurse for wound care, attendant for daily activities and disposables; New India AS.; follow up statement: Invoice combines all three; no item allocation.

**Conversation:**

1. customer: I need nursing at home after surgery and separate consumable supplies.
2. adviser: Which tasks are skilled medical treatment, which are custodial and which supplies are included in a package?
3. customer: Invoice combines all three; no item allocation.
4. adviser: Split service tasks and supplies before applying exclusions. New India's custodial-care exclusion and domiciliary/OPD exclusion require review alongside any related post-hospital grant; prescribed care alone does not make every task payable. Package-subsumed supplies differ from separately excluded expenses.

**Expected assessment:** Split service tasks and supplies before applying exclusions. New India's custodial-care exclusion and domiciliary/OPD exclusion require review alongside any related post-hospital grant; prescribed care alone does not make every task payable. Package-subsumed supplies differ from separately excluded expenses.

**Missing evidence and effect:** Item/task allocation and a supporting applicable home/post-care grant absent; no combined nursing payment.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 11, 7.2; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 13, 7.18; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.43; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.7

**Judging criteria:**

- Preserve the decision boundary: Separate skilled treatment from custodial support and supplies.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Split service tasks and supplies before applying exclusions. New India's custodial-care exclusion and domiciliary/OPD exclusion require review alongside any related post-hospital grant; prescribed care alone does not make every task payable. Package-subsumed supplies differ from separately excluded expenses.
- Retain the material limitation: Item/task allocation and a supporting applicable home/post-care grant absent; no combined nursing payment.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

