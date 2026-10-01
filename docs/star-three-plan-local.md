# Star three-plan local slice

Use branch `feat/star-three-plan-slice` in the Star worktree. Checkpoint 1 is approved;
Checkpoint 2 must approve the extracted review sheet before any knowledge publication.
This remains a single-user local pilot using synthetic profiles.

The ignored `.env.star-slice` (mode 0600) explicitly selects:

| Resource | Isolated destination |
|---|---|
| PostgreSQL | `127.0.0.1:55449/coverguide_star_slice` |
| Test database | `test_coverguide_star_slice` |
| Redis | `127.0.0.1:6401/0`, Compose project `coverguide-star-slice` |
| Backend | `127.0.0.1:8021` |
| Frontend | `127.0.0.1:3021`, backend set by `COVERGUIDE_BACKEND_URL` |
| Data and processing storage | `~/.local/state/coverguide-star-slice/{data,storage,reports}` |
| Manifests | This worktree's `data/manifests/` |
| Existing source objects | `../coverguide-star-pilot-data/objects/` (read only) |

Python dependencies and the existing qualified Docling/BGE model files are shared read only.
Frontend dependencies were copied into this worktree because Turbopack rejects an external
`node_modules` symlink. Do not run dependency installation against the shared virtualenv.
Fresh encryption/commitment keys and a fresh Django secret are in the ignored environment.
The existing application database, storage, broker and model routes are not modified.

The only copied application records are the two matching model routes and the four latest
current qualifications needed for interpretation, extraction, independent review and comparison.
Their IDs, timestamps, observed models, results, schemas and capability hashes were preserved
and checked against the source rows. No new qualification programme was run. The configured
models remain Terra for interpretation/review and Sol for extraction/comparison.

```console
docker compose -p coverguide-star-slice -f compose.star-slice.yaml up -d redis
bash scripts/star_slice.sh manage migrate --noinput
bash scripts/star_slice.sh manage ingest_curated_manifest data/manifests/star-three-plan-2026-09-30.json
bash scripts/star_slice.sh manage process_policy_bundle POLICY_VERSION_UUID
bash scripts/star_slice.sh manage validate_policy_bundle POLICY_VERSION_UUID --manifest data/manifests/star-three-plan-2026-09-30-captured.json
bash scripts/star_slice.sh test
```

The input manifest is version 2. Its three products contain 23 document associations:
16 executable documents, one reference-only Assure sheet, and six excluded brochure/proposal
associations. All are checked against the captured SHA-256 and physical page count before storage.
Only a missing local object permits fetching that document's listed official URL. A corrupt
local object or mismatched page count fails without a network fallback.

Reference/excluded documents retain capture metadata but have no `PolicyVersionDocument`
membership, cannot be processed as part of the bundle, and cannot support published rules.
Prospectuses remain applicable executable bundle members in the unchanged baseline.
Assure consumables evidence comes from wording clause 27 (physical page 20, printed page 19)
and its own List I (physical page 44). The separate sheet is reference only.

Run the unchanged baseline before any version-2-specific processing correction. Keep baseline
logs and validation reports under the isolated report directory. Stop if free disk falls below
3 GB, or if at least 7 of one plan's 13 criteria remain unresolved after validation.

After Checkpoint 2 approval, use the existing build and publish commands with
`--three-product-demo`. The release label is `development_alpha_3_product`, `demo_subset`
is true, and the actual catalogue count is 3. The five-product and three-of-five paths retain
their gates, including verified rules and complete mandatory dependencies.

Runtime processes each use the same explicit branch environment:

```console
bash scripts/star_slice.sh web
bash scripts/star_slice.sh worker
bash scripts/star_slice.sh beat
# Build the frontend with COVERGUIDE_BACKEND_URL=http://127.0.0.1:8021, then:
bash scripts/star_slice.sh frontend
```

Use physical PDF page numbers in citations. Optional covers stay unselected; mandatory base
conditions still apply. Price/budget is unavailable. Do not push or publish before its checkpoint.

Step 2 verification on 2026-09-30: 319 backend tests passed. Ruff, Django check,
migration drift check, frontend lint, typecheck and build passed. The frontend's root,
session and CSRF endpoints returned HTTP 200 through port 3021; ports 3021, 8021 and
6401 bind only to loopback. All 23 associations were acquired from existing local
objects with their SHA-256 and page counts verified; no source URL was fetched.
Processing and release readiness are separate checks still required after ingestion.

Version-2 processing now preserves complete native physical pages after the
unchanged Comprehensive and Optima baselines demonstrated reader/citation failures.
Each of the 13 criteria receives the complete wording, CIS and applicable schedules;
the whole prospectus is added only for insufficient core evidence. Existing output
contracts, configured models, independent review and deterministic rule validation
remain in place. There is at most one corrective extraction retry per criterion.
Quotation text, physical page, source-file hash and character offsets are checked
before evidence is used. Derived `no_copay` preserves the validated copay conditions
and citations, and is excluded from the 13-criterion stop denominator.

Export Checkpoint 2 only after the real validation results are available:

```console
bash scripts/star_slice.sh manage export_star_slice_review data/manifests/star-three-plan-2026-09-30-captured.json
```

The command writes `output/star-three-plan-review.md` without building or publishing
a release. It includes explicit unknown reasons, unavailable price, complete rule
conditions and verbatim citation pages. A plan with seven unresolved criteria is
marked STOP; that report does not authorize continued processing or publication.

Latest processing-code verification on 2026-09-30: all 344 backend tests passed
(18 missing-static-directory warnings); Ruff and diff checks passed. The review
formatter was exercised against 85 retained candidate rule bodies without changing
or promoting their status. A pending-only preview under the isolated report
directory confirmed that unprocessed criteria are not presented as validated
unknowns. Real extraction and independent validation remain separate from these
checks and must finish before Checkpoint 2.


## Remaining criterion calls (2026-10-01)

Completed responses are retained per criterion. Transport errors have two separate
retries and never consume the single validation correction. The prospectus is
supplied only after an explicit missing definition, table or other core-evidence gap.

Version-2 extraction and review place their static instructions and complete bundle
before criterion instructions, candidates and correction context. Extraction uses
`COVERGUIDE_POLICY_EXTRACTION_REASONING_EFFORT` (default `low`) and
`COVERGUIDE_POLICY_EXTRACTION_MAX_OUTPUT_TOKENS` (default `8192`). Independent
review uses `high` effort. Other pipelines keep their existing generation defaults.
The output ceiling includes reasoning tokens; incomplete output still fails validation.

Each actual call logs its attempt ID, wall time, input, cached input, reasoning and
output tokens, and explicit generation options. Missing provider metrics remain
null. Existing usage storage and model-response contracts are unchanged; reasoning
counts and generation settings are in the call log. Retained response commitments
include generation options, so differing options cannot share an exact-response cache.
An independent source-review failure can use a criterion's correction only when
it has not already been spent. Completed criteria and exact successful reviews are
retained. The final deterministic validation runs after those remaining corrections;
it uses the same rule, dependency, citation and seven-unresolved-criteria checks.
The remaining plans run sequentially; the review records observed timing rather than
attributing a difference to one cause when prompt ordering and effort both changed.
