# Star cited-fact processing measurements

Updated Checkpoint 2. All runs use the isolated `coverguide_star_slice` database. No release was built or published.

| Plan | Supported / 13 | Unknown / 13 | Prospectus used |
| --- | ---: | ---: | --- |
| Star Comprehensive Insurance Policy | 13 | 0 | eligibility, family_floater, newborn, sum_insured |
| Family Health Optima Insurance Plan | 13 | 0 | eligibility, sum_insured |
| Star Health Assure Insurance Policy | 13 | 0 | eligibility, sum_insured |

Rule encoding is reported separately from source support. Budget is unavailable; derived `no_copay` is outside the 13 criteria.

Final count: **39/39 supported source facts**, with no unresolved source criteria. Assure PED states 30 months of continuous coverage for a 3-year policy term and 36 months for 1-year and 2-year terms, measured from inception of the first policy with the insurer (wording physical page 27, Code-Excl 01 A).

## Assure PED whitespace fix

Quote matching now removes all whitespace for comparison and makes no other character normalization. The match maps back to original raw-page offsets; the stored/displayed quote and PDF highlighting use that original substring. Case, punctuation, ligatures and non-whitespace control characters must match. Tests cover `Insuredtheexclusionshallapplyafresh`, repeated occurrences, mapped spans, whole-page rejection and non-whitespace differences.

Only Assure PED received a fresh extraction and independent review. It passed on the first call, using wording/CIS/schedules without a prospectus supplement, with no corrective retry or timeout. All 38 previously accepted facts, their progress records and reviews were preserved. Previous PED attempts remain archived.

| New call | Wall time | Input tokens | Cached input | Output tokens | Reasoning tokens |
| --- | ---: | ---: | ---: | ---: | --- |
| PED extraction | 41.267 s | 62191 | 60160 | 1754 | Not recorded |
| Independent review | 12.347 s | 62103 | 0 | 571 | Not recorded |

Extraction attempt: `ee8b7ec4-385a-4b12-878e-4871985b57d5`; independent review: `e0bbba29-b325-4715-ae7d-c471d8be5e4a`; final validation: `e3bbe276-4496-430c-af6a-560ef1c3670f`.

## Timing and cache observation

Comprehensive, sum insured:

| Measurement | Earlier extraction | Updated fresh first call |
| --- | ---: | ---: |
| Wall time (seconds) | 283.187 | 46.581 |
| Input tokens | 72597 | 122965 |
| Cached input tokens | Not recorded | 122752 |
| Output tokens | 5826 | 2438 |
| Reasoning tokens | Not recorded | 285 |

Earlier attempt `ea1f4056-161a-4654-a12f-ea8c7f765536`; updated attempt `b9392a0d-2e0c-4520-8ebc-ba3ed2b80ff0`. The later call was 6.1 times faster. This is an observation, not a controlled benchmark: the fact protocol, full prospectus, prompt, output, effort and concurrency differ. A successful response is not proof of source support; see the review sheet for final status.

The current runs process one plan at a time. Prior runs used up to three concurrent plans. Sequential operation has lower observed call latency, but there is no controlled total-throughput comparison against two concurrent plans. Extraction uses low reasoning and an 8,192-token ceiling; independent review retains high reasoning. Shared bundle text precedes criterion instructions.

## Attempts and retained evidence

All retained calls: 187; status counts: cancelled 3, schema_error 13, succeeded 170, timeout 1.
Since the table-fix rerun: 78 calls, 0 timeouts. Historical timeouts: 1.
Successful extract calls since the table fix: 35, median 46.379 seconds.
Successful independent_review calls since the table fix: 39, median 12.881 seconds.

The two original Comprehensive sum-insured prompt failures are archived and excluded from the fresh first-call/corrective-call budget. The approved six-criterion rerun preserves all seven previously accepted facts and their existing reviews. Transport errors have a separate two-retry allowance. No model output, source PDF or raw text was overwritten.

Newborn uses the prospectus to verify the actual offered sums insured: there is no option strictly between ₹25 lakh and ₹50 lakh. Exact table rows/cells and labels are separate clause citations from the same region. The PED core excludes peripheral grace-period assertions when unsupported.

Per-call timing, input/cache/output/reasoning usage, statuses and attempt IDs: `~/.local/state/coverguide-star-slice/reports/cited-fact-call-metrics.json`. Missing provider usage remains explicitly unavailable.

## Verification

- Backend: 411 tests passed; 18 existing missing-static-directory warnings. Focused quotation/pipeline tests: 80 passed.
- Ruff, Django checks and migration check passed.
- Frontend lint, typecheck and build passed at the preceding checkpoint; no frontend files changed in this fix.
- Clause audit passed for 236 distinct spans across 68 physical document pages: exact stored raw text, physical page, hash, character span and stored highlight rectangles.
- The [Assure PED citation screenshot](playwright/star-assure-ped-whitespace-clause.png) shows the original enhancement clause highlighted on physical page 27. The adjacent term-dependent 30/36-month clauses are visible. The browser check used the existing synthetic local account.
- Isolated database releases: 0. API response schemas and model qualifications were unchanged.
- Step 6 and publication remain unstarted. Full comparison and synthetic-profile UI verification were not run.
