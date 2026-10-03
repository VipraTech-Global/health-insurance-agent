# Ten-insurer demo decisions

## 2026-10-02 — scope and protocol, before scored calls

- Work starts at `b1a5a22` on `feat/ten-insurer-chat-demo`, in the existing pilot worktree. Only `coverguide_star_slice`, its test database and Redis on port 6401 are allowed. API/frontend remain 8021/3021. No push or off-machine publication.
- The supplied final plan supersedes the older brief where they conflict: a Star cell requires complete reference coverage in **both** queries; no customer profile in search queries; preserve old dependencies until their replacements work.
- The user's section 15 addition supersedes the single-model rule. Luna is primary; only an explicit subscription usage/weekly-limit error permits Sonnet on the same `/v1/responses` relay. Ordinary transport errors never switch models. Redis coordinates the model state, probes and six-call cap across processes. Sonnet receives a message list and schema instructions; local schema validation is mandatory for both models.
- The full brief was found at `../health-insurance-agent/output/codex-brief-final-plan.md`. Its ten fallback sample names and twenty answer-sheet topics are available. Comparable official retail-health figures must establish any ranking; otherwise label these insurers a demo sample.
- Preserve the 39 historical facts and the original stored reference memberships. Old Sol maps are incompatible with the new cache configuration. New map caches record every contributing model, PDF/raw hashes, settings and processing version.
- H versus P only. Score = complete Star cells + answered/260*39. Protocol v2: only displayed wrong-plan quotations disqualify; rejected attempts are reported separately. P wins eligible ties within two points. If both disqualify, higher score wins (exact tie P), disclosed, without disabling live answering. No post-result tuning. Thirteen slots remain weighted separately even if physical documents overlap. Missing cases stay in the denominator. See `docs/ten-insurer-bakeoff-protocol.md`.
- Existing local pilot stays intact during replacement. No destructive schema cleanup until source data, authentication and erasure dependencies are preserved and verified.

## 2026-10-02 — protocol version 2, explicit user amendment

Before any scored call, the user changed disqualification to count only wrong-plan quotations shown after all six checks pass. Rejected attempts remain in the report without disqualification because the check worked. If both arms disqualify, use the higher score and disclose the disqualifications; never disable live answering due to this result. Exact double-disqualification ties use P for determinism. This replaces protocol v1 and conflicting supplied-plan text. No scored calls have run.

## Implementation status

Work in progress. No new bake-off has run and no ten-insurer release has been published.

## 2026-10-02 — implemented processing and validation choices

- The relay checks both `error.code` and `error.type`. Continuous Luna 429s without a recognized quota switch emit a critical operator warning after 30 minutes; the warning is shared and rate-limited in Redis. Ordinary throttles still do not trigger model switching.
- Policy statements are extractive: deterministic checks reject unsupported paraphrases because lexical overlap cannot establish semantic entailment. This is deliberately conservative; passing code checks is not an expert correctness review.
- Official source discovery is separate from admission to executable evidence. The sample has seven admitted plan bundles so far (the preserved Star three and four additional flagships); five other insurer flagships remain unavailable or lack confirmed current-edition files. Source links are not counted as plans. ICICI's current product page lists a newer UIN than the older PDF found in search, so that PDF has not been admitted.
- Original Star reference integrity is snapshotted: 39 facts, 236 distinct spans and 273 criterion memberships. Physical files and accepted maps are reused; role metadata changes do not require new model calls. Matching-section vectors are reused only with identical source hashes.
- Missing premium documents are `source_unavailable`, not `unpublished`; absence from our bundle does not prove the insurer publishes no chart.
- A failed or abandoned question retains its immutable release/index pins. Recovery skips completed plan results; execution tokens prevent an old worker from publishing after a replacement claims its lease.

## Verification notes during implementation

- Focused relay/needs/contract checks: 32 passed. Evaluation and encrypted-session checks: 10 passed before adding crash recovery; the expanded session/contract/needs run then passed 23 tests.
- Physical first-page inspection confirms HDFC `HDFHLIP26058V082526`, Tata AIG `TATHLIP26052V052526`, Bajaj `BAJHLIP26074V022526` with EDGE+ Plan 9, and Manipal `MCIHLIP26036V022526` with Protect/Advantage and June 2025 wording. This records identity checks, not review of every clause.
- The existing full BGE-M3 artifact passes its pinned qualification check. No shared model files were changed. One resident CPU worker performs embeddings.
- Browser smoke testing caught a frontend build made without the isolated backend URL. Rebuilds must set `COVERGUIDE_BACKEND_URL=http://127.0.0.1:8021`; a runtime-only environment value does not rewrite Next's compiled proxy routes.

- Full pytest completed with 513 passed and 19 warnings; three additional card/chart projection tests passed afterward. The expanded relay suite, including inner PageIndex JSON repair, passed all 18 tests. These are implementation checks, not a completed application answer sheet.
- PageIndex's outer structured wrapper can contain malformed task-requested JSON. Inner JSON is now locally validated before caching, with the same single JSON repair allowance. Valid completed maps remain reusable; malformed cached internal responses are retained as `.invalid-json` artifacts rather than reused as successes. Transport failures remain pending; deterministic failed maps receive recorded fallback sections.
- Completed-document embeddings now overlap mapping of other documents via a shared source-text cache. Full maps are not rebuilt when other documents finish. The one-command stack probe succeeded for API, frontend, demo worker, database, Redis, relay and the resident BGE worker.

## Before the scored run — table evidence and packet accounting

- All 33 admitted physical PDFs finished processing: 32 accepted maps and one Manipal Protect benefit-illustration fallback. Its original text uses the prescribed 1,024-token / 128-overlap pieces. No scored call has run.
- Physical table regions retain row/column cell positions and exact original-text citations. Table answers must cite the value and each selected axis separately; a label from another row or column fails validation. Ambiguous source cells are not admitted.
- The 16,000-token packet limit includes serialized evidence and citation metadata. Oversized tables/sections are omitted explicitly, without truncating source clauses. The same builder applies to H and P.
- Thirty focused contract, evidence and evaluation tests passed, including table axes, missing labels, isolated numbers and serialized packet accounting. Model/call/token audit scope now records each method/question pair, including split attempts.

- The expanded full suite passed: 522 tests, 19 warnings. Ruff, Django checks, migration drift checks, frontend lint/typecheck and production build passed. These checks precede the scored calls and do not establish answer correctness.
- Offline cards retrieve five small field groups through the winning method to avoid a single oversized response. Only explicit new-business rupee lists are compiled; conditional or renewal-only amounts remain quoted text. Complex family/basis rules remain unresolved until executable support exists.

- Before scored calls, the navigation serializer was changed to emit each document description and shared node summary once, retaining every selectable section ID, title path and physical range. Split pieces no longer repeat the same generated prose. Evidence/index text is unchanged; both arms use this identical navigation map.

## 2026-10-02 — frozen run and browser recovery

- Protocol v2 scored calls started from commit `bc48709`, input fingerprint `db24172e69e7da37cda1aa7e8d2b46e94f67e8aa39b133bcf25cfed69a731a21`. The 13 slots and 260 answer cases per arm remain fixed, including five unavailable flagship slots. New recoveries enter only the application catalogue after winner selection.
- Playwright-rendered official download registers and in-page fetch recovered PDFs that plain HTTP clients could not obtain. Browser viewer HTML, even with a `.pdf` filename, is rejected. Bytes are validated and stored once by SHA-256, initially as unreviewed candidates.
- A separate post-run diagnostic counts failed attempts whose only reported problem is extractive/paraphrase support, final unanswered cases with that sole failure, and discarded split-pair attempts separately. It does not alter the frozen validators, prompts, scoring or pair files.
- Niva's publicly linked premium PDF contains an internal-training/final-version-pending disclaimer. Retain it as reference-only; it cannot produce customer prices without an applicable final chart.

## Frozen-run execution correction — before winner calculation

The runner saved 337 complete pairs and 34 archived retry attempts, then stopped on Tata restoration. The source selector correctly rejected unknown section IDs, but `answer_plan` returned that failure without a model list. The pair runner misclassified the missing label as a model transition. Relay records retain the requested and observed model, including these rejected selections.

A separate accounting command, committed before calculating a winner, uniformly chooses the earliest saved same-model attempt using those call records. Failed selections count as failures; later successes cannot replace them. Actual mixed-model attempts remain inadmissible. All original pair/attempt files remain unchanged, and the accounted rows, provenance and hashes are stored separately. No scored AI calls, source documents, navigation maps, prompts, validators, packet settings, scoring formula or winner rule are changed. This is an execution/accounting repair, not a new retrieval arm or a protocol-tuning run. Extra retry calls and rejected drafts remain reportable.

## Frozen winner and measured answer outcomes

H wins under protocol v2: 11/39 complete Star cells plus 89/260 accepted answers gives 24.35; P has 9/39 plus 70/260, giving 19.50. Each arm retains 100 unavailable answer cases. No accepted/displayed wrong-plan quotation was found. All scored AI calls used Luna; there were no actual model-split pairs. The runner-label correction discarded 33 extra attempts across 15 jobs without replacing first-attempt failures with later successes.

Paraphrase alone caused 8 final unanswered H cases and 7 P cases, with 27 and 24 rejected drafts respectively in the scored attempts. Extra discarded-runner drafts are reported separately (3 H, 7 P). This is a syntactic rejection classification, not proof that a paraphrase was semantically correct.

The source-section audit has **two** fallbacks: HDFC's `c882c2b1…` map has crossing sibling ranges; Manipal's `c6b8580e…` map did not complete. Earlier progress notes counted only the mapping-call failure and missed HDFC's later section-bound validation fallback. The frozen report uses the actual two fallback documents.

H is now the sole application search path. BM25 and the resident BGE-M3 CPU worker remain. P and byte-identical frozen sources are retained under `research/ten-insurer/`; no runtime fallback exists. Idle old Star worker/beat processes were stopped after verifying zero active work, leaving the demo worker and recovery loop.

## 2026-10-03 — Retire legacy runtime entry points, preserve regression data

The local server now mounts only authentication/account controls and the retrieval-demo API. Celery discovers only demo tasks; legacy v1/v2 beat schedules and the v1 provider-registration hook are removed. Historical API tests use an explicit research URL configuration. Historical models, migrations, evidence and account-erasure graph remain because removing their tables would destroy protected facts or private-data erasure coverage. Error handling, source tokenization/BM25, highlighting, quantity checks and BGE artifact qualification now live outside the legacy runtime modules. Removed the old adviser frontend, obsolete evidence route and three unused frontend dependencies. No protected model files were touched. Validation: 532 backend tests passed; frontend lint, typecheck and production build passed.

## 2026-10-03 — Release database connections during queued AI work

Parent card jobs and live question heartbeats/progress updates were holding connections while nested jobs waited for the shared relay. Release those connections before waiting; retain transaction ownership when inside an atomic block. Add question/index scope to relay metrics so application latency reports exclude unrelated live work. The full suite above covers these changes.

## 2026-10-03 — Resume partial cards without blocking other insurers

A PageIndex selector can return an out-of-map section ID. Keep the strict scope check, record the field-group failure, and leave unsupported fields not stated. Persist completed card groups and continue other plan jobs; transport/quota failures remain pending and resumable. No alternative retrieval method is used. This changes only post-bake-off card processing, not frozen scores.

## 2026-10-03 — Typed cards and tax-label safeguards

Compile additional exact, validated adult/child entry-age clauses, an explicit floater-composition clause and decimal lakh sum-insured lists. Complex conditional rules remain unresolved; no renewal age is used as an entry age. Existing unpinned cards can reproject accepted clauses without new AI calls. Premium labels now require printed annual and tax-exclusion evidence, as well as all row/column axes. Unqualified gross-premium figures are not shown. Background card calls may wait up to 30 minutes under the same shared limiter; live deadlines remain bounded. This is operational/card work after the bake-off; frozen extractive answer checks and results are unchanged.

## 2026-10-03 — Preserve data while retiring HNSW and legacy helpers

Migration 0020 is guarded to coverguide_star_slice and test_coverguide_star_slice and removes only the two legacy HNSW indexes. Historical source/fact/customer tables remain intact for regression and erasure. Moved legacy relay/provider helpers and recommendation implementation into the research workspace; the live demo uses its dedicated two-model shared relay. Moved the necessary auth schema hook to accounts and removed the obsolete conversation schema path. No shared embedding artifacts were removed.

## 2026-10-03 — Complete-bundle handoff and broader acquisition

Recovered plans can now proceed to tables, exact vectors and cards as soon as all their document maps finish (including recorded fallbacks), without waiting for the slowest insurer. Accepted maps are reused, not rebuilt. A separate resumable global acquisition queue downloaded the eligible official register links; fetched files remain unreviewed and cannot alter the frozen evaluation or enter executable app evidence without edition admission. Raw PDF text is shared by hash while per-bundle document identity is rebound on reads.

## 2026-10-03 — Measured application timing, initial release

Initial H-only release 0ca1cbae-e717-4842-bed0-17584067e371 contains seven available plans plus five unavailable placeholders. Three-plan p50/p95: 50,397/72,460 ms (n=3). Five-plan p50/p95: 75,169/93,859 ms (n=3). All include queue time during background work. Scoped relay calls: 63; queue p50/p95 618/2,647 ms. Peak relay concurrency observed since start: six. These small-sample observations do not establish a speed improvement. The cross-process cap test now uses an explicit start barrier and waits for six admissions instead of assuming cold-start processes overlap within 180 ms.

## 2026-10-03 — Browser stream and physical table reuse

The browser's EventSource sends Accept: text/event-stream. DRF rejected that header before reaching the stream generator; add an explicit event renderer and retain JSON error rendering. A regression test and a real three-plan browser question now verify streamed completion. A citation click displayed physical PDF page 8 with the exact PED clause highlighted (printed page 7), preserving the physical/printed distinction.

Cache physical table grids once per PDF hash/page/extractor version under a process lock, then bind cells separately to each variant's immutable source sections. This avoids repeating PDF table extraction for shared Niva variant documents. Identity mismatches fail visibly. The typed-needs prompt now requests complete original phrases, including person references; the existing guard still exposes any omitted input as unmapped. Focused checks: 20 tests passed and Ruff passed. Frozen bake-off sources/results remain unchanged.

## 2026-10-03 — Incomplete embedding imports cannot publish

The resident embedding process disconnected during the recovered ICICI import. Its cause was not established; no alternative embedding model was used. Restarted the single task-owned worker and resumed saved section vectors. Publication now verifies every section ID and original-text hash against the complete vector index. The stack waits for the resident model's health endpoint during cold startup. A database regression test covers missing and changed vectors. Price screens omit empty chart controls when no validated combination exists. Full backend run before this added guard: 540 passing tests; guard/services run: 10 passed. Frontend lint, typecheck and build passed.

The official Tata active/withdrawn register records 15 current individual-health entries and 13 withdrawn entries under the parsed individual-health UINs. These are preserved in the register audit, with physical pages and exact row text. Home Guard Plus still needs composite-scope review; this is not a count of admitted variants and does not admit new evidence.

## 2026-10-03 — Archive obsolete review, retrieval and provider commands

Moved the previous v2 processing/review pipeline, FTS/dense/raw/PageIndex retrieval modes, embedding wiring, prepared-fact answer engine and model gateway into `research_workspace/legacy_v2`. Moved 15 old management commands into a research-only command app. Their regression tests use the new imports and research settings; the normal app exposes none of the retired processing/provider qualification commands. Optional Docling and ONNX-building dependencies now belong to the research dependency group. No installed packages or shared model files were deleted.

Post-move verification: 541 tests passed; Django checks and migration checks passed. The isolated application database still contains 39 stored facts, 22 rules and 1,585 evidence spans. The 236-span frozen reference snapshot and protocol-v2 scored source archive were not modified. Authentication, account erasure and historical model/migration compatibility remain in the application.

## 2026-10-03 — Shared vectors and atomic fit-list catalogue updates

Variant indexes now reuse embeddings by exact title-path-plus-source-text hash, independent of plan-specific section IDs, and save new vectors to the shared artifact cache. A two-variant database test verifies one embedding execution with separately bound section identities. The dedicated vector table and cache use the same pinned BGE-M3 artifact.

Fit responses now return the cards and release ID used for that evaluation. The browser updates the catalogue and fit groups together, so a release published while the page is open cannot leave new matching rows hidden behind stale cards. Running questions retain their existing immutable index pins. Focused checks: 12 service/API tests passed; frontend lint, typecheck and build passed.

A further Playwright retry of Star's official product register returned HTTP 403 Access Denied. Preserve that failure and the earlier register snapshot as historical evidence; do not promote its old entries to a verified complete current catalogue.

## 2026-10-03 — Recovered release and four-profile browser verification

Published H-only release `7ec7f75e-8af4-4479-bc62-180ac8fb034f`: 16 variants across 12 products and ten insurers, backed by 53 physical PDFs and 1,795 physical pages. Eight distinct documents use recorded fallback sections (two in the frozen corpus, six in the app-only recoveries). The frozen inputs, protocol text and nine archived scored source files retain their original hashes. No recovered document entered the frozen evaluation.

Playwright exercised all four synthetic profiles on this release: A/C/D show 16 unresolved plans; B shows 15 unresolved and one age-limit failure. All groups remain visible and ordered by insurer, with no ranking. The complete typed phrase “my parent needs OPD cover” mapped once to the parent and OPD, without losing words. A five-plan selection from the full picker successfully streamed cited PED answers for all five recovered flagships. Native citations were visually checked against their highlighted PDF clauses. Desktop columns now fit all five plans at 1,440 pixels; mobile keeps horizontal scrolling. Variant labels distinguish repeated product names in coverage and prices.

The first premium pass found zero fully validated prices: six invalid-chart variants and ten variants without an applicable available price source. The chart-layout audit below supersedes that first-pass count. The broader current retail catalogue and complete executable fact cards remain unfinished; acquired candidate files are not automatically admitted.


## 2026-10-03 — Printed annual chart layout and source-linked prices

The first parser required a separate cell for every fixed axis, including a literal variant label even for an edition without named variants. That rejected Star Comprehensive's published rates. Visually inspected physical page 44 of prospectus SHA `0404693147bd5202e28e39bfdb8fcc87f78e7ee6aa6a6f1032f63cbec63698e1`: annual term, excluded tax and zone share a merged title; family composition spans ten age rows. Added an adapter restricted to that exact prospectus hash. Luna labels the physical layout; code checks its coordinates, complete source rows, composition span and every printed axis. The parser preserves source anomalies and performs no premium arithmetic.

Ten layout calls and eight bounded title-row corrections, all Luna, produced 3,564 exact printed combinations. Four rows (36 combinations) cross original evidence-section boundaries and remain omitted with reasons. Other price statuses: five charts not validated, ten without an applicable available source. The UI is an explicit manual chart lookup, separate from the family profile; it does not infer the insurer's age or zone rules. Price citations use the same physical-page highlight viewer and reject evidence outside accepted chart cells. This is still not an insurer quotation.

## 2026-10-03 — Completed winning application acceptance

The complete fresh H-only application run finished all 86 jobs: 260 answer-sheet cases plus 78 Star reference queries. Outcomes: 140 answered, 120 not found; table-heavy cases 23 answered and 42 not found. Twelve of 39 Star cells contain every required reference span in both the fixed and customer-style packets. This measures packet completeness, not expert-verified answer correctness. The recovered flagships are included only in this application run; frozen bake-off hashes, unavailable denominator slots and scores are unchanged.

All four synthetic profile UI runs, five-plan streaming, desktop/mobile scrolling and native citation highlights were exercised. Final backend checks: 547 tests passed (21 warnings), Ruff, Django checks, migration checks and validated OpenAPI generation passed. Frontend lint, typecheck and production build passed. Historical facts/rules/evidence, erasure and immutable release pins remain intact. No push or off-machine publication occurred.

## Section 16 C — fixed Stage 1 and Stage 2 questions

User clarification: Stage 1 and Stage 2 questions use fixed one-field/decision templates with no AI phrasing call. Luna interprets customer replies and phrases only Stage 3 narrowing questions, within the structured question-intent contract and deterministic fallback. Profiles A–D must report elapsed time for every committed turn as well as total questions and the final stop condition.

## Section 16 A — source assembly v2

Use P/T/C packet-local draft labels and S navigation labels; model output cannot set plan/document/page identity. H's BM25/BGE-M3 reciprocal-rank fusion is unchanged. Reserve 4,000 of the 16,000 evidence tokens for deterministic same-edition governing-context completion, including serialized omission metadata. Publish separate original excerpts under fixed headings. Validate benefits and their attached conditions as units; retain accepted units if the one content correction fails. Schema repair remains inside the relay, independently of content correction and transport retries. Unknown labels/copying errors, context failures and operational/model failures are recorded separately. Focused validation: 45 tests passed before the last packet-reserve adjustment; artifact/cross-page/partial-retention tests pass after context fixes. No frozen protocol sources/results were modified.

### Section 16 A — diagnostic run invalidated after PDF spot-check

Run `section16-a-20261003-01` was stopped and its synthetic pending questions cancelled after a physical-PDF check showed a following “With regard…” stent restriction was omitted from an ICU/list excerpt. Preserve its files as diagnostics, not acceptance. Context completion now retains subsequent normative sentences up to a numbered heading; regression coverage includes this observed failure. An FHO prospectus anchor also failed exact PDF geometry resolution; original offsets remain intact and the highlight failure is reported explicitly.

### Section 16 A — printed boundaries and retained-evidence validation

Run `section16-a-20261003-02` is diagnostic and incomplete. Agent PDF checks found overbroad excerpts crossing wrapped numbered headings and unrelated illustrations. Recognize source title-case/numbered headings including PDF control/newline artifacts, preserve explicit letter-to-letter discretionary line-wrap hyphens with original offsets, and revalidate all retained units before admitting additional context (table metadata must not disappear under the budget). Tests cover the observed heading boundary, failed corrections, operational versus evidence outcomes, local table labels and context overflow. All nine frozen scored-source hashes still match.

### Section 16 A — remove repeated prefix scans before full acceptance

Diagnostic run `section16-a-20261003-03` was interrupted after profiling showed 26.8 seconds in repeated regular-expression scans during a six-unit local replay. Replace the terminal enumeration check with an equivalent bounded backward scan, cache immutable document boundaries, and reuse each packet's reconstructed source documents. A 5,009-example equivalence test covers Unicode word/digit boundaries and long numeric tokens. No diagnostic run results are reused in the fresh acceptance run. This isolated profiling result is not a claim about application latency.

## Section 16 — parallel execution and smoke gate clarification

User steering: leave the current full run running; build C's independent conversation modules/contracts/templates/tests alongside it without changing its execution paths. Profile local validation, use cached normalized source/offset indexes, and record per-answer before/after validation time. Before any further full run, execute and agent-spot-check a 25-case sample spanning tables, Star and several insurers; aim for one further full run only. Generate the flagship/Star card set before remaining variants; background AI work continues under the same relay cap and live priority. Stage 1/2 phrasing remains fixed and call-free. No new user checkpoint is required between parts.


## Section 16 A — fresh application run section16-a-20261003-04

Baseline: 140/260 answered; 23/65 table-heavy answered; 12/39 complete Star packets.

Fresh measured results: `{"answer_cases": 260, "complete_reference_cells": 12, "final_not_found_reasons": {"all_units_rejected": 52, "no_substantive_evidence": 13}, "manifest": "/home/akhilesh/.local/state/coverguide-star-slice/reports/ten-insurer/application-acceptance/section16-a-20261003-04/manifest.json", "method": "H", "note": "Fresh application-service execution, not a rerun or adjustment of the frozen bake-off score.", "outcomes": {"full_answer": 177, "not_found": 65, "partial_answer": 18}, "reference_cells": 39, "rejection_reasons_overlapping": {"copying_error": 159, "incomplete_context_or_validation": 25}, "release_id": "7ec7f75e-8af4-4479-bc62-180ac8fb034f", "run_id": "section16-a-20261003-04", "table_heavy": {"full_answer": 40, "not_found": 21, "partial_answer": 4}}`.
Outcomes are mutually exclusive; rejection reasons overlap. Packet coverage is not displayed evidence or expert verification.


### Section 16 local validation cache measurement

{"run_id": "section16-a-20261003-04", "measurement": "Local six-check validation replay; cold cache per answer; no model or queue time", "samples": 264, "identical_results": true, "uncached_ms": {"p50": 19.0875, "p95": 57.991, "total": 6313.93}, "cached_ms": {"p50": 13.538, "p95": 47.041, "total": 4554.386}}

Cached exact normalized text and immutable offset maps preserve every validation result. These are local validation timings, not end-to-end answer latency.

### Section 16 B — independent reference-card split

Claude is independently preparing reference cards for seven plans. Do not read or wait for `/home/akhilesh/Projects/health-insurance-agent/output/reference-cards/`; do not manually accuracy-spot-check implementation fact cards. Continue A → B → C → D. Export each implementation card to `output/section16-cards/<plan_id>.json`, including immutable version/index, field values, typed rules, original quotes with document and physical page identities, and stated / not covered / not stated status. Existing Part A answer/PDF checks are separate from this reference-card comparison.


### Section 16 smoke gate — 25 fresh cases

`section16-smoke25-20261003-01`: 18 full, 2 partial, 5 not found; zero operational failures. Covers the three Star plans and all ten insurers, including 13 table-heavy cases. Agent inspected ten rendered answer-source pages and resolved every stored anchor in those ten cases. Room limits/variant axes, optional co-pay, OPD's specific-condition scope and PED buy-back conditions remain quoted. No copying, number/axis or missing-highlight defect was found in this sample; source excerpts can still be verbose and include neighboring clauses. This is a bounded agent smoke check, not expert verification or proof of complete semantic coverage. Proceed with one final full application run on the same answer paths; no bake-off rerun.

### Section 16 B — independent comparison requires replacement cards

User findings invalidate the initial field-status/projection approach: optional maternity/OPD cover was counted as stated base evidence; preventive vouchers were conflated with OPD; PED queries missed baseline waits; full-section quotation completion impeded bounded projections. Treat the first card batch as superseded diagnostics, preserve its immutable versions, and generate new versions. Keep optional add-ons/riders separate as optional, extra premium; they cannot satisfy requirements. Revise field queries across every plan, constrain quotation assembly to governing clauses, and confirm typed numbers/keywords against exact original spans. Re-export per-plan/per-field quoted and executable coverage. Do not read the independent reference-card directory.

The HDFC and Bajaj PED omissions in run `section16-a-20261003-04` both ended as `all_units_rejected`: the initial draft and single correction each failed exact quotation copying. Part B then reused those absence results instead of asking a targeted fact-field query. The replacement pipeline does not reuse those field outcomes: it asks for Standard Exclusions / Code Excl01 and distinguishes baseline waits from optional reductions. All 28 fields are regenerated across existing variants, with the flagship/Star priority batch first. Independent reference-card contents remain unread.


## Section 16 A — fresh application run section16-a-20261003-final

Baseline: 140/260 answered; 23/65 table-heavy answered; 12/39 complete Star packets.

Fresh measured results: `{"answer_cases": 260, "complete_reference_cells": 13, "final_not_found_reasons": {"all_units_rejected": 55, "no_substantive_evidence": 11}, "manifest": "/home/akhilesh/.local/state/coverguide-star-slice/reports/ten-insurer/application-acceptance/section16-a-20261003-final/manifest.json", "method": "H", "note": "Fresh application-service execution, not a rerun or adjustment of the frozen bake-off score.", "outcomes": {"full_answer": 175, "not_found": 66, "partial_answer": 14, "temporarily_unavailable": 5}, "reference_cells": 39, "rejection_reasons_overlapping": {"copying_error": 162, "incomplete_context_or_validation": 28}, "release_id": "7ec7f75e-8af4-4479-bc62-180ac8fb034f", "run_id": "section16-a-20261003-final", "table_heavy": {"full_answer": 38, "not_found": 23, "partial_answer": 4}}`.
Outcomes are mutually exclusive; rejection reasons overlap. Packet coverage is not displayed evidence or expert verification.

### Section 16 final answer spot-check and PDF geometry

Ten final-run answers were agent-checked against rendered PDFs (five table-heavy, five other/repeated evaluation slots). One native-character highlight failed because the source used U+2010 while the PDF glyph extractor returned an ASCII hyphen. Add that explicit geometry-only mapping; exact quotation acceptance remains unchanged, and minus signs/punctuation are not dropped. All selected anchors now resolve. The spot-check still finds verbose neighboring clauses and three cataract answers that establish waiting conditions rather than a monetary limit. “Full” means all proposed units passed; it is not proof of exhaustive semantic coverage. Details are in `section16-pdf-spot-checks.md`; Part B cards were not manually spot-checked.

### Section 16 B — base-query and typed-projection corrections

The broad baseline-wait query still selected optional reductions/rider waits in the first replacement batch. A focused H query for the base-policy Excl01 sentence recovered HDFC and Bajaj's 36-month clauses. Short sum-insured queries and separate optional-benefit queries are a further bounded refinement; they use the existing H indexes, maps and embeddings. No document-specific field cells are patched.

Projection corrections recognize the printed maternity Excl18 heading as an exclusion (the word “expenses” alone is never positive coverage); preserve original rider scope before trimming; do not turn neighboring entry ages into renewal rules; consolidate equivalent numeric rules while retaining both quotations; and retain unsupported conditions as unresolved. Lifetime renewal and explicit numeric values pass a closed bounded schema. Optional covers remain separately cited, marked “optional, extra premium”, and cannot satisfy a base requirement. Provisional v4/v5 exports are archived when replaced; only the final manifest defines the comparison-ready export. No manual Part B accuracy review or independent-reference-directory read occurred.

Full backend check at this point: 622 passed, 21 warnings; later projection tests are rerun separately and the final suite will cover the final tree. Django/migration/OpenAPI checks and frontend lint/typecheck/build passed.

### Section 16 independent comparison — rule scope gate before profile acceptance

The user independently expanded the reference check to all 16 variants. The independent directory remains unread; no task is handed off. Export `section16-b-20261003-ready` and profile run `section16-20261003-final` are diagnostic, not accepted: adult and child bounds could be combined, benefit illustrations could incorrectly restrict coverage basis, neighboring PED durations could leak into specified waiting, and partial lists lacked a reliable completeness proof. The user also identified variant-specific OPD and a differently numbered maternity exclusion.

Implement clause/person/field/variant grounding as a mandatory code gate, not a prompt preference. Every projected number, unit and category must be found in the rule's own citations. Unproved lists and basis choices are non-exhaustive and cannot exclude an unlisted choice. Shared benefits require the selected variant's actual table cell or an explicit all-variants clause. Maternity exclusion recognition is independent of the numeric Excl identifier. Keep rejected projections unresolved.

Run `section16-b-20261003-field-recheck` in the background using fresh targeted H queries across all existing variants: force entry age, coverage basis, entire SI lists, specified waits, room entitlement, base/variant OPD and maternity; retry other missing or non-executable fields including PED, renewal, family, product type, restoration, NCB and deductible. Existing maps/embeddings/indexes are reused. Revised deterministic projection code is isolated from this manifest-pinned AI job. Re-export and rerun A–D only after its replacement card versions pass the rule gates.


### Profile comparison contract and independent rehearsal material

Keep the A–D definitions in `run_guided_profiles.py` unchanged: the people, ages, Pune location, needs and must-have/nice-to-have choices remain identical. Every turn, including initial state, now records full groups with policy-version ID, variant, immutable card version and all checks/citations; `deciding_checks` identifies the exclusions or unresolved checks responsible for that group's status. Save measured per-turn elapsed time, counts, question count and stop condition. Independent A–D keys and rehearsal material remain unread in the forbidden reference-card directory. The walkthrough's “Rehearsed questions” section is a placeholder for the user's separately supplied questions.

### Corrected comparison export and local release

Run `section16-b-20261003-grounded` exports all 16 immutable cards and activates local release `91ac5c9b-0f78-4df7-960a-0d53c760b044`, reusing every existing index/map/embedding. Requested 17-field coverage: **177/272 quoted, 88/272 executable**; all 28 retained fields: **274/448 quoted, 89/448 executable**. “Executable field” means a supported bounded rule exists for its stated applicability, not complete eligibility for every person/profile. Unknown fields and unsupported conditions remain unresolved.

HDFC adult entry now preserves 18 years/no maximum, room entitlement is At Actuals, specified waiting is 24 months, and SI choices are from the selected full grid cell. Tata SI retains all extracted options through 3 crore; an unproved list end is non-exhaustive and cannot exclude. Tata adult/child minimum and maximum table rows are paired by their labels. Star Comprehensive's operative individual/floater headers establish both bases; benefit illustrations are rejected even without their title. Family Health Optima's Excl17 maternity clause is not covered. ManipalCigna Protect OPD is not covered: deterministic continuation resolves the exact Protect header on the preceding physical page by matching table/column geometry, with separate page anchors and all six checks.

Every trimmed source unit is revalidated before projection. Numeric values and categorical keywords must be grounded in their own rule evidence; rejected rules cannot fall back to legacy card exclusions. Tests cover incomplete lists, contradictory choices, wrong columns, cross-page headers, adult/child axes, unrelated waiting values, and quotation trimming. Background query manifests retained all pinned source hashes; all nine frozen bake-off source hashes still match. No Part B manual accuracy spot-check or reference-directory read occurred.

The earlier A–D run is diagnostic only. Start replacement run `section16-20261003-grounded` using unchanged profile definitions and the new immutable release; include complete per-turn memberships/reasons and timings.

### Live conversation correction before A–D acceptance

Run `section16-20261003-grounded` is diagnostic: the interpreter duplicated the Stage 1 “hospital expenses” cover-type answer as a requirement, which incorrectly bypassed the intended Stage 2 needs prompt. It also sometimes used `maternity coverage` instead of the fixed registry key. Supply the registry in the interpretation contract, normalize a bounded set of aliases, keep type/basis answers out of extra requirements, and accept “no preference” only from explicit customer wording. Regression checks reproduce both faults.

A–D definitions remain unchanged. The runner now guarantees that each definition's original needs sentence is actually submitted through chat, even if a volunteered earlier preference already passed the open-ended prompt; it never patches the profile directly. Record intended-strength validation alongside the full per-turn trace. Replacement run: `section16-20261003-verified`. No independent answer key or rehearsal question bank was read.

### Section 16 final conversation validation — 2026-10-03

- Stage 1 and Stage 2 questions remain fixed one-question templates, without AI phrasing calls. Luna interprets replies and may phrase the code-selected Stage 3 question. The live interpreter is supplied the fixed needs registry. Hospital-expense/type answers no longer become extra requirements or skip the needs stage.
- Requirement strength is confirmed against the customer's actual words. Model-authored `original_text` cannot invent a must-have; a field merely “mattering” requires the fixed strength follow-up. A policy question still creates no requirement. The A–D definitions (people, ages, Pune, needs and strengths) are unchanged.
- Every profile turn retains all 16 policy-version IDs and variants, card versions, group memberships, all checks and deciding checks. Counts are only a summary. A final fresh delivery run follows the consent gate change; earlier diagnostic runs are not acceptance results.
- Independent reference cards, profile answer key and rehearsal bank were neither read nor awaited. No manual Part B card accuracy spot-checks were performed. `demo-script.md` contains only a short Rehearsed questions placeholder for the separately supplied material.
- Browser inspection found a long immutable card hash overflowing on mobile. Card text now wraps within its container; frontend lint, typecheck and build were rerun.

### Section 16 delivery measurements — 2026-10-03

Final profile run `section16-20261003-delivery` uses release `91ac5c9b-0f78-4df7-960a-0d53c760b044`. Every profile reached details, requirements and narrowing; all original needs and strengths were confirmed. A: 0 fits/4 uncertain/12 non-fits, 10 questions, 40.989 s. B: 0/12/4, 9 questions, 46.820 s. C: 0/4/12, 7 questions, 37.679 s. D: 0/11/5, 9 questions, 47.611 s. All stopped at no supported narrowing question; missing applicable evidence prevented confirmed fits. Per-turn times and complete plan/check memberships are retained in the delivery JSON and profile report.

Final requested-card coverage: 177/272 quoted, 88/272 executable. All retained fields: 274/448 quoted, 89/448 executable. All 16 immutable cards were re-exported with per-field statuses, own-source quotations and typed rules. No reference cards or profile answer key were read.

The final 78 Star probes distinguish 13/39 complete packet pairs from only 3/39 pairs displaying every required reference span in both query styles (43 probes display at least one reference span; eight display every required span). This does not change the already recorded 175 full/14 partial/66 not-found/5 operational outcomes. Validation success is not exhaustive semantic answer coverage.

Measured three-plan p50/p95: 27.378/34.052 s (n=3); five-plan: 69.303/69.646 s (n=3). Queue p50/p95: 2.692/23.486 s (59 calls), throughput 12.84 successful calls/min, global peak six. All measured models were Luna. Shared weekly-limit switching to Sonnet and cross-process capacity/live priority passed isolated tests; no actual weekly-limit event occurred.

Final full pytest: 653 passed, 21 warnings, 56.24 s. Ruff, Django checks, migration drift, OpenAPI validation, frontend lint/typecheck/build passed. Local stack restarted and healthy; shared relay unchanged. Desktop/mobile screenshots include chat, live list, comparison, citations, exact-axis printed price and coverage. Stop acknowledges without a further question. Free disk approximately 13 GB. Implementation commit `2fd73b1`; no push or external publication. Remaining gaps are explicit in the delivery report.

The independent answer correctness check is external to this work. The final A run `section16-a-20261003-final` and `application-answer-sheet.md` are frozen for that comparison. Future answer runs, if necessary, require new IDs. The delivery report has an unfilled Independent answer correctness placeholder under limitations; code checks are not expert verification.

### Final-run step 1 — profile-fit corrections (2026-10-03)

Keep this step separate from the answer-scope/not-found changes. Profile A–D definitions remain byte-for-byte unchanged; expected counts are not acceptance targets. Targeted H card queries use existing pinned indexes and original passages only. No independent reference directory was read and no manual Part B accuracy spot-check was performed.

Purchase geography requires an explicit residence/sales clause or a complete nationwide premium-zone scheme, never treatment territory alone. Coverage basis reads its own typed field. Base maternity can satisfy the general need with its printed waiting periods displayed. General outpatient exclusions retain the governing non-payment introduction, including optional-cover exceptions. Selected shared-table room cells must prove the named variant; optional room modifiers and co-pay menus do not supply base rules. Co-pay penalties for room breaches or late notification remain quoted but cannot execute as unconditional percentages. Sum-insured examples and booster amounts remain ineligible; listed values and Unlimited remain separate.

Bounded age parsing distinguishes adult/child entry rows, lifetime entry from renewal, proposer ages from insured ages, and entry maximum from exit age. Quoted field blocks are clipped at their own headings before projection, so an adjacent rider footnote cannot turn a base eligibility block into a rider. Conditions and citations are retained when equivalent rules are deduplicated. Multiple consistent coverage clauses preserve their waiting periods; contrary clauses remain unresolved. Card-only literal recovery may complete a retrieved heading in the same document edition, counts all context and omission metadata within 16,000 tokens, and retains all six checks. H ranking and frozen answer runs are unchanged.

A new regression initially exposed an exit-age row interfering with a child's entry maximum. It was fixed by bounding the explicit entry table at Exit Age. Additional tests cover parenthetical child definitions, optional table rows, nationwide zone completeness, conditional co-pay penalties, base exclusions with optional exceptions, and literal recovery isolation from navigation summaries. Executable coverage counts fields with any bounded supported rule; this does not promise complete eligibility for every profile. Remaining source/relationship ambiguity stays can't-tell.

Step 1 verification before export: full backend suite **677 passed**, 21 existing missing-static-directory warnings, 55.80 s; focused evidence/rule checks passed. All pinned AI card-generation module hashes match their manifests. The profile-clause runner was formatted after its batch completed (completion 23:31:33 IST; formatting 23:33:25 IST), with no query or algorithm change. A repository-wide Ruff pass also found style issues in two old task-created profiling scripts under output; those are recorded for the final verification step. Changed application modules pass Ruff. Frozen answer-sheet/acceptance checksums still match. Profile-definition runner SHA256: `856847d85d991fd47b229765b0fb4651451a1f828489137b6569affa46c16313`.

Step 1 final rule review also found a primary-insured/spouse-only family footnote. It is now an explicit typed constraint. Two people labelled as the customer's parents are not automatically assumed to be the primary insured and that person's spouse; that pairing remains unresolved rather than excluded. The unchanged A–D definitions do not need alteration. Repeated retained wrappers around the same original answer/packet are deduplicated before revalidation; no evidence check is removed. The final projection manifest also pins its command source.

Step 1 export completed at **2026-10-03 23:54:53.782750 +05:30** (18:24:53 UTC). Card run `section16-b-20261003-profile-fit-release` contains 16 immutable versions; local release `921e3721-d584-4a59-a7e5-132eb25076a2` reuses all indexes, maps and embeddings. Requested fields: **186/272 quoted; 139/272 executable**. All retained fields: **295/448 quoted; 152/448 executable**. Per-plan and per-field Q/E values are in `section16-card-coverage.md`; JSON exports are in `section16-cards/`. Automated regression assertions cover the reported maternity/waiting, HDFC/ICICI base OPD, Niva sum-insured/menu/Elite-room and ICICI room-conflict faults. These are code checks, not manual or expert accuracy verification. All card-generation model identities are `gpt-5.6-luna`.

New unchanged A–D conversation run: `section16-20261003-profile-fit-final`, pinned to this release. The answer-scope/not-found implementation has not started.

Step 1 A–D replay completed. Run `section16-20261003-profile-fit-final`; release `921e3721-d584-4a59-a7e5-132eb25076a2`. All four journeys reached details, requirements and narrowing, delivered their unchanged needs, and classified strengths as specified. Every turn contains all 16 policy-version IDs/variants and deciding checks.
A: 2 fits / 2 can't tell / 12 non-fits; 10 questions; 48.444 s; stop `no_supported_question`.
B: 8 fits / 3 can't tell / 5 non-fits; 11 questions; 49.371 s; stop `no_supported_question`.
C: 2 fits / 2 can't tell / 12 non-fits; 7 questions; 40.824 s; stop `no_supported_question`.
D: 0 fits / 6 can't tell / 10 non-fits; 9 questions; 47.649 s; stop `no_supported_question`.
Remaining uncertainty is retained rather than tuned to expected counts. A/C retain unresolved family evidence for Star Comprehensive and adult/maternity evidence for Activ One; B retains unresolved Activ One entry ages, ICICI selectable sum insured, and ManipalCigna family/sum-insured/basis evidence. D now excludes HDFC Optima Secure and ICICI Elevate using their base outpatient exclusions. This completes step 1 before answer changes begin. Full per-turn timings and memberships are in the new profile JSON and `section16-profile-report.md`.

### Final-run step 2 — scoped answers and bounded not-found recovery (2026-10-04)

The independent grading identified variant/product/add-on leakage and premature not-found as systemic failures. The new draft contract is `scoped-packet-labels/3`: every unit declares base versus `optional, extra premium`, with original-source scope checked in code. Packet scope derives only from original document headings, product declarations and named table axes; generated navigation summaries remain excluded. Foreign product/variant units fail, shared benefit wording requires selected-variant applicability, and benefit illustrations cannot supply that proof. The UI labels optional excerpts without altering quotations. Field-topic checks distinguish PED from specified waits and deductibles from co-pay. Every accepted unit still passes all six original evidence checks.

A final not-found now requires a second H query using alternative printed terms and customer-information/benefit-schedule context. The second packet preserves H ordering and the first packet's independent evidence, with omissions counted inside 16,000 tokens. There is still only one content correction across both packets; JSON repair and transport retries are separate. Passing units survive correction failures. Operational failures remain temporarily unavailable. Original answer runs and the old application-answer-sheet.md remain untouched; new summaries and sheets include the run ID in their filenames.

Pre-smoke verification: full backend **689 passed**, 21 existing static-directory warnings, 55.28 s; two additional focused shared-table/illustration regressions subsequently passed (13 scope tests). Backend Ruff and frontend typecheck passed after fixing one test import order. No new acceptance claim has been made yet. Scope and retry changes are committed separately from profile/card changes before the fresh 25-case smoke sample.

The first scoped smoke (`section16-a-20261004-scope-smoke`) was **not clean**: 8 full, 3 partial, 13 not-found and 1 operational failure. Inspection found false optional classifications caused by ordinary add-on/payment sentences being treated as parent headings, plus a product name that includes its variant being compared against a product-only declaration. No full run was started. Parent scope now requires a genuine optional/rider heading and ends at peer headings; table headers and FAQs cannot govern later base benefits. Product ownership is compared independently of the selected variant. Mixed passages are explicitly marked mixed in the prompt instead of labelling the whole passage optional.

Answer assembly now uses the already tested governing-heading/boilerplate boundaries, retaining separate original spans and page anchors. An invisible PDF BEL layout marker is treated like a layout artifact during matching, with original offsets and displayed wording preserved; punctuation, digits and negation remain exact. The draft prompt asks for short literal anchors and separate heading quotes instead of invented heading/body punctuation. Forty-six affected tests pass, including foreign-product/variant rejection and the new false-optional regressions. A new smoke ID is required because the source manifest changed; old smoke results remain preserved.

Second smoke `section16-a-20261004-scope-smoke2`: **13 full + 4 partial = 17 answered; 8 not-found; 0 operational failures**. It did not yet pass the smoke gate: a definition-only room-rent response is not a limit answer, and shared-table scope proof was often absent because prose filled the packet first. Code now rejects definition-only responses to benefit/limit questions (while permitting an explicitly requested definition). Deterministic packet completion reserves space for queried table rows and the selected variant's original axes, excludes neighbouring variant values, marks the projection non-exhaustive, and retains source-page context. It never manufactures missing/merged headers. H's retrieval ranking is unchanged. Original bullet-style CIS headings also end the preceding unrelated list. Forty-nine affected tests pass; the next smoke uses another fresh manifest.

Third smoke `section16-a-20261004-scope-smoke3`: **13 full + 6 partial = 19 answered; 4 not-found; 2 temporarily unavailable**. Both operational outcomes came from the second-packet union's preserved omission metadata exceeding the evidence budget. The union now repacks with a smaller source allowance until content plus the full omission audit fits; it does not silently discard omissions or weaken checks. Fifty-one affected tests pass.

Ten rendered-PDF agent spot-checks (not expert verification) are preserved under `output/section16-pdf-checks/scope-smoke3/`: Star Comprehensive room p10, Family Health Optima room p9 plus continuation, Star Assure room p11, Care Supreme room p26, ICICI Elevate optional room modifier p57, Star Comprehensive co-pay p13, Family Health Optima voluntary co-pay p28, Star Assure co-pay p13, Star Comprehensive PED p31, Family Health Optima PED p8. All 37 checked anchors resolve to PDF geometry. The source pages support the displayed room categories, room/SI axes, co-pay ages/percentages and PED periods; some excerpts still include neighbouring source material. ICICI's room modifier is optional, not its base room limit. The FHO voluntary co-pay page explicitly offers a premium discount: code now labels such a cited optional choice `optional premium adjustment`, while optional additional cover retains `optional, extra premium`. This avoids asserting an extra charge against a printed discount. Optional-only responses are partial because the base term has not been established. Definition-only and heading-only selections cannot count as benefits. The full run remains gated on the next smoke.

Fourth smoke `section16-a-20261004-scope-smoke4`: **13 full + 3 partial = 16 answered; 9 not-found; 0 operational failures**. Ten rendered pages and all 48 anchors were checked by the agent (not expert verification), preserved in `output/section16-pdf-checks/scope-smoke4/`. This exposed a structural issue: ICICI's base room clause and its pro-rata restriction were emitted as separate units. Before any unit is accepted, conditional-only selections are now attached to all same-field, same-scope benefits in that draft and validated together. An unmatched standalone condition is rejected. A regression proves a failed governing condition drops its benefit while retaining an independent passing OPD unit. Product-owner checking also remains active when the product and variant names are identical. **54 affected tests passed**. The next smoke is fresh; the full run has still not started. A read-only cohort timing command was exercised against smoke3 and measured peak relay concurrency 6 from recorded intervals.

Fifth smoke `section16-a-20261004-scope-smoke5`: **13 full + 5 partial = 18 answered; 7 not-found; 0 operational failures**. Inspection found a real scope leak: a named room-upgrade package under the original parent heading `Optional Packages (Applicable only if opted)` was still labelled base. The parent-heading recognizer now includes Packages and preserves the explicit opted-only qualifier across pages; it does not rely on a product-specific exception. Three new regressions cover Packages/Covers/Benefits parents with opt-in qualifiers. **57 affected tests pass**. The full run has not been launched; another fresh smoke will verify this root fix.

Sixth smoke `section16-a-20261004-scope-smoke6` completed: **13 full + 6 partial = 19 answered; 6 not-found; 0 temporarily unavailable**. Table-heavy: 4 full + 4 partial / 13. All displayed units pass all six checks; all 49 anchors in ten selected answered cases resolve to PDF geometry. Agent PDF spot-checks found no remaining base/optional mismatch in those checked excerpts; details and limitations are in `section16-pdf-spot-checks-scope.md`. The previously leaking named room-upgrade package no longer appears as base. This is a code/scope/geometry smoke gate, not expert or exhaustive semantic verification. Some partial answers still establish only a related benefit rather than the full requested base term, and rejected quotations/unknown axes remain not-found. The full backend suite now passes **707 tests**, 21 existing static-directory warnings, 53.02 s. The full run will use `section16-a-20261004-scope-final`, with a new answer-sheet filename and the original run/sheet preserved. No further answer code changes will occur during that pinned run.
