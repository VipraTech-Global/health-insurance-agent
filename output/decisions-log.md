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
