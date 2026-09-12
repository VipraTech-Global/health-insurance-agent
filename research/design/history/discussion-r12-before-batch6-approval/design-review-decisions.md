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

## Batch 3 — approved 2026-09-12

Scope: autonomous Codex document discovery, URL observations, source captures, preserved bytes, document version history, page accounting and exact evidence locations.

Approved decisions:

1. Use ten narrowly scoped models: `Insurer`, `DiscoveryRun`, `SourceURL`, `SourceObservation`, `SourceCapture`, `OriginalFile`, `DocumentSeries`, `DocumentVersion`, `DocumentPage` and `EvidenceSpan`.
2. Give Codex unrestricted public-web discovery. Remove `approved_host`, insurer-domain allowlists, redirect-control fields and crawler-specific resolver metadata from the database proposal.
3. Simplify `Insurer` to inherited identity/timestamp plus `name`; remove `code`, `regulator_code`, `status` and `successor_id`.
4. `DiscoveryRun` stores the exact Codex instructions, session/model identity and terminal outcome. A completed run means the assigned session finished; it never proves that all documents were found.
5. `SourceURL` is one unique public address. `SourceObservation` retains every discovery path to it, including explicitly explained irrelevant and unresolved observations.
6. `SourceCapture` records each attempt and permits the same URL to return different bytes over time. `OriginalFile` deduplicates exact content by SHA-256 across sources.
7. Rename `SourceLocator` to `SourceURL`, `Acquisition` to `SourceCapture`, `OriginalBlob` to `OriginalFile`, `SourceLinkObservation` to `SourceObservation`, and split the old `DocumentRevision` concept into `DocumentSeries` and `DocumentVersion`.
8. Preserve both location provenance (`SourceURL.source_type`) and document authority (`DocumentSeries.authority`): an insurer-issued document can be found on an archive, while a comparison article remains independent analysis.
9. Derive latest-known versions from `DocumentVersion` dates and supersession. Do not store a stale `is_latest` flag or equate latest discovered, latest published and currently applicable.
10. Keep `DocumentPage` because every page, including unread or failed pages, must be accountable. Remove stored page width, height and rotation because they can be read from preserved PDF bytes.
11. `EvidenceSpan` initially reached the exact file and document version through `source_capture_id`; Batch 5 extends the same evidence model to private customer uploads without duplicating its quote, page or locator fields.
12. Remove `DiscoveryRun.started_at`, `SourceObservation.sequence_number` and `SourceCapture.started_at`; inherited `created_at` records when those activities began.

## Batch 4 — approved 2026-09-12

Scope: product identity, complete policy terms packages, governing document membership, insurer-defined variants and selectable options.

Approved decisions:

1. Remove `LegacyListing` and `ListingCandidate` from the replacement application schema. Historical source records may remain in migration evidence, but there are no live legacy product models.
2. Use five models: `Product`, `PolicyVersion`, `PolicyVersionDocument`, `ProductVariant` and `ProductOption`.
3. `Product` is the stable insurer product family. Rename `canonical_name` to `name`, `kind` to `benefit_type`, `lifecycle` to `lifecycle_status`, `advice_scope` to `recommendation_role`, and `identity_span_id` to `identity_evidence_id`.
4. Keep `benefit_type` for coarse payment-form filtering and `recommendation_role` for primary, supplementary, reference-only or excluded advice use; they answer different questions.
5. Rename `TermsRevision` to `PolicyVersion`. It represents the complete legal terms package, not one source file. Remove redundant `revision_key` and derived `bundle_sha256`.
6. Rename `TermsDocument` to `PolicyVersionDocument`. Its role, required status, applicability and evidenced precedence explain how each DocumentVersion participates in the policy package.
7. Rename `Configuration` to `ProductVariant`. Store allowed base choices in `choices`; do not create one row for every possible customer combination. Remove `variant_code`, duplicate `label` and derived `selection_sha256`.
8. Rename `ConfigurationOption` to `ProductOption`. Keep optional separate terms, selection kind, conditions and identity evidence. The separate policy-version reference is nullable because some options are governed entirely by the base terms.
9. Product selection proceeds from Product to applicable PolicyVersion, then ProductVariant and compatible ProductOption; detailed rule evaluation and evidence remain separate.

## Batch 5 — approved 2026-09-12

Scope: private customer uploads and the exact insurer-issued policy, revision, insured membership and selected option records derived from them.

Approved decisions:

1. Use five models: `CustomerUploadedDocument`, `CustomerPolicy`, `CustomerPolicyRevision`, `PolicyMember` and `CustomerPolicyOption`.
2. `CustomerUploadedDocument` describes one private file supplied by the customer; `OriginalFile` remains the content-addressed byte record. The upload record retains owner, source message, encrypted display name, document kind and review state without copying file content.
3. Amend `EvidenceSpan` so exactly one of `source_capture_id` or `customer_uploaded_document_id` is present. Public and private evidence share the same quote, page, context and locator representation.
4. Rename `PolicyContract` to `CustomerPolicy`. It is the stable identity of an insurer-issued customer policy or personal offer and is never created merely because CoverGuide recommends a public product.
5. Rename `ContractRevision` to `CustomerPolicyRevision`. Separate the full `policy_term` from the interval in which this exact revision is effective. Remove duplicate issue/receipt event fields, the public-document schedule FK and the explicit previous pointer.
6. Store actual base selections in `selected_choices`. The closed structure contains no members or ProductOption selections.
7. Rename `ContractMember` to `PolicyMember`. Remove the duplicate family-role field: `PersonRelationship` records family relationship, while `PolicyMember` records actual issued coverage and its interval.
8. Use `CustomerPolicyOption` for one customer-specific selected, declined or unresolved `ProductOption`. Keep it relational so PostgreSQL can enforce option and variant lineage.
9. Customer statements remain reported facts until sufficient insurer evidence supports verified issued-policy records. The insurer creates the policy; CoverGuide only records and verifies its structured interpretation.
10. Defer personal underwriting terms, additional coverage layers, continuity credits and dated policy events to Batch 6.

## Batch 6 onward — pending

No Batch 6 or later entity or field is approved yet. No Django models, migrations or schema-dependent implementation are authorized until the complete design is explicitly approved.
