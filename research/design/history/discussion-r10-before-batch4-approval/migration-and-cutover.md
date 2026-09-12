# Pilot migration and reversible cutover proposal

The pilot preservation inventory covers 33 concrete declared models and 188 explicit concrete fields, plus the two common fields on the abstract UUID base and inherited/native authentication structures. The earlier “190 explicit fields” included those two abstract declarations. [migration-field-map.json](migration-field-map.json) accounts for every concrete declaration individually and lists inherited account fields, joins and framework tables. It is a proposed mapping, not a data migration. Actual database rows, passwords, sessions and private messages were not read.

## Preserve before translating

Preserve the pilot database backup, originals, extraction artifacts, exact application/dependency/configuration identities, corpus/route manifests, accounts, ownership and deletion outcomes. Verify backup checksums and independent restore. A database dump alone does not preserve filesystem originals. Keep the pilot available while building the replacement in its approved isolated environment.

Each source record gets a `LegacyMapping` with exact source table/key, owner, original payload fingerprint, private/public archive blob and explicit mapping status. All fields lacking a proven semantic translation stay in the preserved record archive. A matching label or UIN is insufficient to invent product edition, person attribution or rule scope. Raw profile JSON is not automatically a set of confirmed medical facts; assistant `profile_suggestion` blocks stay unconfirmed. Historical answer success flags retain their original validation scope.

Accounts keep UUIDs, email identity, complete encoded password bytes, usable/unusable state, privilege flags, join dates and group/permission memberships. Never use `create_user` or `set_password` on an encoded password. Preserve native Group/Permission/ContentType/user-through/session/admin layouts and primary-key types; the dictionary's logical names are not a custom replacement auth system. The migration adapter verifies native SQL constraints and Django ORM deletion semantics separately.

Session continuity requires the same supported password encodings, compatible signing/auth/session backend configuration, cookie scope and expiry behavior. Copying session rows is insufficient proof. Configuration transfer is handled securely outside reports; no secret values appear in this package. If compatibility cannot be retained, the departure returns for discussion before implementation/cutover.

## Unsafe translations requiring explicit curation

- Legacy product versions/variants and original associations: preserve and map only after dimension-specific original reconciliation. Current wordings cannot silently fill historical UIN gaps.
- VerifiedFact/Clause/EvidenceBundle: archive all values, conditions, order and support; map to new typed rules only with independent original review. Existing “verified” is not the new coverage numerator.
- Profiles: preserve absent/blank/null/false and suggestions distinctly. Do not guess insured person, age reference, DOB, units, consent or source turn.
- Old snapshot-to-conversation links: revision integers are conversation-local. Owner/revision without unambiguous conversation provenance remains unresolved.
- Premium/rating observations: a public price or rating is not a private current quote, underwriting acceptance or suitability score.
- SourceObservation hashes and catalogue names: resolve explicit identities; neither has a safe automatic product/blob association merely through display name or URL.
- Evidence coordinates: old physical pages are zero-based; new physical ordinal is one-based. Preserve printed labels, rotations, source-word IDs and extraction revision; validate conversion once rather than regenerating citations silently.
- Old transient SSE progress: unavailable durable events cannot be reconstructed. Preserve final artifacts/attempt history and mark missing progress history explicitly.
- Deleted records: never restore erased medical values from old profiles, backups, snapshots, search derivatives or queued work. Restore must apply tombstones before access.

## Rehearsal and rollback evidence required later

In the isolated approved environment, compare exact account/message/document identities, counts, ownership sets and content hashes; exercise existing-password login/session continuity, original citation resolution and owner isolation. Verify all mapped fields and archive every unmapped source field. Rehearse interruption/retry and repeated import idempotency. Validate PostgreSQL constraints directly, including bulk inserts that bypass Django model validation.

Before cutover, define the active-work drain/cancel boundary and record a final source snapshot. Rehearse restoring the pilot plus its originals under the preserved application configuration. Record whether post-cutover writes are held, mirrored or require an explicit replay; a rollback cannot silently discard new messages or undo deletion. Reverse migration functions are not a rollback plan, especially where old data migrations have no-op reversal.

Release evidence must include the unchanged advice/knowledge/robustness/critical correctness thresholds, customer journeys, engineering checks and measured performance. Obsolete advice logic is removed only after acceptance and a verified rollback path. **Database implementation requires explicit design approval; production cutover remains a separate approval.** No migration, service restart or cutover was performed for this proposal.


Legacy SourceObservation.fetched_at is retained with its original meaning in the exact archived source payload. The pilot ingestion path stamps it after download/storage, while batch discovery may stamp before individual fetches. It may populate `SourceCapture.created_at` only when it truly represents the beginning of that capture attempt; otherwise the migration creates a new timestamp and retains the legacy timestamp in the archived payload. Inventing chronology is forbidden.
