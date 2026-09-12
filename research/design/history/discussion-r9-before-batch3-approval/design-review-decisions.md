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
7. Use `PersonRelationship` for directional family relationships.
8. Keep messages immutable, ordered and idempotent.
9. Keep `ConversationMessageChunk` as a replaceable lexical/local-BGE-M3 retrieval derivative.
10. Rename `Conversation.current_snapshot_id` to `current_profile_revision_id` and remove duplicate `current_fact_revision` as part of the approved Batch 2 simplification.
11. Rename `PersonRelationship.source_assertion_id` to `source_statement_id`.

## Batch 2 — approved 2026-09-11

Scope: unstructured customer statements, structured facts and requirements, correction history, customer-state revisions and advice goals.

Approved decisions:

1. Use five models: `CustomerStatement`, `CustomerProfileRevision`, `CustomerFact`, `CustomerRequirement` and `AdviceRequest`.
2. `CustomerStatement` stores message offsets rather than duplicate text and makes ignored or unresolved meaningful information visible.
3. Remove `CustomerMessageInterpretation`; generic processing attempts will record extraction completion and failure later.
4. Use a finite, reviewed, code-controlled fact-type registry. AI output cannot create new types; unmatched information remains a statement pending clarification or mapping.
5. Facts and requirements are append-only versions grouped by `logical_key` and introduced by a profile revision.
6. Remove `CustomerRequirementPerson`; person-scoped requirements are atomic rows and all-insured or purchase-wide scopes use explicit scope values.
7. Remove `ProfileFactSelection` and `ProfileRequirementSelection`; active historical state is derived from the latest version per logical key at the requested revision.
8. Keep `CustomerProfileRevision` as a minimal immutable checkpoint created only when facts or requirements change.
9. Keep `AdviceRequest` as a long-lived customer goal; later execution records pin the exact profile revision and processing outcome.
10. Defer cross-conversation fact reuse and remove `ConversationReuseGrant` from the current design.
11. Do not add adviser playbooks now. Policy-rule inputs and outcomes will provide customer-to-policy routing and gap detection.

## Batch 3 onward — pending

No Batch 3 or later entity or field is approved yet. No Django models, migrations or schema-dependent implementation are authorized until the complete design is explicitly approved.
