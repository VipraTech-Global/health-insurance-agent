# Source reconciliation supplement r4

All 203 legacy identities and their order are preserved. This revision identifies product families independently of exact historical versions, variants, bundle completeness and eventual policy applicability. It does not finalize the database design or claim completed adviser/reference/evaluation acceptance.

## Results

| Measure | r4 result |
|---|---:|
| Former 65 unresolved selected-insurer listings: family identified in preserved originals | 31 |
| Former 65: family alias candidate requiring corroboration | 2 |
| Former 65: no preserved family association established | 32 |
| All 203: family identified in preserved originals | 147 |
| All 203: alias candidates | 2 |
| All 203: unresolved, including Apollo Munich Test | 33 |
| Outside selected insurer-label scope | 21 |
| Fully reconciled exact historical listings / complete original bundles | 0 |

A missing legacy UIN does not erase the positive family, named-option or source-version evidence. Conversely, the identity of a current wording does not select an edition for a historical listing. The 21 scope exclusions are insurer-roster dispositions, not nonmedical-product findings.

## New original acquisitions

23 distinct PDFs were acquired through the existing acquisition module: 10 Star wordings, 11 Care wordings, ICICI Health AdvantEdge wording and the ICICI product register. Original bytes and individual attempt records remain preserved; the supplemental registers carry the successful Care and ICICI links that may not be discoverable by rebuilding the ordinary source register from raw successful HTML alone.

Care raw downloads HTML returned HTTP403. The official page was readable through the web tool, where exact PDF hrefs were observed. All 11 PDFs then downloaded successfully with the acquisition module. The successful raw HTML acquisition is **not** claimed. All new sources are official insurer originals or official-linked assets; no third-party policy text was used.

The official Star wordings support all 11 formerly unresolved Star labels at family level. Medi Classic Gold is an optional Gold Plan in the Medi Classic Individual wording (hash `440dc2380a83c36fa2e438d98b252c894bef544f52849f15a21d93893e287a3a`, physical p14; interaction note p21). It must not be modeled solely as an unrelated product/UIN.

Joy Today and Joy Tomorrow are explicitly named plans in the Joy original (hash `6e58814aec628c402da27896296ecd40f3fa704a6875c6b0963b77f207af878f`, physical p11). Care Plus family is supported, but Complete/Youth labels are not established by this wording. Care Senior cannot be inferred merely from the Senior Citizen definition in Care; Senior Health Advantage is separately named. Ultimate Care is supported as an alias candidate for the reversed legacy label Care Ultimate.

## Material identity/version conflicts

- Care Heart: main wording `CHIHLIP26053V032526`; annexure physical p40 footer `RHIHLIP21371V022021`. Source hash `c7129fd19a356f30c4e6939c1cac49b1660b968f8fde53e7ab0b9c9ce5d0700c`.
- Care Freedom: main wording `CHIHLIP26052V032526`; physical p23 footer `RHIHLIP21519V022021`. Source hash `17935f320d714e6aa7976724f4f7bc3b25fcfce01b2e5c799ce9c77a362c30c2`.
- Health AdvantEdge: the official current product page links wording `ICIHLIP23075V032223` (hash `ae964e86db482595b201c8bab9d58a03a497dfc0b1f36fbdaf8bb703c66cbba7`). The insurer product register lists later revisions, including `ICIHLIP27056V062627` offered from 26-Jun-2026. Preserve the old wording; do not call the link current contractual evidence.

ICICI product register hash `3631f44d981b1e01897cc4f2ce72a7a8de46fde4f29187794b28d6a51d557d48` gives named health-product rows, UINs and public offer/withdrawal dates (physical pp10,12–14,16–19). Page16 was visually checked against the original table. These are offer windows, not automatic effective/expiry dates for individual policies. Health Booster and Activate Booster remain distinct; Health Shield360 and Health Shield360 Retail remain separately named families. MaxProtect family is identified, but Classic/Premium variants require additional original evidence.

## Source scope classification

The document scope register classifies the 77 originals used in r3 and all 23 new PDFs. Each classification has a hash and physical-page passage. Of this intentionally relevant 100-document subset, 56 contain medical-expense wording grants; 44 are supporting/mixed material such as CIS, proposal/claim forms, brochures, premium tables, prospectuses, riders or mixed-line registers. No standalone nonmedical or unresolved-scope document occurs in this selected subset. This does not classify the entire acquired corpus.

Medical-expense classification means an operative expense grant was read, not that every component is indemnity. Supporting/mixed documents can be essential evidence but do not substitute for applicable wording. Definitions and title keywords alone were not used to approve an operative wording. Rule instances, all figures/tables/footnotes and connected conditions are not yet exhaustively inventoried.

## Access gaps and remaining listings

Oriental original downloads and health-products endpoints timed out. Official indexed pages supplied useful navigation for Happy Family, Mediclaim and other products; their freshness and raw contents are not established. In particular the observed Happy Family page names Silver/Gold/Diamond, not Platinum. United India alternate download/PDF URLs returned404 and the Individual Health node timed out. Indexed official names/UINs are explicitly marked observations, not preserved applicable originals. ICICI downloads returned403 while the directly linked wording and product register were acquired successfully. Failure response bytes, statuses and timestamps remain in the access registers.

The 32 selected-insurer labels still lacking preserved family evidence in this supplement are:

- **Acko:** Standard Health.
- **Aditya Birla:** Activ Health Platinum Enhanced; Activ Health Platinum Essential.
- **Hdfc Ergo:** Optima Lite.
- **Icici Lombard:** Health Elite Plus; Ihealth; Ihealth Plus.
- **Manipal Cigna:** Prohealth Accumulate; Prohealth Plus; Prohealth Preferred; Prohealth Premier; Prohealth Prime Active; Prohealth Prime Advantage; Prohealth Prime Protect; Prohealth Prime Senior Classic; Prohealth Prime Senior Elite; Prohealth Protect; Securehealth.
- **Oriental Insurance:** Happy Family Floater Policy Diamond; Happy Family Floater Policy Gold; Happy Family Floater Policy Platinum; Happy Family Floater Policy Silver; Health Of Privileged Elders; Mediclaim Insurance Policy; Super Health Top Up.
- **Sbi:** Retail Health Policy.
- **Tata Aig:** Medicare Senior.
- **United India:** Family Medicare; Individual Gold Plan; Individual Platinum Plan; Medicare Super Top Up; Senior Citizen Plan.


## Generalized information requirements

1. Store identity assertions at product-family, named variant/option, original-document revision and legacy-alias levels; each needs its own confidence/status and evidence.
2. Retain multiple UIN assertions within one original and their page scope. A conflicting annexure footer must not silently relabel the whole document.
3. Separate public offer/withdrawal dates from policy issue/renewal periods and historical customer applicability.
4. Preserve official-page observation provenance independently of raw-page acquisition success; record which exact observed link produced each original.
5. Distinguish medical-expense wordings, supporting documents, mixed-line registers and standalone unrelated material. Preserve nonmedical rows within a relevant original without ingesting them as medical-policy rules.
6. Represent product-plus-option relationships and plan-specific clauses. Product-name similarity or a shared UIN is insufficient for variant equivalence.

## Verification and remaining boundary

Focused verification passed: exact203 identity fields/order, unchanged r3 input hash,100 original hashes, all scope passages/named-option passages/register rows resolving to their physical pages, all six dimensions present and all counts recalculated. This is artifact/provenance verification; it is not a full insurance-rule audit.

Machine-readable artifacts: `registers/legacy-assessment-r4.json`, `registers/document-scope-r4.json`, `registers/icici-health-product-rows-r4.json`, `registers/care-original-links-r4.json`, `registers/source-access-r4.json`, `registers/additional-source-access-r4.json`, `registers/icici-product-list-access-r4.json`, `registers/icici-product-list-access-r4b.json`, and `reports/source-reconciliation-r4-verification.json`. Earlier revisions and original bytes were preserved.
