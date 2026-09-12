# Legacy listing reconciliation, revision 3

All **203 exact legacy identities** have an explicit disposition in this revision. **None is counted as a completed identity reconciliation.** The original order and earlier registers are preserved.

| Disposition | Listings | Meaning |
|---|---:|---|
| Original-backed candidate, historical version/configuration unresolved | 116 | 150 candidate associations, grounded in selected original identity passages |
| Selected-insurer product identity unresolved | 65 | No manually validated association established for the exact listing in this bounded review |
| Outside the selected insurer labels | 21 | Outside the selected20 roster; this does not mean an invalid product or a nonmedical product |
| Historical insurer/test-label ambiguity | 1 | Apollo Munich “Test”; possible insurer succession and product identity remain unresolved |
| Completed identity reconciliation | 0 | Neither candidate discovery nor explicit unresolved accounting meets this criterion |

The per-listing artifact is [legacy-assessment-r3.json](../registers/legacy-assessment-r3.json). Each record retains its exact identity, original legacy provenance, earlier candidates, source-backed candidates, evidence pages, version/variant uncertainty, insurer-level acquisition context, and completion limitation. The separate [original candidate source register](../registers/legacy-original-candidates-r3.json) preserves77 selected original identity readings and their acquisition provenance.

## Evidence method and practical limits

The assessor first reviewed all203 legacy entries and the preserved acquisition and preview registers for navigation. Associations were then authored from actual preserved original PDFs: product headings and footers, named plan choices, insurer product/UIN registers, and relevant connected identity clauses. Each selected object's SHA-256 was independently verified. Preview keyword matches were not promoted to identity or scope conclusions. A reviewed title establishes a candidate, not a complete policy rule inventory or even a final scope classification.

This is a bounded original-identity review, not a review of every page of the acquired corpus. An unassociated listing is **not established by this review**, rather than proven absent from insurer offerings. Register, brochure, proposal, wording and CIS evidence have different roles. For example, an unfilled proposal can identify available plan names but cannot demonstrate proposal acceptance, individual underwriting terms or policy ownership. The inherited Care Supreme import retains its unverified original acquisition date. No additional third-party product content was ingested; no original bytes were modified.

## Material distinctions found in originals

- **ACKO Platinum:** the preserved Platinum, Platinum Lite and Platinum Super Top-up wordings share UIN `ACKHLIP27040V012627`. A UIN alone does not uniquely identify the configuration. Only the Platinum candidate is associated with the legacy Platinum Health label; the other originals remain explicit alternative configurations.
- **Activ One:** the prospectus explicitly names MAX, MAX+, NXT, VYTL, VIP, VIP+ and SAVR under `ADIHLIP24097V012324`; later acquired variant CISs use `ADIHLIP27048V022627`. Preserve both generations and establish actual applicability dates.
- **Activ Assure:** the legacy label “Activ Assured Diamond” differs from the original “Activ Assure Diamond” and footer “Active Assure.” A spelling similarity is insufficient to declare an authoritative rename.
- **Bajaj:** the insurer's excluded-items register explicitly links base-product names to UINs. It does not establish whether legacy Smart/Ultimo/Vital or Gold/Silver/Platinum labels are current variants, historical variants or marketing groupings.
- **Digit:** Double Wallet, Infinity Wallet and Worldwide Treatment appear as plan choices in the same insurer proposal under `GODHLIP25039V022425`, rather than evidence of three independent base products.
- **HDFC Easy Health:** the original historical-version register associates Standard/Exclusive/Premium with `HDHHLIP21378V062021` for policy-period starts1October2020–31August2022. Premium is marked Withdrawn. It separately gives Standard/Exclusive `HDFHLIP23024V072223` for starts1September2022–17July2024. These original applicability windows must not be replaced by acquisition dates, and withdrawal must not erase historical contracts.
- **Care Supreme:** the preserved base wording does not by itself validate the legacy Senior Premium, Senior Super, Super Saver or Value For Money packages. Keep those labels unresolved even when the base product has an original candidate.
- **New India Floater Mediclaim:** preserved brochure, rate chart and proposal show V08, V09 and V10 generations. They cannot be treated as one coherent bundle merely because their product names agree.
- **Niva Bupa:** Aspire's acquired CIS says `NBHHLIP26042V022526`, while wording/register say `NBHHLIP26049V022526`. Heartbeat's register and wording show V09 and V10 generations. Health Companion's variant2022/2023 prospectus and variant1/2/3 Family First CIS also differ. These are unresolved source/version conflicts, not values to silently correct. Bronze+ is not automatically equivalent to a legacy Bronze label.
- **SBI:** Arogya Supreme CIS and brochure show different UIN generations. The Super Health prospectus explicitly names Prime, Elite, Premier, Platinum and Platinum Infinite; this names variants but does not select one for any actual customer.
- **Star:** Super Surplus Gold is a named grant within a preserved floater original. The legacy label alone does not establish floater versus individual configuration. Star Special Care Platinum cannot substitute for the unresolved legacy Special Care Gold label.
- **Separate add-ons:** the ManipalCigna Lifetime brochure distinguishes its base UIN, Lifetime Plus add-on and Health360 add-on. A TATA AIG Modification of Mandatory Sub-limits add-on specifically requires the Health Supercharge Geo Plan; it is not applicable to every similarly named base configuration.

Exact source hashes and physical pages are in the candidate registers. The associated original texts were read for these identity distinctions; benefit calculations, eligibility conclusions, current sale availability and full contractual reconciliation are outside this revision's claims.

## Information requirements for the later design discussion

1. Preserve a legacy listing and its observation provenance independently from any proposed product association. Several candidates and a rejected substitution can coexist without overwriting history.
2. Represent issuer identity, documented aliases, historical succession and selected-scope membership separately from product identity. Apollo Munich demonstrates why a missing current label cannot automatically establish exclusion.
3. A product, UIN generation and named variant need separate identities; the ACKO examples show several variants can share one UIN.
4. Keep document revisions, product/UIN generations, publication dates, acquisition dates, policy-start applicability windows and individual policy periods distinct. Withdrawal affects sale status and must preserve existing-policy evidence.
5. Attach identity assertions to exact original hashes, physical pages and table row/column context. A generic register heading is not enough when the assertion concerns one product row.
6. Store the role and confidence of each source assertion: wording, CIS, brochure, proposal, premium chart, product register and administrative notice are not interchangeable.
7. Preserve conflicting original values with explicit unresolved status and publication consequences. A later acquisition does not automatically override a historically applicable wording.
8. Separate actual insured/customer selections from available-plan lists, marketing labels, discounts and unfilled proposal choices.
9. Give endorsements and add-ons their own identities and applicability dependencies, including required base product and variant. Do not flatten add-on UINs into a base product's UIN list.
10. Keep scope accounting, candidate association, completed identity reconciliation, complete original-rule inventory and recommendability as separate milestones. This revision establishes only the first two where supported.

## Verification

All203 exact identities and their original ordering are preserved; no duplicate identity was introduced. All77 selected original object hashes were independently checked. Every candidate includes a physical-page evidence locator, and every listed candidate UIN is checked against its preserved original. Earlier registers and original bytes remain untouched. The separate evaluation workspace, combined historical scenario seeds and application implementation were not accessed for this subtask.

This source review does not complete the400-case assessment, freeze evaluation cases, approve a database design, or authorize application implementation.
