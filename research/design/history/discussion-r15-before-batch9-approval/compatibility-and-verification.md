# Proposed stack compatibility and verification sequence

Checked 10 September 2026. This is a design-phase compatibility assessment, not an installed replacement environment. The repository pins and shared pilot remain unchanged. Package metadata can identify declared incompatibilities; it cannot qualify the combined application, OCR, GPU, extension, authentication or recovery behavior.

| Component | Proposed retained/added version | Current evidence and qualification limit |
|---|---|---|
| Python | Existing `>=3.12,<3.13` | Retain the project range. No interpreter replacement. |
| PostgreSQL | 18.6, isolated instance | Official release is dated 13 August 2026. Do not point replacement work at the pilot database. [Release notes](https://www.postgresql.org/docs/18/release-18-6.html) |
| pgvector server extension | 0.8.6 | The tagged source supports PostgreSQL 13+. Build/package qualification against the exact 18.6 image remains necessary. [Tagged source](https://github.com/pgvector/pgvector/tree/v0.8.6) |
| BM25 | Selected `pg_textsearch` 1.4.0 | Tagged source supports PostgreSQL 17 and 18 and requires preload configuration. This is the originally selected extension; no replacement database extension is proposed. [Tagged source](https://github.com/timescale/pg_textsearch/tree/v1.4.0), [release](https://github.com/timescale/pg_textsearch/releases/tag/v1.4.0) |
| Django / DRF | Existing 5.2.17 / 3.18.1 | Current DRF metadata requires Django >=5.2. Django 5.2 supports PostgreSQL 14+. Exact migrations, constraints and authentication must be tested on 18.6. [Django databases](https://docs.djangoproject.com/en/5.2/ref/databases/), [DRF package metadata](https://pypi.org/pypi/djangorestframework/3.18.1/json) |
| psycopg | Existing 3.2.10 binary/pool | Declares Python >=3.8; current Python range fits. Pooling, transaction-local ownership and worker resets remain runtime checks. |
| Celery / Redis client | Existing 5.6.3 / 8.1.0 | Declared Python minima are 3.9 and 3.10. Redis server version, broker recovery and visibility/lease behavior remain to be pinned and qualified in isolation. |
| pdfplumber | Existing 0.11.10 | Declares Python >=3.8. Preserve reader identity, original geometry and explicit failures. |
| Docling | Proposed 2.126.0, qualified reader environment | Current metadata accepts Python >=3.10,<4 and Pydantic >=2,<3 through docling-slim. Torch, OCR assets, memory/GPU compatibility and actual page/table performance remain unqualified. Pin the selected OCR/model assets with hashes; do not use an unversioned download at runtime. [Exact metadata](https://pypi.org/pypi/docling/2.126.0/json) |
| Python pgvector adapter | Proposed 0.5.0 | This is a separate package/version from server extension 0.8.6. Metadata declares Python >=3.10; no adapter installed by this proposal. [Metadata](https://pypi.org/pypi/pgvector/0.5.0/json) |
| BGE-M3 | Local pinned model revision and tokenizer, revision not yet selected | Model card specifies 1024 dense dimensions and an 8192-token input length. Pin the artifact digest and qualify truncation, multilingual text, retrieval and resource usage. [Model card](https://huggingface.co/BAAI/bge-m3) |
| Next.js / React / TypeScript | Existing 16.3.4 / 19.2.0 / 5.9.2 | Local Node is 24.1.0; current Next documentation requires Node >=20.9. This does not establish replacement UI/API compatibility. [System requirements](https://nextjs.org/docs/app/getting-started/installation) |
| PDF.js / Playwright | Existing 5.4.149 / 1.63.0 | Retain pins; later qualify authenticated byte/range access, one-based citation conversion, rotated highlights and browser worker assets. |
| Codex transport | Existing shared CLIProxyAPI strict `/v1/responses` | Preserve exact requested/observed identity and explicit failure states. Qualification must use the actual fact, extraction, review and answer schemas, plus images/context lengths where used. No relay restart or route change belongs to this design phase. |

[dependency-metadata-check.json](dependency-metadata-check.json) preserves live Python package responses and failed lookups. It is intentionally not a lockfile or a claim of transitive resolution. Existing Pydantic 2.11.9 is within Docling's stated major range; a clean isolated lock/install still must resolve all extras. OCR engine/model and Redis server pins remain explicit operational decisions. No forced stack departure has been established by metadata alone.

## Retrieval isolation

The pg_textsearch README states that its index provides corpus statistics even when a sequential scan is used. An owner WHERE filter alone therefore does not establish isolated private ranking. The proposal uses public, revision-qualified BM25 indexes for public corpus material and computes deterministic BM25 statistics over only the already authorized private candidate set in a replaceable adapter. Private dense retrieval likewise uses exact cosine over authorized candidates. GIN text search is a diagnostic/supporting lexical operation, never silently labelled BM25. A future private partition/index design requires isolation and ranking qualification before replacing that path. [pg_textsearch query behavior](https://github.com/timescale/pg_textsearch/tree/v1.4.0)

Mandatory rules come from exact relational closure before supporting ranking. HNSW recall and BM25 top-k results cannot certify that required exclusions or definitions were loaded. Missing mandatory coverage produces a blocked/conditional result. Partition and index choices must be measured against the curated corpus; this proposal does not claim p95 performance.

The runtime database role must not own protected tables or bypass RLS. Transaction-local context must be cleared when pooled connections are reused. RLS supplements exact ownership checks and constraints; table owners normally bypass it unless forced. Native Django `on_delete` describes ORM behavior and does not itself create an SQL ON DELETE clause. The dictionary records both behaviors separately. [PostgreSQL RLS](https://www.postgresql.org/docs/18/ddl-rowsecurity.html), [Django relationship behavior](https://docs.djangoproject.com/en/5.2/ref/models/fields/)

## Verification after explicit design approval

| Stage | Required evidence before proceeding |
|---|---|
| Isolated database and curated knowledge | Exact PostgreSQL/extension build identities; native account preservation; FK/owner/lineage/JSON constraints; original resolution; version selection; all scenario-family selectors against curated records. No parser-derived denominator. |
| Adviser and relay | Persistent attributed facts/corrections, mandatory closure, independently tested unit/calculation rules, claim citations and complete/conditional/clarification/insufficient-evidence/technical-failure outcomes. Qualify every actual relay schema and record model identity, latency, usage and error. |
| DRF and workers | `/api/v2/` OpenAPI ownership/idempotency/revision contracts; durable outbox/event reconnect; cancellation, retries, lease fencing, erasure fencing and partial-failure recovery. Worker owns inference; reconnect never initiates it. |
| Next.js journeys | Generated TypeScript contracts; session and CSRF checks; private cache behavior; buyer-versus-parent, Kota, correction, reopening, comparison, original highlights, cancellation/reconnect and session isolation. |
| Readers and review | Docling/pdfplumber/OCR adapter qualification against independently inventoried originals. Initial attempt plus two targeted retries; unresolved material issues block affected capabilities. Complete corpus reconciliation and coverage accounting. |
| Crawlers and updates | Per-insurer discovery, daily checks, changed-byte detection, historical preservation, recovery, dated provider/quote observations, dependency invalidation and atomic publication. |
| Independent acceptance | At least 180/200 evaluation cases and 9/10 in every family; each passing case succeeds on all three fresh attempts. At least 90% of independently inventoried relevant rules overall and for each insurer; unknown denominators unmeasured. All 60 robustness checks reported separately. Any critical unsupported claim, wrong eligibility, material calculation error or data leak blocks release. |
| Performance | Five concurrent conversations; measured p95 <1 second for stored retrieval/rule evaluation and <20 seconds for validated answers without external lookups. Report cold/warm, queues, timeouts and failures. |
| Migration/cutover | Rehearse accounts/passwords/ownership/messages/originals, quarantine unsafe translations, verify rollback and post-cutover-write preservation. Production cutover requires separate approval. |

The independent benchmark proposal records an unresolved interpretation for operational-family acceptance. That discussion cannot reduce the fixed denominator or permit missing evidence to count as a successful insurance answer. No acceptance attempts, 90% claim, robustness pass, performance pass or migration rehearsal is asserted by this package.
