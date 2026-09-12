# Relationships, ownership and lifecycle — discussion revision 2

[relationships.json](relationships.json) specifies all proposed foreign-key relationships individually: source field, target, required/optional state, access mode, deletion/update behavior, deferral and enforcement. This is a design contract. No constraints have been installed or runtime-tested.

## Access and database invariants

“Public” in the dictionary means globally scoped data, not an unauthenticated HTTP endpoint. Operational metadata, authentication and reviews still require the relevant API role. Public insurance originals are served through citation access checks; private originals never enter a shared public corpus.

Every owned row has a nonnull owner and `UNIQUE(id, owner_id)`. A private-to-private relationship uses the composite FK plus a direct existence FK. Public/mixed relationships cannot use nullable equality to prove ownership. They have a normal target FK and a deferred constraint trigger requiring the target owner to be NULL or equal to the source owner, as appropriate. The predicate must evaluate TRUE; NULL is rejected. A globally scoped source must point only to globally scoped targets. Target ownership and primary keys are immutable. Triggers take key-share locks and validate insertion, reference update and target change/deletion so bulk loading cannot bypass them.

Actor relationships are different from resource ownership. A reviewer or retention approver may be an authorized staff account, not the customer owner. Authorization checks happen under the authenticated service role; the audit receipt identifies operation, role, target and result without copying medical content. Nullable actor identities may be erased while retaining the permitted minimal historical review receipt.

Application owner filters are mandatory. Proposed PostgreSQL RLS is an additional protection for private tables, using a transaction-local owner setting under a non-owner, non-superuser role without BYPASSRLS. Worker transactions set context from persisted owned work, not client-supplied owner IDs. Connection pools reset transaction-local context; privileged migrations/publication use separate restricted roles. Native auth/session tables use their native role-limited access. Public search uses only approved corpus members. Private retrieval materializes the authorized owner/conversation input set before scoring; post-ranking filtering is insufficient.

## Conversation and lineage invariants

A fact snapshot belongs to exactly one conversation and revision. A deferred constraint trigger validates `SnapshotFact -> FactAssertion -> Conversation`, confirmation/import grant and predicate definition. For scalar predicates, no more than one accepted value may exist per subject/predicate in a sealed snapshot. Multiple unresolved conflicting assertions can be present with a conflict key; none is silently chosen. Set predicates deduplicate canonical typed values. Event-series predicates retain event identity and time.

Supersession requires the same conversation, subject and predicate. Authorized imports retain a separate source_assertion_id and never supersede an assertion in the source conversation. It is acyclic and cannot branch into two accepted current values. A model proposal is never promoted merely because an assistant said it. Confirmation creates a new accepted assertion/version with its source confirmation message, preserving the prior proposal. A sealed snapshot cannot gain, lose or change members except through the documented erasure transition; erasure marks it nonreplayable and removes protected payloads.

`Decision`, `Turn`, `DecisionIntent`, input message and snapshot must all share conversation/owner. The turn's expected revision equals its snapshot revision. The conversation current pointer's revision must match its selected snapshot. Contract membership must point to its exact contract revision and an owned person. Individual terms/layers/credits/claims are checked against that same contract/person/period lineage. Deferred triggers perform these joins; cross-row checks are not represented as ordinary PostgreSQL CHECK expressions or ORM save hooks.

A new conversation defaults to no prior medical-fact reuse. A later explicit request creates `ConversationReuseGrant` for exact source/destination conversations and selected assertions. Imported facts link that grant and original assertion; a new query does not imply authorization to import all account history. Revocation blocks future retrieval/import and invalidates dependent current answers. Reopening the same owned conversation retains its own facts but rechecks stale evidence and quotes.

## Durable turns and events

One short transaction validates ownership/idempotency/revision, records the message and accepted fact changes, seals the snapshot, creates the turn and outbox entry, and commits. Duplicate request IDs with the same canonical payload return the saved turn; different payloads return a conflict. One active turn per conversation is proposed; a correction can supersede/cancel older work while creating a new revision.

Workers claim persisted work with leases and fencing tokens. Network/model calls occur outside database transactions. Completion reacquires the turn/conversation lock and verifies lease token, cancellation, owner erasure generation, expected fact revision and corpus/observation dependencies. A stale result is retained only within the authorized historical scope and cannot publish as current. A material source invalidation blocks publication even if inference succeeded.

Each user-visible event is committed once with a monotonically increasing cursor. Reconnect returns events after the supplied cursor. It neither redispatches nor repeats inference. Cancellation is durable and does not erase already accepted facts. Explicit retries create visible attempts under the same work lineage; unknown provider completion is `indeterminate`, not silent retry success. Outbox delivery may repeat; consumers deduplicate its stable key.

## Policy and corpus changes

Product identity, UIN, terms revision and blob hash are separate. Select by the original-supported event predicate, person/variant/options and policy interval. “Latest downloaded” is never a legal precedence rule. Regulatory changes under the same UIN create a new terms revision; existing-policy extension requires an applicable instrument. Personal endorsements and underwriting terms have separate accepted state and scope. Unknown edition selection blocks the affected answer, while unrelated supported claims can remain usable.

Publication first seals a manifest with all exact rule/document/table dependencies and independent review results. It validates each capability and blocks material unresolved issues. A short transaction switches `CorpusPointer` by generation and creates an invalidation outbox event. Existing decisions retain their original corpus ID; current validity is separate from historical reproducibility. URL changes preserve prior acquisitions and bytes. Unread originals and unknown rule denominators do not become coverage through publication.

Quotes bind owner, facts, people, options, term, validity and priced components. A fact correction invalidates affected quotes even if their expiry is later. Hospital observations bind exact branch, insurer, service, observation time and property type. Network participation, exclusion, accessibility, clinician participation and authorization are separate observations. A negative search is unknown unless its scope was completely observed or the source explicitly states absence.

## Ledger corrections

Every posting receives a stable `posting_key` from the durable event/action and accounting component before dispatch. `UNIQUE(owner_id, posting_key)` prevents retries duplicating use or reserves. Claim-line assessments are immutable numbered revisions in a single supersession chain. Reassessment posts reversal/new entries referencing exact versions; it never changes past amounts. Reversal transactions lock the original entry and existing reversals, validate matching pool/currency/role and prevent over-reversal. Separate legitimate partial settlements have different source events and posting keys.

## Erasure and deletion actions

Default domain FK deletion is `NO ACTION`, deferred for authorized graph operations; no broad automatic cascading of insurance evidence. The relationship ledger lists nullable actor `SET NULL` exceptions and retained native Django cascade semantics. Ordinary users cannot delete referenced public originals or rewrite immutable primary keys. Authorized erasure is an explicit operation, not an ordinary cascading model delete.

For selective disclosure erasure: identify the assertion/content target, advance the owner's erasure generation and block affected jobs, enumerate `ContentCopy` and `Dependency` closure, then redact or erase payloads in messages, snapshots, model responses, decisions, chunks, caches, queue references and exports. Preserve unrelated assertions. Exact original private files containing the disclosure are erased as originals; if an authorized redacted derivative is retained it gets a different hash and cannot masquerade as the original. Historical citations become explicitly unavailable rather than exposing removed content. Minimal lineage tombstones retain no erased medical value.

For account purge: authorize and record the request, stop publication by generation, complete scoped payload erasure and copy-store receipts, process valid bounded retention holds separately, delete owned relationship rows in dependency order within deferred-constraint transactions, then purge/anonymize the account according to the approved receipt/retention policy. Native sessions and user privilege joins are handled with their native semantics. Public originals and other customers' records survive. Required customer-owner references are never set to NULL to turn private records public. Reviewer identity minimization follows the individual relationship actions.

Retention duration and legally required holds are unresolved policy decisions; the design provides explicit scope/basis/approver/expiry without inventing a universal retention period. Backups require access restriction, expiration and deletion tombstones applied before any restored data becomes accessible. Old workers, reimports and index rebuilds check erasure generation/tombstones to prevent resurrection. A deletion remains failed or held until every required storage-class receipt is verified. Runtime proof of these operations belongs to the approved implementation phase.

## Revision 3 clarifications from review

Global targets without an `owner_id` column use an ordinary FK and role check. Only genuinely mixed/owned targets use owner predicates; the relationship ledger no longer references nonexistent global-owner columns. Nullable mixed rows pointing to a private parent additionally require a nonnull source owner whenever that FK is present. Content-copy endpoints must match the copy row's scope/owner exactly; a private disclosure copy cannot target a public artifact. Dependency output identity and rule/table/source containment also use exact scope equality where listed.

Native Django ORM `on_delete` behavior is listed separately from physical SQL FK action. Existing native physical constraints remain verified/preserved at migration rehearsal; Django 5.2's ORM cascade is not described as an installed SQL ON DELETE CASCADE. Domain graph erasure still uses the explicit service and deferred NO ACTION constraints.

Fact assertions have explicit subject kind and mutually exclusive person/contract/provider subject FKs; conversation is always the context and is the subject only for conversation predicates. An imported assertion records its exact `source_assertion_id` and grant. Superseding a fact within the destination never overwrites its source conversation. Branch accessibility may be observed without an insurer; network/exclusion/authorization observations require the appropriate insurer and scope.

Legacy source payloads have an `archive_blob_id`. `OriginalBlob.content_role` distinguishes acquired originals, preserved legacy-record archives and processing derivatives. Only acquired originals can establish contractual source truth; neither a migration archive nor parser output qualifies as an independently inventoried insurer original.


## Original locations and link lineage (revision 4)

Every EvidenceSpan identifies its DocumentRevision and immutable original hash. PDF citations require a real DocumentPage and matching bounding box in unrotated PDF points, with the page rotation recorded. HTML uses a versioned selector, occurrence and explicit text/attribute interpretation; JSON uses an RFC 6901 pointer and scalar/canonical-value interpretation; plain text uses an encoding and half-open byte range. Non-PDF citations have no page_id or bbox. A resolver must reject missing/ambiguous selectors, malformed decoding, out-of-range bytes and media mismatches; lexical resolution does not establish contractual entailment. Linked clauses remain explicit EvidenceContext references. HTML original views render escaped text or allow an authorized download; original scripts never execute in the adviser origin.

SourceLocator retains unique owner/URL identity. SourceLinkObservation records every exact discovery occurrence with the preserved parent response, original locator, raw href, observed label, row identity and time. Acquisition may select one observation as its initiating provenance while retaining all other origins. Parent and target scope must match the observation. A deferred cross-row validator verifies blob identity, URL resolution and per-attempt target consistency; immutable parent originals cannot change beneath the observation. A mismatched CMS row title and attachment filename remain separate observed facts. Correcting an observation adds a superseding record; it does not rewrite the source or prior attempt. Unknown provenance remains unresolved, not synthesized.

Account.preferred_route_id and preferred_route_updated_at preserve the pilot's AIPreference without selecting a replacement model. Preference is not qualification: a disabled/unqualified preferred route produces an explicit operational result until an authorized user selects an eligible route. No fallback or preference reset follows migration.


## Claim events, documents and payments added in discussion revision 5

A treatment episode and accepted contract can have a hospitalization notice before a submitted claim exists. `ClaimEvent` retains that episode/contract identity and records its sender, recipient, occurred time and evidence separately from creation time. Other claim events require the claim identity. A correction appends a successor and invalidates dependent calculations; it does not overwrite the earlier communication.

`ClaimDocumentRequirement` records each conditional obligation, its original rule, necessity and accepted original/copy form. `ClaimDocumentReceipt` binds the exact submitted artifact to a recipient receipt event and a specific requirement revision. Adviser upload, insurer receipt, document acceptance and completion of the necessary set are distinct facts. A `documentation_complete` event requires a reviewed requirement/receipt set and authority; an empty upload queue or a count of files cannot establish it. Conditional original-document waivers and certified copies from another insurer retain their exact evidence.

`ClaimPayment` records actual payment independently from claim admissibility or an answer’s calculated ceiling. Its payment event, amount, currency, accounting kind and source evidence allow partial payments, recovery and reversal to remain distinguishable. Private events, documents and payments enforce matching owner, claim, episode and contract identities. Erasure traverses their artifacts and copied payloads through the existing dependency/copy lifecycle.

## Reproducible knowledge denominators added in discussion revision 5

`RuleInventoryItem` retains the original occurrence. `InventoryRevision` seals a particular original manifest and independent counting protocol. `InventoryMembership` states the occurrence’s disposition and count weight for that revision: included atomic instances count once, structural/excluded instances count zero, and unresolved candidates retain an unknown weight. The 589 Star and 792 New India candidate counts are not silently promoted into a measured denominator.

`InventoryLineage` records split, merge, qualification and restatement decisions without deleting the former segmentation. Shared source cells expanded into several configurations must retain that expansion policy; adjacent qualifier rows cannot become independent covered procedures by default. Source closure, relevant scope and segmentation must be settled before a measured denominator is sealed.

`RuleInventorySupport` is an immutable review linking an inventory member to the represented rule and exact supporting review. `CoverageReportSupport` pins which reviewed support records contributed to a historical report. The report counts each included member once even when several rules support it, and retains its exact sealed inventory revision. A later segmentation or support correction creates a new report; it cannot change an earlier percentage retroactively. This public original-inventory accounting contains no private benchmark questions or solutions.
