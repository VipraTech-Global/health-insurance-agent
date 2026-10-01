# Three Star plans: local implementation and verification

The isolated app is running at <http://127.0.0.1:3021>, backed by the loopback API on port 8021 and PostgreSQL database `coverguide_star_slice`. Release `3c1737d7-d755-4ec4-8352-028b81c52cc4` was built and published locally through the existing management commands as `development_alpha_3_product`. Nothing was pushed or published outside this machine.

The synthetic demo login is in the [local runtime notes](/home/akhilesh/.local/state/coverguide-star-slice/reports/star-e2e-local-login.txt), outside Git with permissions 0600.

All **39 prepared facts** are supported and displayed with their conditions and clause links. **36 are not executable**. The three executable Comprehensive facts (deductible, portability and geography) supply five verified rule records; no descriptive fact or free-text answer becomes an executable rule. The comparison does not claim personal eligibility, payable claim amounts or waiting periods already served. Prices remain unavailable.

The [retrieval benchmark](star-retrieval-benchmark.md) records the mechanical selection, every cell and failed packet, latency, and the full PageIndex indexing/search call cost. Its references are our own reviewed facts, **not an independent gold set**. The actual reference set contains 236 distinct clauses and 273 cell-clause associations, correcting the brief's older count of 231.

## Retrieval result and runtime decision

PageIndex won the frozen selection rule and is now the default (`COVERGUIDE_EVIDENCE_RETRIEVAL=pageindex`). It completed **16/39 cells at 16k and 15/39 at 8k**, compared with BM25 **10/39 and 3/39**, current FTS+dense **6/39 and 3/39**, and MiniLM **4/39 and 3/39**. A cell requires every reference in both prewritten query variants. At 16k, PageIndex recalled 424/546 references (77.7%), with zero wrong-plan hits. Its median/p95 search latency was **9.555/15.987 seconds**, versus BM25 **1.775/5.471 milliseconds**. It completed 8/18 table-heavy queries at 16k; this remains a retrieval limitation, not a replacement for the approved facts.

Its actual benchmark cost was **2,996 calls** (2,918 indexing, 78 search), **10,192,703 input tokens**, **2,463,232 cached input tokens**, **35,462 reasoning tokens** and **354,297 output tokens**. Cached/reasoning tokens are subsets, not additional totals. The relay reported no HTTP timeout/failure in those calls. The adapter failure described below is included in the actual indexing cost. No dollar estimate is inferred from subscription calls.

The app consumes the cached local SDK trees after checking PDF hash, raw-page hash, SDK revision, node identity and physical page bounds. It uses the exact measured search prompt and maps selected nodes to untouched original pages. Generated titles/summaries never enter the answer evidence. Node selection is untrusted retrieval, not a new insurance-output contract; the existing extraction route qualification is checked, and qualified extraction/review plus deterministic validation remain mandatory. Invalid/missing trees or relay output produce a specific visible unknown rather than substituting another source. BM25 remains available behind the setting without a dense-qualification dependency.

## Real app runs

Every row below used the browser → API → durable turn/outbox → isolated Celery worker → model extraction and independent review → saved comparison → browser path. City and premium budget were answered as unknown. The hypothetical optional covers in the two family seeds remained unselected.

| Synthetic profile | Ages | Requested sum insured | Additional question | Final PageIndex result |
|---|---|---:|---|---|
| Adult individual | 32 | INR 1,000,000 | Road ambulance | Three cited answers |
| Family with child | 38, 35, 4 | INR 2,000,000 | AYUSH inpatient treatment | Comprehensive and Assure cited; Optima unknown |
| Older parent | 68 | INR 500,000 | Organ-donor expenses | Assure cited; Optima and Comprehensive unknown |
| Mixed-age family | 61, 59, 22 | INR 5,000,000 | Consumables/non-medical expenses | Assure cited; Optima and Comprehensive unknown |

All four show the same 39 supported cells, three equally sized columns, neutral wording, clause links and unavailable prices. The extra questions produced **seven cited plan answers and five explicit unknowns**. The earlier BM25 baseline (retained in commit `225f8ae`) produced nine cited answers and three unknowns. Thus this small live sample did **not** improve the overall validated-answer count, despite PageIndex winning the frozen reference-retrieval benchmark. Generated answers and independent reviews also differed; these runs do not isolate retrieval as the sole cause. PageIndex remains the default because the brief specifies the frozen selection rule.

The five final unknowns are:

- **Optima AYUSH:** the packet ended the hospital definition before its required facility criteria continued.
- **Optima organ donor:** independent review identified nonexistent secondary-statement indexes, so a valid reviewed projection could not be formed. This is a review-output failure, not evidence of exclusion.
- **Comprehensive organ donor:** the answer omitted continuous coverage, first-policy inception and portability conditions from the transplant waiting period.
- **Optima consumables:** the answer treated infusion-pump cost in a subsumed-cost list as covered without distinguishing the base wording's express aid exclusion.
- **Comprehensive consumables:** the answer omitted the sections to which day-care coverage applies and its policy-schedule Sum Insured limit.

These results remain unknown after the allowed correction; no source or review gate was weakened. Assure's consumables answer now cites **its own wording at physical pages 20, 44 and 45**, including the List I heading and short item quotes. It confirms List I coverage on an admissible inpatient/day-care claim and distinguishes Lists II–IV as costs subsumed into room/procedure/treatment charges. The separate expense sheet is absent from executable/retrievable evidence and remains reference only. No consumables rule was added.

Final turn elapsed times were 545.0 seconds (adult), 210.6 (family with child), 312.6 (older parent), and 362.5 (mixed-age family). Adult elapsed time includes waiting behind the consumables run on the single worker. These are full interactive turns, including interpretation, retrieval, extraction, review, corrective calls and queue time; they are not the benchmark's search-only latency.

The live PageIndex runs, including the superseded ambulance run caused by our prompt bug, made **15 additional search calls**: 1,119,604 input tokens, 857,856 cached input tokens, 7,820 output tokens, 4,850 reasoning tokens and 189.216 summed call seconds, with no transport failures or retries. The audit stores per-call usage and wall time for each final turn, plus all normal model-attempt timings and earlier unknowns. These live costs are separate from the 2,996 benchmark calls.

The [saved audit](star-e2e-review.json) includes all four conversation IDs, final questions and comparisons, profile snapshots, source answers, model-attempt statuses, wall times and token usage, earlier failed turn IDs and superseded unknown statements. It checks **285 distinct native clause anchors**, including every prepared citation and the final free-answer citations, against the applicable plan's raw pages, hashes, original offsets and PDF rectangles. No wrong-plan or excluded-document citation passed.

The [browser citation audit](star-ui-citation-audit.json) opened a clause in **each of the 39 cells**, checked the page and exact quote against the evidence API, and observed the PDF highlight. All 273 prepared citation associations were also checked during release validation. The [final PageIndex browser audit](star-pageindex-ui-audit.json) checked 39 fact cells, three unavailable prices and the saved source answers in each of the four conversations. The final PageIndex run additionally opened and highlighted Assure's wording List I on physical page 44. A delayed profile-loading browser test verified that Send is disabled until the matching profile is loaded.

- [Full three-plan comparison](screenshots/star-three-plan-comparison.png)
- [Opened clause with highlight](screenshots/star-opened-citation.png)
- [Three cited ambulance answers](screenshots/star-free-text-answer.png)
- [Consumables answer and explicit validation reasons](screenshots/star-consumables-answer.png)
- [Assure wording List I on physical page 44, highlighted](screenshots/star-consumables-citation.png)

## Decisions and reasons

- Preserve the approved 39 facts and their accepted calls. Revalidate their exact stored anchors at publication instead of re-extracting them. When whitespace folding finds an earlier duplicate phrase, retain the approved raw anchor after verifying its exact text, hash, page, offsets and geometry.
- Keep fact membership separate from rule membership. A source-supported fact can be useful for comparison without authorizing a calculation. Publication retains the verified-rule, dependency, applicability, qualification, completeness and immutability gates, including the existing five-product path.
- Keep each plan's raw evidence in a separate 16k source-token packet. Use the customer's question as the lexical query; pass structured profile facts only to the answer stage. Whole chunks/pages that do not fit are accounted for explicitly. Incomplete evidence produces a reason, never an inferred exclusion.
- Use the existing qualified extraction/review response contracts for free answers, followed by exact raw quote, number, source-scope, independent-review and PDF-geometry checks. Keep one corrective validation retry and a separate limit of two transport retries. Source answers never enter the deterministic rule engine.
- Use low reasoning and an 8,192-token output cap for extraction, high reasoning for independent review, and sequential plan calls. Extend only this isolated runtime's turn deadline to 900 seconds so the required per-plan calls can finish. Per-call timings and input/cached/reasoning/output usage are logged; older calls made before INFO logging was enabled lack a retained reasoning-token breakdown.
- Use a worktree-local `.venv-star` and ignored environment file because the shared environment lacked a required ONNX package. Keep the existing model routes and qualification identities; run no new qualification programme or 400-case evaluation. Use PostgreSQL/pgvector as the foundation and leave the shared relay untouched.
- Adopt PageIndex despite its higher latency because it wins the stated rule at both budgets. Retain BM25 as the simpler configured alternative. Reuse all 39 approved facts; only the four extra customer questions are rerun against the winning retriever. Preserve incomplete evidence as explicit unknowns rather than retrying until a preferred answer appears.

## Failures found and fixed

The first isolated full test run lacked ONNX (409 passed, two failed); installing the locked dependency in `.venv-star` resolved both. The first local release build rejected an already approved clause because whitespace folding found an earlier duplicate; exact stored-anchor replay fixed that cause without relaxing raw-text or publication checks.

Live browser runs exposed a lakh/crore currency conversion error, profile-date JSON serialization, a per-plan prompt that tried to answer for all three policies, medically contextual “better” tripping the unchanged neutrality gate, missing bed-count unit recognition, combined bullet quotes that omitted raw control characters, and statute year 1994 incorrectly requested as a duration. These were repaired with focused regression coverage or prompt corrections. Original failed/unknown attempts remain recorded; accepted prepared facts were reused.

A rapid conversation switch produced a legitimate HTTP 409 when Send carried the previous profile revision. The UI now waits for the matching profile and ignores stale conversation/stream responses. The delayed-loading browser check and subsequent real profile run passed. The `unknown` support state is declared in the model and design dictionary; its choice-only migration was applied only to the isolated runtime and its tests. Customer-visible reasons omit internal field markers while stored reasons remain intact.

The first PageIndex ambulance run exposed our own prompt example narrowing “better medical treatment” to “a higher level.” The example now uses “improved medical treatment” and explicitly forbids narrowing the condition. After that prompt correction, the same question passed for all three plans with exact original quotes. The superseded Optima unknown and every extra call remain in the audit. This correction did not change the neutrality, quote, number, review or retry rules.

A router regression check also caught bare “family” suppressing retrieval for unrelated questions such as psychiatric treatment. Only explicit family-size/composition or floater questions now match that prepared criterion; other family coverage questions reach retrieval.

The initial PageIndex run encountered an adapter finish-reason mismatch (`stop` versus `finished`). The adapter was corrected, completed responses cached, and the run resumed. Its full actual call cost, including that earlier run, is in the benchmark report.

## Verification

| Check | Actual result |
|---|---|
| Ruff: backend, scripts and Star research harness | Passed |
| Full pytest suite in isolated test DB | **461 passed**, 18 warnings, 32.05 seconds |
| Focused PageIndex and raw-retrieval suite | 36 passed |
| Django system check | No issues |
| Migration consistency | No changes detected |
| OpenAPI and TypeScript API generation | Passed; generated contracts retained |
| Frontend lint, typecheck and production build | Passed |
| Four real UI profiles | Completed; ages, sums insured, unknown city/budget and unselected options checked |
| All-cell citation UI audit | 39/39 opened with correct page and visible clause highlight |
| Native source audit | 285 distinct anchors; zero wrong-plan/excluded-source citations |

PDF.js emitted one font warning during browser inspection; the inspected PDF pages still rendered and their clause highlights were verified. The 18 pytest warnings report the absent local `staticfiles/` collection directory; no test failed. Disk free space stayed above 3 GB (about 13 GB at the final app checks). Changes were confined to the Star worktree, isolated database/runtime and local research environment; existing apps, shared credentials and model artifacts were retained.

Reproduce the checks using `bash scripts/star_slice.sh test -q`, `bash scripts/star_slice.sh check`, and `bash scripts/star_slice.sh manage makemigrations --check --dry-run`. Load `.env.star-slice` before building the frontend so its backend rewrite remains on port 8021. Research harnesses live in `research/pilots/star/`; captured PDFs, raw text and PageIndex trees remain in local ignored storage.

## Local commits

Implementation commits since the approved checkpoint, before this final evidence/report commit:

- `27f5cff` Freeze the Star retrieval benchmark questions
- `1fc5ee3` Publish reviewed facts separately from executable rules
- `a407f60` Preserve lakh and crore amounts when normalizing currency units
- `8702436` Answer uncovered questions from separate per-plan evidence packets
- `036763f` Show all reviewed facts and clause sources in the three-plan comparison
- `71e1f69` Validate hospital bed counts and preserve raw bullet quotations
- `c9dd994` Measure four retrieval arms against frozen raw clause references
- `05a9f09` Keep statutory identifiers separate from measured quantities
- `dd97be7` Wait for the matching profile before sending a conversation message
- `610328d` Review source identifiers without inventing measurement units
- `1f4e123` Represent source unknowns and keep their displayed reasons readable
- `225f8ae` Record four local profile runs and clause highlight evidence
- `aa37dcb` Retrieve uncovered family questions instead of treating them as floater facts
- `15f8d3c` Record the completed four-arm retrieval benchmark
- `8d628fa` Use measured PageIndex retrieval with original per-plan evidence
- `2b7e370` Show the review reason without its internal issue label
- `54eaabd` Document the published local slice and measured retrieval runtime
- `107d38f` Preserve the scope of medical treatment conditions in source answers
- `af85f8e` Explain remaining source-review failures in plain language
