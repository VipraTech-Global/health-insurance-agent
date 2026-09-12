# Worked examples against the proposed records

All customer configurations and dates below are explicitly synthetic. Policy text comes from preserved originals linked in the reference assessments. These walkthroughs demonstrate the proposed storage and decision path; no application was run, and no insurer settlement or release acceptance is claimed. [worked-record-examples.json](worked-record-examples.json) contains representative typed records, with synthetic UUIDs clearly identified.

## Buyer and parent correction — references 20-02, 20-08

Create one owned `Person` for the buyer and another for the father. Customer statements point to the exact message spans identifying the intended insured and each medical disclosure. Structured facts retain separate subjects through their source statements. A correction creates a later fact version with the same logical key and a new customer profile revision. A turn pins its exact profile revision; if a later correction advances the conversation pointer, that older turn cannot publish as current. Reopening the same conversation retains its revision history. A new conversation starts empty because cross-conversation reuse is deferred.

The decisive records are `CustomerStatement`, `CustomerFact.logical_key`, `CustomerFact.introduced_in_revision_id`, `CustomerProfileRevision.revision`, `Turn.profile_revision_id` and `Conversation.current_profile_revision_id`.

## Room choice and liquidity — reference 01-07

Stipulate base SI ₹100,000, earned available bonus ₹10,000, three room days, surgeon ₹80,000, medicines ₹20,000, no other restrictions/usage and an otherwise admissible accident. The original room limit is min(2% of base SI, ₹5,000/day), so ₹2,000/day. Original sources: New India AS hash `890ab4…`, physical pages 7, 8 and 15; full spans E14–E16.

| Step | Eligible room ₹2,000/day | Upgrade ₹4,000/day |
|---|---:|---:|
| Gross room cost | ₹6,000 | ₹12,000 |
| Gross total bill | ₹106,000 | ₹112,000 |
| Allowed room | ₹6,000 | ₹6,000 |
| Allowed surgeon | ₹80,000 | ₹40,000 |
| Medicines, outside proportional reduction | ₹20,000 | ₹20,000 |
| Admissible subtotal | ₹106,000 | ₹66,000 |
| 5% co-pay | ₹5,300 | ₹3,300 |
| Conditional insurer amount | ₹100,700 | ₹62,700 |
| Customer balance | ₹5,300 | ₹49,300 |

The ₹110,000 available pool is sufficient for this illustration. Without that stipulated bonus, the first branch requires another aggregate-cap calculation. The room percentage uses base SI, not displayed base-plus-bonus. A ₹10,000 emergency cash limit fits the first branch and fails the second. Choosing the upgrade changes customer exposure by ₹44,000, not merely the ₹6,000 gross room-price difference.

`ExpenseLine/Allocation` preserve categories and affected portions; separate `CustomerPolicyFact` records retain base and bonus; rules select room base and medicine exception; `Calculation.trace` stores each step. A quote or claim cannot silently reuse this result after changed room availability, SI, bonus or bill items.

## Different table selectors — reference 09-02 and supplementary 09-11

The preserved Star Super Surplus Floater original `c0b419…`, physical pages 3–4, has Silver limits selected by deductible and Gold limits selected by sum insured. Gold's ₹1,000,000 SI column and robotic-surgery row give a ₹300,000 per-procedure/policy-period ceiling. New India AS §4.6 gives 50% of SI for listed procedures in its stated setting; a ₹500,000 base yields a ₹250,000 nominal ceiling. Neither is a final payment.

`RuleTable.axes` gives meaning, quantity dimension and exact header; `RuleTableCell.selectors` selects the procedure and amount axis. Cell geometry, continuation pages and footnotes remain linked. “Up to SI” is an expression referring to finite SI, not unlimited. The Star oral-chemotherapy footnote addresses with/without-hospitalization inclusion, while its defined-limit condition concerns hospitalization expenses. Both are retained; the design cannot resolve that interaction by deleting one clause.

## Threshold, payment and premium debt — references 14-02, 14-09, 11-05

Under a stipulated Star Gold ₹300,000 threshold, its independently admitted ₹200,000 and ₹250,000 hospital expenses produce ₹150,000 threshold excess. A base insurer's refusal because its policy expired does not automatically exclude the expense from Gold's independently assessed threshold. The premise that Gold admits it is explicit; base refusal alone is insufficient.

Separately, where an ₹800,000 actual indemnity loss has already received ₹400,000 from another insurer, a ₹500,000 standalone threshold calculation cannot create ₹900,000 total recovery. Remaining loss and each contract's conditions constrain settlement. In another bounded example, an already calculated ₹100,000 benefit and ₹30,000 unpaid future instalments can yield ₹70,000 remittance under Star V.12's acceleration/recovery provision. Premium recovery is neither an extra disease co-pay nor threshold consumption.

`ClaimLineAssessment` separates admitted expense, threshold contribution, cover use and paid amount. `UsageEntry` references immutable assessment revisions, source events and unique posting keys. A correction reverses entries under locks; retrying a worker cannot double-count them.

## Unresolved operation order — reference 11-02

For a hypothetical ₹100,000 admitted amount, ₹10,000 deductible and 20% co-pay: deductible then co-pay gives ₹72,000; co-pay then deductible gives ₹70,000. Both intermediate results are arithmetically valid. Without applicable ordering evidence, the adviser cannot choose one as entitlement. Store two conditional calculation traces and a material `RuleIssue` identifying the missing ordering authority. The displayed answer may explain the difference and request the decisive clause.

## Clocks and amount layers — references 15-07, 16-10

A hypothetical accepted Gold migration credits 12 months to the retained ₹300,000 and zero to a ₹200,000 enhancement. Against the stipulated 12-month PED wait, remaining durations are zero and 12 months respectively. Two `CustomerPolicyFact` records and separate `CustomerPolicyFact` entries prevent a single waited flag from covering the enhancement.

A regulatory modification may retain UIN. The HDFC notice's listed-product renewal condition is separate from accrued continuity. A stipulated relevant renewal on 1 October 2024 with 24 continuous months against a newly applicable 36-month maximum leaves 12 months; it does not reset all credit. This is an explanation of the identified notice and hypothetical chronology, not a ruling that its historical application or current law is fully resolved. The image-only product/UIN table and the applicable legal instrument are dependencies.

## Provider status and stabilization — reference 17-03

A facility can be non-network without being excluded; excluded-provider treatment may have a narrow emergency/accident stabilization exception under the identified wording. Keep branch, insurer, configuration, exclusion observation and clinical stabilization event separately. Expense service intervals and allocation evidence determine which portions are before versus after stabilization. A date-only bill line spanning that instant remains unresolved. Neither an admission cashless deadline nor a refused cashless request is guaranteed coverage/payment.

## Contradictory originals — references 05-01, 09-10

New India AS's detailed PED clause states 36 months while its benefit table states four years. Its CIS agrees with one clause and says wording governs, but that does not resolve the wording's internal contradiction. The road-ambulance grant and excluded-item ambulance row likewise require connected interpretation. Store both original spans, a material issue and any later authoritative resolution. Retrieval returns the conflict; publication cannot silently choose the more attractive term.

## Quote correction and selective erasure — references 18-09, 20-10

A quote obtained for the wrong residence is bound to the old customer profile revision; a later correct residence invalidates that price comparison. Unknown tax/fees remain unknown, not zero. Loading applies to the evidenced component base, not automatically base-plus-addon.

If the customer erases one medical disclosure, the system traces its statement/fact lineage and content copies, fences older jobs, removes/redacts dependent payloads and marks affected snapshots/answers nonreplayable. Unrelated facts can survive. A private original containing the disclosure is erased as an original; a retained authorized redacted derivative has a new hash. Historical citation unavailability is explicit. Backup restoration must apply deletion tombstones before serving data.


## Claim submission, documentary completeness and payment are different events

In [the additional reimbursement-clock case](../reference/additional-claim-clock-case-r10.json), the synthetic claim is submitted on August 1, uploaded to the adviser on August 5, confirmed complete at the insurer on August 7 and paid on August 26. The preserved New India original, physical page 15, clause 9.6, uses submission for its fifteen-day settlement obligation and receipt of the last necessary document for delayed-payment interest. The independently checked elapsed intervals are 25 and 19 calendar days respectively.

`ClaimEvent` stores each event's actual time, sender, recipient and provenance. A user upload does not establish insurer receipt. `ClaimDocumentRequirement` records which documents are necessary, accepted forms and authoritative waivers; `ClaimDocumentReceipt` ties a delivered document to a particular requirement and insurer receipt. A completeness determination must reference its actual requirement and receipt set. Corrections produce new revisions and invalidate dependent calculations.

`ClaimPayment` records the actual synthetic indemnity payment of INR 100,000 separately from estimated entitlement and interest. Clause 3.8 on physical page 2 fixes the Bank Rate observation to the first day of the financial year in which the claim falls due. The example requires the April 1, 2026 rate, plus two percentage points. That rate, day-count convention and rounding are not established here, so `Calculation.result` for interest remains unknown. Neither the adviser upload date nor an assumed current rate supplies these missing inputs. The exact passages and input assumptions remain in the case record.

## Original rule counts retain their adjudication history

The Star and New India independent original-reading inventories contain 589 and 792 candidate occurrences respectively. These are working occurrence inventories, not approved relevant-rule denominators. A merged table cell may expand to several configurations; an exclusion may be a qualifier or a separate rule; repeated summaries need a declared counting treatment.

`InventoryRevision` freezes the counting protocol and exact original manifest. `InventoryMembership` retains each occurrence's included, excluded, structural or disputed disposition and its weight. Candidate and disputed weights stay unknown. `InventoryLineage` records split, merge and qualifier decisions without rewriting the prior revision. `RuleInventorySupport` independently judges whether a curated rule represents an included occurrence; `CoverageReportSupport` binds a historical coverage result to that exact membership and support revision. Repeated supporting rules cannot inflate the count of distinct included occurrences. No percentage is publishable until the relevant denominator and review set are established for the required scope.

## 12. A life-only request affects both policies in a combi

In the [additional Health Maximiser case](../reference/additional-combi-case-r13.json), Meera owns a new package: Health Premier covers Meera and Arjun, while Kotak Term Plan covers Meera alone. The original separately identifies the wrapper, both product UINs and their issuers. Its connected free-look clause prohibits cancelling either policy individually and makes an application for either cancel the entire combi. This does not make their benefits identical.

The proposed public component records preserve those identities. One owned package revision maps its health and life slots to the actual component policy revisions. Arjun remains absent from the life policy's insured membership. Meera's older separate health policy is excluded from this package, so the coupled consequence does not reach it.

Meera first calls the package a renewal, then corrects it to a new issue. She later corrects complete-package receipt from 25 August to 28 August; 25 August was an incomplete upload to her own folder. Append both corrections to the package subject and invalidate receipt/renewal conclusions using the earlier facts. The fictional assessment date remains 10 September. The supported answer explains the whole-package free-look consequence and the original's non-revival/new-proposal term. Refund deductions are identified, but amounts and actual cancellation remain unknown.

The [record example](combi-worked-records-r6.json) shows the rule shape and synthetic association IDs. It records no cancelled contracts. Owner mismatch, uncertain membership, an unrelated target policy or an unresolved wrapper edition prevents a complete consequence result. These are proposed enforcement requirements; no replacement database or adviser has been implemented.
