# Reference family 20

Ten cases in the fixed reference set. Missing originals, configuration or customer evidence cannot count as successful insurance advice.

## ref-20-01 — I need insurance, I am 35, I live in Kota, and I have no health insurance.

**Decision tested:** Age information is known while the insured subject remains initially unknown; a fluent first-person introduction alone does not authorize assuming who will be insured.

**Customer and facts:** buyer: P01; age subject: P01; age years: 35; residence: Kota; existing insurance: False; intended insured: None

**Conversation:**

1. customer: I need insurance. I am 35, live inKota and have no health insurance.
2. adviser: Who should the policy cover: you, or someone else?
3. customer: Me only. I can spend 15000 rupees per year.
4. adviser: I have you as the person to insure, with an annual budget of₹15000. Do you have any diagnosed conditions, ongoing medicines or recent medical advice that should be disclosed?

**Expected assessment:** Confirm the insured person before assigning eligibility. Preserve age35 as customer-reported age, not a fabricated birth date. Kota establishes residence, not a hospital branch or guaranteed cashless access. Budget and an explicit self-only confirmation may be saved; do not produce a product shortlist before material facts and originals support it.

**Missing evidence and effect:** Exact DOB/age reference event, medical disclosures, priorities and applicable product/quote originals. Intended insured and budget are now confirmed, so do not repeat those questions.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- Exactly one intended insured afterturn3
- No derived birth date from age alone
- No question repeats already confirmed Kota/age unless clarification is needed
- No unsupported plan recommendation
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-02 — I said I was 35 but I need to correct my age to 36.

**Decision tested:** Correcting age need not change every result, but it must trigger reevaluation of dependencies that used age.

**Customer and facts:** buyer: P01; insured: P01; initial age: 35; corrected age: 36; correction revision: 2

**Conversation:**

1. customer: I am 35 and need a policy for myself.
2. adviser: I have recorded age 35 for you.
3. customer: Correction: I am 36, not 35.
4. adviser: I have corrected your age to 36. Any eligibility or quote that used 35 needs to be checked again.

**Expected assessment:** The current fact is age36 with the correction as provenance. Preserve the superseded35only as permitted revision history, never as a competing current fact or a second insured person. Invalidate dependent eligibility/pricing; do not fabricate a birth date, claim that premiums definitely change, or silently reuse an old quote.

**Missing evidence and effect:** Applicable insurer originals, actual accepted configuration and further case-specific disclosures remain required before any product or eligibility answer.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- One current age36 forP01
- Original correction source retained subject to deletion policy
- Decisions depending onA1 cannot be presented as current
- No unrelated family fact changes
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-03 — I am 35 but the insurance is for my 70-year-old mother.

**Decision tested:** Buyer, payer, proposer and insured roles can belong to different people.

**Customer and facts:** buyer: P01; buyer age: 35; insured: P02; insured relationship: mother; insured age: 70; buyer is insured: False

**Conversation:**

1. customer: I am 35 and live inKota. I need insurance.
2. adviser: Who should it cover?
3. customer: My 70-year-old mother, not me. I will pay.
4. adviser: The cover is for your mother, age 70, and you are the buyer and payer. Where does she live, and what conditions or ongoing medicines should be disclosed for her?

**Expected assessment:** Assign35 andKota to the buyer unless corrected; assign70 to the mother. Do not copy buyer location or medical history to her, add the buyer to coverage, or select products for a35-year-old. Payment responsibility does not establish insured membership or an insurer-approved proposer relationship.

**Missing evidence and effect:** Applicable insurer originals, actual accepted configuration and further case-specific disclosures remain required before any product or eligibility answer.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- Mother is the sole intended insured
- Buyer age35 does not enter mother eligibility
- Mother residence remains unknown until confirmed
- No age-based product exclusion without applicable originals
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-04 — I closed this conversation yesterday and want to continue with the saved details.

**Decision tested:** Persisted customer facts and a saved answer have separate freshness; reopening is not proof that an old answer remains valid.

**Customer and facts:** owner: ACCOUNT-A; conversation: CONV-A; saved revision: 7; last saved date: 2026-09-09; reopened date: 2026-09-10; saved insured: motherP02,70

**Conversation:**

1. customer: Continue yesterday’s conversation about my mother.
2. adviser: I have the saved conversation for your mother, age 70. Have any medical details or priorities changed since yesterday?
3. customer: Her doctor added a new medicine today.
4. adviser: Please give its name and the reason it was prescribed. I will update her disclosure and recheck any advice affected by it.

**Expected assessment:** After ownership check, reopen the same saved conversation and fact revision instead of creating a guessed profile. Retain the new medicine as an incomplete reported fact until clarified; do not infer its diagnosis. Recheck both customer-dependent decisions and corpus revisions that changed since the saved decision.

**Missing evidence and effect:** Applicable insurer originals, actual accepted configuration and further case-specific disclosures remain required before any product or eligibility answer.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- Reopening retains person and conversation identity
- No other account history is loaded
- No repeated inference merely to replay stored events
- Stale prior decisions are visibly pending recheck
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-05 — I started a new conversation and do not want old medical details reused without asking.

**Decision tested:** An account may own both conversations while the user still prohibits reuse between them.

**Customer and facts:** owner: ACCOUNT-A; old conversation: CONV-A; new conversation: CONV-B; permission to reuse old medical facts: False

**Conversation:**

1. customer: Start a new conversation. Do not reuse my earlier medical details unless I ask.
2. adviser: Who should this new conversation cover?
3. customer: My spouse. We can discuss her details here.
4. adviser: What is her age, and what cover does she already have?

**Expected assessment:** Honor the explicit no-reuse preference. The new conversation starts with its own confirmed insured subjects and facts. Do not expose old diagnoses in a reminder or confirmation question, use them invisibly for recommendations, or treat account ownership as consent to copy medical context across conversations.

**Missing evidence and effect:** Applicable insurer originals, actual accepted configuration and further case-specific disclosures remain required before any product or eligibility answer.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- No old diagnosis appears in messages or decisions forCONV-B
- No hidden decision dependency onoldmedicalfacts
- Reuse requires an explicit later request with scope
- OriginalCONV-A is not silently deleted
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-06 — Mujhe mummy ke liye insurance chahiye; unki umar sattar saal hai.

**Decision tested:** Language normalization must preserve fact subject, negation and number without collapsing them into an English keyword bag.

**Customer and facts:** buyer: P01; intended insured: P02; relationship: mother; age: 70; language: Hindi-Roman

**Conversation:**

1. customer: Mujhe mummy ke liye insurance chahiye; unki umar sattar saal hai.
2. adviser: Aapki mummy ke liye cover chahiye aur unki umar 70 saal hai. Woh kis shehar mein rehti hain, aur kya unka pehle se koi health insurance hai?
3. customer: WohKota mein rehti hain. Abhi insurance nahi hai.
4. adviser: Unhe koi diagnosed bimari hai, regular dawa chalti hai, ya doctor ne haal mein koi treatment bataya hai?

**Expected assessment:** Interpret mummy as the mother and sattar as70, retaining the original utterance and the interpretation. Ask about the mother’s residence and prior cover. Do not assign70 to the buyer, translate sattar to17, or assume the buyer has no insurance. Match the requested language while retaining exact insurer evidence later.

**Missing evidence and effect:** Mother medical disclosures and exact DOB/age date; applicable product originals. Mother residence and absence of insurance are confirmed by turn3.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- Correct person and number interpretation
- Original Hindi-Roman utterance retained for audit
- No invented buyer age or diagnosis
- Focused follow-up in understandable Hindi-Roman
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-07 — I have no insurance; by cover I meant an emergency savings account.

**Decision tested:** A financial asset and an insurance contract may have the same colloquial label but different decision consequences.

**Customer and facts:** buyer: P01; initial cover report: I have cover; corrected meaning: emergency savings; savings inr: 300000; insurance policies: 0

**Conversation:**

1. customer: I have cover of 3 lakh.
2. adviser: Do you mean an insurance policy or money you have saved for emergencies?
3. customer: Savings. I have₹300000 in my bank and no insurance.
4. adviser: I have recorded₹300000 as emergency savings and no existing insurance. No insurer continuity or waiting-period credit can be inferred from the reported savings.

**Expected assessment:** Correct the semantic type from ambiguous cover to savings. Keep monetary currency/unit and accessibility as facts needing confirmation for funding decisions. Do not invent an insurer, policy number, start date or portability credit. Recompute any earlier top-up comparison that assumed an existing base policy.

**Missing evidence and effect:** Applicable insurer originals, actual accepted configuration and further case-specific disclosures remain required before any product or eligibility answer.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- No synthetic policy row or continuitycredit created
- 3lakh normalized to300000INR
- Old base-policy-dependent advice invalidated
- Accessible funding remains distinct from total savings
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-08 — My father has diabetes but I do not; please keep our histories separate.

**Decision tested:** A statement can contain different polarities for the same condition across two people.

**Customer and facts:** buyer: P01; buyer diabetes: False; father: P03; father diabetes: True; intended insured: P03

**Conversation:**

1. customer: My father has diabetes, but I do not. The cover is for him.
2. adviser: I have recorded diabetes for your father, not for you. How old is he, and when was he diagnosed or last treated?
3. customer: He is 68. He was diagnosed five years ago and takes prescribed medicine now.
4. adviser: I have his age as 68 and ongoing treatment. We will need the exact disclosure and applicable policy terms when checking waiting periods and acceptance.

**Expected assessment:** Attach diabetes and ongoing treatment toP03. Preserve the buyer’s explicit negative statement separately from unknown medical history in other conditions. Do not use a shared family-wide diabetes flag or infer that old diagnosis means no current PED because ongoing treatment remains material.

**Missing evidence and effect:** Father exact diagnosis/treatment details and dates, current cover and applicable product originals. Father reported age68 and ongoing treatment are known; buyer diabetes is explicitly denied.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- Positive and negative disclosures have different personsubjects
- No medical fact propagated between relatives
- Fiveyears is approximate diagnosis history, not an exact date
- Insurer acceptance not inferred from disclosure
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-09 — I sent a correction while an earlier advice request was still processing.

**Decision tested:** Worker completion order is not customer-fact order; concurrent turns require explicit revision dependencies.

**Customer and facts:** owner: ACCOUNT-A; conversation: CONV-A; turn T1 read revision: 4; correction revision: 5; T1 status when corrected: processing; corrected fact: motherage70instead60

**Conversation:**

1. customer: My mother is 60; compare options.
2. adviser: The request has been saved and is being processed.
3. customer: Correction: she is 70.
4. adviser: I have updated her age to 70. The comparison using 60 needs to be rechecked before it can be shown as current.

**Expected assessment:** Persist revision5 and invalidate the relevance of an answer computed only fromrevision4. T1may finish technically, but its result must not overwrite current facts or appear as a current validated comparison. Link a replacement turn torevision5, enforce idempotency and stream durable status. Exact cancellation/retry mechanics remain for the design discussion.

**Missing evidence and effect:** Applicable insurer originals, actual accepted configuration and further case-specific disclosures remain required before any product or eligibility answer.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- No last-finishing-worker overwrite
- No stale comparison presented as current
- Reconnect replays saved events without dispatching duplicate inference
- Each result declares fact revision and invalidation status
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

## ref-20-10 — I want my medical disclosure deleted and earlier derived advice invalidated.

**Decision tested:** Erasing a primary fact alone is insufficient when derived copies or in-flight tasks can resurrect it.

**Customer and facts:** owner: ACCOUNT-A; conversation: CONV-A; medical fact: F-DIABETES; derived decisions: D1,D2; deletion requested: 2026-09-10

**Conversation:**

1. customer: Delete my diabetes disclosure and invalidate advice that used it.
2. adviser: I will apply the deletion request to that disclosure and mark dependent advice as invalid. Deleting a disclosure here does not change a declaration already given to an insurer.
3. customer: Include copies in search and saved summaries.
4. adviser: The request must cover those copies and derived summaries too. Completion should be confirmed only after the affected stores and dependent advice have been checked.

**Expected assessment:** Identify the owned fact, derived decisions, summaries, retrieval copies and processing payloads. Apply deletion or permitted redaction according to the eventual approved retention policy; do not announce completion before verification. Preserve only a minimized audit event where permitted, without retaining the deleted medical value. Do not claim this edits insurer records or creates a right to nondisclosure.

**Missing evidence and effect:** Applicable insurer originals, actual accepted configuration and further case-specific disclosures remain required before any product or eligibility answer.

**Original anchors:** No contractual passage used for this operational or explicitly hypothetical branch.

**Judging criteria:**

- Dependent decisions marked invalid and excluded from currentadvice
- No stale embedding/summary/worker payload restores deletedfact
- Ownership checked before anydelete
- Completion includes failures/pendingretentionexceptions honestly
- Retained audit event doesnotrepeatmedicalvalue
- Current facts reflect all customer turns; superseded assertions cannot remain current.

**Status:** `operational_scope_complete`; no adviser attempt or acceptance pass.

