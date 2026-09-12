# ManipalCigna and HDFC ERGO family reconciliation — r10

The nine requested legacy rows now have reviewed original-wording candidates. Named tiers and plans are supported where specified below. The generic Lifetime Health row and the historical “Prohealth” prefix on Prime Senior still need qualification. This batch does not complete historical applicability, complete document bundles or independent rule inventories.

The integration artifact is `research/registers/cigna-hdfc-family-reconciliation-r10.json`. It contains `newly_classified_documents`, `reread_existing_documents`, `per_listing_results`, original acquisition outcomes, exact passages and remaining dependencies for every row. Earlier and cumulative registers were not changed.

| Population | Count |
|---|---:|
| Requested family groups / exact legacy rows | 5 / 9 |
| PDFs reviewed for bounded identity and scope | 16 |
| New manual PDF classifications relative to r9 | 14 |
| Existing manual PDFs rechecked | 2 |
| New medical-expense PDF classifications | 7 |
| New supporting PDF classifications | 7 |
| New manually classified official HTML directories | 3 |
| Acquisition attempts | 17 |
| Successful PDF / HTML acquisitions | 12 / 3 |
| Preserved failed original-access attempts | 2 |
| Completed historical-version or complete-bundle reconciliations | 0 |

The seven new medical-expense PDFs are four ManipalCigna base wordings, the Lifetime Plus add-on wording, the already-preserved current Easy Health wording, and the newly acquired historical Easy Health combined CIS/wording. The seven new supporting PDFs are six ManipalCigna CIS and one already-preserved historical HDFC register. Optima Secure wording and another historical HDFC register were already classified and must not be counted twice.

## Per-listing results

| Exact legacy suffix | Original identity and observed UIN | Supported result and remaining selection |
|---|---|---|
| `manipal-cigna/lifetime-health/` | Lifetime Health India Plan; MCIHLIP27041V022627 | Main title p1, domestic grant p17 and plan table p66 support India Plan. The generic legacy name alone does not explicitly select India over Global; the domestic association remains qualified. |
| `manipal-cigna/lifetime-health-global/` | Lifetime Health Global Plan; MCIHLIP27041V022627 | Explicit Global identity and separate domestic/foreign grants. Geography, major-illness option, SI1/SI2 and deductible/waiver remain customer selections. |
| `manipal-cigna/prohealth-prime-senior-classic/` | ManipalCigna Prime Senior — Classic; MCIHLIP27039V022627 | Classic explicitly named p1 and p53. The observed title omits the legacy Prohealth prefix; no formal historical rename is invented. |
| `manipal-cigna/prohealth-prime-senior-elite/` | ManipalCigna Prime Senior — Elite; MCIHLIP27039V022627 | Elite explicitly named p1 and p53. Historical prefix equivalence, version and selected SI/options remain unverified. |
| `manipal-cigna/super-top-up/` | ManipalCigna Super Top Up; MCIHLIP23022V032223 | Original grant p6 and Plus/Select table p27. Generic legacy name does not choose a plan or permitted SI/deductible combination. |
| `hdfc-ergo/easy-health-standard/` | Easy Health; HDFHLIP26054V102526 and historical HDHHLIP21378V062021 | Standard named in current Individual/Family schedules and historical schedules. Cover form and applicable historical version remain separate. |
| `hdfc-ergo/easy-health-exclusive/` | Easy Health; same two observed UINs | Exclusive named in those schedules. SI, cover form, options and issue applicability remain unresolved. |
| `hdfc-ergo/easy-health-premium/` | Historical Easy Health combined CIS/wording; HDHHLIP21378V062021 | Premium named in CIS p1 and wording tables p28–29. Official register marks Premium withdrawn and supplies an interval for policy starts. Current Standard/Exclusive wording is not a substitute. |
| `hdfc-ergo/optima-lite/` | my: Optima Secure; HDFHLIP26058V082526 | Optima Lite explicitly appears as a plan in Annexure C p61, with inbuilt modifications in pp26–28. It is not a separate base-product UIN. |

All paths above retain the existing `/health-insurance/` prefix in the machine-readable register. No identities were renamed.

## Material distinctions established from originals

**Lifetime Health:** India and Global have separate wording artifacts sharing one UIN. The Global wording distinguishes SI1 for treatment in India from SI2 for treatment outside India within the chosen area. Major-illness selection and deductible conditions further restrict the foreign cover. A general “global coverage” label cannot substitute for these dimensions. The Lifetime Plus add-on has its own UIN, MCIHLIA27042V022627. Its preamble requires an underlying policy and explicit selection in the schedule; p19 associates it with India or Global plans. It is not automatically selected for either legacy row.

**Prime Senior:** Classic and Elite are explicit plan names. The current source title is “MANIPALCIGNA PRIME SENIOR.” This supports the observed family/tier candidate without proving a historical renaming from the legacy Prohealth label. The Health 360 identifier in the wording is a referenced add-on identifier, not a second Prime Senior base UIN.

**Super Top Up:** The original p1 expressly aggregates covered hospitalization expenses by individual for an individual policy and by family floater for a family-floater policy, per policy year. P27 specifies allowed deductible/SI combinations separately for Plus and Select. A chosen amount must belong to the selected combination. The body references ProHealth Protect UIN MCIHLIP22211V062122 as a continuity destination; the annexure refers to MCIHLIP21546V052021. Those assertions remain separate and unresolved, rather than being treated as Super Top Up versions. CIS additionally references Health 360 with its own UIN.

**Easy Health Premium:** The current reviewed wording schedules name Standard and Exclusive. The preserved historical register p1 row6 names “Easy Health Premium (Withdrawn),” UIN HDHHLIP21378V062021, and policy starts “01-Oct-2020 and 31st-Aug-2022.” Following that original register's customer-portal URL successfully acquired a31-page combined original. Its Premium CIS begins at physical p1, while policy wording begins at physical p5 (printed p1). The operative grant is physical p10 (printed p6); Premium tables appear at physical pp28–29. The interval is source-backed, but the undated legacy listing has not been assigned to it.

**Optima Lite:** The preserved my:Optima Secure wording is sufficient to establish this named plan. Its plan chart and inbuilt room/ICU and pre/post-hospitalization modifications demonstrate why retrieval must apply plan-specific rules before general base-product defaults. Exact customer selection and historical version still require evidence.

## Source failures and remaining work

Two official older Premium CIS routes returned HTTP406. Both attempts and response bytes remain preserved. These failures do not establish that Premium evidence is unavailable: a separate original register-linked customer-portal route succeeded. The discovery lineage and each result are retained individually.

The three ManipalCigna category pages yielded exact links to prospectuses, proposal forms, benefit illustrations, CIS annexures, brochures and add-ons. The register accounts for these per family and marks unacquired or unread candidates explicitly. They are remaining work, not missing-source assertions. Six matching product/plan/UIN CIS were acquired and read for identity and medical scope; matching UIN does not establish complete clause agreement. Current HDFC standalone CIS/prospectus matching and the full applicable endorsement set remain unassessed in this batch.

Issued schedules, underwriting decisions and selected endorsements were not supplied. They are needed for individual/floater form, insured people, optional benefits, SI, deductibles, policy dates and historical application. Template placeholders do not fill these gaps.

The Lifetime Global CIS p2 uses covers17–26 for area selection but16–25 for major-illness selection. This cross-reference mismatch remains visible. The India wording main title is clear, while its printed footer misspells “Maninalciana”; the source spelling is preserved separately from the normalized display name. Super Top Up has font-encoded native text; its relevant headings, grant and configuration table were visually checked. The historical Premium Family table prints a per-insured-person SI heading, which needs connected-scope review before normalization.

## Verification boundary

All19 reviewed original-object hashes were checked:16 PDFs and3 HTML directories. Stored identity and evidence passages were checked against their physical original pages. Twelve PDF pages were visually inspected, including nontrivial plan tables and native-text gaps. HTML discovery hrefs are stored with exact original bytes and byte offsets. Full acquisition attempts retain their original outcomes.

This is manual document-relevance and bounded source-identity work. No full-page rule denominator, insurer knowledge coverage, customer recommendation, adviser acceptance or evaluation result is claimed. No protected evaluation data or application code was changed.
