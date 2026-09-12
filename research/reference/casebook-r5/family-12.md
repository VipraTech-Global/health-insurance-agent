# Reference family 12

Ten cases in the fixed reference set. Missing originals, configuration or customer evidence cannot count as successful insurance advice.

## ref-12-01 — My first claim exhausts the base sum insured and I want restoration for the same admission.

**Decision tested:** Restoration may be unavailable to the claim that triggers it.

**Customer and facts:** authored stipulations: Buyer-insured Jaya 39; Star Gold base SI 500000, defined limit 300000; ordinary admission exhausts SI; wants recharge on same episode.; follow up statement: Ordinary treatment, not modern; no final claim ledger.

**Conversation:**

1. customer: My first claim exhausts the base sum insured and I want restoration for the same admission.
2. adviser: Is the treatment excluded from recharge and what defined-limit tier controls the recharge amount?
3. customer: Ordinary treatment, not modern; no final claim ledger.
4. adviser: Star Gold III.L expressly permits same-admission recharge once, with tiered amount and no carryover, but V.23 automatic expiry on exhaustion creates a precedence dependency. Do not generalize another product's later-claim restoration restriction or promise this payment until the conflict and qualifying ledger are resolved.

**Expected assessment:** Star Gold III.L expressly permits same-admission recharge once, with tiered amount and no carryover, but V.23 automatic expiry on exhaustion creates a precedence dependency. Do not generalize another product's later-claim restoration restriction or promise this payment until the conflict and qualifying ledger are resolved.

**Missing evidence and effect:** Recharge/expiry precedence and actual exhausted-cover ledger unresolved; no final extended payment.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III.L; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 7, V.23; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note3

**Judging criteria:**

- Preserve the decision boundary: Restoration may be unavailable to the claim that triggers it.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Star Gold III.L expressly permits same-admission recharge once, with tiered amount and no carryover, but V.23 automatic expiry on exhaustion creates a precedence dependency. Do not generalize another product's later-claim restoration restriction or promise this payment until the conflict and qualifying ledger are resolved.
- Retain the material limitation: Recharge/expiry precedence and actual exhausted-cover ledger unresolved; no final extended payment.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-02 — My second admission is for the same illness and restoration has a related-illness condition.

**Decision tested:** Relatedness can depend on both disease and a relapse interval.

**Customer and facts:** authored stipulations: Buyer-insured Jaya 39; second admission for possibly same illness; last consultation 1 Aug 2026, next admission 10 Sep; restoration rider unknown.; follow up statement: No rider supplied; medical relatedness uncertain.

**Conversation:**

1. customer: My second admission is for the same illness and restoration has a related-illness condition.
2. adviser: What does the applicable restoration clause mean by related illness and does it use the any-one-illness definition?
3. customer: No rider supplied; medical relatedness uncertain.
4. adviser: Forty elapsed days fit within a 45-day relapse interval in the read illness definition, but that does not prove every restoration rider uses that definition or excludes the episode. Star Gold expressly allows same-illness recharge under its own conditions. Require the exact chosen rider and clinical link before deciding.

**Expected assessment:** Forty elapsed days fit within a 45-day relapse interval in the read illness definition, but that does not prove every restoration rider uses that definition or excludes the episode. Star Gold expressly allows same-illness recharge under its own conditions. Require the exact chosen rider and clinical link before deciding.

**Missing evidence and effect:** Applicable restoration relatedness rule and medical attribution missing; no inference from diagnosis labels alone.

**Calculations:**

- label: Relapse elapsed interval; inputs: last consultation: 2026-08-01; assessment: 2026-09-10; result unit: elapsed_day; reference expression: assessment-last_consultation; expected: 40; assumptions: Definition-specific45day interval only; do not apply it automatically to another restoration clause.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 1, 3.3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III.L; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: Relatedness can depend on both disease and a relapse interval.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Forty elapsed days fit within a 45-day relapse interval in the read illness definition, but that does not prove every restoration rider uses that definition or excludes the episode. Star Gold expressly allows same-illness recharge under its own conditions. Require the exact chosen rider and clinical link before deciding.
- Retain the material limitation: Applicable restoration relatedness rule and medical attribution missing; no inference from diagnosis labels alone.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-03 — Two members share a floater and only one has made a claim.

**Decision tested:** Shared balance is reduced by one member even when another has no claims.

**Customer and facts:** authored stipulations: Buyer Jaya 39, spouse 37; hypothetical shared SI 500000; Jaya eligible paid claim 300000; spouse has no claims; prior others 0.; follow up statement: The SI is shared. There are no other reserves, paid claims or restored amounts.

**Conversation:**

1. customer: Two members share a floater and only one has made a claim.
2. adviser: Is SI shared and are there any reserves or restored amounts already granted?
3. customer: The SI is shared. There are no other reserves, paid claims or restored amounts.
4. adviser: The shared base remainder is 200000, not 500000 for the unclaimed spouse. Preserve paid usage and each member while keeping restoration grants and benefit sublimits separate. This numerical fixture does not establish that a later 200000 bill is admissible or that restoration occurs.

**Expected assessment:** The shared base remainder is 200000, not 500000 for the unclaimed spouse. Preserve paid usage and each member while keeping restoration grants and benefit sublimits separate. This numerical fixture does not establish that a later 200000 bill is admissible or that restoration occurs.

**Missing evidence and effect:** Actual named policy and claims ledger needed for real availability; broader restoration terms not supplied.

**Calculations:**

- label: Shared remaining base pool; inputs: si: 500000; paid used: 300000; result unit: INR; reference expression: si-paid_used; expected: 200000; assumptions: All stated monetary inputs are INR and hypothetical. Only the specified arithmetic is resolved; broader insurance dependencies remain in the case record.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note7; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 21, 12 Sum insured

**Judging criteria:**

- Preserve the decision boundary: Shared balance is reduced by one member even when another has no claims.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: The shared base remainder is 200000, not 500000 for the unclaimed spouse. Preserve paid usage and each member while keeping restoration grants and benefit sublimits separate. This numerical fixture does not establish that a later 200000 bill is admissible or that restoration occurs.
- Retain the material limitation: Actual named policy and claims ledger needed for real availability; broader restoration terms not supplied.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-04 — My policy restores cover only after complete exhaustion.

**Decision tested:** One rupee remaining can change an exhaustion-only trigger.

**Customer and facts:** authored stipulations: Buyer-insured Jaya 39; benefit claimed exhaustion-only; base SI 500000; paid 499999; no reserves; original Star Gold considered.; follow up statement: Read Star Gold says SI exhausted/exceeded; 1 rupee remains.

**Conversation:**

1. customer: My policy restores cover only after complete exhaustion.
2. adviser: Does the trigger require exhaustion and can partial expenditure trigger it?
3. customer: Read Star Gold says SI exhausted/exceeded; 1 rupee remains.
4. adviser: A strict exhaustion condition is not met merely because all but 1 rupee is used. At 500000 usage it crosses the exhaustion boundary; other recharge conditions and the expiry conflict remain required. Do not round 499999 up or confuse near-exhaustion with a trigger.

**Expected assessment:** A strict exhaustion condition is not met merely because all but 1 rupee is used. At 500000 usage it crosses the exhaustion boundary; other recharge conditions and the expiry conflict remain required. Do not round 499999 up or confuse near-exhaustion with a trigger.

**Missing evidence and effect:** Complete ledger and recharge/expiry interpretation unresolved; threshold illustration is not approval of restored benefit.

**Calculations:**

- label: Exhaustion equality boundary; inputs: used: 499999; base: 500000; result unit: boolean; reference expression: used >= base; expected: False; assumptions: Do not round nearly exhausted to exhausted.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III.L; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 7, V.23

**Judging criteria:**

- Preserve the decision boundary: One rupee remaining can change an exhaustion-only trigger.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: A strict exhaustion condition is not met merely because all but 1 rupee is used. At 500000 usage it crosses the exhaustion boundary; other recharge conditions and the expiry conflict remain required. Do not round 499999 up or confuse near-exhaustion with a trigger.
- Retain the material limitation: Complete ledger and recharge/expiry interpretation unresolved; threshold illustration is not approval of restored benefit.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-05 — My insurer advertises unlimited restoration but there is a per-claim limit.

**Decision tested:** Unlimited restoration frequency does not establish unlimited payment for one claim.

**Customer and facts:** authored stipulations: Buyer-insured Jaya 39; marketing says unlimited restoration; per-claim limit reportedly 500000; one bill 900000.; follow up statement: Only headline known; detailed wording missing.

**Conversation:**

1. customer: My insurer advertises unlimited restoration but there is a per-claim limit.
2. adviser: Does unlimited refer to number of restorations or monetary cover for a single claim?
3. customer: Only headline known; detailed wording missing.
4. adviser: Unlimited frequency is a distinct dimension from a per-claim amount. Under the reported fixed 500000 per-claim cap, a 900000 claim cannot be treated as fully payable simply by repeated restoration. Obtain the actual restoration grant, trigger, same-claim permission and caps; no unlimited amount may be inferred.

**Expected assessment:** Unlimited frequency is a distinct dimension from a per-claim amount. Under the reported fixed 500000 per-claim cap, a 900000 claim cannot be treated as fully payable simply by repeated restoration. Obtain the actual restoration grant, trigger, same-claim permission and caps; no unlimited amount may be inferred.

**Missing evidence and effect:** Actual unlimited-restoration original and per-claim interactions absent; 500000 cap is scenario-reported, not product fact.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III.L; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44

**Judging criteria:**

- Preserve the decision boundary: Unlimited restoration frequency does not establish unlimited payment for one claim.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Unlimited frequency is a distinct dimension from a per-claim amount. Under the reported fixed 500000 per-claim cap, a 900000 claim cannot be treated as fully payable simply by repeated restoration. Obtain the actual restoration grant, trigger, same-claim permission and caps; no unlimited amount may be inferred.
- Retain the material limitation: Actual unlimited-restoration original and per-claim interactions absent; 500000 cap is scenario-reported, not product fact.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-06 — I earned a cumulative bonus and want to know how a claim affects it at renewal.

**Decision tested:** A claim reported after renewal can invalidate already awarded bonus.

**Customer and facts:** authored stipulations: Buyer-insured Jaya 39; New India AS base SI 500000, earned CB 100000; claim in expiring year reported after renewal accepted; compare HDFC notice.; follow up statement: New India AS; I found HDFC notice saying claim does not reduce bonus.

**Conversation:**

1. customer: I earned a cumulative bonus and want to know how a claim affects it at renewal.
2. adviser: Which exact insurer/version and claim-report event govern the bonus?
3. customer: New India AS; I found HDFC notice saying claim does not reduce bonus.
4. adviser: Do not apply HDFC's insurer/product-scoped notice to New India. New India section 5, note h says an awarded bonus is withdrawn if an expiring-year claim is notified after renewal acceptance; its other bonus rules and applicable regulation must be read together. Retain earned, awarded, withdrawn bonus events rather than rewriting historical SI.

**Expected assessment:** Do not apply HDFC's insurer/product-scoped notice to New India. New India section 5, note h says an awarded bonus is withdrawn if an expiring-year claim is notified after renewal acceptance; its other bonus rules and applicable regulation must be read together. Retain earned, awarded, withdrawn bonus events rather than rewriting historical SI.

**Missing evidence and effect:** Exact policy/claim dates and governing amendments needed before final renewal amount; cross-insurer notice is not a valid override.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 9, 5; 9bdf3e5379a494ffe61af7a07496bb0e7333124da45ec72fcf21583435d0352e physical page 3, 2a; 9bdf3e5379a494ffe61af7a07496bb0e7333124da45ec72fcf21583435d0352e physical page 3, 2b; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 9, 5 including notes a-h

**Judging criteria:**

- Preserve the decision boundary: A claim reported after renewal can invalidate already awarded bonus.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Do not apply HDFC's insurer/product-scoped notice to New India. New India section 5, note h says an awarded bonus is withdrawn if an expiring-year claim is notified after renewal acceptance; its other bonus rules and applicable regulation must be read together. Retain earned, awarded, withdrawn bonus events rather than rewriting historical SI.
- Retain the material limitation: Exact policy/claim dates and governing amendments needed before final renewal amount; cross-insurer notice is not a valid override.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-07 — My restoration benefit applies to unrelated illnesses and the diagnosis is uncertain.

**Decision tested:** Do not assert unrelated illness when diagnosis is pending.

**Customer and facts:** authored stipulations: Buyer-insured Jaya 39; restoration rider requires unrelated illness reportedly; second admission diagnosis pending.; follow up statement: Neither; investigations ongoing.

**Conversation:**

1. customer: My restoration benefit applies to unrelated illnesses and the diagnosis is uncertain.
2. adviser: Has the second condition been established and how does the rider define relatedness?
3. customer: Neither; investigations ongoing.
4. adviser: Represent relatedness as unknown, not false. Retrieve the exact rider and clinical evidence; a new admission identifier does not prove an unrelated illness. Keep an eligible-alternative branch and an unresolved branch without inventing diagnosis or restoration credit.

**Expected assessment:** Represent relatedness as unknown, not false. Retrieve the exact rider and clinical evidence; a new admission identifier does not prove an unrelated illness. Keep an eligible-alternative branch and an unresolved branch without inventing diagnosis or restoration credit.

**Missing evidence and effect:** Authentic relatedness condition and final clinical linkage missing.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 1, 3.3; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III.L

**Judging criteria:**

- Preserve the decision boundary: Do not assert unrelated illness when diagnosis is pending.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Represent relatedness as unknown, not false. Retrieve the exact rider and clinical evidence; a new admission identifier does not prove an unrelated illness. Keep an eligible-alternative branch and an unresolved branch without inventing diagnosis or restoration credit.
- Retain the material limitation: Authentic relatedness condition and final clinical linkage missing.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-08 — A claim crosses the policy-year boundary and I need the correct year's limits.

**Decision tested:** Do not split one claim between years solely because dates cross renewal.

**Customer and facts:** authored stipulations: Buyer-insured Jaya 39; admission 28 Sep 2026, discharge 5 Oct; renewal 1 Oct; bill 600000; first year balance 200000, next year SI 500000.; follow up statement: No allocation clause found; hospital bill spans both years.

**Conversation:**

1. customer: A claim crosses the policy-year boundary and I need the correct year's limits.
2. adviser: Does the contract allocate an ongoing admission by admission date, service date or another explicit rule?
3. customer: No allocation clause found; hospital bill spans both years.
4. adviser: Do not split the bill across years solely to use 700000 combined balance. Preserve episode dates and time-attributed expenses, both policy revisions and any explicit continuing-admission rule. Annual reset and no-carryover do not by themselves settle which year bears each cost.

**Expected assessment:** Do not split the bill across years solely to use 700000 combined balance. Preserve episode dates and time-attributed expenses, both policy revisions and any explicit continuing-admission rule. Annual reset and no-carryover do not by themselves settle which year bears each cost.

**Missing evidence and effect:** Specific cross-renewal allocation clause, accepted renewed terms and itemized service dates absent.

**Original anchors:** c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III note5; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 6, 3.44; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 20, 10.21

**Judging criteria:**

- Preserve the decision boundary: Do not split one claim between years solely because dates cross renewal.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Do not split the bill across years solely to use 700000 combined balance. Preserve episode dates and time-attributed expenses, both policy revisions and any explicit continuing-admission rule. Annual reset and no-carryover do not by themselves settle which year bears each cost.
- Retain the material limitation: Specific cross-renewal allocation clause, accepted renewed terms and itemized service dates absent.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-09 — My bonus is capped as a percentage of base sum insured.

**Decision tested:** Bonus cap and displayed total cover have different monetary meanings.

**Customer and facts:** authored stipulations: Buyer-insured Jaya 39; New India AS base SI 500000, CB 250000; displayed total 750000; asks next claim-free year increase.; follow up statement: Base unchanged; current CB already 250000.

**Conversation:**

1. customer: My bonus is capped as a percentage of base sum insured.
2. adviser: Is the bonus maximum 50% of base SI and has the base changed?
3. customer: Base unchanged; current CB already 250000.
4. adviser: Under the preserved 50% base ceiling, 250000 already reaches the bonus cap; total 750000 is not a new base for earning another 50%. If base or insurer changes, apply its explicit recalculation rule. Keep base, CB and displayed total separate; final renewal depends on claims and governing version.

**Expected assessment:** Under the preserved 50% base ceiling, 250000 already reaches the bonus cap; total 750000 is not a new base for earning another 50%. If base or insurer changes, apply its explicit recalculation rule. Keep base, CB and displayed total separate; final renewal depends on claims and governing version.

**Missing evidence and effect:** Actual renewal/claim status and applicable amendments needed before confirming insurer-awarded bonus.

**Calculations:**

- label: Bonus ceiling and displayed total; inputs: base: 500000; bonus ratio: 0.50; result unit: INR; reference expression: base+base*bonus_ratio; expected: 750000; assumptions: All stated monetary inputs are INR and hypothetical. Only the specified arithmetic is resolved; broader insurance dependencies remain in the case record.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 9, 5; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 9, 5 note g; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 9, 5 including notes a-h

**Judging criteria:**

- Preserve the decision boundary: Bonus cap and displayed total cover have different monetary meanings.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Under the preserved 50% base ceiling, 250000 already reaches the bonus cap; total 750000 is not a new base for earning another 50%. If base or insurer changes, apply its explicit recalculation rule. Keep base, CB and displayed total separate; final renewal depends on claims and governing version.
- Retain the material limitation: Actual renewal/claim status and applicable amendments needed before confirming insurer-awarded bonus.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

## ref-12-10 — My family has made several claims and an annual benefit sublimit is exhausted.

**Decision tested:** Restored base cover need not restore an exhausted sublimit.

**Customer and facts:** authored stipulations: Buyer Jaya 39 and spouse 37; shared base 500000; annual procedure cap 100000 exhausted; base reportedly 'restored'; new procedure cost 50000.; follow up statement: No express cap-reset term supplied.

**Conversation:**

1. customer: My family has made several claims and an annual benefit sublimit is exhausted.
2. adviser: Does the restoration original replenish that specific procedure cap as well as base SI?
3. customer: No express cap-reset term supplied.
4. adviser: Base restoration does not establish replenishment of every annual sublimit. Retain the procedure-cap usage and request an explicit reset or augmentation clause. If the cap remains 100000 and 100000 has been used, the additional 50000 has no remaining allowance under that cap, regardless of the nominal restored base. The actual contract still needs to establish whether that condition applies.

**Expected assessment:** Base restoration does not establish replenishment of every annual sublimit. Retain the procedure-cap usage and request an explicit reset or augmentation clause. If the cap remains 100000 and 100000 has been used, the additional 50000 has no remaining allowance under that cap, regardless of the nominal restored base. The actual contract still needs to establish whether that condition applies.

**Missing evidence and effect:** Specific sublimit/reset relationship and accepted restoration event missing; do not silently reset all benefit ledgers.

**Calculations:**

- label: Exhausted independent sublimit; inputs: annual cap: 100000; prior use: 100000; result unit: INR; reference expression: max(annual_cap-prior_use,0); expected: 0; assumptions: Restored base does not restore a distinct exhausted cap without applicable original authority.

**Original anchors:** 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.6; 890ab4794c98a56eda8ef2749124e2114589cc00a5e596bed0392ea13667efce physical page 8, 4.3; c0b41932d7d57e1165dd5524cbe526e8bec9b38258404f62281198264ea52a31 physical page 4, III.L

**Judging criteria:**

- Preserve the decision boundary: Restored base cover need not restore an exhausted sublimit.
- After the customer reply, do not ask again for information explicitly supplied in that reply.
- Reach the supported assessment: Base restoration does not establish replenishment of every annual sublimit. Retain the procedure-cap usage and request an explicit reset or augmentation clause. If the cap remains 100000 and 100000 has been used, the additional 50000 has no remaining allowance under that cap, regardless of the nominal restored base. The actual contract still needs to establish whether that condition applies.
- Retain the material limitation: Specific sublimit/reset relationship and accepted restoration event missing; do not silently reset all benefit ledgers.
- Resolve cited original hash/page/context and load connected restrictions before an entitlement claim.

**Status:** `customer_decision_has_material_gaps`; no adviser attempt or acceptance pass.

