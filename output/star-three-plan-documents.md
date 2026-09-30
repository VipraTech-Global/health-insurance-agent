# Star three-plan document review - Checkpoint 1

Status: Checkpoint 1 approved with the Assure correction below. This is the document decision sheet; the executable version-2 manifest is `data/manifests/star-three-plan-2026-09-30.json`.

Branch: `feat/star-three-plan-slice`, created from the clean Star worktree at `bfa1c25`. Only the three products below are in scope. No new documents were sought or fetched.

## Decisions for all three plans

- Selected variant: **Base policy without optional covers**. Optional-cover clauses remain identifiable in the wording but must not become selected base benefits. Individual/floater differences belong in eligibility rules, not extra variants.
- Accept the captured linked current editions under the brief's decision. The capture files were locally rechecked by SHA-256 and physical PDF page count; this is not a new live-currentness check.
- Wording, CIS and prospectus are applicable. Retain every prospectus as reference and in the unchanged baseline processing. Later omission from an extraction prompt does not change applicability.
- Captured excluded-expenses, modern-treatment and preventive-health schedules are applicable, with the separate Assure expense sheet retained as reference only.
- Brochures and proposal forms are not applicable for rules. `ManifestProduct.complete_minimum_bundle` does not require proposal forms for eligibility.
- Premium-table role is not applicable. No separate premium-table capture is listed for these bundles; price and budget remain unavailable, including if a prospectus contains premium illustrations.
- Preserve excluded and unresolved document metadata outside executable evidence. Assure consumables coverage uses clause 27 and List I inside its wording.
- The exact captured PDF host is `d28c6jni2fmamz.cloudfront.net`; the captured official listing provenance uses `www.starhealth.in`. No wildcard CloudFront allowance.

## Compact document table

Numbers are physical PDF page counts. Full original filenames, URLs, SHA-256 values and individual reasons follow. Yes means applicable for the proposed bundle; it does not mean rules are already validated.

| Role | Star Comprehensive | Family Health Optima | Star Health Assure | Decision reason |
|---|---|---|---|---|
| Base wording | Yes, 48 | Yes, 44 | Yes, 47 | Captured linked edition accepted. |
| Customer information sheet | Yes, 20 | Yes, 17 | Yes, 21 | Captured linked edition accepted. |
| Prospectus | Yes, 53 | Yes, 59 | Yes, 56 | Applicable reference; retained in baseline. |
| Excluded expenses | Yes, 1 | Yes, 1 | Reference only, 1 | Assure coverage uses wording clause 27 and List I. |
| Modern-treatment schedule | Yes, 2 | Yes, 2 | Yes, 1 | Captured product-specific supporting schedule. |
| Preventive-health schedule | Yes, 1 | Yes, 1 | No separate capture listed | Include both captured schedules; no new search. |
| Brochure | No, 13 | No, 14 | No, 18 | Marketing material excluded from rules. |
| Proposal form | No, 4 | No, 4 | No, 2 | Not required by manifest eligibility schema. |
| Premium table | Not applicable | Not applicable | Not applicable | Price remains unavailable. |

## Optional covers - none selected

Only one optional-cover section was found in each of the three complete raw wording text scans. The named pages were also rendered and visually checked. This is bounded to the captured wordings; no additional documents were searched.

| Plan | Optional cover and choices | Physical PDF page | Base decision |
|---|---|---|---|
| Star Comprehensive | Buy Back of Pre-Existing Disease Waiting Period: 36 to 12 months, additional premium; first purchase only up to initially chosen sum insured; not renewal or ported policies; medical screening required. | 30 (printed 29/47) | Not selected. Retain base PED waiting period. |
| Family Health Optima | Voluntary co-payment: 10% or 20% for the specified coverages. For entry age 61 or above, this is additional to mandatory copay; applies to every claim. | 28 (printed 27/43) | Not selected. Mandatory base copay must still be assessed. |
| Star Health Assure | Aggregate deductible: Rs. 50,000 or Rs. 1,00,000 each policy year; discount depends on sum insured. | 25 (printed 24/46); illustration on 26 | Not selected. Do not apply this deductible to the base variant. |

## Assure consumables decision - approved correction

There is no unresolved conflict or `needs_human_decision` for Assure. Wording clause 27
(physical PDF page 20, printed page 19) makes List I items payable when there is an admissible
inpatient or day-care claim. Its own List I (physical PDF page 44, printed page 43) is headed
"Items for which coverage is available in the policy". These wording passages are executable evidence.

The separate one-page sheet remains reference only and cannot support rules or replace the wording list.
All 68 numbered items were compared with wording List I using the captured PDF tables, then checked
visually. No item-content differences were found after normalizing case, whitespace and punctuation.
There are formatting/capitalization differences, a different title, and a different column break
(the wording's left column ends at 35; the sheet's at 34). Preserve this comparison in the later
rule review sheet; it does not change the reference-only boundary.

## Edition decision

Accept Comprehensive's captured wording (`POL / COMP / V.24 / 2025`), CIS and prospectus (`PROS / COMP / V.15 / 2025`) despite their 2025 document codes against roster UIN `SHAHLIP26044V092526`. Record this mismatch; it is not a blocker under the brief. Optima's prospectus footer is `PROS / FHO / V.16 / 2026`; Assure's is `PROS / SHA / V.6 / 2026`. The existing page review identifies stray `POL / SS / V.1 / 2024` / SUPER STAR text as other template text, not the pilot prospectus edition.

## Exact document records

### Star Comprehensive Insurance Policy

UIN: `SHAHLIP26044V092526`. Variant: **Base policy without optional covers**.

| Role | Original filename | Pages | Applicability | Reason |
|---|---|---:|---|---|
| `base_wording` | [Policy_Star_Comprehensive_Insurance_Policy_V_21_3a414ab104.pdf](https://d28c6jni2fmamz.cloudfront.net/Policy_Star_Comprehensive_Insurance_Policy_V_21_3a414ab104.pdf) | 48 | `applicable` | Accept captured linked current edition under the brief. Document code year 2025 differs from roster UIN year 2026; accepted mismatch. |
| `customer_information_sheet` | [CIS_Star_Comprehensive_Insurance_Policy_V_2_69c15a9ee1.pdf](https://d28c6jni2fmamz.cloudfront.net/CIS_Star_Comprehensive_Insurance_Policy_V_2_69c15a9ee1.pdf) | 20 | `applicable` | Accept captured linked current edition under the brief. Document code year 2025 differs from roster UIN year 2026; accepted mismatch. |
| `prospectus` | [Prospectus_Star_Comprehensive_Insurance_Policy_V_12_dc6058c95e.pdf](https://d28c6jni2fmamz.cloudfront.net/Prospectus_Star_Comprehensive_Insurance_Policy_V_12_dc6058c95e.pdf) | 53 | `applicable` | Accept captured linked current edition under the brief. Document code year 2025 differs from roster UIN year 2026; accepted mismatch. Retain applicable reference and unchanged baseline processing. |
| `excluded_expenses` | [star_comprehensive_other_excluded_expenses_new_ae97610427.pdf](https://d28c6jni2fmamz.cloudfront.net/star_comprehensive_other_excluded_expenses_new_ae97610427.pdf) | 1 | `applicable` | Captured product-specific supporting schedule; accepted under the brief. |
| `modern_treatment_schedule` | [Modern_Treatment_Star_Comprehensive_Insurance_Policy_627f5a8912.pdf](https://d28c6jni2fmamz.cloudfront.net/Modern_Treatment_Star_Comprehensive_Insurance_Policy_627f5a8912.pdf) | 2 | `applicable` | Captured product-specific supporting schedule; accepted under the brief. |
| `preventive_health_schedule` | [Preventive_Health_Checkup_Star_Comprehensive_Insurance_Policy_87eabc5749.pdf](https://d28c6jni2fmamz.cloudfront.net/Preventive_Health_Checkup_Star_Comprehensive_Insurance_Policy_87eabc5749.pdf) | 1 | `applicable` | Captured product-specific supporting schedule; accepted under the brief. |
| `brochure` | [Brochure_Star_Comprehensive_Insurance_Policy_V_15_Web_633bcfcaaf.pdf](https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Comprehensive_Insurance_Policy_V_15_Web_633bcfcaaf.pdf) | 13 | `not_applicable` | Marketing material; not rule evidence. |
| `proposal_form` | [Offline_Proposal_Form_138e10d5db.pdf](https://d28c6jni2fmamz.cloudfront.net/Offline_Proposal_Form_138e10d5db.pdf) | 4 | `not_applicable` | Underwriting form; manifest schema does not require it for eligibility. |

Integrity/provenance (each URL above is the original captured official URL):

- `base_wording`: SHA-256 `b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`; captured `2026-09-27T07:51:00.571042+00:00`; local object `objects/b1/b1dbe8fb78646f75566d47c32b7ebfa27c4071941c8f548224c461ee35a8021f`.
- `customer_information_sheet`: SHA-256 `afe91f7446ed4dfc6090d3ce746386cf182ab5b094c9c6ae1b5af81a1375e665`; captured `2026-09-27T07:50:57.453679+00:00`; local object `objects/af/afe91f7446ed4dfc6090d3ce746386cf182ab5b094c9c6ae1b5af81a1375e665`.
- `prospectus`: SHA-256 `0404693147bd5202e28e39bfdb8fcc87f78e7ee6aa6a6f1032f63cbec63698e1`; captured `2026-09-27T07:51:03.249704+00:00`; local object `objects/04/0404693147bd5202e28e39bfdb8fcc87f78e7ee6aa6a6f1032f63cbec63698e1`.
- `excluded_expenses`: SHA-256 `ae1e4a9fec23d65f8f983e22b9b76b6c8601baa9dcd2a0dc7b35530607b0f0b8`; captured `2026-09-27T07:51:04.288025+00:00`; local object `objects/ae/ae1e4a9fec23d65f8f983e22b9b76b6c8601baa9dcd2a0dc7b35530607b0f0b8`.
- `modern_treatment_schedule`: SHA-256 `a167e20343d2dfbecf51bebcd64ac0fde4e3ba35431f27490fe94ca6cfadc480`; captured `2026-09-27T07:50:59.161858+00:00`; local object `objects/a1/a167e20343d2dfbecf51bebcd64ac0fde4e3ba35431f27490fe94ca6cfadc480`.
- `preventive_health_schedule`: SHA-256 `c7f4ceb7fb7d3ee02937d107c96f81859b3ecab5c045fbf63aa312bb07770358`; captured `2026-09-27T07:51:01.844706+00:00`; local object `objects/c7/c7f4ceb7fb7d3ee02937d107c96f81859b3ecab5c045fbf63aa312bb07770358`.
- `brochure`: SHA-256 `cca93014d1edc07a3e17d73cf70f900cb1ca85db3398bd637fa81d916ad3d564`; captured `2026-09-27T07:50:55.699144+00:00`; local object `objects/cc/cca93014d1edc07a3e17d73cf70f900cb1ca85db3398bd637fa81d916ad3d564`.
- `proposal_form`: SHA-256 `ca3c33d9bdc5f52898743c69956864b4cc2329ae79a82bf2b87f9ffca0b06bf3`; captured `2026-09-27T07:50:59.678167+00:00`; local object `objects/ca/ca3c33d9bdc5f52898743c69956864b4cc2329ae79a82bf2b87f9ffca0b06bf3`.

### Family Health Optima Insurance Plan

UIN: `SHAHLIP26046V092526`. Variant: **Base policy without optional covers**.

| Role | Original filename | Pages | Applicability | Reason |
|---|---|---:|---|---|
| `base_wording` | [Policy_Family_Health_Optima_Insurance_Plan_V_21_bbe089bd74.pdf](https://d28c6jni2fmamz.cloudfront.net/Policy_Family_Health_Optima_Insurance_Plan_V_21_bbe089bd74.pdf) | 44 | `applicable` | Accept captured linked current edition under the brief. |
| `customer_information_sheet` | [CIS_Family_Health_Optima_Insurance_Plan_V_2_b5d9cdf635.pdf](https://d28c6jni2fmamz.cloudfront.net/CIS_Family_Health_Optima_Insurance_Plan_V_2_b5d9cdf635.pdf) | 17 | `applicable` | Accept captured linked current edition under the brief. |
| `prospectus` | [Prospectus_Family_Health_Optima_Insurance_Plan_V_10_79f547c311.pdf](https://d28c6jni2fmamz.cloudfront.net/Prospectus_Family_Health_Optima_Insurance_Plan_V_10_79f547c311.pdf) | 59 | `applicable` | Accept captured linked current edition under the brief. Retain applicable reference and unchanged baseline processing. |
| `excluded_expenses` | [FHO_Other_excluded_b6ac7e9f79.pdf](https://d28c6jni2fmamz.cloudfront.net/FHO_Other_excluded_b6ac7e9f79.pdf) | 1 | `applicable` | Captured product-specific supporting schedule; accepted under the brief. |
| `modern_treatment_schedule` | [Modern_Treatment_Family_Health_Optima_Insurance_Plan_9428c181fe.pdf](https://d28c6jni2fmamz.cloudfront.net/Modern_Treatment_Family_Health_Optima_Insurance_Plan_9428c181fe.pdf) | 2 | `applicable` | Captured product-specific supporting schedule; accepted under the brief. |
| `preventive_health_schedule` | [Preventive_Health_Check_up_Family_Health_Optima_Insurance_Plan_13ff4299eb.pdf](https://d28c6jni2fmamz.cloudfront.net/Preventive_Health_Check_up_Family_Health_Optima_Insurance_Plan_13ff4299eb.pdf) | 1 | `applicable` | Captured product-specific supporting schedule; accepted under the brief. |
| `brochure` | [Brochure_Family_Health_Optima_Insurance_Plan_V_15_Web_74cee1b82f.pdf](https://d28c6jni2fmamz.cloudfront.net/Brochure_Family_Health_Optima_Insurance_Plan_V_15_Web_74cee1b82f.pdf) | 14 | `not_applicable` | Marketing material; not rule evidence. |
| `proposal_form` | [Offline_Proposal_Form_138e10d5db.pdf](https://d28c6jni2fmamz.cloudfront.net/Offline_Proposal_Form_138e10d5db.pdf) | 4 | `not_applicable` | Underwriting form; manifest schema does not require it for eligibility. |

Integrity/provenance (each URL above is the original captured official URL):

- `base_wording`: SHA-256 `033d6a9576c73efc25aae29c20e97a0cc89d43e43896269a4ed64d663798a54c`; captured `2026-09-27T07:50:59.996156+00:00`; local object `objects/03/033d6a9576c73efc25aae29c20e97a0cc89d43e43896269a4ed64d663798a54c`.
- `customer_information_sheet`: SHA-256 `5527cb614c86736ca494d8ce97cce70abeca12ef861c425bbf011627dbc8ae35`; captured `2026-09-27T07:50:56.984024+00:00`; local object `objects/55/5527cb614c86736ca494d8ce97cce70abeca12ef861c425bbf011627dbc8ae35`.
- `prospectus`: SHA-256 `abe38283100d6402e1ac22929bb94c23bb53994bef7a378196e48900cd4da025`; captured `2026-09-27T07:51:02.499342+00:00`; local object `objects/ab/abe38283100d6402e1ac22929bb94c23bb53994bef7a378196e48900cd4da025`.
- `excluded_expenses`: SHA-256 `1def1773a1a07694531572b226a8ecbd1faefaec2e348d5e191cd32633e4c9b4`; captured `2026-09-27T07:50:58.172578+00:00`; local object `objects/1d/1def1773a1a07694531572b226a8ecbd1faefaec2e348d5e191cd32633e4c9b4`.
- `modern_treatment_schedule`: SHA-256 `066c9150d12c1df1f1fa04c326bd273afd3f78639c705195c5923e9293019c11`; captured `2026-09-27T07:50:58.802377+00:00`; local object `objects/06/066c9150d12c1df1f1fa04c326bd273afd3f78639c705195c5923e9293019c11`.
- `preventive_health_schedule`: SHA-256 `667646c6e403db44541256481b8cf26f13ee23369206c0125bb4b7f8063b09a9`; captured `2026-09-27T07:51:01.520751+00:00`; local object `objects/66/667646c6e403db44541256481b8cf26f13ee23369206c0125bb4b7f8063b09a9`.
- `brochure`: SHA-256 `9f86ed7d514afe927911b26f6c2b4141e81decfdb3bb835886e8655bae5a04c3`; captured `2026-09-27T07:50:55.021332+00:00`; local object `objects/9f/9f86ed7d514afe927911b26f6c2b4141e81decfdb3bb835886e8655bae5a04c3`.
- `proposal_form`: SHA-256 `ca3c33d9bdc5f52898743c69956864b4cc2329ae79a82bf2b87f9ffca0b06bf3`; captured `2026-09-27T07:50:59.678167+00:00`; local object `objects/ca/ca3c33d9bdc5f52898743c69956864b4cc2329ae79a82bf2b87f9ffca0b06bf3`.

### Star Health Assure Insurance Policy

UIN: `SHAHLIP26048V032526`. Variant: **Base policy without optional covers**.

| Role | Original filename | Pages | Applicability | Reason |
|---|---|---:|---|---|
| `base_wording` | [Policy_Star_Health_Assure_Insurance_Policy_V_9_c53663e68a.pdf](https://d28c6jni2fmamz.cloudfront.net/Policy_Star_Health_Assure_Insurance_Policy_V_9_c53663e68a.pdf) | 47 | `applicable` | Accept captured linked current edition under the brief. |
| `customer_information_sheet` | [CIS_Star_Health_Assure_Insurance_Policy_V_2_380ce4ce6b.pdf](https://d28c6jni2fmamz.cloudfront.net/CIS_Star_Health_Assure_Insurance_Policy_V_2_380ce4ce6b.pdf) | 21 | `applicable` | Accept captured linked current edition under the brief. |
| `prospectus` | [Prospectus_Star_Health_Assure_Insurance_Policy_V_3_9b8479dfdd.pdf](https://d28c6jni2fmamz.cloudfront.net/Prospectus_Star_Health_Assure_Insurance_Policy_V_3_9b8479dfdd.pdf) | 56 | `applicable` | Accept captured linked current edition under the brief. Retain applicable reference and unchanged baseline processing. |
| `excluded_expenses` | [Health_Assure_List_of_Excluded_Expenses_9be58ee6be.pdf](https://d28c6jni2fmamz.cloudfront.net/Health_Assure_List_of_Excluded_Expenses_9be58ee6be.pdf) | 1 | `applicable`, reference only | Wording clause 27 and its own List I establish consumables coverage. Separate sheet retained only as reference. |
| `modern_treatment_schedule` | [Modern_Treatment_Star_Health_Assure_Insurance_Policy_7746fe52d9.pdf](https://d28c6jni2fmamz.cloudfront.net/Modern_Treatment_Star_Health_Assure_Insurance_Policy_7746fe52d9.pdf) | 1 | `applicable` | Captured product-specific supporting schedule; accepted under the brief. |
| `brochure` | [Brochure_Star_Health_Assure_Insurance_Policy_V_5_Web_8153c42b87.pdf](https://d28c6jni2fmamz.cloudfront.net/Brochure_Star_Health_Assure_Insurance_Policy_V_5_Web_8153c42b87.pdf) | 18 | `not_applicable` | Marketing material; not rule evidence. |
| `proposal_form` | [Proposal_Form_0b4f1c4c9c.pdf](https://d28c6jni2fmamz.cloudfront.net/Proposal_Form_0b4f1c4c9c.pdf) | 2 | `not_applicable` | Underwriting form; manifest schema does not require it for eligibility. |

Integrity/provenance (each URL above is the original captured official URL):

- `base_wording`: SHA-256 `e0f774a84f3bfd7ab952119d3c57e107ed8c993909a80e50f225f81aeadb146a`; captured `2026-09-27T07:51:01.266167+00:00`; local object `objects/e0/e0f774a84f3bfd7ab952119d3c57e107ed8c993909a80e50f225f81aeadb146a`.
- `customer_information_sheet`: SHA-256 `9b577e1226bbfde552575bedf8e0b74edf792a2db5c788b008196d99f23d5f2e`; captured `2026-09-27T07:50:57.850042+00:00`; local object `objects/9b/9b577e1226bbfde552575bedf8e0b74edf792a2db5c788b008196d99f23d5f2e`.
- `prospectus`: SHA-256 `91a761206899caafe957f0c874d75c1b05b9e0b53601d2f57761309a9b0899be`; captured `2026-09-27T07:51:03.893128+00:00`; local object `objects/91/91a761206899caafe957f0c874d75c1b05b9e0b53601d2f57761309a9b0899be`.
- `excluded_expenses`: SHA-256 `1f277749e6cbce0dac5e9a1ca0fdf2a8790c71a2bf12d7169a7ebf9a897e04da`; captured `2026-09-27T07:50:58.561561+00:00`; local object `objects/1f/1f277749e6cbce0dac5e9a1ca0fdf2a8790c71a2bf12d7169a7ebf9a897e04da`.
- `modern_treatment_schedule`: SHA-256 `4e199d99893cb7966344788f6994137c4d09a7aa8c59aff6439c6e2036ec0667`; captured `2026-09-27T07:50:59.413095+00:00`; local object `objects/4e/4e199d99893cb7966344788f6994137c4d09a7aa8c59aff6439c6e2036ec0667`.
- `brochure`: SHA-256 `2c4e128c6ddacb9a809d5e4ec52d6468ed8bed4cd9b23ee7234078257eb4dc7b`; captured `2026-09-27T07:50:56.811306+00:00`; local object `objects/2c/2c4e128c6ddacb9a809d5e4ec52d6468ed8bed4cd9b23ee7234078257eb4dc7b`.
- `proposal_form`: SHA-256 `10d59c5e7a6b08c963da9942f59415ae9cb72614a3069807a74b49e9d785d683`; captured `2026-09-27T07:51:02.144679+00:00`; local object `objects/10/10d59c5e7a6b08c963da9942f59415ae9cb72614a3069807a74b49e9d785d683`.

## Verification and saved work

- All 23 document associations (22 distinct local objects) passed SHA-256 and physical-page-count verification. No listed object was missing; no re-fetch was needed.
- Read existing capture, audit, edition-page and option-lead records. Only the three captured wordings were newly text-inspected for optional covers, using `pdftotext -raw` with page breaks; their option pages were visually checked. The subsequent approved correction was verified against wording clause 27, wording List I and the separate sheet; all 68 item descriptions match after presentation normalization.
- Experiment commit: `635ed34` (`research: save uncommitted experiment runners and notes`) on `research/comparative-programme-20260925`. All 14 modified plus 51 untracked files were committed byte-for-byte unchanged, verified against their pre-test SHA-256 hashes.
- Tests: 21 changed/new experiment test files, 73 cases: **71 passed, 2 skipped**. The skipped isolated-database tests are `test_experiments.py:348` and `:368`; `COVERGUIDE_RESEARCH_TEST_STATE` was not configured. No failures. These results and skips are in the commit body.
- Disk available: about 17 GB at this checkpoint, above the 3 GB stop threshold.
- The above checks were the Checkpoint 1 baseline. Implementation after approval is documented in `docs/star-three-plan-local.md`. This is not Checkpoint 2's extracted-rule review.

## Source records

- `research/pilots/star/captures-2026-09-27.json`
- `research/pilots/star/pilot-audit-2026-09-27.json`
- `research/pilots/star/edition-page-review-2026-09-29.json`
- `research/pilots/star/pilot-option-leads-2026-09-29.json`
- `backend/apps/adviser_v2/manifest.py` (read only, proposal-role requirement)

Checkpoint 1 is approved. Continue implementation and independent validation; wait at Checkpoint 2 before publication.
