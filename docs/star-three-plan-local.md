# Star three-plan local slice

The completed local pilot is on `main` and runs from this repository
(`bash scripts/demo_stack.sh start`, settings in the untracked `.env.star-slice`). Checkpoint 2 approved all 39 cited facts; the subsequent
architecture brief authorized local publication and end-to-end verification without further
checkpoints. Nothing is pushed or published outside this machine. Use synthetic profiles only.

## Isolated runtime

The ignored `.env.star-slice` (0600) explicitly selects these resources:

| Resource | Destination |
|---|---|
| PostgreSQL | `127.0.0.1:55449/coverguide_star_slice` |
| Test database | `test_coverguide_star_slice` |
| Redis | `127.0.0.1:6401/0`, Compose project `coverguide-star-slice` |
| Backend | `127.0.0.1:8021` |
| Frontend | `127.0.0.1:3021`, proxy set by `COVERGUIDE_BACKEND_URL` |
| Data, source text and reports | `~/.local/state/coverguide-star-slice/` |
| Python environment | Worktree-local `.venv-star`, selected by the wrapper |
| Source objects | `../coverguide-star-pilot-data/objects/` (read only) |

The wrapper refuses a different DB, test DB or broker. Shared model files and the loopback
CLIProxyAPI relay on port 8317 are retained. The existing model-route and qualification
identities, timestamps, results and hashes were preserved; no new qualification programme ran.
Terra handles interpretation/review, Sol handles extraction/comparison. The isolated turn
deadline is 900 seconds, allowing sequential calls for all three plans.

Start only missing services; do not start duplicate workers or servers:

```console
bash scripts/star_slice.sh web
bash scripts/star_slice.sh worker
bash scripts/star_slice.sh beat
bash scripts/star_slice.sh frontend
```

Before rebuilding the frontend, load `.env.star-slice` with `set -a; source .env.star-slice;
set +a` so its proxy targets 8021. Then run `npm --prefix frontend run build` and restart only
this slice's frontend. The synthetic login is stored outside Git in the runtime report folder.

## Published facts and sources

Release `3c1737d7-d755-4ec4-8352-028b81c52cc4` is published locally as
`development_alpha_3_product`, with `demo_subset: true` and catalogue count 3.
It was built and published with the existing `build_knowledge_release` (using
`--three-product-demo`) and `publish_knowledge_release` commands; all gates remain enabled.
The existing five-product publication path also retains its gates.

The version-2 captured manifest has 23 document associations: 16 executable documents,
one reference-only Assure expense sheet and six excluded brochure/proposal associations.
SHA-256 and physical page counts are verified before storage. Only a missing local object
permits fetching its listed official URL; a corrupt object does not trigger a network fallback.
Reference/excluded metadata is retained but cannot enter executable or retrieved evidence.
Prospectuses remain applicable. Assure consumables evidence is wording clause 27 (physical
page 20, printed 19) and its own List I (physical page 44); the separate expense sheet is
reference only.

All 39 prepared cells display their approved value, conditions and clause citations. Thirty-six
facts are not executable, and never supply personal eligibility, claim amounts or waiting-period
calculations. Three Comprehensive facts (deductible, portability, geography) support five verified
rule records. Prices remain unavailable and optional covers stay unselected. Citation checks
preserve exact native characters, allowing only whitespace differences, and map back to original
clause offsets and visible PDF rectangles.

## Retrieval for additional questions

`COVERGUIDE_EVIDENCE_RETRIEVAL` defaults to `pageindex`, the measured winner. The alternative
`bm25` remains available without dense-embedding qualification. The original qualified
FTS+dense implementation remains a challenger. Retrieval is scoped to each plan's exact
applicable bundle. The query is the customer's question, without profile JSON; structured
profile context goes separately to the answer model.

`COVERGUIDE_PAGEINDEX_TREE_ROOT` defaults to
`COVERGUIDE_REPORT_ROOT/retrieval-benchmark/pageindex-trees`. The local classic SDK builds
SHA-keyed trees in the separate research environment; the app verifies PDF/raw-text hashes,
SDK revision and physical page bounds before selecting original pages. Generated summaries
are search metadata only. Missing/invalid trees produce visible unknowns, never fabricated
source evidence. Tree selection uses the measured existing Sol route, low reasoning and an
8,192-token output cap; its route qualification is checked. Candidate node selection is not
an insurance-output contract and cannot create a policy fact or rule.

`COVERGUIDE_EVIDENCE_TOKEN_BUDGET` defaults to 16,000 source tokens per plan. Whole pages or
BM25 chunks that cannot fit are counted as omitted; text is never silently shortened. BM25
uses 1,024-token native-text chunks with 128-token overlap. Every source answer passes the
existing qualified extraction and independent-review contracts, exact quote/number/condition
checks and PDF geometry validation. One corrective retry follows validation failure; up to
two transport retries are separate. Unresolved evidence stays unknown with its specific reason.

PageIndex call wall time and input/cached/reasoning/output usage are retained in
`COVERGUIDE_REPORT_ROOT/pageindex-live-calls.jsonl`. Answer calls retain their normal model
attempts and metrics. The benchmark, cached trees and response cache remain in isolated reports.
The reproducible harness is in `research/pilots/star/`; do not rerun it casually because PageIndex
indexing made thousands of relay calls.

## Verification and evidence

Use `bash scripts/star_slice.sh test -q`, `bash scripts/star_slice.sh check`,
`bash scripts/star_slice.sh manage makemigrations --check --dry-run`, and the frontend/API
checks in README. Run Ruff with `.venv-star/bin/ruff check backend scripts research/pilots/star`.

- [Final implementation and live-run report](../output/star-e2e-review.md)
- [All four benchmark arms, failures and call costs](../output/star-retrieval-benchmark.md)
- [Four-profile native citation and source-answer audit](../output/star-e2e-review.json)
- [39-cell browser citation audit](../output/star-ui-citation-audit.json)

The final report records current test counts and screenshots. Earlier extraction checkpoints
and their timing evidence remain in Git history and `output/star-three-plan-review.md`.
