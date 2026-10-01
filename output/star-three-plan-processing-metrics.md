# Star cited-fact processing measurements

Updated Checkpoint 2. All runs use the isolated `coverguide_star_slice` database. No release was built or published.

| Plan | Supported / 13 | Unknown / 13 | Prospectus used |
| --- | ---: | ---: | --- |
| Star Comprehensive Insurance Policy | 13 | 0 | eligibility, family_floater, newborn, sum_insured |
| Family Health Optima Insurance Plan | 13 | 0 | eligibility, sum_insured |
| Star Health Assure Insurance Policy | 12 | 1 | eligibility, sum_insured |

Rule encoding is reported separately from source support. Budget is unavailable; derived `no_copay` is outside the 13 criteria.

The remaining unknown is Assure's PED waiting period: the retained quotations do not match wording physical page 27 word for word after the corrective attempt. The raw text contains fused words that the model separated. Exact-match validation remains in place.

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

All retained calls: 185; status counts: cancelled 3, schema_error 13, succeeded 168, timeout 1.
Since the table-fix rerun: 76 calls, 0 timeouts. Historical timeouts: 1.
Successful extract calls since the table fix: 34, median 46.451 seconds.
Successful independent_review calls since the table fix: 38, median 12.926 seconds.

The two original Comprehensive sum-insured prompt failures are archived and excluded from the fresh first-call/corrective-call budget. The approved six-criterion rerun preserves all seven previously accepted facts and their existing reviews. Transport errors have a separate two-retry allowance. No model output, source PDF or raw text was overwritten.

Newborn uses the prospectus to verify the actual offered sums insured: there is no option strictly between ₹25 lakh and ₹50 lakh. Exact table rows/cells and labels are separate clause citations from the same region. The PED core excludes peripheral grace-period assertions when unsupported.

Per-call timing, input/cache/output/reasoning usage, statuses and attempt IDs: `~/.local/state/coverguide-star-slice/reports/cited-fact-call-metrics.json`. Missing provider usage remains explicitly unavailable.

## Verification

- Backend: 402 tests passed; 18 existing missing-static-directory warnings.
- Ruff, Django checks and migration check passed.
- Frontend lint, typecheck and build passed.
- Clause audit passed for 231 distinct clause spans: exact raw page text, physical page, hash, character span and stored highlight rectangles.
- The seven previously accepted Comprehensive facts retain their values, conditions, citations, attempt IDs and independent reviews.
- PDF viewer verified with a [portability clause](playwright/star-portability-clause.png) and a [maternity table row](playwright/star-maternity-table-row.png); both highlight the cited text on the physical page shown.
- Isolated database releases: 0. API response schemas and model qualifications were unchanged.
- Full comparison and synthetic-profile UI verification await publication approval; they were not run at this checkpoint.
