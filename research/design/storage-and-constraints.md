# Storage, privacy and database constraints

The application uses PostgreSQL with typed foreign keys, enum/check constraints, range types, GIN/GiST indexes, full-text search and pgvector where approved. Original bytes and large operational/model results live in private encrypted object storage; database rows retain opaque keys and integrity values.

Public corpus files and private uploads use separate storage namespaces and credentials. Private content is encrypted at rest and restricted by owner-aware services. Raw hashes are kept only where exact byte identity is required, such as owner-scoped `OriginalFile`. Messages, selections and requests use keyed commitments so a party cannot test guesses against stored hashes. Result checksums identify encrypted stored bytes.

All JSON columns use the closed schemas in `json-contracts.schema.json`. Schema validation is necessary but relational IDs, units, rule scopes, dependency closure and evidence authority also require versioned semantic validators. Unknown properties fail validation; zero, unlimited, unknown and not applicable use distinct typed representations.

Foreign keys use protective deletion in ordinary ORM paths. Deferred owner/lineage checks and short locking transactions enforce cross-row invariants, including same-owner links, exact policy-version membership, current turn publication, knowledge-release completeness and package-component consistency. External calls never run inside these transactions.

Search indexes are derivatives. Private conversation chunks are invalidated after message erasure or correction and cannot become the source of truth. Public policy chunks may improve recall, but mandatory rule selection and citations come from published `PolicyRule` and `EvidenceSpan` records.

Audit metadata contains only identifiers, revisions, counts and safe reason/error codes. It cannot contain message text, diagnoses, document bytes, prompts, responses, credentials or secrets. Backups must honor deletion tombstones before restored private data is made accessible.

The benchmark database is physically and administratively separate from application storage. Its protected cases, oracles, responses and per-case scores have no application foreign keys, search indexes or implementation-readable exports.
