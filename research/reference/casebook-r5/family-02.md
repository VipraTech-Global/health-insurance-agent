# Reference family 02

Ten cases in the fixed reference set. Missing originals, configuration or customer evidence cannot count as successful insurance advice.

## ref-02-01 — We are a couple with two young children and want individual cover versus a floater compared.

**Decision tested:** Two concurrent claims can exhaust shared cover while leaving an individual policy intact.

**Customer and facts:** authored stipulations: Buyer Dev, 38; spouse Mira, 36; children 6 and 9; compare one INR 1000000 floater with INR 1000000 per person; two otherwise eligible claims INR 700000 and INR 600000 in one year.; follow up statement: For this illustration, assume exactly those limits, no other deductions and no previous usage. The first claim is for Dev and the second for Mira; prices are unknown.

**Conversation:**

1. customer: We are a couple with two young children and want individual cover versus a floater compared.
2. adviser: Is the quoted SI shared or available separately to each named person, and are benefits otherwise comparable?
3. customer: For this illustration, assume exactly those limits, no other deductions and no previous usage. The first claim is for Dev and the second for Mira; prices are unknown.
4. adviser: The New India benefit table distinguishes per-member SI from entire-family SI. In the fixture the floater has INR 300000 left after the first 700000 claim, leaving 300000 of the second 600000 unfunded; separate per-person limits can cover both assumed amounts. This is allocation arithmetic, not proof of comparative premiums or actual admissibility.

**Expected assessment:** The New India benefit table distinguishes per-member SI from entire-family SI. In the fixture the floater has INR 300000 left after the first 700000 claim, leaving 300000 of the second 600000 unfunded; separate per-person limits can cover both assumed amounts. This is allocation arithmetic, not proof of comparative premiums or actual admissibility.

**Missing evidence and effect:** Actual individual/floater quotes, complete current terms and accepted family membership are absent; no recommendation from nominal SI alone.

**Calculations:**

- label: Shared cover shortfall on second member claim; inputs: shared si: 1000000; first claim: 700000; second claim: 600000; result unit: INR; reference expression: second_claim-(shared_si-first_claim); expected: 300000; assumptions: All stated monetary inputs are INR and hypothetical. Only the specified arithmetic is resolved; broader insurance dependencies remain in the case record.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 7, 4.1a; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 21, 12 Sum insured

**Judging criteria:**

- Preserve the decision boundary: Two concurrent claims can exhaust shared cover while leaving an individual policy intact.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: The New India benefit table distinguishes per-member SI from entire-family SI. In the fixture the floater has INR 300000 left after the first 700000 claim, leaving 300000 of the second 600000 unfunded; separate per-person limits can cover both assumed amounts. This is allocation arithmetic, not proof of comparative premiums or actual admissibility.
- Retain the material limitation: Actual individual/floater quotes, complete current terms and accepted family membership are absent; no recommendation from nominal SI alone.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-02 — I want to put my healthy spouse and my diabetic parent on one floater.

**Decision tested:** Relationship eligibility and medical acceptance are independent gates.

**Customer and facts:** authored stipulations: Buyer Dev, 38; healthy spouse Mira 36; father 71 with diabetes; proposes one Star Gold floater for all; priorities simplicity and parent protection.; follow up statement: One policy. Father has regular diabetes treatment; no insurer has accepted him.

**Conversation:**

1. customer: I want to put my healthy spouse and my diabetic parent on one floater.
2. adviser: Which relationships does the selected wording admit, and are you asking for one policy or just one account?
3. customer: One policy. Father has regular diabetes treatment; no insurer has accepted him.
4. adviser: Star's family definition is self, spouse, dependent children; it does not support adding a parent to this floater merely because he is family. New India lists parents as a relationship, but that alone does not establish age/medical acceptance. Keep separate-policy alternatives open and require original eligibility plus individual terms.

**Expected assessment:** Star's family definition is self, spouse, dependent children; it does not support adding a parent to this floater merely because he is family. New India lists parents as a relationship, but that alone does not establish age/medical acceptance. Keep separate-policy alternatives open and require original eligibility plus individual terms.

**Missing evidence and effect:** Father's acceptable product/age terms and medical underwriting remain missing; do not generalize Star's relationship restriction to all insurers.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, Specific definitions: Family; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 3, 3.20; ce59f6f9785af314739a4b9a1b7bce63880793e5923d8d39ed20c91053312b48 physical page 19, I.1 note

**Judging criteria:**

- Preserve the decision boundary: Relationship eligibility and medical acceptance are independent gates.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Star's family definition is self, spouse, dependent children; it does not support adding a parent to this floater merely because he is family. New India lists parents as a relationship, but that alone does not establish age/medical acceptance. Keep separate-policy alternatives open and require original eligibility plus individual terms.
- Retain the material limitation: Father's acceptable product/age terms and medical underwriting remain missing; do not generalize Star's relationship restriction to all insurers.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-03 — Two family members may need planned procedures in the same policy year.

**Decision tested:** Reserved and paid amounts must not be double counted or silently ignored.

**Customer and facts:** authored stipulations: Buyer Dev, 38 and spouse 36; one hypothetical SI INR 500000 floater; paid eligible claim 200000; pending admission authorization reserve 150000; another proposed procedure estimated 250000.; follow up statement: It belongs to a new unpaid admission; neither amount duplicates the other. Another procedure may cost 250000.

**Conversation:**

1. customer: Two family members may need planned procedures in the same policy year.
2. adviser: Is the 150000 reserve additional to the paid 200000, and does it belong to the same claim?
3. customer: It belongs to a new unpaid admission; neither amount duplicates the other. Another procedure may cost 250000.
4. adviser: Maintain paid and reserved amounts with claim identity and reservation status. The illustrative uncommitted balance is 150000, while ultimate payable balance depends on the pending claim's final amount. Do not subtract the same authorization and settlement twice. Expected procedure cost does not itself consume final claim cover or prove admissibility.

**Expected assessment:** Maintain paid and reserved amounts with claim identity and reservation status. The illustrative uncommitted balance is 150000, while ultimate payable balance depends on the pending claim's final amount. Do not subtract the same authorization and settlement twice. Expected procedure cost does not itself consume final claim cover or prove admissibility.

**Missing evidence and effect:** Issued shared-limit terms and actual claim/authorization ledgers absent; distinguish exposure estimate from settled availability.

**Calculations:**

- label: Uncommitted cover after paid amount and reserve; inputs: si: 500000; paid: 200000; reserve: 150000; result unit: INR; reference expression: si-paid-reserve; expected: 150000; assumptions: All stated monetary inputs are INR and hypothetical. Only the specified arithmetic is resolved; broader insurance dependencies remain in the case record.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note7; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 21, 12 Sum insured

**Judging criteria:**

- Preserve the decision boundary: Reserved and paid amounts must not be double counted or silently ignored.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Maintain paid and reserved amounts with claim identity and reservation status. The illustrative uncommitted balance is 150000, while ultimate payable balance depends on the pending claim's final amount. Do not subtract the same authorization and settlement twice. Expected procedure cost does not itself consume final claim cover or prove admissibility.
- Retain the material limitation: Issued shared-limit terms and actual claim/authorization ledgers absent; distinguish exposure estimate from settled availability.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-04 — My spouse has separate insurance and I only need cover for myself and our child.

**Decision tested:** Do not add the spouse simply because the buyer is married.

**Customer and facts:** authored stipulations: Buyer Dev, 38; spouse 36 has separate employer policy; intended insureds Dev and child 6 only; preference no duplicate membership.; follow up statement: Yes. Only me and our daughter; I will pay for both.

**Conversation:**

1. customer: My spouse has separate insurance and I only need cover for myself and our child.
2. adviser: Should spouse remain outside this purchase even though she is part of the household?
3. customer: Yes. Only me and our daughter; I will pay for both.
4. adviser: Record spouse as a related person with separate cover, not automatically as a proposed insured. Select configurations by the two intended members and confirm dependent-child eligibility. Preserve spouse cover only where expressly relevant to coordination. A shared account or legal marriage does not authorize silently adding someone to a quote.

**Expected assessment:** Record spouse as a related person with separate cover, not automatically as a proposed insured. Select configurations by the two intended members and confirm dependent-child eligibility. Preserve spouse cover only where expressly relevant to coordination. A shared account or legal marriage does not authorize silently adding someone to a quote.

**Missing evidence and effect:** Exact configuration, child eligibility and personal quotes missing; no insurer acceptance inferred from relationship list.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 3, 3.20; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 3, 3.20; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: Do not add the spouse simply because the buyer is married.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Record spouse as a related person with separate cover, not automatically as a proposed insured. Select configurations by the two intended members and confirm dependent-child eligibility. Preserve spouse cover only where expressly relevant to coordination. A shared account or legal marriage does not authorize silently adding someone to a quote.
- Retain the material limitation: Exact configuration, child eligibility and personal quotes missing; no insurer acceptance inferred from relationship list.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-05 — My partner and I are not married and want to know whether one floater accepts us.

**Decision tested:** A family label must not imply acceptance of an unmarried partner.

**Customer and facts:** authored stipulations: Buyer Dev, 38; unmarried partner Mira 36; want one floater; neither has existing insurance; no legal marriage documents.; follow up statement: No. The candidate is New India AS; we have only seen the word family.

**Conversation:**

1. customer: My partner and I are not married and want to know whether one floater accepts us.
2. adviser: Are you legally married, and which exact product's relationship definition is being considered?
3. customer: No. The candidate is New India AS; we have only seen the word family.
4. adviser: The preserved New India definition specifies legally wedded spouse. It does not establish the partner's eligibility as spouse. Retain alternative separate policies or products with explicit partner eligibility as uncertain candidates; do not falsify relationship or exclude either person from all insurance.

**Expected assessment:** The preserved New India definition specifies legally wedded spouse. It does not establish the partner's eligibility as spouse. Retain alternative separate policies or products with explicit partner eligibility as uncertain candidates; do not falsify relationship or exclude either person from all insurance.

**Missing evidence and effect:** No original product explicitly supporting this relationship supplied; quotation and accepted terms remain unknown.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 3, 3.20; ce59f6f9785af314739a4b9a1b7bce63880793e5923d8d39ed20c91053312b48 physical page 19, I.1 note

**Judging criteria:**

- Preserve the decision boundary: A family label must not imply acceptance of an unmarried partner.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: The preserved New India definition specifies legally wedded spouse. It does not establish the partner's eligibility as spouse. Retain alternative separate policies or products with explicit partner eligibility as uncertain candidates; do not falsify relationship or exclude either person from all insurance.
- Retain the material limitation: No original product explicitly supporting this relationship supplied; quotation and accepted terms remain unknown.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-06 — I want to include my parents-in-law alongside my spouse and parents.

**Decision tested:** A relationship listed as allowed may still exceed the configuration member limit.

**Customer and facts:** authored stipulations: Buyer Dev 38; spouse 36; parents 66 and 63; parents-in-law 64 and 61; six proposed insureds; wants one New India AS floater.; follow up statement: The document lists parents and parents-in-law, but I have no six-member offer.

**Conversation:**

1. customer: I want to include my parents-in-law alongside my spouse and parents.
2. adviser: Does the selected configuration permit six people with these relationships and ages, not only list the relationship names?
3. customer: The document lists parents and parents-in-law, but I have no six-member offer.
4. adviser: The family definition supports these relationship categories, but a category list is not proof of every age/member-count configuration. Retain each person's relationship, DOB and disclosure separately. Obtain schedule/prospectus/configuration limits before confirming one floater; compare separate arrangements if no compliant six-member option is established.

**Expected assessment:** The family definition supports these relationship categories, but a category list is not proof of every age/member-count configuration. Retain each person's relationship, DOB and disclosure separately. Obtain schedule/prospectus/configuration limits before confirming one floater; compare separate arrangements if no compliant six-member option is established.

**Missing evidence and effect:** Member-count and age configuration rules, disclosures and an actual offer are missing; no six-person acceptance or price manufactured.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 3, 3.20; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44; ce59f6f9785af314739a4b9a1b7bce63880793e5923d8d39ed20c91053312b48 physical page 19, I.1 note

**Judging criteria:**

- Preserve the decision boundary: A relationship listed as allowed may still exceed the configuration member limit.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: The family definition supports these relationship categories, but a category list is not proof of every age/member-count configuration. Retain each person's relationship, DOB and disclosure separately. Obtain schedule/prospectus/configuration limits before confirming one floater; compare separate arrangements if no compliant six-member option is established.
- Retain the material limitation: Member-count and age configuration rules, disclosures and an actual offer are missing; no six-person acceptance or price manufactured.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-07 — How much does adding my older mother change these joint-versus-split quote costs?

**Decision tested:** Compute marginal and total quote costs while preserving different risk pools; do not infer causal age loading or equivalent cover.

**Customer and facts:** authored stipulations: Buyer Ritu, 40; spouse, 42; mother, 68. Synthetic complete written offers for the same term: couple only, INR 18000 for shared SI 1000000; all three jointly, INR 26000 for shared SI 1000000; mother alone, INR 11000 for individual SI 1000000. Quote ownership, term, taxes and equal options except for member grouping and cover pools are stipulated. Issuer acceptance of the relationships has not been independently verified.; follow up statement: They are complete totals for the same term. The joint quote has just one 1000000 pool; splitting keeps a 1000000 couple pool and a separate 1000000 mother pool.

**Conversation:**

1. customer: How much does adding my older mother change these joint-versus-split quote costs?
2. adviser: Are all three figures complete for the same term, and does the joint quote add a separate cover pool for your mother?
3. customer: They are complete totals for the same term. The joint quote has just one 1000000 pool; splitting keeps a 1000000 couple pool and a separate 1000000 mother pool.
4. adviser: The marginal quoted cost of adding the mother to the joint pool is 26000 minus 18000 = INR 8000. The split total is 18000 plus 11000 = INR 29000, or 3000 more than the joint quote. These are not equivalent insurance amounts: the joint quote shares one 1000000 pool; splitting creates separate pools. Do not call 8000 a standalone mother premium or infer an age-rating formula from the difference. Actual suitability still requires verified family acceptance and comparable original terms.

**Expected assessment:** The marginal quoted cost of adding the mother to the joint pool is 26000 minus 18000 = INR 8000. The split total is 18000 plus 11000 = INR 29000, or 3000 more than the joint quote. These are not equivalent insurance amounts: the joint quote shares one 1000000 pool; splitting creates separate pools. Do not call 8000 a standalone mother premium or infer an age-rating formula from the difference. Actual suitability still requires verified family acceptance and comparable original terms.

**Missing evidence and effect:** Quotes and acceptance are explicit synthetic inputs, not evidence that an insurer sells this grouping. Complete offer originals and eligibility remain required.

**Calculations:**

- label: Marginal joint quote cost; inputs: joint premium inr: 26000; couple premium inr: 18000; result unit: INR; reference expression: joint_premium_inr - couple_premium_inr; expected: 8000; assumptions: Synthetic complete same-term quotes. This difference is not a standalone mother premium or a causal age loading.
- label: Split policy quote total; inputs: couple premium inr: 18000; mother premium inr: 11000; result unit: INR; reference expression: couple_premium_inr + mother_premium_inr; expected: 29000; assumptions: Synthetic complete same-term quotes with separate couple and mother cover pools; no insurer sale or acceptance inferred.
- label: Additional cost of split quotes; inputs: split premium inr: 29000; joint premium inr: 26000; result unit: INR; reference expression: split_premium_inr - joint_premium_inr; expected: 3000; assumptions: Different cover pools remain explicit. Equal options and complete totals are fixture premises.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 21, 12 Sum insured

**Judging criteria:**

- Compute marginal and total quote costs while preserving different risk pools; do not infer causal age loading or equivalent cover.
- Reach the exact bounded disposition: The marginal quoted cost of adding the mother to the joint pool is 26000 minus 18000 = INR 8000. The split total is 18000 plus 11000 = INR 29000, or 3000 more than the joint quote. These are not equivalent insurance amounts: the joint quote shares one 1000000 pool; splitting creates separate pools. Do not call 8000 a standalone mother premium or infer an age-rating formula from the difference. Actual suitability still requires verified family acceptance and comparable original terms.
- Preserve the unresolved effect: Quotes and acceptance are explicit synthetic inputs, not evidence that an insurer sells this grouping. Complete offer originals and eligibility remain required.
- Do not promote fixture inputs to issuer evidence or count this as completed insurance advice.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-08 — A child has a chronic illness and we want to avoid exhausting everyone else's cover.

**Decision tested:** Higher overall SI may leave the child's disease sublimit unchanged.

**Customer and facts:** authored stipulations: Buyer Dev 38; child 9 with chronic kidney disease; family SI options 500000 and 1000000; child treatment sublimit claimed 200000 by sales summary.; follow up statement: The summary does not say; expected dialysis spend 250000/year.

**Conversation:**

1. customer: A child has a chronic illness and we want to avoid exhausting everyone else's cover.
2. adviser: Does the disease sublimit increase with SI or remain fixed, and does restoration replenish it?
3. customer: The summary does not say; expected dialysis spend 250000/year.
4. adviser: Higher shared SI need not change a fixed disease cap. Obtain the exact child eligibility, daycare/dialysis grant, waiting, sublimit base and replenishment rule. A 250000 expense estimate against a stipulated fixed 200000 cap would leave at least 50000 before other deductions, but this cap is not yet original-backed. Keep that arithmetic explicitly hypothetical.

**Expected assessment:** Higher shared SI need not change a fixed disease cap. Obtain the exact child eligibility, daycare/dialysis grant, waiting, sublimit base and replenishment rule. A 250000 expense estimate against a stipulated fixed 200000 cap would leave at least 50000 before other deductions, but this cap is not yet original-backed. Keep that arithmetic explicitly hypothetical.

**Missing evidence and effect:** Child acceptance and authentic disease-cap/restoration provisions missing; no fixed 200000 cap published as a policy fact.

**Calculations:**

- label: Hypothetical unchanged child sublimit gap; inputs: assumed cap: 200000; expense: 250000; result unit: INR; reference expression: expense-assumed_cap; expected: 50000; assumptions: The200000 cap is an explicit hypothetical premise, not a sourced benefit of any named insurer.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 32, Annexure C row 90; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.6; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 10, 6.2c; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III.L

**Judging criteria:**

- Preserve the decision boundary: Higher overall SI may leave the child's disease sublimit unchanged.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Higher shared SI need not change a fixed disease cap. Obtain the exact child eligibility, daycare/dialysis grant, waiting, sublimit base and replenishment rule. A 250000 expense estimate against a stipulated fixed 200000 cap would leave at least 50000 before other deductions, but this cap is not yet original-backed. Keep that arithmetic explicitly hypothetical.
- Retain the material limitation: Child acceptance and authentic disease-cap/restoration provisions missing; no fixed 200000 cap published as a policy fact.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-09 — We live in different cities and need a family plan usable in both places.

**Decision tested:** One person's usable network is not evidence for another city.

**Customer and facts:** authored stipulations: Buyer Dev, 38, in Kota; spouse, 36, in Delhi for work; child, 9, in Kota; one floater requested; the family needs access to hospitals in both cities.; follow up statement: Two named branches are essential; I have only a Kota network listing.

**Conversation:**

1. customer: We live in different cities and need a family plan usable in both places.
2. adviser: Which branches need cashless access, and is the Delhi address temporary residence or a changed policy address?
3. customer: Two named branches are essential; I have only a Kota network listing.
4. adviser: Record residence and treatment preferences per person. A Kota network observation proves nothing about the Delhi branch; territory India does not establish network or zone co-pay. Request exact dated branch matches and applicable residential/treatment-zone terms for the chosen configuration.

**Expected assessment:** Record residence and treatment preferences per person. A Kota network observation proves nothing about the Delhi branch; territory India does not establish network or zone co-pay. Request exact dated branch matches and applicable residential/treatment-zone terms for the chosen configuration.

**Missing evidence and effect:** Delhi branch evidence and relevant zone conditions absent; one city's match cannot validate the family network requirement.

**Original anchors:** ce59f6f9785af314739a4b9a1b7bce63880793e5923d8d39ed20c91053312b48 physical page 26, II.A.I.5a; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 5, IV.11; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 6, V.2B note; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 7, V.22

**Judging criteria:**

- Preserve the decision boundary: One person's usable network is not evidence for another city.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Record residence and treatment preferences per person. A Kota network observation proves nothing about the Delhi branch; territory India does not establish network or zone co-pay. Request exact dated branch matches and applicable residential/treatment-zone terms for the chosen configuration.
- Retain the material limitation: Delhi branch evidence and relevant zone conditions absent; one city's match cannot validate the family network requirement.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-02-10 — We want to split a large family between two floaters without duplicating anyone.

**Decision tested:** Every intended person appears once and membership changes invalidate both comparisons.

**Customer and facts:** authored stipulations: Buyer Dev 38; family roster Dev, Mira 36, child 9, child 6, father 66, mother 63; considers two floaters; initial grouping accidentally lists child 9 twice.; follow up statement: Correction: first policy Dev, Mira, children; second policy father, mother. No duplicates intended.

**Conversation:**

1. customer: We want to split a large family between two floaters without duplicating anyone.
2. adviser: Confirm the intended membership of each policy and whether anyone needs deliberate overlapping cover.
3. customer: Correction: first policy Dev, Mira, children; second policy father, mother. No duplicates intended.
4. adviser: Preserve one canonical person identity per family member and explicit membership sets. The correction removes the duplicate from the second quote and invalidates both premium/limit comparisons derived from the old grouping. Parent-product eligibility still needs its own original evidence; arithmetic grouping is not acceptance.

**Expected assessment:** Preserve one canonical person identity per family member and explicit membership sets. The correction removes the duplicate from the second quote and invalidates both premium/limit comparisons derived from the old grouping. Parent-product eligibility still needs its own original evidence; arithmetic grouping is not acceptance.

**Missing evidence and effect:** Both configurations and quotes absent. Current roster can be resolved while product suitability remains unestablished.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 3, 3.20; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 2, Specific definitions: Family

**Judging criteria:**

- Preserve the decision boundary: Every intended person appears once and membership changes invalidate both comparisons.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Preserve one canonical person identity per family member and explicit membership sets. The correction removes the duplicate from the second quote and invalidates both premium/limit comparisons derived from the old grouping. Parent-product eligibility still needs its own original evidence; arithmetic grouping is not acceptance.
- Retain the material limitation: Both configurations and quotes absent. Current roster can be resolved while product suitability remains unestablished.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

