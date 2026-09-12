# Reference family 11

Ten cases in the fixed reference set. Missing originals, configuration or customer evidence cannot count as successful insurance advice.

## ref-11-01 — My private room exceeds the room-rent limit and I need proportionate deductions calculated.

**Decision tested:** My private room exceeds the room-rent limit and I need proportionate deductions calculated.

**Customer and facts:** insured id: self; base si inr: 100000; room actual inr day: 4000; room days: 3; surgeon inr: 80000; medicines inr: 20000; assumed admissible accident: True; fact provenance: Synthetic case-author facts, not a real customer or insurer-issued schedule; contract assumption: New India Arogya Sanjeevani NIAHLIP25044V022425; applicability of individual schedule remains unverified

**Conversation:**

1. My private room exceeds the room-rent limit and I need proportionate deductions calculated.
2. What is the base SI, actual room tariff, duration, medicine subtotal and other eligible charges?
3. For this synthetic calculation: SI 100000; room 4000/day for 3 days; surgeon 80000; medicines 20000; all eligibility is assumed pending originals.

**Expected assessment:** Conditional illustration: room cap 2000/day; room allowed 6000, surgeon allowed 40000, medicines 20000; admissible subtotal 66000, 5% co-pay 3300; insurer amount 62700 and customer balance 49300 of bill 112000. This requires the assumed items to be otherwise admissible and sufficient cover; it is not a settlement promise.

**Missing evidence and effect:** Missing individual original schedule and endorsements: numerical illustrations do not establish this customer claim; Full across-insurer candidate and evidence assessment remains unfinished

**Calculations:**

- label: Room-limited claim illustration; inputs: base si: 100000; actual room rate: 4000; room days: 3; surgeon: 80000; medicines: 20000; copay rate: 0.05; expected: 62700; assumptions: All values INR; daily room rate INR/day; rates dimensionless; No other excluded items, sublimits, deductible or prior exhausted cover; admissible accident assumed; Medicines excluded from proportional reduction per section 4.1 note b

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1a; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.1 note b; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1a-d; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.1 note and 4.2-4.3; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5

**Judging criteria:**

- Proportionate deduction affects only the items identified by the applicable clause.
- Use the exact original version and explain all stated calculation assumptions
- Do not report a conditional illustration as confirmed eligibility or completed advice

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-02 — My policy has a co-pay and a deductible and I need the order of calculation checked.

**Decision tested:** Deduct-then-percentage and percentage-then-deduct can produce different results.

**Customer and facts:** authored stipulations: Buyer-insured Ishan 44; admissible amount 100000; deductible reported 10000; co-pay 20%; order unknown.; follow up statement: No clause supplied; both numbers are summary-only.

**Conversation:**

1. customer: My policy has a co-pay and a deductible and I need the order of calculation checked.
2. adviser: Which original says whether deductible precedes or follows the percentage and defines its base?
3. customer: No clause supplied; both numbers are summary-only.
4. adviser: Under explicitly hypothetical terms, subtracting the deductible and then applying the 20% co-pay gives an insurer payment of 72000; applying 20% first and then subtracting 10000 gives 70000. Neither order is established without the original. Preserve the operation order, percentage base and cap stage; do not infer order from a list of amounts.

**Expected assessment:** Under explicitly hypothetical terms, subtracting the deductible and then applying the 20% co-pay gives an insurer payment of 72000; applying 20% first and then subtracting 10000 gives 70000. Neither order is established without the original. Preserve the operation order, percentage base and cap stage; do not infer order from a list of amounts.

**Missing evidence and effect:** Exact deductible/co-pay interaction absent; keep both conditional results and block a definitive amount.

**Calculations:**

- label: Deductible before co-pay counterfactual; inputs: amount: 100000; deductible: 10000; copay ratio: 0.20; result unit: INR; reference expression: (amount-deductible)*(1-copay_ratio); expected: 72000; assumptions: Order is unresolved; this is one counterfactual and not selected policy logic.
- label: Co-pay before deductible counterfactual; inputs: amount: 100000; deductible: 10000; copay ratio: 0.20; result unit: INR; reference expression: amount*(1-copay_ratio)-deductible; expected: 70000; assumptions: Alternative order; do not choose without controlling original.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, II operative grant; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: Deduct-then-percentage and percentage-then-deduct can produce different results.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Under explicitly hypothetical terms, subtracting the deductible and then applying the 20% co-pay gives an insurer payment of 72000; applying 20% first and then subtracting 10000 gives 70000. Neither order is established without the original. Preserve the operation order, percentage base and cap stage; do not infer order from a list of amounts.
- Retain the material limitation: Exact deductible/co-pay interaction absent; keep both conditional results and block a definitive amount.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-03 — My bill includes consumables and I did not buy the consumables add-on.

**Decision tested:** Excluded, subsumed and separately payable items need separate states.

**Customer and facts:** authored stipulations: Buyer-insured Ishan 44; itemized hospital bill contains gloves, room kit, implant; consumables add-on not selected; New India AS.; follow up statement: Item mapping not provided; add-on only advertised elsewhere.

**Conversation:**

1. customer: My bill includes consumables and I did not buy the consumables add-on.
2. adviser: Which original list classifies each item and is any cost already inside an inclusive room/procedure package?
3. customer: Item mapping not provided; add-on only advertised elsewhere.
4. adviser: New India 4.7 distinguishes excluded items from those subsumed into room, procedure or treatment costs. Do not treat every consumable as excluded or deduct a package component twice. The unselected option creates no exception. Require row-level original mapping and package relationships before item arithmetic.

**Expected assessment:** New India 4.7 distinguishes excluded items from those subsumed into room, procedure or treatment costs. Do not treat every consumable as excluded or deduct a package component twice. The unselected option creates no exception. Require row-level original mapping and package relationships before item arithmetic.

**Missing evidence and effect:** Exact item rows, package bill allocation and any selected applicable exception missing.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.7; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 24, Annexure A List II row 1; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 25, Annexure A List III row 14; ce59f6f9785af314739a4b9a1b7bce63880793e5923d8d39ed20c91053312b48 physical page 20, I.1b

**Judging criteria:**

- Preserve the decision boundary: Excluded, subsumed and separately payable items need separate states.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: New India 4.7 distinguishes excluded items from those subsumed into room, procedure or treatment costs. Do not treat every consumable as excluded or deduct a package component twice. The unselected option creates no exception. Require row-level original mapping and package relationships before item arithmetic.
- Retain the material limitation: Exact item rows, package bill allocation and any selected applicable exception missing.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-04 — A cataract sublimit is lower than my sum insured.

**Decision tested:** A cataract sublimit is lower than my sum insured.

**Customer and facts:** insured id: self; base si inr: 100000; eye: left; eligible cataract bill inr: 60000; prior left eye usage inr: 0; fact provenance: Synthetic case-author facts, not a real customer or insurer-issued schedule; contract assumption: New India Arogya Sanjeevani NIAHLIP25044V022425; applicability of individual schedule remains unverified

**Conversation:**

1. A cataract sublimit is lower than my sum insured.
2. Which eye, base SI, eligible cost and previous same-eye claims in this policy year?
3. Synthetic left-eye claim; base SI 100000, eligible cost 60000, no earlier left-eye claim. Waiting and acceptance evidence are still needed.

**Expected assessment:** Conditional cap=min(25000,40000)=25000 for this eye/year; after 5% co-pay, illustration pays 23750 and leaves 36250 of the 60000 bill to the customer. The listed daycare procedure does not remove cataract waiting-period requirements.

**Missing evidence and effect:** Missing individual original schedule and endorsements: numerical illustrations do not establish this customer claim; Full across-insurer candidate and evidence assessment remains unfinished

**Calculations:**

- label: Cataract sublimit then co-pay; inputs: base si: 100000; eligible bill: 60000; cap rate: 0.25; absolute cap: 40000; copay rate: 0.05; expected: 23750; assumptions: INR; one eye within one policy year; no prior usage; Waiting and all other acceptance conditions assumed only for arithmetic

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.3; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 31, Annexure C row 66; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1a-d; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.1 note and 4.2-4.3; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5

**Judging criteria:**

- Calculate cap before co-pay and track each eye in its policy year.
- Use the exact original version and explain all stated calculation assumptions
- Do not report a conditional illustration as confirmed eligibility or completed advice

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-05 — Why can the remitted amount be below an otherwise calculated top-up benefit?

**Decision tested:** Premium acceleration changes cash remittance without changing threshold/admissibility arithmetic.

**Customer and facts:** authored stipulations: Buyer-insured Vimal40; Star Gold within-term instalment policy; otherwise calculated benefit100000 stipulated; three future instalments10000 each unpaid; claim triggers acceleration; no other adjustment.; follow up statement: Yes. Future instalments total30000; all earlier dues paid and policy in force.

**Conversation:**

1. customer: Why can the remitted amount be below an otherwise calculated top-up benefit?
2. adviser: Does the100000 represent final contractual benefit before premium recovery, and what unpaid instalments remain?
3. customer: Yes. Future instalments total30000; all earlier dues paid and policy in force.
4. adviser: V.12 makes subsequent instalments due on a claim and permits recovery from claim amount. With the stipulated100000 benefit and30000 remaining premium, remittance can be70000. Premium recovery is debt settlement, not an extra disease co-pay, excluded treatment or reduction of admissible hospital expense for the threshold ledger. Preserve the100000 benefit,30000 recovery and70000 cash separately.

**Expected assessment:** V.12 makes subsequent instalments due on a claim and permits recovery from claim amount. With the stipulated100000 benefit and30000 remaining premium, remittance can be70000. Premium recovery is debt settlement, not an extra disease co-pay, excluded treatment or reduction of admissible hospital expense for the threshold ledger. Preserve the100000 benefit,30000 recovery and70000 cash separately.

**Missing evidence and effect:** Actual payment schedule and settlement statement remain required for an actual remittance; this is a bounded hypothetical.

**Calculations:**

- label: Remittance after premium recovery; inputs: benefit: 100000; unpaid instalments: 3; each instalment: 10000; result unit: INR; reference expression: benefit-unpaid_instalments*each_instalment; expected: 70000; assumptions: Stipulated benefit and issued instalments. Premium debt differs from claim admissibility and co-pay.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 7, V.12 premium instalments i-viii; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 7, V.12vi-vii

**Judging criteria:**

- Premium acceleration changes cash remittance without changing threshold/admissibility arithmetic.
- Reach this bounded assessment: V.12 makes subsequent instalments due on a claim and permits recovery from claim amount. With the stipulated100000 benefit and30000 remaining premium, remittance can be70000. Premium recovery is debt settlement, not an extra disease co-pay, excluded treatment or reduction of admissible hospital expense for the threshold ledger. Preserve the100000 benefit,30000 recovery and70000 cash separately.
- Preserve this unresolved effect: Actual payment schedule and settlement statement remain required for an actual remittance; this is a bounded hypothetical.
- Do not convert hypothetical inputs into issuer evidence or adviser acceptance success.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-06 — My room upgrade was medically necessary and ICU wording differs from ordinary-room wording.

**Decision tested:** A medically necessary upgrade needs an explicit exception to alter a cap.

**Customer and facts:** authored stipulations: Buyer-insured Ishan 44; New India AS SI 100000; ICU rate 12000/day; 2 days; ordinary room cap different; medical necessity reported.; follow up statement: No waiver or endorsement supplied.

**Conversation:**

1. customer: My room upgrade was medically necessary and ICU wording differs from ordinary-room wording.
2. adviser: Does the contract give an explicit exception for the medically necessary upgrade and which ICU cap applies?
3. customer: No waiver or endorsement supplied.
4. adviser: The ICU cap is the lower of 5% of SI and 10000: 5000/day in this fixture, rather than the ordinary room cap of 2000. Medical necessity alone does not create a waiver. Any proportionate effect on other costs must follow the exact ICU clause and affected items; a full claim amount cannot be computed from room rates alone.

**Expected assessment:** The ICU cap is the lower of 5% of SI and 10000: 5000/day in this fixture, rather than the ordinary room cap of 2000. Medical necessity alone does not create a waiver. Any proportionate effect on other costs must follow the exact ICU clause and affected items; a full claim amount cannot be computed from room rates alone.

**Missing evidence and effect:** Clinical/accepted terms and full eligible itemized bill missing; no unwritten upgrade exception.

**Calculations:**

- label: ICU daily cap; inputs: si: 100000; ratio: 0.05; fixed cap: 10000; result unit: INR; reference expression: min(si*ratio,fixed_cap); expected: 5000; assumptions: All stated monetary inputs are INR and hypothetical. Only the specified arithmetic is resolved; broader insurance dependencies remain in the case record.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1b; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.1 note b; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 20, 10.20; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1a-d

**Judging criteria:**

- Preserve the decision boundary: A medically necessary upgrade needs an explicit exception to alter a cap.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: The ICU cap is the lower of 5% of SI and 10000: 5000/day in this fixture, rather than the ordinary room cap of 2000. Medical necessity alone does not create a waiver. Any proportionate effect on other costs must follow the exact ICU clause and affected items; a full claim amount cannot be computed from room rates alone.
- Retain the material limitation: Clinical/accepted terms and full eligible itemized bill missing; no unwritten upgrade exception.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-07 — I selected a voluntary co-pay in return for a lower premium.

**Decision tested:** Saving premium does not remove the selected future cost share.

**Customer and facts:** authored stipulations: Buyer-insured Ishan 44; selected voluntary 20% co-pay in unaccepted offer; premium discount 2000/year reported; hypothetical admissible claim 100000.; follow up statement: Selected for lower price, but not yet accepted; original clause missing.

**Conversation:**

1. customer: I selected a voluntary co-pay in return for a lower premium.
2. adviser: Was the co-pay deliberately selected and what base does its original define?
3. customer: Selected for lower price, but not yet accepted; original clause missing.
4. adviser: Separate requested selection from acceptance and quantify the trade-off conditionally: 20% of 100000 is 20000 cost share, ten times the reported annual discount. That comparison does not establish expected value or affordability; claim probability and other terms are unknown. Do not discard the co-pay because it was voluntary.

**Expected assessment:** Separate requested selection from acceptance and quantify the trade-off conditionally: 20% of 100000 is 20000 cost share, ten times the reported annual discount. That comparison does not establish expected value or affordability; claim probability and other terms are unknown. Do not discard the co-pay because it was voluntary.

**Missing evidence and effect:** Authentic option/base/discount quote and final acceptance absent; 20% and 2000 remain explicit scenario inputs.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 20, 10.20; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: Saving premium does not remove the selected future cost share.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Separate requested selection from acceptance and quantify the trade-off conditionally: 20% of 100000 is 20000 cost share, ten times the reported annual discount. That comparison does not establish expected value or affordability; claim probability and other terms are unknown. Do not discard the co-pay because it was voluntary.
- Retain the material limitation: Authentic option/base/discount quote and final acceptance absent; 20% and 2000 remain explicit scenario inputs.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-08 — My hospital bill has non-admissible items and co-pay applies only to admissible costs.

**Decision tested:** My hospital bill has non-admissible items and co-pay applies only to admissible costs.

**Customer and facts:** insured id: self; gross bill inr: 100000; excluded items inr: 10000; fact provenance: Synthetic case-author facts, not a real customer or insurer-issued schedule; contract assumption: New India Arogya Sanjeevani NIAHLIP25044V022425; applicability of individual schedule remains unverified

**Conversation:**

1. My hospital bill has non-admissible items and co-pay applies only to admissible costs.
2. What is the eligible subtotal after excluded items and other restrictions?
3. Synthetic eligible subtotal 90000 from gross bill 100000; no other deductions assumed.

**Expected assessment:** Conditional co-pay=4500; insurer illustration=85500; customer=10000 excluded+4500 co-pay=14500. Exact item-list and all other contractual restrictions must be established.

**Missing evidence and effect:** Missing individual original schedule and endorsements: numerical illustrations do not establish this customer claim; Full across-insurer candidate and evidence assessment remains unfinished

**Calculations:**

- label: Admissible basis for co-pay; inputs: gross bill: 100000; excluded items: 10000; copay rate: 0.05; expected: 85500; assumptions: INR; excluded items already assessed against the applicable list; No room reduction, other cap, deductible or exhausted balance

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.7; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1a-d; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.1 note and 4.2-4.3; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5

**Judging criteria:**

- Do not apply co-pay to excluded charges already paid wholly by the customer.
- Use the exact original version and explain all stated calculation assumptions
- Do not report a conditional illustration as confirmed eligibility or completed advice

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-09 — A percentage room limit is based on sum insured and my bonus increased the displayed cover.

**Decision tested:** A percentage room limit is based on sum insured and my bonus increased the displayed cover.

**Customer and facts:** insured id: self; base si inr: 100000; bonus inr: 50000; displayed cover inr: 150000; fact provenance: Synthetic case-author facts, not a real customer or insurer-issued schedule; contract assumption: New India Arogya Sanjeevani NIAHLIP25044V022425; applicability of individual schedule remains unverified

**Conversation:**

1. A percentage room limit is based on sum insured and my bonus increased the displayed cover.
2. Does the room clause use base sum insured or an amount including cumulative bonus?
3. For this synthetic contract reading the base SI is 100000 and cumulative bonus is separately stated as 50000.

**Expected assessment:** The clause-level room ceiling is min(2% of stated SI 100000,5000)=2000/day, subject to checking the actual schedule and whether any endorsement changes the base. Using displayed 150000 would incorrectly yield 3000/day under these assumptions.

**Missing evidence and effect:** Missing individual original schedule and endorsements: numerical illustrations do not establish this customer claim; Full across-insurer candidate and evidence assessment remains unfinished

**Calculations:**

- label: Room limit basis; inputs: base si: 100000; bonus: 50000; room percent: 0.02; daily cap: 5000; expected: 2000; assumptions: Result unit INR/day; SI amount in INR; Actual schedule must distinguish SI from bonus; no modifying endorsement assumed

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1a; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1a-d; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.1 note and 4.2-4.3; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 15, 9.5

**Judging criteria:**

- Displayed total cover and the room-limit calculation base may differ.
- Use the exact original version and explain all stated calculation assumptions
- Do not report a conditional illustration as confirmed eligibility or completed advice

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-11-10 — My procedure limit includes implant costs and my estimate itemises them separately.

**Decision tested:** Do not add a separately itemised implant again above the inclusive cap.

**Customer and facts:** authored stipulations: Buyer-insured Ishan 44; procedure inclusive cap 150000 reported; operation 120000 and implant 60000 estimated; other deductions unknown.; follow up statement: Assume inclusive cap for arithmetic; actual wording not provided.

**Conversation:**

1. customer: My procedure limit includes implant costs and my estimate itemises them separately.
2. adviser: Does the 150000 cap explicitly include the implant and is any expense counted twice?
3. customer: Assume inclusive cap for arithmetic; actual wording not provided.
4. adviser: The combined 180000 cost exceeds a stipulated inclusive 150000 cap by 30000; listing the implant separately does not add another 60000 of cover. Keep package membership and the cap stage explicit. Actual admissibility, order and insurer amount remain unsupported until the original is read.

**Expected assessment:** The combined 180000 cost exceeds a stipulated inclusive 150000 cap by 30000; listing the implant separately does not add another 60000 of cover. Keep package membership and the cap stage explicit. Actual admissibility, order and insurer amount remain unsupported until the original is read.

**Missing evidence and effect:** Authentic inclusive-cap provision and other deduction rules missing; this is a bounded synthetic cap example.

**Calculations:**

- label: Hypothetical inclusive cap excess; inputs: total: 180000; inclusive cap: 150000; result unit: INR; reference expression: total-inclusive_cap; expected: 30000; assumptions: 150000 inclusive cap is stipulated; exact selected insurer cap remains unresolved.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.7; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: Do not add a separately itemised implant again above the inclusive cap.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: The combined 180000 cost exceeds a stipulated inclusive 150000 cap by 30000; listing the implant separately does not add another 60000 of cover. Keep package membership and the cap stage explicit. Actual admissibility, order and insurer amount remain unsupported until the original is read.
- Retain the material limitation: Authentic inclusive-cap provision and other deduction rules missing; this is a bounded synthetic cap example.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

