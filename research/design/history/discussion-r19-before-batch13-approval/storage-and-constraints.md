# Physical storage and enforcement contract — proposed revision 19

This document resolves logical dictionary types and common enforcement rules for the proposed PostgreSQL 18.6 implementation. It is a design contract, not executable DDL or a migration. Native Django tables retain their actual layouts and primary-key types; logical catalogue names do not authorize replacing authentication tables.

## Type mapping

| Dictionary type | Proposed storage and validation |
|---|---|
| `uuid` | PostgreSQL UUID; UUID4 default for newly generated application identities where declared. Preserve migrated UUIDs. IDs and owners are immutable. |
| `fk:Entity` | Same physical type as the target primary key, including native integer/string framework IDs. Ordinary existence FK plus the declared composite-owner or compatible-scope check. |
| `instant`, `timestamptz` | `timestamp with time zone`; normalize transport to UTC. Preserve any source-local timezone/precision needed to interpret the rule in the typed temporal payload. |
| `date` | PostgreSQL date. No inferred birth date from reported age or implicit midnight from a date-only observation. |
| `daterange` | PostgreSQL date range for a known date-granularity coverage interval. Require nonempty ordered intervals where declared. Preserve the originating bound convention/evidence; PostgreSQL canonical range form does not establish contractual inclusivity. An unbounded endpoint means established unboundedness, not unknown. |
| `smallint`, `integer`, `bigint` | Signed 16/32/64-bit values; entity-specific positive/nonnegative checks apply. Counts, revisions and sequences never share a semantic unit merely because storage matches. |
| `numeric(p,s)` | Exact PostgreSQL decimal within the declared precision/scale. Reject overflow or precision loss in validated ingestion instead of silently rounding an insurance input. |
| `enum` | Text with a database CHECK for the exact field-specific allowed set. Required fields are NOT NULL. A vocabulary change requires a reviewed contract/migration revision; arbitrary new strings cannot bypass validation. |
| `char(n)`, `varchar(n)`, `text` | PostgreSQL string types with the listed bounds and field validation. Hashes additionally require the exact hexadecimal form and algorithm. Encryption-required values use the approved encrypted representation; no raw sensitive value is permitted in logs. |
| `boolean` | PostgreSQL boolean. Absence is not false: use optional NULL or an explicit typed unknown where the dictionary requires it. |
| `json:Name` | JSONB with the pinned named JSON Schema and versioned semantic validator. Closed structure is necessary but insufficient: relational IDs, dimensions, units, scope, ownership and dependency closure are independently checked. |
| `tsvector` | Replaceable lexical derivative with pinned parser/configuration identity. It cannot replace the original evidence or prove mandatory-rule completeness. |
| `vector(1024)` | Dense BGE-M3 derivative with exact model/tokenizer/chunk lineage. Required dimensions and finite numeric components validated before indexing. |

Unknown or partially known intervals belong in `TemporalExtentV1` or the originating fact/evidence record until a required concrete range can be established. Do not insert an empty or unbounded range to satisfy NOT NULL. Optional `PersonRelationship.valid_from` and `valid_to` remain NULL when the dates are not established or material. “No default” means the writer must supply a value; optional NULL and an explicitly declared empty collection have different meanings. Empty collections never prove that no relevant condition or source exists.

The field dictionary supplies every field's purpose, units, allowed values, required status, default, validation and example availability. Quantity JSON preserves up to 24 integer and 12 fractional decimal digits using strings; exact calculation and final settlement rounding follow the value contract. An authentic value is supplied only where the original evidence establishes it; synthetic fixtures and uninspected private values are labelled.

## Private content, encryption and reader isolation

The proposed application uses encrypted block/filesystem storage beneath PostgreSQL. Protection covers database files, indexes (including private lexical/vector derivatives), WAL, temporary tables/files, snapshots and backups. Private object storage, reader scratch space and Redis persistence/backups also require encryption at rest. Encryption keys are managed separately from the data and backups, available only to restricted deployment identities; keys, credentials and raw provider payloads never belong in route, attempt, audit or migration-report fields. The isolated deployment must demonstrate encryption for every storage class before importing private data. A plaintext database dump is not an acceptable backup.

Private JSONB remains typed and queryable within an authorized database session. Medical facts, calculation inputs/results/traces and private search material receive the same storage protection as message content and policy identifiers. Treat all owner-scoped content and its derivatives as potentially sensitive health/financial/identity data, regardless of whether an individual field currently contains a medical word. Mixed tables inherit the private classification when owner-scoped; operational logs contain only permitted minimal metadata. Public insurance data is not permission to expose private relationships to it.

The dictionary's encryption annotations mean this common encryption-at-rest requirement; they do **not** silently specify a second, undefined column-cipher format or alter the declared SQL string/JSONB types. This proposal does not add application-level column encryption. Introducing it later would require discussion of ciphertext types, equality/search behavior, key rotation and migration. Storage encryption protects copied storage and backups; it does not prevent an authorized database administrator from reading live values. RLS, ownership checks, restricted administration, transport protection and minimization therefore remain required. This explicit trust boundary is part of the design discussion. PostgreSQL distinguishes storage encryption from protection against live privileged access in its [encryption options documentation](https://www.postgresql.org/docs/18/encryption-options.html).

Codex discovery sessions may navigate the public web autonomously and are not limited to approved insurer domains. `SourceURL.source_type` records provenance after discovery; it is not an allowlist. Every successful SourceCapture preserves the returned bytes and detected media type before the content is relied upon. Parser/OCR workers read only the selected input and cannot silently skip pages while publishing a complete document. A missing reader profile, unsupported format, resource limit or parser failure produces explicit failed or incomplete work.

Reader output and retrieved passages cannot issue tool instructions, modify authorization or choose arbitrary executable expressions. Only closed validated extraction/review payloads enter the candidate-rule workflow. An initial read/extraction attempt and two targeted retries retain their own outcomes; unresolved material omissions block publication. Qualification must exercise malformed documents and exhaustion limits in the isolated reader environment. These controls are proposed, not claimed to be installed by this document.

## Constraint responsibility

| Invariant | Required enforcement boundary |
|---|---|
| Identity, ownership and existence | Primary keys, immutable ownership, ordinary FKs, composite `(id, owner_id)` uniqueness/FKs, and true compatible-scope predicates for mixed records. Public NULL ownership never authorizes reading a private target. |
| Allowed local values | NOT NULL, CHECK, unique and partial-unique constraints as declared per entity. Application serializers provide understandable errors but are not the only enforcement layer. |
| Cross-record references in JSON | Closed target registry and deferred semantic validation of exact target type, owner, corpus/version and existence. No dynamic SQL or model-supplied table/column name. |
| Membership overlap | All mutations lock affected CustomerPolicyRevision parents FOR UPDATE before writing, in deterministic ID order. READ COMMITTED validation uses a fresh post-lock statement. Reject overlapping verified membership for the same revision/person and reject empty intervals. |
| Combi membership and seal | Lock exact bundle-revision parents for every membership mutation; validate slot/product/issuer/owner lineage, required/missing/stipulated/verified states, underlying-policy uniqueness, deterministic digest and commit-time seal. Reject persisted unsealed revisions and later member append/update/delete outside authorized erasure. |
| Concurrent turns | Unique idempotency scope, revision compare-and-swap, worker lease/fencing token, monotonic durable event sequence and erasure generation. A stale worker cannot publish after correction/cancellation/deletion. |
| Published graph | Immutable corpus member set, complete mandatory dependency closure, resolved material issues and exact validated evidence before atomic pointer advance. Search ranking cannot supply a missing mandatory edge. |
| Coverage denominator and numerator | Sealed independent inventory membership and counting protocol, reviewed split/merge lineage, exact immutable support selection. Unknown source scope or segmentation prohibits a measured percentage. |
| History and deletion | Immutable revisions with explicit supersession; authorized erasure follows copy/dependency records, retention holds and verification receipts. Referential protection is not permission to retain all private content indefinitely. |

Key-share locks protect referenced identities but are mutually compatible, so they do not prove set-wide uniqueness or aggregate balance safety. Parent locks must precede mutation, including in bulk imports. Higher isolation levels need a separately qualified retry/snapshot protocol. All locks are short-lived and exclude network calls, inference, OCR and long parsing. PostgreSQL describes the conflict behavior in its [explicit locking documentation](https://www.postgresql.org/docs/18/explicit-locking.html).

Database constraints, sealed immutable records and semantic publication validators have complementary responsibilities. Cross-record checks must cover raw/bulk writes and target mutation as well as the normal ORM service. The isolated implementation must demonstrate failure on invalid direct writes; a passing serializer test is insufficient.

## Indexes and query boundaries

Every entity lists proposed indexes in the typed dictionary. Primary/unique indexes enforce identity and idempotency; private lookup indexes begin with the appropriate owner/conversation scope where that supports the actual selector. Revision and event indexes support stable ordered replay. Foreign-key joins and reverse-dependency invalidation need lookup indexes; ownership constraints alone do not provide every reverse lookup index.

B-tree handles exact ownership, identity, status and ordered history. GiST supports the declared date-range intersections. GIN supports the specific lexical/JSON lookups declared in the catalogue; do not add blanket JSON indexes to every payload. The selected BM25 extension and pgvector index are qualified against the pinned corpus, retrieval quality and query plans before acceptance. No particular index configuration or approximate-neighbor behavior is accepted merely because a dependency installs.

Mandatory rule loading uses relational identifiers and dependency closure before supporting BM25/semantic ranking. Private search is authorized before scoring, with no inaccessible private documents contributing to customer-visible ranking statistics or cache results. Exact filters include owner, conversation/reuse grant, fact revision, knowledge release, terms/configuration, temporal applicability and open material issues.

Each of the [20 family operations](retrieval-operations.md) and every case's required operations is mapped to these records. The implementation must measure representative cardinality and execution plans, rather than treating this proposed index list as a performance result. Worker database connections reset transaction-local ownership state between jobs; ordinary request roles cannot bypass RLS.

## Required execution evidence after design approval

Run two-connection membership, payment, bundle-seal, fact-correction and stale-worker schedules against the isolated database. Include direct/bulk writes, conflicting corrections, duplicate retries, owner mismatches, target deletion, failed publication and rollback. Validate all JSON contracts with semantic counterexamples, not only schema-valid examples. Exercise wrong units, percentage bases, temporal boundaries, family/person/claim/year scope, missing connected clauses and changing original versions.

These checks accompany the preserved acceptance targets and migration rehearsal in the final proposal. They have not been executed by this design-phase package.
