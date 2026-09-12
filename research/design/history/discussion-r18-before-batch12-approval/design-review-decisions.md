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

## Batch 6 — approved 2026-09-12

Scope: sourced customer-specific policy facts and dated policy events.

Approved decisions:

1. Replace `IndividualTerm`, `CoverageLayer` and `ContinuityCredit` with one `CustomerPolicyFact` model. Those three concepts are kinds of sourced facts about a particular issued-policy revision and do not need separate tables.
2. Use a finite, code-controlled `fact_type` registry. AI output cannot create a new fact type. Information that cannot be mapped stays reported or unresolved rather than being forced into an invented type.
3. Validate `value` against the fact type using the closed `CustomerPolicyFactValueV1` contract. Personal terms use a typed rule value; additional cover records its amount, start and scope; continuity records credited duration or amount and the benefits to which it applies.
4. Keep customer statements and reported facts in `CustomerStatement` and `CustomerFact`. A `CustomerPolicyFact` becomes verified only when private policy evidence supports it.
5. Use `related_customer_policy_id` only when continuity or another permitted policy fact genuinely refers to another customer policy. Use `supersedes_id` for corrections without rewriting history.
6. Keep `PolicyEvent` as a small sourced timeline model with: identity and timestamps, owner, policy, event type, occurrence time, optional amount, source evidence or message, verification status, event sequence link, correction link and optional delegated-authority evidence.
7. Remove package-revision targeting and structured sender/recipient payloads from `PolicyEvent` at this stage. Package-specific event targeting is deferred until the package models are reviewed.
8. `related_event_id` records a real sequence such as request followed by receipt. `supersedes_event_id` records a correction. The two relationships have different meanings.
9. A customer inquiry remains a `Message` or `AdviceRequest`; it is not a policy event. Creating a database record never contacts an insurer, cancels cover or causes a payment.
10. **Superseded by the approved buyer-only scope revision:** the proposed `UsageEntry` model was removed because CoverGuide does not maintain actual claim or cover-usage ledgers.

## Batch 7 — approved 2026-09-12

Scope: structured public policy rules, their exact source passages, connected-rule closure and table cells.

Approved decisions:

1. Use four live models: `PolicyRule`, `PolicyRuleEvidence`, `PolicyRuleLink` and `PolicyRuleTableCell`.
2. Rename the generic `Rule` model to `PolicyRule`. A rule belongs to exactly one public `PolicyVersion`; customer-specific modifications remain `CustomerPolicyFact` records.
3. Use a finite `rule_type` registry. Codex may select a registered type but cannot create a type through extracted data.
4. Store typed conditions, required inputs, effects and an optional table definition in the closed `RuleV1` body. Stored policy text, SQL or Python is never executed.
5. Keep policy rules immutable. A correction creates a new row with the same `rule_key` and a `supersedes_id` link to the earlier interpretation.
6. `PolicyRuleEvidence` links every supporting, defining, restricting, exception, contradiction, precedence, header, cell or footnote passage. A required passage must be present before the parent rule can be verified.
7. Replace `RuleDependency` with the smaller `PolicyRuleLink`. Conditions stay in the linked rule body and precedence proof stays in rule evidence, so the link needs no duplicate scope or evidence field.
8. Fold `RuleTable` axes, result units and scope into `PolicyRule.body`. Keep `PolicyRuleTableCell` relational for indexed selectors, typed values and exact cell evidence.
9. Remove `RuleIssue`. `PolicyRule.review_status=blocked`, contradictory evidence roles and the later generic review record preserve the blocking outcome and detailed finding without a rule-specific issue table.
10. Move the independent rule inventory, lineage, support and coverage-measurement records out of the customer-advice application schema. They remain mandatory for the 90% knowledge target and will receive a separately isolated quality-store review.
11. Publication accepts only verified, unsuperseded rules with complete required evidence and verified mandatory rule-link closure.

## Batch 8 — approved 2026-09-12

Scope: dated insurer provider-network sources and evidence-backed personal quotes.

Approved decisions:

1. Use four models: `ProviderLocation`, `ProviderNetworkSnapshot`, `ProviderNetworkEntry` and `Quote`.
2. `ProviderLocation` identifies an exact facility branch. Name-only matches never merge branches; external identifiers and supported address information establish identity.
3. Replace generic `ProviderCheck` with `ProviderNetworkSnapshot`. It records the exact insurer, optional product variant, preserved source capture, query scope, observation time and completeness.
4. Keep snapshot completeness because zero results from a failed or partial search cannot prove provider absence.
5. Replace generic `ProviderObservation` with `ProviderNetworkEntry`. Each entry stores only an exact facility's network, restricted, excluded or unknown status, its restrictions, applicable dates and exact evidence.
6. Derive insurer, variant and observation time from the parent snapshot instead of repeating them on every entry. A later directory creates a new immutable snapshot, so entries need no supersession link.
7. Defer `Clinician`. A named-doctor requirement remains a `CustomerRequirement`; lack of reliable participation evidence stays unknown. A clinician identity store requires a later source-backed use case.
8. Keep `Quote` as an immutable private record tied to the exact customer profile revision, product variant, selections, issue/expiry dates, coverage term and private evidence.
9. A verbal customer-reported price remains `CustomerFact`. A structured `Quote` is created only from adequate insurer quote evidence, so it needs no separate verification-status field.
10. Fold `QuoteComponent` into the closed `Quote.price_breakdown` structure. Keep `Quote.total` directly accessible for quick comparison.
11. Fold quoted instalments into the closed `Quote.payment_schedule` structure. Insurer-confirmed payments remain `PolicyEvent`; no separate payment-accounting model is introduced here.
12. Hospital listing, cashless authorization, claim coverage, physical accessibility and clinician participation remain separate conclusions. Batch 8 establishes only supported provider-network and personal-quote facts.

## Batch 9 — revised and approved 2026-09-12

Scope: deterministic arithmetic needed for buying, filtering and comparing policies.

Approved decisions:

1. Retain only `Calculation` from the earlier Batch 9 proposal. It supports premium, age, waiting-period, deductible, percentage, limit and ranking calculations.
2. Remove `TreatmentEpisode`, `TreatmentExpense`, `CoverageAssessment` and `ExpenseCoverageResult`. CoverGuide does not administer treatment bills or estimate itemized customer claims.
3. A planned treatment or prior claim relevant to buying remains a sourced `CustomerFact` or `CustomerRequirement` about the affected person.
4. Public claim procedures, documentary conditions, limits and deductions remain `PolicyRule` records so they can be compared before purchase.
5. A buyer-focused `PolicyCandidateAssessment` will be reviewed with saved recommendation records; it will evaluate one candidate against customer facts and requirements rather than model a claim.

## Batch 10 scope exclusion — approved 2026-09-12

Scope: customer-specific claim administration.

Approved decisions:

1. CoverGuide is specifically a health-insurance buying and comparison adviser.
2. Remove `Claim`, `ClaimEvent`, `ClaimDocumentRequirement`, `ClaimDocumentReceipt`, `ClaimPayment` and `UsageEntry` from the proposed application database.
3. Do not store claim submission timelines, insurer receipts, actual payments, treatment bills or cover-usage ledgers.
4. Customer-reported past claims are stored only as relevant `CustomerFact` records. Public claim rules remain searchable policy knowledge.
5. Claim-administration cases remain preserved research artifacts but are outside application acceptance. The independent evaluation cohort must be refreshed with buyer/comparison cases before final acceptance is claimed.

## Batch 11 — approved 2026-09-12

Scope: published policy knowledge and fast public-policy search for buying and comparison.

Approved decisions:

1. Rename and simplify `CorpusRevision` to `KnowledgeRelease`: one immutable set of reviewed policy rules that the adviser may use together.
2. `supported_scope` states exactly which insurers, product variants, request types and rule types the release supports, including known gaps.
3. Rename `CorpusMember` to `KnowledgeReleaseRule`; retain only the release and exact policy-rule foreign keys. Policy version and scope are derivable and are not repeated per member.
4. Rename `CorpusPointer` to `KnowledgeChannel`; it atomically selects the published release for an environment such as production, review or pilot.
5. Replace mixed/private `SearchChunk` with public-only `PolicySearchChunk`. It indexes exact document sections and always resolves back to `EvidenceSpan` records.
6. Do not duplicate chunks per release. Retrieval first filters rules through the selected release, then reaches reusable document chunks through rule evidence.
7. Remove generic `Artifact` and `Dependency`. Saved recommendation lineage will use direct typed foreign keys reviewed with the recommendation models.
8. Defer the unreviewed `ReviewRecord` and `ContentCopy` models because their only target was the removed generic artifact table. Necessary review and erasure behavior will be redesigned later with explicit typed targets.
9. This batch serves buying and comparison only: it publishes searchable policy facts and does not model claims administration.

## Batch 12 onward — pending

No Batch 12 or later entity or field is approved yet. No Django models, migrations or schema-dependent implementation are authorized until the complete design is explicitly approved.
