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
