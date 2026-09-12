# Original-source reconciliation r5

R5 assesses all 32 selected-insurer family gaps left by r4. It establishes 31 additional source-backed family identities and one qualified Tata AIG MediSenior alias candidate. All 203 original legacy listing identities and their order are retained. No exact historical-policy reconciliation or complete original bundle is claimed.

| Dimension | Result |
|---|---:|
| Source-backed product family identities | 178 |
| Original-backed but unconfirmed aliases | 3 |
| Unresolved legacy identity, Apollo Munich “Test” | 1 |
| Outside the original selected 20-insurer roster | 21 |
| Fully reconciled historical listing/version/bundle | 0 |

The three alias candidates are Care Senior, Care Ultimate and Tata AIG Medicare Senior. The original supports Ultimate Care and MediSenior as products, but an explicit mapping of those legacy names remains unproven. Care Senior is not established by a generic definition of a senior insured. These are substantive candidate dispositions, not completed identity reconciliation.

## What the remaining 32 listings now establish

| Legacy group | Listings | Original-backed result and remaining limitation |
|---|---:|---|
| ACKO Standard Health | 1 | Preserved official Standard page establishes the family; another official page explicitly calls Platinum Lite “also known as the ACKO Standard Plan.” This current marketing alias does not prove the historical wording/UIN applied to the legacy listing. The unrelated name overlap in ACKO Health/Health II was not used to force an association. |
| Aditya Birla Activ Health Platinum Enhanced/Essential | 2 | Activ Health wording, physical page 28, explicitly names both plans. Essential brochure and wording carry different UIN revisions, ADIHLIP23071V042223 and ADIHLIP24102V052324. They cannot be treated as a reconciled single-version bundle. |
| HDFC ERGO Optima Lite | 1 | Original leaflet, physical page 4, explicitly says this is a plan under my: Optima Secure. Original bytes print HDFHLIP25041V062425; a web-index spelling is not substituted for it. Full plan-specific wording and endorsements remain outstanding. |
| ICICI Health Elite Plus, Ihealth, Ihealth Plus | 3 | Elite Plus original explicitly names its plan. Complete Health brochure page 13 visually confirms a separate I Health column; the neighboring Health Smart Plus column is not part of that name. Separate iHealth Plus wording names iHealth Plus (ICICI Lombard Complete Health Insurance). The historical brochure’s short printed “UIN 3288” is retained without invented conversion. |
| ManipalCigna ProHealth five plans | 5 | V8 prospectus page 1 explicitly names Protect, Accumulate, Plus, Preferred and Premier in connected room-category clauses. V8 wording corroborates the names. Public register records MCIHLIP25024V082425 withdrawn 02-Aug-25; withdrawal does not select the customer’s historical policy. |
| ManipalCigna Prime Active/Advantage/Protect | 3 | Preserved historical wording footers explicitly name the plans under MCIHLIP22224V012122. Their in-patient medical-expense grant on physical page 8 was visually checked. Newer brochure prints MCIHLIP26036V022526. Public register records the older revision modified 02-Jun-25. |
| ManipalCigna Prime Senior Classic/Elite | 2 | Original prospectus page 1 names Prime Senior and both plans. Actual current bytes have MCIHLIP27039V022627 / April 2026, despite older indexed content at the same URL. Legacy “Prohealth” prefix is retained as a label variation. Older MCIHLIP23151V012223 was modified 10-Apr-26 in the public register. |
| ManipalCigna Securehealth | 1 | Original SecureHealth title/footer and operative indemnity clause establish family. Disability/HIV-specific eligibility remains part of the required complete rule inventory. |
| Oriental Happy Family Floater four plans | 4 | Actual wording page 7 names Silver, Gold, Diamond and Platinum; page 34 also names four plan ranges. The original title says 2021 while UIN is OICHLIP23134V052223. Title year, UIN revision, CMS metadata and actual applicability must remain separate. |
| Oriental HOPE, Individual Mediclaim, Super Health Top-Up | 3 | Three preserved original wordings establish family titles and medical-expense grants. HOPE is a specified-disease policy; no conventional UIN was reliably established in the selected text. Individual Mediclaim page 14 contains a Diamond-plan cross-reference requiring conflict review, not automatic variant creation. |
| SBI Retail Health | 1 | Wording and existing CIS/prospectus establish family; wording SBIHLIP11002V021011 and CIS/prospectus SBIHLIP22138V042122 are different revisions. |
| Tata AIG Medicare Senior | 1 | Original MediSenior wording establishes a plausible product candidate. No insurer original explicitly equates the exact legacy label Medicare Senior with MediSenior. Alias remains unconfirmed. |
| United India five listings | 5 | Original CIS names Family Medicare. Individual Health CIS/prospectus explicitly list Platinum, Gold and Senior Citizen as plans, with member age at entry and continuation rules. Original Super Top-Up Medicare wording establishes the aggregate-threshold family. These sources do not complete every associated wording/CIS/endorsement bundle. |

Every listing has its own record in `registers/legacy-assessment-r5.json`, with source hashes, physical-page passages or original HTML locators, identifiers, named variant status, specific unresolved issues and historical/applicability limits. R4 and earlier remain preserved.

## Access and provenance

R5 acquired 21 additional unique relevant original PDFs and read seven previously preserved PDFs beyond the 100 scoped in r4. It also manually read four preserved public non-PDF sources: two ACKO pages, the ManipalCigna withdrawal register, and Oriental’s public document CMS response.

Oriental’s public page is a JavaScript shell. Static reading of public navigation assets revealed its public CMS endpoint; an anonymous request returned a 93-row document list. No authentication, JavaScript execution or browser-runtime repair was needed. The acquisition module preserved the valid JSON while retaining its unsupported-media-type processing outcome. The CMS has rows whose attached filenames do not match the row labels, so actual PDF identity was checked before association. Four relevant official-linked S3 PDFs were preserved through the acquisition module.

United India’s www URLs returned 404 while the corresponding official non-www `/web/` paths succeeded; both attempts are retained. ICICI’s old base-wording URL returned 404, while the original brochure and named iHealth Plus wording were available. Raw ICICI selection-page access returned 403 despite a readable web-index observation. These are access-specific outcomes, not insurer/product absence.

Per-attempt provenance is retained in the r5 source-access registers, `oriental-original-links-r5.json`, `oriental-cms-access-r5.json`, and the unchanged acquisition-attempt records. Original bytes were not rewritten.

## Full acquired-corpus accounting

`registers/source-corpus-accounting-r5.json` enumerates every object in a frozen filesystem snapshot; `registers/source-corpus-inputs-r5.json` records its input paths and hashes. The object set was stable during the recorded scan.

| Mutually exclusive accounting status | Objects |
|---|---:|
| R5 manual PDF relevance classification, including 100 inherited from r4 | 128 |
| Additional r2 manual PDF assertions, kept separately and not re-reviewed here | 7 |
| PDF automated preview only; relevance remains unreviewed | 2,222 |
| R5 manually read public HTML/JSON sources | 4 |
| Other non-PDF objects; relevance remains unreviewed | 453 |
| **Total** | **2,814** |

These are 2,357 PDFs and 457 non-PDF objects. All 2,814 object hashes verified. The 128 manually scoped PDFs comprise 72 medical-expense wordings and 56 supporting/mixed documents. The four additional non-PDF sources are supporting/mixed navigation or marketing evidence. No automated title signal is promoted to reviewed relevance.

The snapshot includes 3,284 acquisition-attempt records: 2,596 module-acquired and 688 module-failed outcomes. There are 296 attempts with no preserved bytes and no attempt referencing a missing object. Failed module outcomes with preserved bytes remain visible. Of 13 objects without an acquisition-attempt record, one is the documented legacy Care Supreme import with unknown original acquisition time; the other 12 non-PDF objects still need provenance reconciliation. No stored object disappears because it lacks a PDF header, has failed acquisition status, or lacks provenance.

A scope classification is not an independent original-rule inventory. The relevant rule denominator remains unknown; most of the corpus is unreviewed, and even manually scoped documents still need complete page/table/figure/footnote/connected-clause inventory. R5 does not claim knowledge acceptance, adviser acceptance, design readiness or completion of the user’s next major deliverable.

## General information requirements derived from the source work

- Preserve the exact legacy label separately from source product names, explicit marketing aliases, named plans and unresolved aliases.
- Store family identity, variant identity, observed source revision, exact historical association, bundle completeness and later applicability as independent evidence-backed findings.
- Represent multiple plans under a product and multiple differently titled wordings sharing a UIN; neither product title nor UIN alone proves identical configuration.
- Track stable URLs serving changed bytes, withdrawal/modification observations, title years, printed revision labels and conflicting indexed content without inferring a policy effective date.
- Require document-role and version compatibility when assembling a bundle. A matching product title does not make an older wording compatible with a newer CIS.
- Retain acquisition outcome separately from preserved-byte readability, scope review and rule-inventory progress. Unsupported JSON and failed HTML responses must remain auditable.
- Keep source attachment identity distinct from navigation-row labels, and preserve mismatches rather than allowing them to contaminate product associations.
- Keep source scope and the complete rule denominator separate; every frozen acquired object must have an accounting disposition, including unreviewed and unresolved objects.

The mandatory database-design discussion boundary is unchanged. No application, schema, evaluation or private customer data was read or changed in this source-reconciliation subtask.
