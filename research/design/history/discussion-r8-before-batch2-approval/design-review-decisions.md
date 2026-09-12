# Staged human database-design review

The overall database design is still under review. Approval of a batch does not approve unreviewed batches, models, migrations or implementation.

## Batch 1 — approved 2026-09-11

Scope: authentication, people, relationships, conversations, messages and long-conversation retrieval derivatives.

Approved decisions:

1. Keep the existing `accounts.User(AbstractUser)` as the physical authentication model; `Account` remains its logical ERD name.
2. Preserve UUID account identity and native Django authentication, permissions, password hashes and sessions.
3. Use abstract `UUIDModel`, `CreatedAtModel` and `MutableTimeStampedModel`; they create no tables.
4. Keep `AIPreference` separate from the authentication table.
5. Simplify `Person` to `id`, `created_at`, `owner_id` and `display_name`.
6. Remove `Person.local_key`, `identity_status`, `merged_into_id` and `identity_evidence_id`.
7. Rename `Relationship` to `PersonRelationship`; retain explicit owner, direction and sourced assertion; replace the range with optional `valid_from` and `valid_to`.
8. Keep `Conversation.current_fact_revision` and `current_snapshot_id`; remove `fact_reuse_policy` because reuse requires an explicit grant.
9. Keep messages immutable with owner/conversation ordering and idempotent submission fields.
10. Use `FactSnapshot` as authoritative customer memory. Recent messages are loaded by token budget.
11. Add `ConversationMessageChunk` for scoped lexical and local BGE-M3 semantic retrieval of exact old message sections. Exact source messages are loaded after ranking; corrected current facts override historical matches.
12. Delete or invalidate every derived chunk before or with source-message erasure.

## Batch 2 onward — pending

No other entity or field is approved yet.
