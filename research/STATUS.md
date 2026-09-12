# Implementation status — 10 September 2026

The requested replacement is **not complete**. Parts A and B have an implemented offline
evidence foundation; the running pilot remains unchanged.

## Measured artifacts

| Measure | Result |
|---|---:|
| Selected insurers represented in the seed register | 20 |
| Existing listing identities accounted for | 203 |
| Distinct discovered document URLs, scope unresolved | 4,028 |
| Unique acquired PDFs, including documents awaiting scope classification | 2,300 |
| Original pages accounted for in those PDFs | 43,003 |
| Response objects with independently rechecked hashes | 2,724 |
| Acquisition attempts retained | 3,193 |
| Failed attempts retained, including earlier reader/URL errors | 662 |
| Running acquisition attempts at final audit | 0 |
| Case records: reference / evaluation drafts | 200 / 200 |
| Reference records with evidence-linked partial answers | 8 |
| Fully worked cases / independent evaluation cases frozen | 0 / 0 |
| Original rule instances in the inspected sample | 19 |
| Focused tests passed | 26 |

Current source outcomes: {'acquired': 2412, 'failed': 148, 'not_acquired': 1468}. Acquisition counts include broad-directory material,
not only in-scope medical-expense policies. They are not product, variant or readiness counts.
No percentage is reported for policy-knowledge coverage because the full independent denominator
is unknown. Neither acceptance target has been measured.

## What works

The new offline Python modules preserve original bytes and source provenance, retain duplicate
and changed-file observations, account for each acquired PDF page, and expose download failures.
The exact 203-entry legacy identity set was independently compared with the saved pilot snapshot.
The case contracts and accounting functions reject unsupported completion, duplicate attempts,
reused conversation state and family-level shortfalls. Original source hashes, pages and all
19 sampled passages resolve. Ruff, mypy, Django checks and migration-drift checks pass.

The existing strict CLIProxyAPI adapter passed a fresh read-only probe of its existing interview
schema with exact requested/reported `gpt-6-astra` identity. New review/extraction/image workloads
are not qualified. Accounts, passwords, sessions, live services and relay configuration were not
changed. No database migration, cutover or deployment was performed.

## Remaining gaps

The complete insurer product/version/variant/add-on register and all original bundles still need
reconciliation. Some source pages return access failures or need JavaScript-driven discovery.
Every file's policy scope, version association and processing outcome require further assessment.
Native page preservation does not complete table/figure inventory, OCR, rule interpretation or
independent review. The 19-rule sample has unresolved dependencies and is not publishable.

All 400 cases still require complete worked decisions, substantive distinctness and compound-factor
assessment, boundary and multi-turn coverage, independent calculations and original evidence.
Evaluation drafts have not been frozen or used to tune an adviser. Full evaluation independence
has not been established.

The final schema/ERD/data dictionary, PostgreSQL 18 environment and extensions, fresh models,
curated imports, `/api/v2/`, replacement memory/advice/retrieval/calculations, Next.js replacement,
production readers/automatic review, crawlers and atomic publication remain unimplemented.
The original repeated-intake/Kota issue in the active pilot has not been changed by this work.
The 600 evaluation attempts, 60 robustness checks, performance targets and migration/rollback
rehearsal have not run. Independent reviewer agents were not run in this session.

See [the workspace guide](README.md), [source index](registers/source-index.csv),
[per-insurer coverage](reports/insurer-coverage.csv), [final audit](reports/final-audit.json),
and [verification record](reports/verification.json).
