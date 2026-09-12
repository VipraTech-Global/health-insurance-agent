# Proposed entity and field dictionary — discussion revision 6

**Proposal only; not approved for implementation.** Every field below has purpose, type, required status, default, units, allowed values, validation, example and requirement trace. Examples may be illustrative; the typed JSON companion retains exact provenance and relationship enforcement metadata.

## Account

Authentication principal retained compatibly with the pilot. Access: framework_private. Basis: OPS-01, OPS-06.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| email | varchar(254) required | none / None | Login identity; Unique exact existing email; no silent normalization merge | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| password | varchar(128) required | none / None | Django encoded password and algorithm marker; Preserve encoded bytes; never hash an existing hash | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-06"] |
| last_login | instant optional | NULL / instant | Last successful login; UTC; preserve legacy value | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_superuser | boolean required | false / None | Global administration privilege; Authorized changes only | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_staff | boolean required | false / None | Administration interface access; Authorized changes only | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_active | boolean required | true / None | Whether login is permitted; Deleted account cannot be active | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| first_name | varchar(150) required | empty string / None | Optional display given name; No medical use | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| last_name | varchar(150) required | empty string / None | Optional display surname; No insured identity inference | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| date_joined | instant required | now / instant | Original account creation; Preserve during migration | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| deleted_at | instant optional | NULL / instant | Deletion completion marker; No retained personal content after completed deletion without hold | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| erasure_generation | bigint required | 0 / None | Fence work started before erasure; Monotonic; workers compare before storing/publishing | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "OPS-02"] |
| preferred_route_id | fk:ModelRoute optional | NULL / None | Preserved user-selected AI route revision; Selection retained even if route disabled; ordinary users may invoke only separately qualified active route; never auto-fallback | null | No authentic private or generated identity inspected; synthetic fixture required. | ["OPS-04", "OPS-06"] |
| preferred_route_updated_at | instant optional | NULL / instant | When the user preference last changed; Preserve pilot AIPreference.updated_at; not route qualification time | null | No authentic private or generated identity inspected; synthetic fixture required. | ["OPS-04", "OPS-06"] |

Constraints: email unique; id immutable.
Indexes: email unique B-tree.

## Person

A person described by one account; may be buyer, insured or neither. Access: private. Basis: CUS-01, CUS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| display_name | varchar(200) optional | NULL / None | Customer supplied label; Not a deduplication key | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |
| local_key | varchar(80) required | none / None | Stable account-local conversational identity; Unique within owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |
| identity_status | enum required | unconfirmed / None | Whether conversational subject is resolved; unconfirmed,confirmed,merged,tombstoned | unconfirmed,confirmed,merged,tombstoned | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |
| merged_into_id | fk:Person optional | NULL / None | Explicit reviewed duplicate-person merge; Same owner; no cycles; preserve old identity | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |
| identity_evidence_id | fk:EvidenceSpan optional | NULL / None | Documentary basis if identity verified; Same owner or public; absent is not verified | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |

Constraints: unique(owner_id,local_key); merge cannot target self; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; merged_into_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,local_key.

## Relationship

Dated directional relationship assertion, independent of enrolment. Access: private. Basis: CUS-01, INS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| from_person_id | fk:Person required | none / None | Person whose relationship is described; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| to_person_id | fk:Person required | none / None | Related person; Same owner; not self | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| relationship | enum required | none / None | Legal or household relationship; spouse,parent,child,parent_in_law,guardian,other | spouse,parent,child,parent_in_law,guardian,other | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| assertion_id | fk:FactAssertion required | none / None | Provenance and confirmation of relationship; Same owner; matching subjects | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| valid_during | daterange optional | NULL / None | Period relationship is asserted to hold; Explicit interval boundaries; NULL means unknown interval | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |

Constraints: different persons; owner composite FKs; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; from_person_id IS NULL OR owner_id IS NOT NULL; to_person_id IS NULL OR owner_id IS NOT NULL; assertion_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,from_person_id,to_person_id; GiST valid_during.

## Conversation

Persistent conversation and its current accepted state. Access: private. Basis: CUS-02, OPS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| title | varchar(200) required | empty string / None | History list label; No automatic sensitive diagnosis in title | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| current_fact_revision | bigint required | 0 / None | Optimistic concurrency version; Nonnegative; monotonic on accepted changes | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| current_snapshot_id | fk:FactSnapshot optional | NULL / None | Current immutable accepted facts; Same conversation and matching revision | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| status | enum required | open / None | Conversation lifecycle; open,archived,deleting,deleted | open,archived,deleting,deleted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| updated_at | instant required | now / instant | Most recent durable interaction; Monotonic per transaction | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| preferred_language | varchar(35) optional | NULL / None | Customer communication locale; BCP47; not a medical fact | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| fact_reuse_policy | enum required | none / None | Whether prior conversation facts may be reused; none,explicit_grants_only | none,explicit_grants_only | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02", "OPS-01"] |

Constraints: unique(id,owner_id); snapshot pointer matches conversation and revision; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; current_snapshot_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,updated_at DESC.

## Message

Immutable submitted or published conversational content. Access: private. Basis: CUS-02, OPS-02, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Parent history; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| sequence | bigint required | none / None | Durable ordering in conversation; Positive; allocated under conversation lock | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| role | enum required | none / None | Speaker role; customer,assistant,system_notice | customer,assistant,system_notice | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| content | text required | none / None | Exact displayed message; Size bound proposed 100000 characters; encrypted storage | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| origin | enum required | none / None | How content entered history; user,validated_answer,operational_notice,legacy_import | user,validated_answer,operational_notice,legacy_import | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| client_request_id | uuid optional | NULL / None | Submission idempotency identifier; Unique per owner when nonnull | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| payload_sha256 | char(64) required | none / None | Hash of canonical submitted payload; Lowercase SHA256; compare duplicate request contents | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| submitted_at | instant required | none / instant | Original receipt time; UTC; not rewritten on retry | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| turn_id | fk:Turn optional | NULL / None | Processing turn producing or consuming message; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| answer_id | fk:Decision optional | NULL / None | Published answer artifact; Same conversation; assistant output only | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| redacted_at | instant optional | NULL / instant | Content erasure event; Content and copies cleared atomically or deletion job blocks access | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |

Constraints: unique(conversation_id,sequence); unique(owner_id,client_request_id) where nonnull; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; turn_id IS NULL OR owner_id IS NOT NULL; answer_id IS NULL OR owner_id IS NOT NULL.
Indexes: conversation_id,sequence; turn_id.

## FactAssertion

An immutable statement with a subject, provenance and uncertainty. Access: private. Basis: CUS-02, CUS-03, INS-06.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Context in which statement was obtained; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| person_id | fk:Person optional | NULL / None | Person to whom fact applies; Required for person-scoped predicate; never infer buyer=insured | null | Intentionally no real customer/authentication values inspected or included. | ["CUS-02", "CUS-03", "INS-06"] |
| predicate | varchar(100) required | none / None | Versioned fact concept identifier; Registered predicate; determines value kind and subject requirements | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| value | json:TypedValueV1 required | none / None | Typed fact, unknown or explicit not applicable; Strict schema; quantity units required; no NaN or implicit null semantics | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| source_kind | enum required | none / None | Authority and origin of assertion; customer_statement,document,model_proposal,case_stipulation,legacy_unresolved,authorized_import | customer_statement,document,model_proposal,case_stipulation,legacy_unresolved,authorized_import | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| source_message_id | fk:Message optional | NULL / None | Exact conversational provenance; Same conversation; required for customer statement | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| source_evidence_id | fk:EvidenceSpan optional | NULL / None | Original supporting document span; Required for document origin; compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| confirmation | enum required | unconfirmed / None | Acceptance status; unconfirmed,confirmed,disputed,retracted | unconfirmed,confirmed,disputed,retracted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| valid_during | json:TemporalExtentV1 required | none / None | When statement applies; Date/instant/unknown granularity; bounds explicit | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| recorded_revision | bigint required | none / None | Conversation revision in which assertion entered; Nonnegative | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| supersedes_id | fk:FactAssertion optional | NULL / None | Previous assertion corrected by this one; Same owner, subject and predicate; no cycles | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| confirmation_message_id | fk:Message optional | NULL / None | Customer confirmation of a proposed interpretation; Same conversation; no assistant self-confirmation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "CUS-03", "INS-06"] |
| predicate_definition_id | fk:FactPredicate required | none / None | Exact vocabulary revision; Predicate string must match definition key | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02"] |
| import_grant_id | fk:ConversationReuseGrant optional | NULL / None | Authorized source-to-destination reuse; Required for authorized_import source; matching conversations and selected assertion | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02", "OPS-01"] |
| subject_kind | enum required | none / None | Explicit subject identity independent of conversational context; person,conversation,contract,provider,contract_bundle | person,conversation,contract,provider,contract_bundle | No authentic private value inspected; see synthetic worked examples. | ["CUS-02"] |
| subject_contract_id | fk:PolicyContract optional | NULL / None | Contract that the assertion describes; Same owner; required only for subject_kind contract | null | No authentic private value inspected; see synthetic worked examples. | ["CUS-02"] |
| subject_provider_id | fk:Provider optional | NULL / None | Exact branch that the assertion describes; Public provider identity; required only for subject_kind provider | null | No authentic private value inspected; see synthetic worked examples. | ["CUS-02", "OBS-02"] |
| source_assertion_id | fk:FactAssertion optional | NULL / None | Exact original assertion authorized for cross-conversation import; Same owner; source conversation named by grant; not supersedes_id | null | No authentic private value inspected; see synthetic worked examples. | ["CUS-02", "OPS-01"] |
| subject_bundle_id | fk:ContractBundle optional | NULL / None | Owned package concerned by a receipt, transaction-kind or membership assertion; Set exactly for subject_kind contract_bundle; all other subject FKs NULL; preserve subject on correction | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: append-only except authorized erasure; source checks by source_kind; supersession preserves prior assertion; Accepted active fact state comes only from SnapshotFact; confirmation history remains append-only or separate replacement assertion; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; predicate subject_kind equals assertion subject_kind;authorized_import requires source_assertion_id and import_grant_id, matching source/destination/granted assertion;supersedes remains within destination conversation; source_assertion_id allowed only for authorized_import;source/import lineage acyclic;erasure of source invalidates copied payloads; conversation_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL; source_message_id IS NULL OR owner_id IS NOT NULL; supersedes_id IS NULL OR owner_id IS NOT NULL; confirmation_message_id IS NULL OR owner_id IS NOT NULL; import_grant_id IS NULL OR owner_id IS NOT NULL; subject_contract_id IS NULL OR owner_id IS NOT NULL; source_assertion_id IS NULL OR owner_id IS NOT NULL; Exactly one subject branch: person => person_id only; contract => subject_contract_id only; provider => subject_provider_id only; contract_bundle => subject_bundle_id only; conversation => all four subject FKs NULL and conversation_id is subject. Supersession preserves subject identity and predicate..
Indexes: conversation_id,recorded_revision; owner_id,person_id,predicate.

## FactSnapshot

Immutable selection of accepted facts at a conversation revision. Access: private. Basis: CUS-02, DEC-01, OPS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Owning conversation; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01", "OPS-02"] |
| revision | bigint required | none / None | Accepted fact revision; Nonnegative | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01", "OPS-02"] |
| content_sha256 | char(64) required | none / None | Canonical selected assertion digest; Verified against ordered snapshot members | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01", "OPS-02"] |
| previous_id | fk:FactSnapshot optional | NULL / None | Prior accepted state; Same conversation; lower revision | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01", "OPS-02"] |
| sealed_at | instant required | none / instant | Time immutable snapshot was completed; No members may change after sealing | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01", "OPS-02"] |

Constraints: unique(conversation_id,revision); immutable sealed content; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; previous_id IS NULL OR owner_id IS NOT NULL.
Indexes: conversation_id,revision DESC.

## SnapshotFact

Membership of an assertion in a fact snapshot. Access: private. Basis: CUS-02, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| snapshot_id | fk:FactSnapshot required | none / None | Snapshot selection; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01"] |
| assertion_id | fk:FactAssertion required | none / None | Selected assertion; Same conversation; confirmed or explicitly disputed state | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01"] |
| resolution | enum required | none / None | How conflicting assertions are represented; accepted,unresolved_conflict | accepted,unresolved_conflict | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01"] |
| conflict_key | varchar(160) optional | NULL / None | Groups incompatible assertions without discarding them; Required when unresolved_conflict | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "DEC-01"] |

Constraints: unique(snapshot_id,assertion_id); one accepted value per scalar subject/predicate; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; snapshot_id IS NULL OR owner_id IS NOT NULL; assertion_id IS NULL OR owner_id IS NOT NULL.
Indexes: snapshot_id; assertion_id.

## DecisionIntent

A customer objective and required conditions, distinct from known facts. Access: private. Basis: CUS-01, CUS-03, RET-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Decision context; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-03", "RET-01"] |
| snapshot_id | fk:FactSnapshot required | none / None | Fact revision for this request; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-03", "RET-01"] |
| kind | enum required | none / None | Requested decision scope; purchase,comparison,claim_explanation,renewal,portability,clarification | purchase,comparison,claim_explanation,renewal,portability,clarification | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-03", "RET-01"] |
| requirements | json:IntentV1 required | none / None | Priorities and material dependencies; Typed persons, constraints, preferences and required fact predicates; no untyped arbitrary expressions | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-03", "RET-01"] |
| source_message_id | fk:Message required | none / None | Request provenance; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-03", "RET-01"] |

Constraints: immutable per fact revision; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; snapshot_id IS NULL OR owner_id IS NOT NULL; source_message_id IS NULL OR owner_id IS NOT NULL.
Indexes: conversation_id,snapshot_id.

## Insurer

Identified insurer and official discovery authority. Access: public. Basis: INS-01, INS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| code | varchar(80) required | none / None | Stable research roster identifier; Unique; original20 roster preserved | null | new-india (preserved20-insurer roster). | ["INS-01", "INS-04"] |
| legal_name | varchar(250) required | none / None | Insurer legal name; Original-backed; former names in alias records | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04"] |
| regulator_code | varchar(80) optional | NULL / None | Regulatory organization identifier; Unknown remains NULL | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04"] |
| status | enum required | unverified / None | Organization status; unverified,active,merged,closed,historical | unverified,active,merged,closed,historical | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04"] |
| successor_id | fk:Insurer optional | NULL / None | Evidenced organizational successor; No cycle; not automatic policy transfer | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04"] |

Constraints: code unique.
Indexes: code unique B-tree.

## SourceLocator

Official or linked location with approved acquisition scope. Access: mixed. Basis: INS-04, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| insurer_id | fk:Insurer optional | NULL / None | Publishing insurer where applicable; Regulator sources may omit | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| url | text required | none / None | Exact discovered URL; HTTPS/HTTP only; preserve query; length bound 8192 | null | {"value": "https://acko-cms.ackoassets.com/Policy_Wordings_ACKO_Health_III_Platinum_43d3abfe1b.pdf", "authentic": true, "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page 1 and its preserved acquisition record; proposed association remains version-qualified"} | ["INS-04", "OPS-03"] |
| kind | enum required | none / None | Expected original type; register,wording,cis,prospectus,endorsement,regulation,quote,provider_list,unknown | register,wording,cis,prospectus,endorsement,regulation,quote,provider_list,unknown | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| linking_observation_id | fk:Acquisition optional | NULL / None | First known parent acquisition retained as a legacy provenance hint; Same scope/owner; immutable first-known hint only; all later and concurrent origins retained in SourceLinkObservation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| approved_host | varchar(253) required | none / None | Host authorized for this fetch; Exact allowlist; redirects separately checked | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| scope | enum required | none / None | Public corpus versus private document; public,private | public,private | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| last_checked_at | instant optional | NULL / instant | Latest completed acquisition check; Not proof document validity | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |

Constraints: scope public iff owner NULL; unique(owner_id,url) NULLS NOT DISTINCT; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: insurer_id,kind; last_checked_at.

## Acquisition

One durable fetch attempt, including access failures and changed bytes. Access: mixed. Basis: INS-04, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| locator_id | fk:SourceLocator required | none / None | Requested original location; Same scope/owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| started_at | instant required | none / instant | Persisted attempt start before network request; UTC | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| completed_at | instant optional | NULL / instant | Fetch completion; At or after start | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| status | enum required | queued / None | Acquisition state; queued,running,stored,not_modified,access_failed,invalid_content,interrupted | queued,running,stored,not_modified,access_failed,invalid_content,interrupted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| http_status | smallint optional | NULL / None | Actual HTTP response status; 100..599 or NULL if no response | null | {"value": 200, "authentic": true, "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page 1 and its preserved acquisition record; proposed association remains version-qualified"} | ["INS-04", "OPS-03"] |
| final_url | text optional | NULL / None | Observed post-redirect URL; Never substitute for requested URL | null | {"value": "https://acko-cms.ackoassets.com/Policy_Wordings_ACKO_Health_III_Platinum_43d3abfe1b.pdf", "authentic": true, "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page 1 and its preserved acquisition record; proposed association remains version-qualified"} | ["INS-04", "OPS-03"] |
| redirect_chain | json:RedirectChainV1 required | empty array / None | Dated redirect observations; Bounded ordered URL/status list; no secret headers | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| blob_id | fk:OriginalBlob optional | NULL / None | Preserved actual response bytes; Store error bodies where appropriate; compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| error_code | varchar(100) optional | NULL / None | Explicit transport/content failure; Safe bounded code, no credentials | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| response_metadata | json:HttpMetadataV1 required | empty object / None | Selected headers and media identity; Allowlisted content type, ETag, Last-Modified, length only | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| source_link_observation_id | fk:SourceLinkObservation optional | NULL / None | Exact discovery observation used to initiate this attempt; Same scope/owner; observation.target_locator_id equals acquisition.locator_id; parent acquisition differs from current attempt | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04", "OPS-03"] |

Constraints: stored requires blob and completion; failed states require error code; chronology check; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Stored response blob has content_role acquired_original and exact matching source scope; A source_link_observation_id, when present, must target this locator and predate attempt; never replace the parent attempt or other origins; direct seeds retain NULL with explicit seed provenance.
Indexes: locator_id,started_at DESC; status,started_at.

## OriginalBlob

Content-addressed original bytes with private access and deletion ownership. Access: mixed. Basis: INS-04, OPS-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| sha256 | char(64) required | none / None | Cryptographic byte identity; Lowercase hex verified on write/read | null | {"value": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb", "authentic": true, "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page 1 and its preserved acquisition record; proposed association remains version-qualified"} | ["INS-04", "OPS-01"] |
| storage_key | varchar(500) required | none / None | Private object storage location; Unique opaque key; never expose direct filesystem path | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-01"] |
| byte_size | bigint required | none / None | Stored original length; Nonnegative | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-01"] |
| media_type | varchar(150) required | none / None | Detected actual media type; Not trusted URL extension | null | {"value": "application/pdf", "authentic": true, "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page 1 and its preserved acquisition record; proposed association remains version-qualified"} | ["INS-04", "OPS-01"] |
| scope | enum required | none / None | Access classification; public,private | public,private | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-01"] |
| availability | enum required | stored / None | Original retention state; stored,quarantined,erasure_pending,erased | stored,quarantined,erasure_pending,erased | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-01"] |
| verified_at | instant required | none / instant | Last successful hash verification; UTC | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-01"] |
| content_role | enum required | acquired_original / None | Distinguish originals from internal archives and derivatives; acquired_original,legacy_record_archive,processing_derivative | acquired_original,legacy_record_archive,processing_derivative | No authentic private value inspected; see synthetic worked examples. | ["INS-04", "OPS-03"] |

Constraints: unique(owner_id,sha256) NULLS NOT DISTINCT; public iff owner NULL; private dedup only within owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: sha256; owner_id,availability.

## DocumentRevision

Identified document edition bound to original bytes. Access: mixed. Basis: INS-02, INS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| blob_id | fk:OriginalBlob required | none / None | Exact original content; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| insurer_id | fk:Insurer optional | NULL / None | Original issuing insurer; Regulatory originals may omit | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| kind | enum required | unknown / None | Classified evidence role; wording,cis,prospectus,endorsement,schedule,proposal,regulation,notice,provider_list,quote,source_register,web_page,public_json,unrelated,unknown,medical_report,bill,claim_form,claim_correspondence,payment_receipt | wording,cis,prospectus,endorsement,schedule,proposal,regulation,notice,provider_list,quote,source_register,web_page,public_json,unrelated,unknown,medical_report,bill,claim_form,claim_correspondence,payment_receipt | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| title | text required | none / None | Printed title; Retain original text and language | null | {"value": "ACKO Health III (Platinum) – Policy Wordings", "authentic": true, "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page 1 and its preserved acquisition record; proposed association remains version-qualified"} | ["INS-02", "INS-04"] |
| language | varchar(35) optional | NULL / None | Printed language or multilingual code; BCP47 or undetermined | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| printed_identifiers | json:IdentifiersV1 required | empty array / None | All UINs, edition labels and conflicting footers; Each identifier retains span and status; never silently choose one | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| issued_on | date optional | NULL / calendar date | Printed issue/publication date; Original-supported only | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| supersedes_id | fk:DocumentRevision optional | NULL / None | Explicit previous edition; Same document lineage; evidence link required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| classification | enum required | unresolved / None | Medical scope assessment; medical_expense,supporting_mixed,nonmedical,out_of_roster,unresolved | medical_expense,supporting_mixed,nonmedical,out_of_roster,unresolved | {"value": "medical_expense", "authentic": true, "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page 1 and its preserved acquisition record; proposed association remains version-qualified"} | ["INS-02", "INS-04"] |
| classification_evidence_id | fk:EvidenceSpan optional | NULL / None | Original basis of classification; Points to this original or authoritative scope instrument | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |
| review_status | enum required | unreviewed / None | Original review completeness; unreviewed,partial,complete,conflicted | unreviewed,partial,complete,conflicted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04"] |

Constraints: document identity distinct from blob; supersession acyclic; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Insurer/regulator original evidence requires blob.content_role acquired_original;legacy archive or processing derivative cannot establish contractual truth or independent original denominator.
Indexes: insurer_id,kind; blob_id; classification,review_status.

## DocumentPage

Physical page identity and geometry independent of printed numbering. Access: mixed. Basis: INS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentRevision required | none / None | Exact edition; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04"] |
| physical_page | integer required | none / count | One-based PDF page ordinal; >=1; bounded by original page count | null | 21 | ["INS-04"] |
| printed_label | varchar(80) optional | NULL / None | Visible page label; May conflict with physical count | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04"] |
| width_pt | numeric(12,4) required | none / None | Original page width; Positive PDF points | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04"] |
| height_pt | numeric(12,4) required | none / None | Original page height; Positive PDF points | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04"] |
| rotation | smallint required | 0 / None | Original page orientation; 0,90,180,270 | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04"] |
| review_state | enum required | unread / None | Independent original-reading coverage; unread,text_read,visually_read,fully_inventoried,unresolved | unread,text_read,visually_read,fully_inventoried,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04"] |
| review_notes | text required | empty string / None | Tables, figures, footnotes and unread regions; Empty only when no notes required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04"] |

Constraints: unique(document_id,physical_page); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Only actual PDF pages may be represented; HTML/JSON/text evidence uses document-level OriginalLocatorV1 without fabricated page rows.
Indexes: document_id,physical_page.

## EvidenceSpan

Exact support with page geometry, context and review method. Access: mixed. Basis: INS-04, INS-05, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| page_id | fk:DocumentPage optional | NULL / None | Physical original page; Required only for PDF-region locator; same document_id, owner and physical page; NULL for HTML/JSON/text originals | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| section_label | varchar(200) optional | NULL / None | Printed section or table identifier; Preserve incorrect printed cross-reference separately | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| quote | text required | none / None | Exact original text or faithful visual transcription; Hash/geometry verified; no paraphrase passed as quote | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| bbox | json:BoundingBoxV1 optional | NULL / None | Original page location for citation highlight; Required for PDF-region locator and identical to original_locator.bbox; four PDF-point coordinates inside page; NULL for non-PDF | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| context | json:EvidenceContextV1 required | none / None | Surrounding clause, table headers, selectors and footnotes; Typed ordered context span references plus literal labels | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| method | enum required | none / None | How passage was read; native_text,manual_visual,ocr_verified,html_original,json_original,text_original | native_text,manual_visual,ocr_verified,html_original,json_original,text_original | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| verification | enum required | unverified / None | Original comparison status; unverified,lexically_verified,visually_verified,reviewed,failed | unverified,lexically_verified,visually_verified,reviewed,failed | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| transcription_sha256 | char(64) required | none / None | Stable quoted-content identity; Recompute on any transcription correction | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "DEC-01"] |
| document_id | fk:DocumentRevision required | none / None | Immutable document containing the exact passage; Same scope and owner; document original hash must match locator; all media types | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| original_locator | json:OriginalLocatorV1 required | none / None | Exact retrievable location in preserved original bytes; Typed PDF region, HTML element, JSON pointer or text range; hash and resolver version checked; no fabricated pages | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |

Constraints: append-only reviewed spans; bbox within page; context references same or connected originals; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; original_locator.blob_sha256 equals document.blob.sha256; locator kind matches actual media type; pdf_region requires page_id and bbox,matching page.document_id and physical_page;other locator kinds require page_id and bbox NULL and corresponding original method; exact quote must resolve using the stored decoder/resolver on immutable bytes;transcription_sha256 hashes UTF-8 quote;reviewed semantic support separate from lexical resolution.
Indexes: page_id,section_label; transcription_sha256.

## LegacyListing

Preserved identity of each acquired legacy catalogue listing. Access: public. Basis: INS-01, INS-04, OPS-06.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| original_key | varchar(500) required | none / None | Exact old listing path or ID; Unique; preserve all203 and order externally | null | {"value": "/health-insurance/acko/platinum-health/", "authentic": true, "source": "../registers/legacy-assessment-r5.json", "locator": "unchanged legacy listing identity; not new canonical product key"} | ["INS-01", "INS-04", "OPS-06"] |
| original_label | text required | none / None | Unmodified legacy display label; Never overwrite with matched product | null | {"value": "Platinum Health", "authentic": true, "source": "../registers/legacy-assessment-r5.json", "locator": "unchanged exact legacy label"} | ["INS-01", "INS-04", "OPS-06"] |
| insurer_id | fk:Insurer optional | NULL / None | Resolved roster insurer; NULL when ambiguous/outside roster | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04", "OPS-06"] |
| source_blob_id | fk:OriginalBlob optional | NULL / None | Preserved catalogue original; Public | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04", "OPS-06"] |
| scope_status | enum required | unresolved / None | Roster and product scope accounting; in_scope,outside_roster,nonmedical,historical_test,unresolved | in_scope,outside_roster,nonmedical,historical_test,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04", "OPS-06"] |
| scope_reason | text required | none / None | Evidence-based disposition explanation; Nonempty; accounting not complete reconciliation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-04", "OPS-06"] |

Constraints: original_key unique.
Indexes: insurer_id,scope_status.

## ListingCandidate

Dimension-specific reconciliation, with ambiguity retained. Access: public. Basis: INS-01, INS-02, INS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-02", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| listing_id | fk:LegacyListing required | none / None | Legacy identity being reconciled; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-02", "INS-04"] |
| product_id | fk:Product optional | NULL / None | Candidate family identity; NULL allowed only unresolved or exclusion | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-02", "INS-04"] |
| configuration_id | fk:Configuration optional | NULL / None | Candidate variant/options; Must belong to product when supplied | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-02", "INS-04"] |
| terms_id | fk:TermsRevision optional | NULL / None | Candidate actual edition; Must belong to product | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-02", "INS-04"] |
| identity_dimensions | json:ReconciliationV1 required | none / None | Family, variant, historical edition, bundle and applicability findings; Each dimension resolved/unresolved/conflicted/not_applicable with original spans and reason | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-02", "INS-04"] |
| status | enum required | candidate / None | Overall disposition; candidate,verified_dimension,fully_reconciled,excluded,unresolved | candidate,verified_dimension,fully_reconciled,excluded,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-02", "INS-04"] |
| reviewed_at | instant optional | NULL / instant | Last original-backed assessment; Fully reconciled requires all material dimensions resolved | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-02", "INS-04"] |

Constraints: no name-only automatic merge; full reconciliation requires evidence for all material dimensions; Family,variant,observed_source_revision,historical_version,complete_bundle,applicability assessed separately; unresolved Care Senior,Care Ultimate,Tata AIG Medicare Senior aliases cannot be auto-canonicalized.
Indexes: listing_id,status; product_id.

## Product

Insurer product family independent of versions and variants. Access: public. Basis: INS-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| insurer_id | fk:Insurer required | none / None | Primary catalogue/source organization; for a joint combi wrapper this is not an assertion of sole issuer. Each component retains its own issuing organization.; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01"] |
| canonical_name | varchar(250) required | none / None | Original-backed family name; Not globally unique | null | {"value": "ACKO Health III (Platinum)", "authentic": false, "derived_from_authentic_original": true, "normalization": "Remove document-role suffix from exact original title; proposed product heading, not a verbatim source label.", "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page1"} | ["INS-01"] |
| kind | enum required | unresolved / None | Insurance benefit class; medical_indemnity,fixed_benefit,hybrid,addon,unresolved | medical_indemnity,fixed_benefit,hybrid,addon,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01"] |
| identity_span_id | fk:EvidenceSpan required | none / None | Original supporting identity; Public | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01"] |
| lifecycle | enum required | unresolved / None | Product family lifecycle; open,withdrawn,renewal_only,historical,unresolved | open,withdrawn,renewal_only,historical,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01"] |
| advice_scope | enum required | unresolved / None | Catalogue scope distinct from benefit class and package structure; selected_medical,medical_support,nonmedical_reference,excluded,unresolved | selected_medical,medical_support,nonmedical_reference,excluded,unresolved | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: no unique name assumption; identity anchored to insurer original; nonmedical_reference products are available only for evidenced package identity/consequences; exclude from medical recommendations and selected-insurer knowledge denominator. Referenced life issuer does not enlarge the fixed20-insurer roster.; A joint combi is explicitly identified through source-backed component issuer identities; a missing or conflicting issuer blocks complete package identification..
Indexes: insurer_id,canonical_name.

## TermsRevision

An immutable legal terms edition, even when UIN stays unchanged. Access: public. Basis: INS-02, INS-05.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| product_id | fk:Product required | none / None | Product family; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-05"] |
| revision_key | varchar(120) required | none / None | Internal exact terms identity; Unique within product; not UIN alone | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-05"] |
| uin | varchar(100) optional | NULL / None | Printed product identifier where resolved; Conflicts retained in DocumentRevision and RuleIssue | null | {"value": "ACKHLIP27040V012627", "authentic": true, "source": "../registers/document-scope-r5.json", "locator": "cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb physical page 1 and its preserved acquisition record; proposed association remains version-qualified"} | ["INS-02", "INS-05"] |
| edition_label | varchar(200) optional | NULL / None | Printed edition marker; Acquisition date not edition | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-05"] |
| state | enum required | draft / None | Curated edition lifecycle; draft,reviewed,published,superseded,blocked | draft,reviewed,published,superseded,blocked | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-05"] |
| supersedes_id | fk:TermsRevision optional | NULL / None | Prior known terms revision; Same product; acyclic | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-05"] |
| bundle_sha256 | char(64) optional | NULL / None | Digest of complete selected governing originals; Required before publication | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-05"] |
| applicability | json:ApplicabilityV1 required | none / None | Issue/renewal/treatment events and boundaries selecting terms; Strict typed predicate; unknown bounds block affected use | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-05"] |

Constraints: unique(product_id,revision_key); publication requires closed material dependencies.
Indexes: product_id,uin; state.

## TermsDocument

Role and precedence evidence of a document in a terms bundle. Access: public. Basis: INS-02, INS-04, INS-05.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| terms_id | fk:TermsRevision required | none / None | Terms edition; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04", "INS-05"] |
| document_id | fk:DocumentRevision required | none / None | Exact component original; Public | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04", "INS-05"] |
| role | enum required | none / None | Contractual role; base_wording,cis,prospectus,regulatory_modification,endorsement,referenced_schedule,other_dependency | base_wording,cis,prospectus,regulatory_modification,endorsement,referenced_schedule,other_dependency | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04", "INS-05"] |
| mandatory | boolean required | true / None | Whether bundle requires component; False only with recorded scope reason | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04", "INS-05"] |
| scope | json:ApplicabilityV1 required | none / None | Component applicability; No universal latest-document priority | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04", "INS-05"] |
| precedence_span_id | fk:EvidenceSpan optional | NULL / None | Express controlling wording; NULL means no priority proven | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-04", "INS-05"] |

Constraints: unique(terms_id,document_id,role).
Indexes: terms_id,mandatory; document_id.

## Configuration

Offered variant and option combination before personal acceptance. Access: public. Basis: INS-01, INS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| terms_id | fk:TermsRevision required | none / None | Applicable edition; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| variant_code | varchar(120) required | none / None | Exact variant identity; Original-backed; Silver and Gold distinct | null | Gold; Star Super Surplus Floater original SHAHLIP22034V062122. | ["INS-01", "INS-03"] |
| label | varchar(200) required | none / None | Customer-facing variant name; No implied coverage | null | {"value": "Platinum", "authentic": true, "source": "../registers/legacy-assessment-r5.json", "locator": "Oriental Happy Family Floater original e1cb2183141818a1215529947f4c9758a3da80204dec937235cf713e84084459 pages 7 and 34; no universal plan code inferred"} | ["INS-01", "INS-03"] |
| selection | json:ConfigurationV1 required | none / None | SI, deductible, room category and allowed option selectors; Typed quantities and stable option IDs; versioned schema | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| selection_sha256 | char(64) required | none / None | Canonical configuration identity; Unique within terms | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| availability | json:ApplicabilityV1 required | none / None | New-sale/renewal dates, territory and offered people; Unresolved availability not exclusion | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| identity_span_id | fk:EvidenceSpan required | none / None | Original selector support; Public | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |

Constraints: unique(terms_id,selection_sha256).
Indexes: terms_id,variant_code; availability GIN for supported exact filters.

## ConfigurationOption

A selectable add-on, rider or election with its own terms. Access: public. Basis: INS-01, INS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| configuration_id | fk:Configuration required | none / None | Base configuration; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| option_terms_id | fk:TermsRevision required | none / None | Exact optional terms; May refer to separate add-on product | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| code | varchar(120) required | none / None | Stable option selector; Unique within configuration | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| selection_kind | enum required | none / None | Selection behavior; optional,mandatory,incompatible_group | optional,mandatory,incompatible_group | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |
| conditions | json:ApplicabilityV1 required | none / None | Allowed people, dates, waits and incompatibilities; Dependencies explicit; availability is not selection | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-01", "INS-03"] |

Constraints: unique(configuration_id,code).
Indexes: configuration_id.

## PolicyContract

A customer policy relationship; proposed cover remains a separate status. Access: private. Basis: INS-03, INS-07, INS-08.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| policy_number | varchar(200) optional | NULL / None | Issued identifier; Encrypted; not globally unique | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| insurer_id | fk:Insurer required | none / None | Issuing insurer; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| proposer_id | fk:Person optional | NULL / None | Named proposer; Same owner; unknown distinct from buyer | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| payer_id | fk:Person optional | NULL / None | Premium payer; Same owner; need not be insured | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| kind | enum required | none / None | Individual or group relationship; individual,floater,group_member | individual,floater,group_member | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| status | enum required | proposed / None | Contract acceptance state; proposed,offered,accepted,in_force,expired,cancelled,declined,unresolved | proposed,offered,accepted,in_force,expired,cancelled,declined,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| acceptance_span_id | fk:EvidenceSpan optional | NULL / None | Issuer acceptance evidence; Required before asserted acceptance | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| group_master_reference | varchar(250) optional | NULL / None | Employer/master policy identifier; Group member only; not member-cover proof | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |

Constraints: owner protected; status assertion requires evidence; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; proposer_id IS NULL OR owner_id IS NOT NULL; payer_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,insurer_id; owner_id,status.

## ContractRevision

Exact selected and individually endorsed terms for one contract interval. Access: private. Basis: INS-02, INS-03, INS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_id | fk:PolicyContract required | none / None | Owned policy; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| revision | integer required | none / count | Contract revision sequence; Positive | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| configuration_id | fk:Configuration required | none / None | Selected public variant; No automatic latest terms | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| valid_during | daterange required | none / None | Coverage applicability interval; Explicit lower/upper bounds; no inferred midnight coverage rule | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| issued_at | instant optional | NULL / instant | Insurer issue event; Original-supported | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| received_at | instant optional | NULL / instant | Customer receipt event for rights clocks; Independent of issuance | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| schedule_document_id | fk:DocumentRevision optional | NULL / None | Personal issued schedule; Same owner; required for verified in-force configuration | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| selection | json:AcceptedSelectionV1 required | none / None | Accepted options, person scope and sums; Strict IDs and evidence; distinguish unknown option status | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| status | enum required | unverified / None | Applicability assessment; unverified,verified,conflicted,superseded | unverified,verified,conflicted,superseded | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| previous_id | fk:ContractRevision optional | NULL / None | Prior accepted revision; Same contract; acyclic | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |

Constraints: unique(contract_id,revision); overlap allowed only with explicit transition/endorsement scope resolution; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; contract_id IS NULL OR owner_id IS NOT NULL; previous_id IS NULL OR owner_id IS NOT NULL.
Indexes: contract_id,revision; GiST valid_during.

## ContractMember

Actual named insured membership and individual commencement. Access: private. Basis: CUS-01, INS-03, INS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_revision_id | fk:ContractRevision required | none / None | Issued revision; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| person_id | fk:Person required | none / None | Insured person; Same owner | null | Intentionally no real customer/authentication values inspected or included. | ["CUS-01", "INS-03", "INS-07"] |
| role | enum required | none / None | Membership role; self,spouse,child,parent,other | self,spouse,child,parent,other | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| valid_during | daterange required | none / None | Member coverage interval; Birth, addition, termination and renewal distinguished | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| membership_span_id | fk:EvidenceSpan optional | NULL / None | Member certificate/schedule proof; Required for verified membership | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| status | enum required | unverified / None | Membership certainty; proposed,verified,unverified,terminated | proposed,verified,unverified,terminated | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| member_identifier | varchar(160) optional | NULL / None | Insurer employee/member certificate ID; Encrypted; owner-scoped | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |

Constraints: no overlapping duplicate verified membership for same revision/person/scope; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; contract_revision_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: contract_revision_id,person_id; GiST valid_during.

## IndividualTerm

Accepted underwriting modification scoped to people and benefits. Access: private. Basis: INS-03, INS-05, INS-06.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_revision_id | fk:ContractRevision required | none / None | Personal configuration; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| person_id | fk:Person optional | NULL / None | Affected insured if person-specific; Required when rule scope is person | null | Intentionally no real customer/authentication values inspected or included. | ["INS-03", "INS-05", "INS-06"] |
| kind | enum required | none / None | Individual modification; exclusion,copay,loading,waiver,waiting_change,other_endorsement | exclusion,copay,loading,waiver,waiting_change,other_endorsement | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| rule_body | json:RuleV1 required | none / None | Typed conditional personal effect; Must identify override target and exact scope | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| status | enum required | proposed / None | Acceptance of personal term; proposed,offered,accepted,rejected,unresolved | proposed,offered,accepted,rejected,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| evidence_span_id | fk:EvidenceSpan required | none / None | Original offer/accepted endorsement; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| valid_during | daterange required | none / None | Effective term interval; Must intersect covered membership | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |

Constraints: accepted modification requires issuer evidence and accepted configuration; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; contract_revision_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: contract_revision_id,person_id,kind.

## CoverageLayer

Original, enhanced, bonus or restored cover with separate clocks. Access: private. Basis: INS-07, CAL-03, CAL-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_revision_id | fk:ContractRevision required | none / None | Personal policy interval; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| person_id | fk:Person optional | NULL / None | Individual layer subject; NULL for shared pool; Scope required in limit_scope | null | Intentionally no real customer/authentication values inspected or included. | ["INS-07", "CAL-03", "CAL-04"] |
| kind | enum required | none / None | Cover origin; base,enhancement,bonus,recharge,restoration | base,enhancement,bonus,recharge,restoration | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| amount | json:QuantityV1 required | none / None | Nominal cover for this layer; Money or dependent expression; not headline total | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| inception | date optional | NULL / calendar date | Layer clock start; Unknown retained | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| limit_scope | json:LimitScopeV1 required | none / None | Person/family/year/body-part/benefit scope; Explicit reset and member identity | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Issued layer/bonus evidence; Unverified status if absent | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| status | enum required | unverified / None | Layer validity; stipulated,unverified,verified,exhausted | stipulated,unverified,verified,exhausted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |

Constraints: layer amounts nonnegative where finite; no inferred sum-insured consumption from copay; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; contract_revision_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: contract_revision_id,kind,person_id.

## ContinuityCredit

Accepted prior history credited to an amount, person and benefit. Access: private. Basis: INS-07, INS-08.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| layer_id | fk:CoverageLayer required | none / None | Receiving cover layer; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| prior_contract_id | fk:PolicyContract required | none / None | Historical source contract; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| person_id | fk:Person required | none / None | Person receiving credit; Same owner | null | Intentionally no real customer/authentication values inspected or included. | ["INS-07", "INS-08"] |
| credit_kind | enum required | none / None | Specific continuity measure; ped_wait,specific_wait,moratorium,bonus | ped_wait,specific_wait,moratorium,bonus | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| period | json:DurationV1 required | none / None | Accepted credited duration; Calendar versus elapsed units explicit | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| amount_scope | json:QuantityV1 required | none / None | Cover extent receiving credit; Money; unknown cannot mean whole SI | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| accepted_span_id | fk:EvidenceSpan optional | NULL / None | Receiving insurer acceptance; Required when status accepted | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| status | enum required | requested / None | Credit assessment state; requested,accepted,disputed,unresolved | requested,accepted,disputed,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |

Constraints: no blanket personless continuity boolean; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; layer_id IS NULL OR owner_id IS NOT NULL; prior_contract_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: layer_id,person_id,credit_kind.

## PolicyEvent

Dated policy and rights events with original receipt provenance. Access: private. Basis: INS-08, INS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_id | fk:PolicyContract optional | NULL / None | Policy relationship; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| kind | enum required | none / None | Event type; issue,receipt,renewal_due,premium_paid,instalment_due,cancellation_notice,withdrawal_notice,port_request_received,port_information_received,group_exit,claim_notified,cancellation_enquiry,cancellation_requested,cancellation_received,cancellation_accepted,coverage_terminated,refund_calculated,refund_paid,refund_received,cancellation_declined,refund_reversed | issue,receipt,renewal_due,premium_paid,instalment_due,cancellation_notice,withdrawal_notice,port_request_received,port_information_received,group_exit,claim_notified,cancellation_enquiry,cancellation_requested,cancellation_received,cancellation_accepted,coverage_terminated,refund_calculated,refund_paid,refund_received,cancellation_declined,refund_reversed | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| occurred_at | json:TemporalExtentV1 required | none / None | Actual event time/date and precision; Timezone and uncertain interval retained | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| amount | json:QuantityV1 optional | NULL / None | Payment/debt/refund if event includes money; Typed money; missing not zero | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Documentary event proof; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| source_message_id | fk:Message optional | NULL / None | Customer event assertion; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| status | enum required | reported / None | Evidence certainty; reported,verified,disputed | reported,verified,disputed | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| related_event_id | fk:PolicyEvent optional | NULL / None | Receipt/payment connected event; Same contract or explicitly linked port contract | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| bundle_revision_id | fk:ContractBundleRevision optional | NULL / None | Exact package interpretation for a package-level receipt/request/event; Exactly one of contract_id or bundle_revision_id is set; retain revision even after membership correction | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| sender | json:PolicyEventPartyV1 required | {'kind': 'unknown', 'reason': 'Not established'} / None | Party making the evidenced communication or payment; Typed identity; person belongs to owner; insurer is the targeted contract issuer or one of the exact package component issuers. Unknown party cannot substantiate verified insurer receipt, acceptance, termination or payment. | null | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| recipient | json:PolicyEventPartyV1 required | {'kind': 'unknown', 'reason': 'Not established'} / None | Party receiving the evidenced communication or payment; Typed identity; person belongs to owner; insurer is the targeted contract issuer or one of the exact package component issuers. Unknown party cannot substantiate verified insurer receipt, acceptance, termination or payment. | null | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| authority_span_id | fk:EvidenceSpan optional | NULL / None | Authority of an insurer delegate to receive or decide for the target contract/package; Required for a TPA or other delegated authority before event can be verified; same owner or public agreement with exact issuer/scope/period; not established by a TPA name alone | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-10", "INS-08"] |

Constraints: at least one provenance source; port clocks use actual relevant receipt; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; contract_id IS NULL OR owner_id IS NOT NULL; source_message_id IS NULL OR owner_id IS NOT NULL; related_event_id IS NULL OR owner_id IS NOT NULL; num_nonnulls(contract_id,bundle_revision_id)=1; related events have same owner but do not imply shared contract or confirmed cancellation; Event kinds distinguish enquiry, requested, received, accepted, effective termination, calculated refund, paid refund and received refund. Legacy cancellation_notice is ambiguous and cannot be promoted without a new attributed specific event.; verified cancellation_received requires evidenced authorized insurer recipient; verified cancellation_accepted/coverage_terminated/refund_paid require evidenced authorized issuer sender, exact target, and authoritative source_span_id. Customer message or model explanation alone is insufficient.; refund_paid and refund_received are separate events; amount must state actual currency/value or remain explicitly unknown; no completed-refund claim from a calculated amount.; Sender/recipient typed references enforce owner and exact targeted component issuer set; a delegated party requires authority_span_id. Events record observations and do not dispatch external actions.; A verified cancellation_declined event requires authoritative issuer evidence; it does not imply coverage termination. It references the relevant request through related_event_id.; A verified refund_reversed event requires authoritative payment/reversal evidence and related_event_id targeting the exact prior refund_paid event with the same owner and contract or bundle revision. Store an actual reversal amount or explicit unknown; reject reversal above the remaining unreversed amount under event/target locks when amounts are known. Refund reversal never reinstates insurance cover by inference..
Indexes: contract_id,kind.

## Rule

Immutable original-backed condition or calculation instruction. Access: mixed. Basis: INS-05, CAL-01, CAL-02, CAL-03, CAL-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| terms_id | fk:TermsRevision optional | NULL / None | Public product edition; Required for product rule; absent for general legal scope | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| rule_key | varchar(160) required | none / None | Stable logical rule identity; Unique within revision | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| revision | integer required | 1 / count | Rule representation revision; Positive; changed body creates new row | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| kind | enum required | none / None | Rule purpose; definition,grant,eligibility,exclusion,exception,waiting,limit,deduction,accumulation,precedence,operational_right | definition,grant,eligibility,exclusion,exception,waiting,limit,deduction,accumulation,precedence,operational_right | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| body | json:RuleV1 required | none / None | Versioned typed conditions and effects; Strict AST; no executable strings; unit and dependency validation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| body_sha256 | char(64) required | none / None | Canonical rule digest; Recompute before publication | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| critical | boolean required | true / None | Whether unsupported use can materially harm advice; Reviewer may downgrade only with reason | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| review_state | enum required | draft / None | Rule approval state; draft,reviewed,blocked,published,superseded | draft,reviewed,blocked,published,superseded | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| inventory_item_id | fk:RuleInventoryItem optional | NULL / None | Optional original occurrence pointer for legacy/draft convenience; Not sufficient for numerator credit; exact counted-member support must be recorded by RuleInventorySupport | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-07"] |

Constraints: unique(owner_id,terms_id,rule_key,revision) NULLS NOT DISTINCT; public product rules have NULL owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: terms_id,kind,review_state; body GIN for registered filter keys.

## RuleEvidence

Claim-to-original support including exceptions and contradiction. Access: mixed. Basis: INS-04, INS-05.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| rule_id | fk:Rule required | none / None | Curated rule; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| span_id | fk:EvidenceSpan required | none / None | Exact original passage; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| role | enum required | none / None | How passage relates to rule; supports,defines,restricts,excepts,contradicts,precedence,table_header,table_cell,footnote | supports,defines,restricts,excepts,contradicts,precedence,table_header,table_cell,footnote | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| mandatory | boolean required | true / None | Whether this passage is needed to justify use; Omission blocks affected rule | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| review_status | enum required | unreviewed / None | Semantic entailment review; unreviewed,supported,unsupported,unresolved | unreviewed,supported,unsupported,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |

Constraints: unique(rule_id,span_id,role); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: rule_id; span_id.

## RuleDependency

Explicit connected-rule closure and direction. Access: mixed. Basis: INS-05, RET-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| from_rule_id | fk:Rule required | none / None | Rule needing the dependency; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| to_rule_id | fk:Rule required | none / None | Required connected rule; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| kind | enum required | none / None | Dependency semantics; definition,prerequisite,exception,override,calculation_input,scope | definition,prerequisite,exception,override,calculation_input,scope | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| scope | json:ApplicabilityV1 required | none / None | When edge is mandatory; Explicit unknown conditions retained | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| precedence_span_id | fk:EvidenceSpan optional | NULL / None | Original evidence authorizing override; Required for override; no last-write-wins | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |

Constraints: no self dependency; calculation/override cycles rejected; definition cycles bounded and flagged; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: from_rule_id,kind; to_rule_id.

## RuleIssue

Missing evidence, contradiction or unread original region blocking capabilities. Access: mixed. Basis: INS-04, INS-05, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentRevision optional | NULL / None | Affected original; At least document or rule | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| rule_id | fk:Rule optional | NULL / None | Affected rule; At least document or rule | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| kind | enum required | none / None | Unresolved matter; missing_original,unread_region,conflict,ambiguous_boundary,identity_conflict,unsupported_transcription,missing_dependency | missing_original,unread_region,conflict,ambiguous_boundary,identity_conflict,unsupported_transcription,missing_dependency | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| severity | enum required | material / None | Impact on affected use; material,nonmaterial | material,nonmaterial | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| description | text required | none / None | Precise unresolved dependency and consequence; Nonempty; no generic unknown substituted for known facts | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| required_action | text required | none / None | Evidence needed to resolve issue; Specific original/interpretation request | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| status | enum required | open / None | Review resolution state; open,resolved,accepted_nonmaterial | open,resolved,accepted_nonmaterial | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| resolution_span_id | fk:EvidenceSpan optional | NULL / None | Authoritative resolution proof; Required for source-based resolution | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| resolved_at | instant optional | NULL / instant | Resolution event; Required when resolved | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |

Constraints: material open issue blocks affected publication; do not delete historical issue; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: status,severity; rule_id; document_id.

## RuleInventoryItem

Immutable original source occurrence or independently derived atomic segment; its final count membership belongs to a sealed InventoryRevision. Access: public. Basis: INS-04, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| document_id | fk:DocumentRevision required | none / None | Original independently inventoried; Public | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| span_id | fk:EvidenceSpan required | none / None | Exact independently read rule location; Same document or connected span | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| instance_key | varchar(200) required | none / None | Original rule instance identity; Unique within original; separate per relevant variant/limit scope | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| scope | json:InventoryScopeV1 required | none / None | Relevance, insurer and count membership; Explicit inclusion/exclusion basis and connected-page coverage | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| reader_identity | varchar(150) required | none / None | Independent assessor identity; Not extraction process identity | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| review_state | enum required | unreviewed / None | Initial independent reading/transcription confidence of this immutable source occurrence; unreviewed,confirmed,disputed; not final denominator membership; that belongs to InventoryMembership | unreviewed,confirmed,disputed | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| count_weight | integer optional | NULL / count | Preserved initial count suggestion, never an authoritative denominator contribution; NULL means no initial suggestion; nonnegative historical suggestion only. Coverage must use sealed InventoryMembership.count_weight instead | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-07"] |
| occurrence_kind | enum required | none / None | What this stable original identity denotes; printed_assertion,printed_table_cell,printed_qualifier,independent_atomic_segment | printed_assertion,printed_table_cell,printed_qualifier,independent_atomic_segment | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |

Constraints: unique(document_id,instance_key); inventory origin independent of candidate extraction; Original document/key/span and initial reading content are immutable; new segmentation creates new item identities linked by InventoryLineage; Initial review_state/count_weight cannot enter a coverage denominator; parser output cannot create independent inventory identities.
Indexes: document_id,review_state.

## Provider

Legal hospital organization and exact branch identity. Access: public. Basis: OBS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| legal_name | varchar(300) required | none / None | Provider organization name; Not a unique key | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| branch_name | varchar(250) optional | NULL / None | Specific facility branch; Unknown cannot match all branches | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| address | text optional | NULL / None | Original-backed branch address; No fuzzy automatic merge | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| city | varchar(150) optional | NULL / None | Branch city; Not customer residence | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| postal_code | varchar(20) optional | NULL / None | Branch postcode; Country-specific validation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| country_code | char(2) required | IN / None | ISO3166 country; Explicit country for territory comparisons | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| external_identifiers | json:IdentifiersV1 required | empty array / None | Insurer/registry provider codes with provenance; Issuer scoped; conflicts preserved | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| identity_status | enum required | unresolved / None | Branch identity resolution; unresolved,verified,conflicted | unresolved,verified,conflicted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |

Constraints: no name-only uniqueness; verified external identity keys scoped by issuer.
Indexes: city,postal_code; external_identifiers GIN.

## ProviderObservation

Dated insurer- and service-specific hospital status. Access: mixed. Basis: OBS-02, INS-05.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| provider_id | fk:Provider required | none / None | Exact facility branch; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| insurer_id | fk:Insurer optional | NULL / None | Insurer reporting status; Required for network_membership,exclusion,restricted_network,authorization; optional for clinician participation/search scope; NULL permitted for insurer-independent wheelchair_access | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| configuration_id | fk:Configuration optional | NULL / None | Restricted product scope; NULL is insurer-wide only if original supports | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| service_scope | json:ProviderScopeV1 required | none / None | Treatment, network tier and geographic scope; Explicit all/selected/unknown values | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| status | enum required | unknown / None | Legacy-style summary only for network/exclusion observations; kind/value are authoritative; network,nonnetwork,restricted,excluded,unknown,not_applicable | network,nonnetwork,restricted,excluded,unknown,not_applicable | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| observed_at | instant required | none / instant | Observation date; Not future guarantee | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| valid_during | json:TemporalExtentV1 required | none / None | Original stated validity if any; Unknown validity distinct from observation time | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| span_id | fk:EvidenceSpan required | none / None | Original dated directory/notice evidence; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| supersedes_id | fk:ProviderObservation optional | NULL / None | Prior status observation; Same branch/insurer/scope | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| kind | enum required | none / None | Independent observed provider property; network_membership,exclusion,restricted_network,wheelchair_access,clinician_participation,authorization,search_completeness | network_membership,exclusion,restricted_network,wheelchair_access,clinician_participation,authorization,search_completeness | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| value | json:ObservationValueV1 required | none / None | Typed observed value and evidence certainty; Boolean/code/unknown plus source completeness; absence of hit not false | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| clinician_id | fk:Clinician optional | NULL / None | Named specialist participation subject; Required for clinician_participation; otherwise NULL | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| search_coverage | json:SearchCoverageV1 required | none / None | Scope and completeness of the observed directory/query; Exact source revision, query, pagination and completeness; unmeasured if unknown | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |

Constraints: immutable history; overlapping contradictory observations produce issue; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; network/exclusion/restricted_network/authorization kinds require insurer_id;clinician_participation requires clinician_id;wheelchair_access can be branch-wide with insurer_id NULL;configuration requires its matching insurer.
Indexes: provider_id,insurer_id,observed_at DESC; configuration_id.

## Quote

Private insurer offer bound to exact people, facts and configuration. Access: private. Basis: OBS-01, INS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Comparison context; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| snapshot_id | fk:FactSnapshot required | none / None | Facts used to obtain quote; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| configuration_id | fk:Configuration required | none / None | Quoted public options basis; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| quoted_selection | json:AcceptedSelectionV1 required | none / None | People, option selections, SI and deductible; Typed IDs/quantities; no default acceptance | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| insurer_quote_id | varchar(200) optional | NULL / None | Issuer quote identifier; Owner-scoped; encrypted | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| issued_at | instant optional | NULL / instant | Issuer quote time; Source-supported | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| valid_until | instant optional | NULL / instant | Offer expiry; Unknown not indefinite | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| status | enum required | unverified / None | Offer/acceptance state; unverified,offered,accepted,expired,declined,invalidated | unverified,offered,accepted,expired,declined,invalidated | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| source_document_id | fk:DocumentRevision required | none / None | Original quote; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| total | json:QuantityV1 required | none / None | Verified payable total or explicit unknown; Money; components reconcile before finite validated total | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| coverage_term | json:TemporalExtentV1 required | none / None | Quoted insurance term; Distinct from payment frequency | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |

Constraints: fact correction invalidates reuse; accepted quote alone not in-force policy; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; snapshot_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,conversation_id,status; valid_until.

## QuoteComponent

A source-backed premium, loading, discount or tax component. Access: private. Basis: OBS-01, CAL-01, CAL-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| quote_id | fk:Quote required | none / None | Owned quote; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| sequence | integer required | none / count | Calculation/order on source quote; Positive | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| kind | enum required | none / None | Premium component; base,addon,loading,discount,tax,fee,instalment_charge | base,addon,loading,discount,tax,fee,instalment_charge | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| amount | json:QuantityV1 required | none / None | Money or explicit unknown amount; Signed only discount/refund; currency consistent | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| basis | json:ExpressionV1 optional | NULL / None | Original rate/base calculation when given; Strict typed expression; no assumed tax rate | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| span_id | fk:EvidenceSpan required | none / None | Exact quote/tax evidence; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| applies_to | json:ComponentScopeV1 required | none / None | Person, option or component base IDs; Explicit set; no implicit total premium basis | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |

Constraints: unique(quote_id,sequence); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; quote_id IS NULL OR owner_id IS NOT NULL.
Indexes: quote_id,sequence.

## PaymentScheduleItem

Quoted or issued instalment schedule with distinct debt status. Access: private. Basis: OBS-01, INS-08.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| quote_id | fk:Quote optional | NULL / None | Quoted schedule parent; Exactly one quote or contract | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| contract_id | fk:PolicyContract optional | NULL / None | Issued schedule parent; Exactly one quote or contract | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| sequence | integer required | none / count | Payment ordinal; Positive | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| amount | json:QuantityV1 required | none / None | Payable amount; Money; unknown explicit | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| due_on | date optional | NULL / calendar date | Scheduled due date; Unknown distinct from paid | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| paid_event_id | fk:PolicyEvent optional | NULL / None | Actual receipt evidence; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| span_id | fk:EvidenceSpan required | none / None | Original instalment terms; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |

Constraints: exactly one parent; unique(parent,sequence) with two partial constraints; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; quote_id IS NULL OR owner_id IS NOT NULL; contract_id IS NULL OR owner_id IS NOT NULL; paid_event_id IS NULL OR owner_id IS NOT NULL.
Indexes: quote_id,sequence; contract_id,due_on.

## TreatmentEpisode

Actual or synthetic treatment event, separate from insurer claim. Access: private. Basis: INS-06, CAL-02, CAL-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| person_id | fk:Person required | none / None | Treated insured subject; Same owner | null | Intentionally no real customer/authentication values inspected or included. | ["INS-06", "CAL-02", "CAL-03"] |
| provider_id | fk:Provider optional | NULL / None | Facility branch; Unresolved branch remains NULL | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| started_at | json:TemporalExtentV1 required | none / None | Admission/treatment date with precision; Date-only not invented timestamp | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| ended_at | json:TemporalExtentV1 required | none / None | Discharge or unknown end; Cannot precede start when both known | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| setting | enum required | unknown / None | Treatment setting; inpatient,daycare,outpatient,home,ayush,unknown | inpatient,daycare,outpatient,home,ayush,unknown | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| clinical_facts | json:ClinicalFactsV1 required | none / None | Diagnosis/advice/procedure assertion IDs; References owned facts; no AI diagnosis inferred | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| last_related_consultation | date optional | NULL / calendar date | Illness episode reference event; Original/customer provenance required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| provenance | enum required | reported / None | Event certainty; reported,documented,case_stipulated | reported,documented,case_stipulated | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| source_document_id | fk:DocumentRevision optional | NULL / None | Treatment original; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |

Constraints: temporal consistency; person ownership; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,person_id; provider_id.

## ExpenseLine

Item-level billed expense with clinical and event association. Access: private. Basis: CAL-02, CAL-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| episode_id | fk:TreatmentEpisode required | none / None | Treatment event; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| line_number | integer required | none / count | Invoice line identity; Positive | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| label | text required | none / None | Original bill description; Do not overwrite with normalized classification | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| category | enum required | unknown / None | Reviewed cost classification; room,icu,medicine,procedure,implant,diagnostic,consultation,ambulance,consumable,other,unknown | room,icu,medicine,procedure,implant,diagnostic,consultation,ambulance,consumable,other,unknown | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| service_on | date optional | NULL / calendar date | Expense service date; Needed for pre/post membership | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| amount | json:QuantityV1 required | none / None | Gross billed money; Nonnegative finite or unknown | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| quantity | json:QuantityV1 optional | NULL / None | Days or other billed units; Unit explicit; not inferred from dates alone | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| relatedness_assertion_id | fk:FactAssertion optional | NULL / None | Relation to covered hospitalization; Same owner; clinical relation not date proximity alone | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| span_id | fk:EvidenceSpan optional | NULL / None | Original bill line evidence; Required for documented amount | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| service_extent | json:TemporalExtentV1 required | none / None | Actual service interval and timestamp precision; Date-only remains uncertain around stabilization instant; no invented midnight | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |

Constraints: unique(episode_id,line_number); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; episode_id IS NULL OR owner_id IS NOT NULL; relatedness_assertion_id IS NULL OR owner_id IS NOT NULL.
Indexes: episode_id,line_number; category.

## Claim

An insurer claim for an episode under one specific contract. Access: private. Basis: CAL-02, CAL-03, INS-08.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| episode_id | fk:TreatmentEpisode required | none / None | Treatment event; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| contract_revision_id | fk:ContractRevision required | none / None | Claimed personal terms; Same owner; treatment applicability checked | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| insurer_claim_id | varchar(200) optional | NULL / None | Issuer claim identifier; Encrypted; insurer/owner scoped | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| kind | enum required | none / None | Claim process type; cashless,reimbursement,preauthorization | cashless,reimbursement,preauthorization | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| status | enum required | reported / None | Observed insurer outcome; reported,pending,authorized,part_paid,paid,repudiated,withdrawn,unresolved | reported,pending,authorized,part_paid,paid,repudiated,withdrawn,unresolved | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| submitted_at | instant optional | NULL / instant | Convenience summary of the currently accepted submission event; May be NULL; authoritative history is ClaimEvent claim_submitted/claim_received with exact recipient; derive only from a selected verified event and do not replace receipt clocks | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| settlement_document_id | fk:DocumentRevision optional | NULL / None | Insurer outcome original; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| primary_claim_id | fk:Claim optional | NULL / None | First indemnity insurer selection for balance coordination; Same episode/owner; no cycle | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |

Constraints: authorization not final entitlement; no duplicate recovery by summing separate claims; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; episode_id IS NULL OR owner_id IS NOT NULL; contract_revision_id IS NULL OR owner_id IS NOT NULL; primary_claim_id IS NULL OR owner_id IS NOT NULL.
Indexes: episode_id,contract_revision_id; owner_id,status.

## ClaimLineAssessment

Per-insurer expense treatment with distinct monetary roles. Access: private. Basis: CAL-02, CAL-03, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| claim_id | fk:Claim required | none / None | Insurer-specific claim; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| expense_id | fk:ExpenseLine required | none / None | Bill item being assessed; Same episode | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| status | enum required | unknown / None | Item admissibility; admissible,inadmissible,conditional,unknown | admissible,inadmissible,conditional,unknown | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| admissible_amount | json:QuantityV1 required | none / None | Expense after contract exclusions/limits; Money; unknown propagation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| threshold_amount | json:QuantityV1 required | none / None | Contribution to deductible accumulation; Separate from admissible/payment | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| cover_consumption | json:QuantityV1 required | none / None | Consumption of relevant cover pool; Not inferred from insurer paid amount | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| paid_amount | json:QuantityV1 required | none / None | Actual insurer payment if known; Separate from estimated payable | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| reason | text required | none / None | Specific inclusion/exclusion reason; Must cite applicable rule or insurer settlement | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| rule_id | fk:Rule optional | NULL / None | Governing rule when curated; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| span_id | fk:EvidenceSpan optional | NULL / None | Original settlement or contract proof; At least rule or span for supported status | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| revision | integer required | 1 / None | Immutable item-assessment revision; Positive; never overwrite earlier assessment | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03", "DEC-01"] |
| supersedes_id | fk:ClaimLineAssessment optional | NULL / None | Earlier assessment corrected by this revision; Same claim/expense; lower revision; acyclic | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03"] |

Constraints: expense belongs to claim episode; unknown is not zero; unique(claim_id,expense_id,revision);supersession is a single nonbranching chain;current selection is latest accepted revision as of decision snapshot; usage entries reference exact immutable assessment revision;correction posts reversals/new entries rather than edits; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; claim_id IS NULL OR owner_id IS NOT NULL; expense_id IS NULL OR owner_id IS NOT NULL; supersedes_id IS NULL OR owner_id IS NOT NULL.
Indexes: claim_id,expense_id.

## UsageEntry

Append-only signed utilization or reversal for a scoped pool. Access: private. Basis: CAL-03, CAL-04, INS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| layer_id | fk:CoverageLayer required | none / None | Cover/limit pool; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| claim_line_id | fk:ClaimLineAssessment optional | NULL / None | Claim item causing use; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| kind | enum required | none / None | Accounting role; reserve,admissible_threshold,cover_use,payment,reversal,bonus_award,bonus_withdrawal | reserve,admissible_threshold,cover_use,payment,reversal,bonus_award,bonus_withdrawal | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| amount | json:QuantityV1 required | none / None | Signed posted quantity; Finite money; reversals point to original | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| scope | json:LimitScopeV1 required | none / None | Exact person/illness/year/body-part scope; No cross-year aggregation unless original authorizes | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| posted_at | instant required | none / instant | Ledger posting time; Immutable | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| occurred_on | date required | none / calendar date | Underlying policy event date; Not posting date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| reverses_id | fk:UsageEntry optional | NULL / None | Entry corrected or released; Same pool/scope; reversal sum cannot exceed original | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Insurer usage or bonus evidence; Unverified reservations distinctly labelled | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| posting_key | uuid required | none / None | Stable source-event/component posting identity; Unique per owner across all posting kinds; stored before worker dispatch | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03", "OPS-02"] |
| policy_event_id | fk:PolicyEvent optional | NULL / None | Source policy event for nonclaim postings; Same owner; optional if exact claim-line revision is provenance | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03"] |
| claim_payment_id | fk:ClaimPayment optional | NULL / None | Exact disbursement that funds an insurer-payment ledger posting; Same owner and claim as claim_line_id; only indemnity component; optional for legacy/unverified/nonpayment entries | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CAL-03"] |

Constraints: append-only; finite quantities only; unique(owner_id,posting_key);posting_key generated from durable source-event action and component identity;retry reuses key; one explicit source event or claim-line revision;atomic reversal sum locks original entry and prevents over-reversal; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; layer_id IS NULL OR owner_id IS NOT NULL; claim_line_id IS NULL OR owner_id IS NOT NULL; reverses_id IS NULL OR owner_id IS NOT NULL; policy_event_id IS NULL OR owner_id IS NOT NULL; New verified payment postings require claim_payment_id; aggregate non-reversed postings cannot exceed the known indemnity of that payment; interest and other amounts never consume cover; Claim payment corrections/reversals create new evidenced transactions and ledger reversals rather than changing historical UsageEntry amounts.
Indexes: layer_id,occurred_on; claim_line_id; reverses_id.

## CorpusRevision

Immutable published knowledge manifest. Access: public. Basis: OPS-03, RET-01, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| sequence | bigint required | none / None | Corpus release sequence; Positive unique | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| manifest_sha256 | char(64) required | none / None | Digest of exact member set and dependencies; Verified before publication | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| state | enum required | draft / None | Publication state; draft,validated,published,retired,blocked | draft,validated,published,retired,blocked | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| validated_at | instant optional | NULL / instant | Independent closure/coverage validation; Required before publish | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| published_at | instant optional | NULL / instant | Atomic publication event; Single publication transaction | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| previous_id | fk:CorpusRevision optional | NULL / None | Previous published corpus; Acyclic | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| coverage_report_id | fk:CoverageReport optional | NULL / None | Independent inventory completeness measurements; Unknown denominators explicitly block coverage claim | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |

Constraints: sequence unique; sealed member set immutable.
Indexes: state,sequence DESC.

## CorpusMember

Exact terms and rule revisions included in a corpus. Access: public. Basis: OPS-03, RET-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| corpus_id | fk:CorpusRevision required | none / None | Immutable publication; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| rule_id | fk:Rule required | none / None | Exact curated rule revision; Public; reviewed | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| terms_id | fk:TermsRevision optional | NULL / None | Applicable product edition; Must match rule when product-bound | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| capabilities | json:CapabilityScopeV1 required | none / None | Supported intents, insurers and rule scopes; Unknown/blocked capability never silently included | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |

Constraints: unique(corpus_id,rule_id); all mandatory dependencies present.
Indexes: corpus_id,terms_id; rule_id.

## CorpusPointer

Atomic current corpus selection for one publication channel. Access: public. Basis: OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| channel | varchar(80) required | none / None | Publication channel; production,review,pilot; explicit allowlist | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| corpus_id | fk:CorpusRevision required | none / None | Selected immutable corpus; Published/validated as required by channel | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| generation | bigint required | 0 / None | Compare-and-swap publication revision; Monotonic | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| changed_at | instant required | now / instant | Pointer update time; Atomic with durable invalidation event | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |

Constraints: channel unique; production target must be published.
Indexes: channel unique.

## SearchChunk

Replaceable searchable derivative with exact original coverage. Access: mixed. Basis: INS-04, RET-01, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentRevision required | none / None | Source edition; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| span_ids | json:UuidListV1 required | none / None | Ordered evidence spans in chunk; All IDs exist and belong to original/owner; validated closure | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| text | text required | none / None | Retrieval derivative text; Never treated as independent original truth | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| lexical_vector | tsvector required | derived / None | PostgreSQL text-search representation; Rebuildable; language configuration version recorded | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| embedding | vector(1024) optional | NULL / None | BGE-M3 dense vector derivative; Only qualified1024-dim adapter output; no evaluation material | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| index_revision | varchar(160) required | none / None | Tokenizer, embedding and chunking version; Immutable identity | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| corpus_id | fk:CorpusRevision required | none / None | Corpus under which retrieval is allowed; Member source and access checks precede ranking | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| chunk_sha256 | char(64) required | none / None | Derivative content fingerprint; Hash includes text/span ordering/index revision | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |

Constraints: unique(owner_id,corpus_id,index_revision,chunk_sha256) NULLS NOT DISTINCT; private owner filters before retrieval; equal private derivatives are separate owner records;public corpus cannot include private chunks; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: Public corpus BM25 via qualified pg_textsearch 1.4.0, version-qualified index and corpus/document filters; Private search uses owner-prefiltered deterministic BM25 in the replaceable retrieval adapter until private index isolation is proven; GIN lexical_vector is only lexical fallback/diagnostics and never labelled BM25; HNSW embedding vector_cosine_ops for public corpus; exact cosine over owner-prefiltered private candidates; document_id.

## Artifact

Stable dependency identity for immutable inputs and outputs. Access: mixed. Basis: DEC-01, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| kind | enum required | none / None | Typed artifact class; fact_assertion,message,fact_snapshot,terms,rule,document,quote,provider_observation,decision,calculation,model_qualification,corpus,search_chunk,processing_output,model_response,contract_revision,individual_term,coverage_layer,usage_entry,reuse_grant,claim_event,claim_document_requirement,claim_document_receipt,claim_payment,inventory_item,inventory_revision,inventory_membership,inventory_lineage,inventory_support,coverage_report,terms_component,contract_bundle_revision,contract_bundle_member,policy_event | fact_assertion,message,fact_snapshot,terms,rule,document,quote,provider_observation,decision,calculation,model_qualification,corpus,search_chunk,processing_output,model_response,contract_revision,individual_term,coverage_layer,usage_entry,reuse_grant,claim_event,claim_document_requirement,claim_document_receipt,claim_payment,inventory_item,inventory_revision,inventory_membership,inventory_lineage,inventory_support,coverage_report,terms_component,contract_bundle_revision,contract_bundle_member,policy_event | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| object_id | uuid required | none / None | Typed target row UUID; Deferred constraint trigger resolves kind to exact allowed table and matching owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| content_sha256 | char(64) required | none / None | Immutable target digest; Verified on registration | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| validity | enum required | current / None | Whether valid for current reuse; current,stale,blocked,erased | current,stale,blocked,erased | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| invalidated_at | instant optional | NULL / instant | First invalidation event; Historical target remains readable only if authorized | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |

Constraints: unique(kind,object_id); typed target existence and owner trigger; no arbitrary table names; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; New claim artifact kinds resolve to exact owner-bound ClaimEvent/ClaimDocumentRequirement/ClaimDocumentReceipt/ClaimPayment; inventory/coverage artifact kinds resolve only to public immutable inventory/review/report rows.
Indexes: kind,object_id; validity.

## Dependency

Input dependency used for replay and selective invalidation. Access: mixed. Basis: DEC-01, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| dependent_id | fk:Artifact required | none / None | Computed artifact; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| input_id | fk:Artifact required | none / None | Exact input artifact; Public or same owner; never another owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| purpose | enum required | none / None | Why input is necessary; facts,applicability,rule,evidence,quote,provider,model,corpus | facts,applicability,rule,evidence,quote,provider,model,corpus | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| material | boolean required | true / None | Whether invalidity blocks dependent reuse; False needs recorded nonmaterial reason | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| reason | text required | none / None | Specific dependency scope; No generic undocumented edge | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |

Constraints: unique(dependent_id,input_id,purpose); no self/cycles in computed graph; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: input_id; dependent_id.

## Decision

Validated adviser outcome for exact inputs and evidence. Access: private. Basis: DEC-01, RET-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Customer context; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| turn_id | fk:Turn required | none / None | Owning processing turn; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| intent_id | fk:DecisionIntent required | none / None | Requested scope; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| snapshot_id | fk:FactSnapshot required | none / None | Accepted fact revision; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| corpus_id | fk:CorpusRevision required | none / None | Immutable knowledge inputs; Published allowed corpus | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| outcome | enum required | none / None | Answer completeness state; complete,conditional,clarification,insufficient_evidence,technical_failure | complete,conditional,clarification,insufficient_evidence,technical_failure | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| answer_text | text required | none / None | Validated rendered answer; Citations resolve; no unsupported critical claims | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| scope | json:DecisionScopeV1 required | none / None | Precisely answered question and unresolved remainder; Conditional calculation not full entitlement | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| validation | json:ValidationV1 required | none / None | Claim support and material correctness results; Failed critical check prevents publication | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| published_at | instant optional | NULL / instant | User-visible publication time; Fact revision/current turn still matches under lock | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| validity | enum required | current / None | Current replay validity; current,stale,blocked,erased | current,stale,blocked,erased | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| supersedes_id | fk:Decision optional | NULL / None | Prior answer revised by correction; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |

Constraints: one published decision per successful turn; publication fact CAS; critical errors block; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; conversation_id IS NULL OR owner_id IS NOT NULL; turn_id IS NULL OR owner_id IS NOT NULL; intent_id IS NULL OR owner_id IS NOT NULL; snapshot_id IS NULL OR owner_id IS NOT NULL; supersedes_id IS NULL OR owner_id IS NOT NULL.
Indexes: conversation_id,created_at DESC; turn_id; validity.

## DecisionClaim

One independently supported statement or candidate disposition. Access: private. Basis: DEC-01, INS-05.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| decision_id | fk:Decision required | none / None | Answer artifact; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| ordinal | integer required | none / count | Claim order; Positive | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| text | text required | none / None | Exact supported assertion; Scope restricted to cited evidence | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| kind | enum required | none / None | Statement type; fact,eligibility,exclusion,calculation,comparison,clarification,limitation | fact,eligibility,exclusion,calculation,comparison,clarification,limitation | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| critical | boolean required | true / None | Material correctness flag; Eligibility/calculation/privacy claims critical | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| support | enum required | unverified / None | Evidence validation result; supported,conditional,unsupported,conflicted | supported,conditional,unsupported,conflicted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| candidate_configuration_id | fk:Configuration optional | NULL / None | Candidate to which statement applies; No market-wide extrapolation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| missing_dependency | text optional | NULL / None | Precise unresolved condition and effect; Required for conflicted/conditional when material | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |

Constraints: unique(decision_id,ordinal); unsupported critical claim cannot publish; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; decision_id IS NULL OR owner_id IS NOT NULL.
Indexes: decision_id,ordinal.

## ClaimCitation

Original support attached to one answer claim. Access: private. Basis: DEC-01, INS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| claim_id | fk:DecisionClaim required | none / None | Supported statement; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| span_id | fk:EvidenceSpan required | none / None | Exact original citation target; Public or same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| role | enum required | none / None | Support relationship; supports,restricts,excepts,conflicts,assumption_source | supports,restricts,excepts,conflicts,assumption_source | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| rule_id | fk:Rule optional | NULL / None | Interpreted rule connecting original to claim; Exact corpus revision | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| ordinal | integer required | none / count | Display order; Positive | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |

Constraints: unique(claim_id,span_id,role); all cited originals accessible to owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; claim_id IS NULL OR owner_id IS NOT NULL.
Indexes: claim_id,ordinal; span_id.

## Calculation

Independent deterministic result with complete trace. Access: private. Basis: CAL-01, CAL-02, CAL-03, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| decision_id | fk:Decision required | none / None | Owning answer; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| label | varchar(200) required | none / None | Calculation purpose; No entitlement implication beyond scope | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| engine_version | varchar(120) required | none / None | Deterministic evaluator identity; Immutable qualified build | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| expression | json:ExpressionV1 required | none / None | Typed calculation AST; No eval strings; no hidden operation order | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| inputs | json:CalculationInputsV1 required | none / None | Values, units and assertion/span references; Complete required inputs or explicit unknown | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| result | json:TypedValueV1 required | none / None | Computed result or unknown; Finite Decimal money; never binary float | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| trace | json:CalculationTraceV1 required | none / None | Ordered intermediate results and rule applications; Reproducible from stored inputs | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| assumptions | json:AssumptionsV1 required | none / None | Explicit hypothetical and unresolved premises; Synthetic not issuer acceptance | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| scope | enum required | none / None | Meaning of result; hypothetical,threshold_only,conditional_payable,verified_entitlement | hypothetical,threshold_only,conditional_payable,verified_entitlement | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| verified_by | varchar(160) optional | NULL / None | Independent method/reviewer identifier; Required for curated benchmark oracle, not model self-assertion | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |

Constraints: deterministic hash/replay check; complete result requires known inputs; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; decision_id IS NULL OR owner_id IS NOT NULL.
Indexes: decision_id.

## Turn

Durable unit of customer work owned by a worker. Access: private. Basis: OPS-02, OPS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Persistent context; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| request_id | uuid required | none / None | Idempotent customer request; Unique per owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| payload_sha256 | char(64) required | none / None | Canonical request hash; Same request different hash => conflict | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| input_message_id | fk:Message required | none / None | Persisted customer input; Same conversation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| expected_revision | bigint required | none / None | Requested accepted fact revision; CAS before dispatch/publication | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| snapshot_id | fk:FactSnapshot required | none / None | Immutable processing facts; Same conversation and expected revision | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| state | enum required | queued / None | Durable processing outcome; queued,running,cancel_requested,cancelled,completed,failed,stale | queued,running,cancel_requested,cancelled,completed,failed,stale | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| lease_token | uuid optional | NULL / None | Current worker fencing token; Required when running; changes on recovery | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| lease_until | instant optional | NULL / instant | Lease expiry; UTC; expired worker cannot publish | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| deadline | instant required | none / instant | Bounded turn deadline; After creation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| cancelled_at | instant optional | NULL / instant | Accepted cancellation event; Does not erase committed customer facts | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| error_code | varchar(100) optional | NULL / None | Explicit technical failure; Safe bounded code, no raw provider secrets | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |

Constraints: unique(owner_id,request_id); one active turn per conversation or explicitly serialized revisions; fenced publication; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; input_message_id IS NULL OR owner_id IS NOT NULL; snapshot_id IS NULL OR owner_id IS NOT NULL.
Indexes: state,lease_until; conversation_id,created_at.

## TurnEvent

Durable ordered stream event reused by reconnecting clients. Access: private. Basis: OPS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn required | none / None | Owning work item; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| sequence | bigint required | none / None | Monotonic replay cursor; Positive | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| kind | enum required | none / None | Durable event class; queued,started,clarification,progress,decision,cancelled,failed,stale | queued,started,clarification,progress,decision,cancelled,failed,stale | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| payload | json:TurnEventV1 required | none / None | Safe UI event content/reference; Strict kind union; no raw model chain-of-thought or private-other-owner IDs | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| recorded_at | instant required | now / instant | Event commit time; Not generated on reconnect | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |

Constraints: unique(turn_id,sequence); append-only except authorized erasure; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; turn_id IS NULL OR owner_id IS NOT NULL.
Indexes: turn_id,sequence.

## Outbox

Transactional dispatch/event publication awaiting delivery. Access: mixed. Basis: OPS-02, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| topic | enum required | none / None | Dispatch destination; turn,processing,invalidation,deletion,publication | turn,processing,invalidation,deletion,publication | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| aggregate_id | uuid required | none / None | Typed target key determined by topic; Trigger validates topic target and owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| idempotency_key | varchar(200) required | none / None | Stable delivery deduplication key; Unique within topic | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| payload | json:OutboxPayloadV1 required | none / None | Minimal dispatch reference; No copied medical values; target ID and generation only | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| state | enum required | pending / None | Delivery state; pending,leased,delivered,failed | pending,leased,delivered,failed | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| attempt_count | integer required | 0 / count | Explicit dispatch tries; Nonnegative | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| available_at | instant required | now / instant | Earliest retry time; Backoff explicit | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| lease_until | instant optional | NULL / instant | Dispatcher recovery lease; Required when leased | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| last_error_code | varchar(100) optional | NULL / None | Safe transport failure; Failed cannot silently disappear | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |

Constraints: unique(topic,idempotency_key); persist in same transaction as work; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: state,available_at; lease_until.

## ModelRoute

Exact immutable shared relay/model route configuration. Access: public. Basis: OPS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| route_key | varchar(120) required | none / None | Stable route identity; Unique revision-qualified name | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| endpoint_profile | varchar(120) required | none / None | Secret-free configured relay reference; Shared CLIProxyAPI strict /v1/responses; no credentials here | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| requested_model | varchar(160) required | none / None | Exact required model identity; No silent fallback | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| adapter_version | varchar(120) required | none / None | Strict adapter implementation identity; Immutable | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| configuration_sha256 | char(64) required | none / None | Secret-free model/adapter settings digest; Changes require new qualification | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| status | enum required | unqualified / None | User availability; unqualified,qualified,disabled | unqualified,qualified,disabled | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |

Constraints: route_key unique; immutable route revisions.
Indexes: status,route_key.

## ModelQualification

Evidence of actual schema and capability qualification. Access: public. Basis: OPS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| route_id | fk:ModelRoute required | none / None | Qualified route revision; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| schema_name | enum required | none / None | Actual use schema; fact_interpretation,extraction,review,answer | fact_interpretation,extraction,review,answer | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| schema_sha256 | char(64) required | none / None | Exact tested JSON schema; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| observed_model | varchar(160) required | none / None | Actual returned model identity; Must exactly satisfy strict identity policy | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| capabilities | json:QualificationV1 required | none / None | Context/image/structured output checks used; Measured capability, test inputs hashes, results and limits | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| qualified_at | instant required | none / instant | Qualification time; UTC | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| result | enum required | none / None | Qualification outcome; passed,failed,expired | passed,failed,expired | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| artifact_sha256 | char(64) required | none / None | Stored qualification evidence digest; Reproducible private-safe evidence | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |

Constraints: route/schema/capability changes invalidate prior qualification.
Indexes: route_id,schema_name,qualified_at DESC.

## ModelAttempt

Every provider call, failure and usage record. Access: mixed. Basis: OPS-04, OPS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn optional | NULL / None | Adviser call context; Exactly one turn or processing job | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| processing_job_id | fk:ProcessingJob optional | NULL / None | Corpus call context; Exactly one turn or processing job | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| qualification_id | fk:ModelQualification required | none / None | Qualified exact route/schema; Must be passed/current for attempted use | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| attempt_number | integer required | none / count | Explicit call ordinal; Positive; no hidden retries | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| started_at | instant required | none / instant | Request start; UTC | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| completed_at | instant optional | NULL / instant | Provider completion; At or after start | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| observed_model | varchar(160) optional | NULL / None | Actual response identity; Mismatch => technical failure | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| status | enum required | started / None | Provider call result; started,succeeded,timeout,transport_error,schema_error,identity_error,cancelled,indeterminate | started,succeeded,timeout,transport_error,schema_error,identity_error,cancelled,indeterminate | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| usage | json:UsageV1 required | none / None | Reported token counts and measured latency; Unknown usage explicit; never estimated as reported | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| error_code | varchar(100) optional | NULL / None | Safe operational failure category; No raw credentials or inherited environment | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| request_sha256 | char(64) required | none / None | Canonical request fingerprint; No benchmark inputs in implementation store | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| response_artifact_key | varchar(500) optional | NULL / None | Private safely retained structured response; Owner access and deletion; no hidden reasoning retention | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |

Constraints: exactly one parent; attempt state cannot swallow operational failure; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; turn_id IS NULL OR owner_id IS NOT NULL.
Indexes: turn_id,attempt_number; processing_job_id,attempt_number; status.

## ProcessingJob

Resumable original reading/extraction/review task. Access: mixed. Basis: OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentRevision required | none / None | Preserved input original; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| stage | enum required | none / None | Replaceable processing step; classify,read,ocr,extract,validate,independent_review,reconcile | classify,read,ocr,extract,validate,independent_review,reconcile | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| adapter_version | varchar(160) required | none / None | Reader/model pipeline identity; Original inventory workflow separately identified | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| input_sha256 | char(64) required | none / None | Input bytes/parameters digest; Stable retry identity | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| attempt_number | integer required | 1 / count | Initial or targeted retry; 1..3 for automated extract/review cycle | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| parent_job_id | fk:ProcessingJob optional | NULL / None | Previous targeted attempt; Same document/stage; no cycle | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| state | enum required | queued / None | Recoverable stage status; queued,running,succeeded,failed,blocked,cancelled | queued,running,succeeded,failed,blocked,cancelled | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| lease_until | instant optional | NULL / instant | Worker recovery deadline; Running requires fencing via lease token | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| lease_token | uuid optional | NULL / None | Stale-worker fencing identity; Rotate on retry/recovery | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| result_blob_id | fk:OriginalBlob optional | NULL / None | Immutable processing derivative artifact; Marked derivative metadata; never original rule denominator | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| issues | json:ProcessingIssuesV1 required | empty array / None | Omissions/errors and targeted retry requirements; Material unresolved issues block affected capabilities | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| error_code | varchar(100) optional | NULL / None | Explicit technical failure; Safe bounded value | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |

Constraints: unique(document_id,stage,input_sha256,attempt_number); initial plus2 targeted retries; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; result_blob_id must have content_role processing_derivative and matching scope/owner.
Indexes: state,lease_until; document_id,stage.

## CoverageReport

Measured original-inventory coverage, with unknown denominator explicit. Access: public. Basis: OPS-03, OPS-05.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| corpus_id | fk:CorpusRevision optional | NULL / None | Assessed curated publication; May be prepublication | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| insurer_id | fk:Insurer optional | NULL / None | Per-insurer or overall measurement; NULL means overall only with explicit scope | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| inventory_revision | varchar(160) required | none / None | Human-readable mirror of the referenced inventory revision key; Must equal inventory_revision_id.revision_key; never authoritative by itself | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-07"] |
| relevant_instances | bigint optional | NULL / None | Verified denominator; NULL unmeasured; zero requires complete scope proof | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| supported_instances | bigint required | 0 / None | Matched reviewed numerator; Nonnegative count of exact CoverageReportSupport memberships; <= known denominator; partial support never earns a credit | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-07"] |
| status | enum required | unmeasured / None | Measurement completeness; unmeasured,partial,measured | unmeasured,partial,measured | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| scope | json:InventoryScopeV1 required | none / None | Documents/pages/variants included and excluded; All required originals must be accounted for | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| report_sha256 | char(64) optional | NULL / None | Independent audit artifact fingerprint; NULL while draft; required canonical report/support/inventory digest at finalization; immutable thereafter | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| inventory_revision_id | fk:InventoryRevision required | none / None | Exact sealed independent inventory snapshot underlying denominator and numerator; Public; required even for unmeasured reports; same scope as report; no unbound version string | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| finalized_at | instant optional | NULL / instant | Time the exact inventory and support selection was frozen; NULL means draft; set once when hash and membership counts have been validated | null | No authentic private/database value established; proposal representation only. | ["OPS-07"] |

Constraints: measured requires known complete denominator; NULL denominator cannot yield percentage; inventory_revision_id must name a sealed revision; measured requires sealed_measured and full relevant scope; otherwise relevant_instances stays NULL; Known denominator equals sum of included membership weights in exact declared report scope; do not count candidates or structural rows; Finalized report is immutable; report_sha256 covers inventory manifest, exact scope, corpus identity and selected CoverageReportSupport identities; No numerator from a parser-derived inventory or private/evaluation rule; general aggregate evaluation status is not inventory evidence; finalized_at IS NULL iff report_sha256 IS NULL; draft reports are not acceptance evidence and cannot be used by a published CorpusRevision; Finalization transaction locks report, exact support rows, sealed inventory and corpus validation inputs; all are checked before setting finalized_at and report_sha256 atomically.
Indexes: corpus_id,insurer_id.

## ReviewRecord

Independent review and its bounded approval scope. Access: mixed. Basis: OPS-03, OPS-04, OPS-06.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| artifact_id | fk:Artifact required | none / None | Exact reviewed immutable target; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewer_account_id | fk:Account optional | NULL / None | Human reviewer if applicable; Retain anonymous role after permitted deletion | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewer_identity | varchar(160) required | none / None | Independent human/agent/version role; Not implementer self-certification when independence required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| scope | text required | none / None | What was and was not checked; Precise original/code/schema boundaries | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| outcome | enum required | none / None | Review disposition; approved,rejected,changes_requested,incomplete | approved,rejected,changes_requested,incomplete | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| findings | json:ReviewFindingsV1 required | none / None | Material findings and resolution evidence; No silent dismissal | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewed_at | instant required | none / instant | Review time; UTC | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |

Constraints: review does not imply design/cutover authorization; immutable; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: artifact_id,reviewed_at DESC.

## ConsentRecord

Specific customer authorization and revocation history. Access: private. Basis: OPS-01, CUS-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| person_id | fk:Person optional | NULL / None | Person whose data/action consent concerns; Same owner; authority separately established | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "CUS-01"] |
| purpose | enum required | none / None | Consent scope; medical_share,abha_creation,optional_processing,representation | medical_share,abha_creation,optional_processing,representation | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| recipient | varchar(250) optional | NULL / None | Specific authorized recipient; Required for medical_share | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| instance_key | uuid required | none / None | Single consent transaction identity; Per-instance sharing consent; not blanket ABHA permission | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| status | enum required | requested / None | Consent state; requested,granted,revoked,expired | requested,granted,revoked,expired | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| source_message_id | fk:Message optional | NULL / None | Exact customer authorization; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Documented authority/consent; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| valid_until | instant optional | NULL / instant | Explicit expiry; Unknown is not perpetual authorization | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| revoked_at | instant optional | NULL / instant | Withdrawal event; Pending dispatch must recheck | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |

Constraints: granted requires explicit provenance; instance_key unique within owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; person_id IS NULL OR owner_id IS NOT NULL; source_message_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,purpose,status.

## DeletionRequest

Durable erasure workflow and approved scope. Access: private. Basis: OPS-01, OPS-02, OPS-06.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| scope | json:DeletionScopeV1 required | none / None | Account/conversation/person/artifact deletion targets; Owned IDs only; derived copies included | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| requested_at | instant required | none / instant | Request receipt; UTC | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| state | enum required | pending / None | Erasure progress; pending,blocked_by_hold,running,completed,failed | pending,blocked_by_hold,running,completed,failed | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| completed_at | instant optional | NULL / instant | Verified erasure completion; Requires all required stores/caches/jobs checked | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| verification | json:DeletionVerificationV1 required | none / None | Store-level erasure evidence without medical values; Private originals, derived indexes, responses, queues, backups/tombstone policy | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| error_code | varchar(100) optional | NULL / None | Explicit erasure failure; No false completed flag | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |

Constraints: completed requires verification of all scope targets; account record anonymized/purged after final receipt policy; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: owner_id,state.

## RetentionHold

Explicit approved exception to deletion; no invented retention period. Access: private. Basis: OPS-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| deletion_request_id | fk:DeletionRequest required | none / None | Affected deletion; Same owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| scope | json:DeletionScopeV1 required | none / None | Precisely retained subset; Minimum necessary; access restricted | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| basis | text required | none / None | Verified legal/contractual basis; Requires authoritative reviewed evidence; not model assertion | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| approved_by_id | fk:Account optional | NULL only after authorized actor erasure / None | Authorized human decision; Authorized human at creation; signed minimal review receipt retained after actor erasure | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| expires_at | instant required | none / instant | Bounded hold expiry/review date; No indefinite default | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| released_at | instant optional | NULL / instant | Hold release; Triggers remaining erasure | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |

Constraints: hold cannot retain unrelated targets; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; deletion_request_id IS NULL OR owner_id IS NOT NULL.
Indexes: deletion_request_id; expires_at.

## AuditEvent

Minimal authorization and lifecycle audit without copied medical values. Access: mixed. Basis: OPS-01, OPS-02, OPS-06.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| actor_id | fk:Account optional | NULL / None | Authenticated actor if retained; Pseudonymize/erase according to approved retention | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| operation | varchar(100) required | none / None | Authorized action category; Registered allowlist | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| object_kind | varchar(100) required | none / None | Target resource type; Registered allowlist | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| object_id | uuid optional | NULL / None | Target identity if retention allows; No raw content | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| occurred_at | instant required | now / instant | Audit event time; Append-only until approved retention purge | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| outcome | enum required | none / None | Action result; allowed,denied,succeeded,failed | allowed,denied,succeeded,failed | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| metadata | json:AuditMetadataV1 required | empty object / None | Safe request/revision/error metadata; Allowlist IDs/counts/codes; no diagnoses, tokens or payload excerpts | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |

Constraints: no personal content in metadata; append-only with explicit retention purge; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: owner_id,occurred_at; operation,occurred_at.

## LegacyMapping

Lossless migration identity and unresolved semantic translations. Access: mixed. Basis: OPS-06.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| source_table | varchar(150) required | none / None | Pilot model/table; Allowlisted frozen source manifest | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| source_key | varchar(250) required | none / None | Original PK/compound identity; Preserve exact UUID/string representation | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| source_sha256 | char(64) required | none / None | Canonical preserved record fingerprint; Hash sensitive content only within private audit boundary | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| target_kind | varchar(150) optional | NULL / None | Approved replacement target; Registered mapping type | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| target_id | json:TargetKeyV1 optional | NULL / None | Replacement identity; Tagged UUID, integer or opaque string key; target_kind resolves native table and owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| status | enum required | preserved_unmapped / None | Translation safety; preserved_unmapped,mapped,quarantined,erased | preserved_unmapped,mapped,quarantined,erased | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| reason | text required | none / None | Mapping evidence or unsafe limitation; No guessed fact subject or version | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| migration_run_key | varchar(160) required | none / None | Rehearsal/cutover manifest identity; No implicit live migration | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| archive_blob_id | fk:OriginalBlob required | none / None | Preserved exact source record payload; Same owner/scope; content_role legacy_record_archive; hash matches source record fingerprint | null | No authentic private value inspected; see synthetic worked examples. | ["OPS-06"] |

Constraints: unique(migration_run_key,source_table,source_key); unmapped source payload kept in private immutable archive; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; archive_blob_id.content_role legacy_record_archive;retained archive scope matches source owner;erased source payload cannot reimport.
Indexes: migration_run_key,status; target_kind,target_id.

## AuthGroup

Existing Django privilege group identity. Access: public. Basis: OPS-01, OPS-06.

Retain native Django table and integer primary keys. Logical names here do not require custom auth models. ID/created_at common proposal defaults do not apply to these framework-managed tables.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native Django primary key, not UUID | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| name | varchar(150) required | none / None | Permission group name; Unique; no inferred privilege promotion | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: name unique.
Indexes: name unique.

## AuthPermission

Django model permission identity preserved semantically. Access: public. Basis: OPS-01, OPS-06.

Retain native Django table and integer primary keys. Logical names here do not require custom auth models. ID/created_at common proposal defaults do not apply to these framework-managed tables.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native Django primary key, not UUID | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| codename | varchar(100) required | none / None | Permission operation; Unique per content type | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| name | varchar(255) required | none / None | Human-readable permission label; Not authorization key | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| content_type_id | fk:ContentType required | none / None | Native Permission content-type relationship; Native django_content_type FK; do not flatten into fields | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "OPS-06"] |

Constraints: unique(content_type_id,codename);native AutoField primary key.
Indexes: content_type_id,codename.

## AccountGroup

Explicit account group membership. Access: private. Basis: OPS-01, OPS-06.

Retain native Django table and integer primary keys. Logical names here do not require custom auth models. ID/created_at common proposal defaults do not apply to these framework-managed tables.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | bigint required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native pilot user through-table BigAutoField; preserve exact PK | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| user_id | fk:Account required | none / None | Native user_id through-table FK, logically the account owner; Native Account FK; not a second physical owner_id column | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| group_id | fk:AuthGroup required | none / None | Granted privilege group; Authorized administration only | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(user_id,group_id).
Indexes: user_id,group_id.

## AccountPermission

Explicit account permission grant. Access: private. Basis: OPS-01, OPS-06.

Retain native Django table and integer primary keys. Logical names here do not require custom auth models. ID/created_at common proposal defaults do not apply to these framework-managed tables.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | bigint required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native pilot user through-table BigAutoField; preserve exact PK | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| user_id | fk:Account required | none / None | Native user_id through-table FK, logically the account owner; Native Account FK; not a second physical owner_id column | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| permission_id | fk:AuthPermission required | none / None | Granted model permission; Authorized administration only | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(user_id,permission_id).
Indexes: user_id,permission_id.

## GroupPermission

Permission granted to a group. Access: public. Basis: OPS-01, OPS-06.

Retain native Django table and integer primary keys. Logical names here do not require custom auth models. ID/created_at common proposal defaults do not apply to these framework-managed tables.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native Django primary key, not UUID | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| group_id | fk:AuthGroup required | none / None | Privilege group; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| permission_id | fk:AuthPermission required | none / None | Granted operation; Required | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(group_id,permission_id).
Indexes: group_id,permission_id.

## AuthSession

Existing signed Django session retained with compatible settings. Access: framework_private. Basis: OPS-01, OPS-06.

Retain django_session with session_key primary key, session_data and expire_date exactly. Owner/backend verification is decoded through Django securely, not a proposed physical owner column.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| session_key | varchar(40) required | none / None | Django session primary lookup key; Unique; secret; not exposed in reports | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| session_data | text required | none / None | Django signed session payload; Preserve encoding/signature configuration; never log | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-06"] |
| expire_date | instant required | none / instant | Session expiry; UTC; expired sessions excluded | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: session_key primary key; native signed Django semantics; authenticated session resolves account before private data retrieval.
Indexes: session_key unique; expire_date.

## RuleTable

Original-backed table with semantic axes, not unlabelled numeric arrays. Access: mixed. Basis: CAL-04, INS-04, INS-05.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| rule_id | fk:Rule required | none / None | Rule containing table lookup; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| table_key | varchar(160) required | none / None | Stable lookup identifier; Unique within rule | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| axes | json:TableAxesV1 required | none / None | Named selector definitions and exact source headers; SI and deductible axes distinct even with same currency | null | Star Gold III.J uses sum_insured_inr; Silver II.E uses deductible_inr, original physical pages3-4. | ["CAL-04", "INS-04", "INS-05"] |
| result_unit | varchar(80) required | none / None | Dimension of returned cell; Registered quantity unit | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| scope | json:LimitScopeV1 required | none / None | Per-treatment/person/period extent; Original-supported | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| header_span_ids | json:UuidListV1 required | none / None | Original header and continuation-page context; Required nonempty; validated span IDs | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| state | enum required | partial / None | Table reading completeness; partial,complete,conflicted | partial,complete,conflicted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |

Constraints: unique(rule_id,table_key); complete requires every original axis/cell/footnote inventoried; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: rule_id,table_key.

## RuleTableCell

One value and its complete selector/footnote context. Access: mixed. Basis: CAL-04, INS-04.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| table_id | fk:RuleTable required | none / None | Semantic table; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| selectors | json:TableSelectorsV1 required | none / None | Axis values selecting this cell; Exactly all declared axes; quantity/code types match | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| selector_sha256 | char(64) required | none / None | Canonical selector identity; Unique within table | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| value | json:ExpressionV1 required | none / None | Finite amount, SI reference or other supported expression; Up to SI is bounded by SI, not unlimited | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| cell_span_id | fk:EvidenceSpan required | none / None | Original cell geometry/transcription; Compatible owner | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| footnote_span_ids | json:UuidListV1 required | empty array / None | All applicable footnotes; Empty means verified none only if table review complete | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| review_state | enum required | unreviewed / None | Independent cell review; unreviewed,verified,conflicted | unreviewed,verified,conflicted | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |

Constraints: unique(table_id,selector_sha256); overlapping selector ranges cannot publish unresolved; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: table_id,selector_sha256.

## FactPredicate

Versioned fact vocabulary and cardinality used to validate snapshots. Access: public. Basis: CUS-02, RET-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs / None | Stable row identity; Primary key; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02", "RET-01"] |
| created_at | instant required | now / None | Row recording time; UTC; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02", "RET-01"] |
| key | varchar(100) required | none / None | Registered predicate name; Unique within vocabulary revision | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02"] |
| revision | integer required | 1 / None | Vocabulary revision; Positive | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02"] |
| subject_kind | enum required | none / None | Required fact subject; person,conversation,contract,provider,contract_bundle | person,conversation,contract,provider,contract_bundle | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02"] |
| cardinality | enum required | none / None | Allowed accepted fact multiplicity; scalar,set,event_series | scalar,set,event_series | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02"] |
| value_schema | json:PredicateValueSchemaV1 required | none / None | Permitted tagged value and units; Strict registered type; no executable code | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02"] |
| sensitivity | enum required | none / None | Erasure/access handling; ordinary,personal,medical | ordinary,personal,medical | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |

Constraints: unique(key,revision);published predicate definitions immutable.
Indexes: key,revision.

## ConversationReuseGrant

Explicit scoped permission to reuse facts in another conversation. Access: private. Basis: CUS-02, OPS-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs / None | Stable row identity; Primary key; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02", "OPS-01"] |
| created_at | instant required | now / None | Row recording time; UTC; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02", "OPS-01"] |
| owner_id | fk:Account required | none / None | Account authorization boundary; Owner-bound relationships; no cross-owner targets | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| source_conversation_id | fk:Conversation required | none / None | Origin context; Same owner; different destination | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| destination_conversation_id | fk:Conversation required | none / None | Permitted new context; Same owner | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| assertion_ids | json:UuidListV1 required | none / None | Exact facts authorized for reuse; Source conversation; no implicit all future facts | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CUS-02"] |
| authorization_message_id | fk:Message required | none / None | Explicit customer request; Destination conversation | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| state | enum required | none / None | Grant lifecycle; granted,revoked,expired | granted,revoked,expired | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| revoked_at | instant optional | NULL / None | Revocation event; Required when revoked | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |

Constraints: source != destination;revocation blocks future reuse and invalidates dependent current outputs;copied assertion links import_grant and source assertion; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; source_conversation_id IS NULL OR owner_id IS NOT NULL; destination_conversation_id IS NULL OR owner_id IS NOT NULL; authorization_message_id IS NULL OR owner_id IS NOT NULL.
Indexes: destination_conversation_id,state.

## ContentType

Native Django model content-type identity. Access: framework_private. Basis: OPS-01, OPS-06.

Retain native Django table and existing primary keys; these are physical fields, not replacement models.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | native sequence / None | Native AutoField primary key; Preserve exact PK | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| app_label | varchar(100) required | none / None | Application label; Part of natural key | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| model | varchar(100) required | none / None | Model name; Part of natural key | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |

Constraints: primary key(id);unique(app_label,model).
Indexes: app_label,model.

## AdminLogEntry

Preserved Django administration audit, with privacy review of free text. Access: framework_private. Basis: OPS-01, OPS-06.

Retain native Django table and existing primary keys; these are physical fields, not replacement models.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | native sequence / None | Native LogEntry AutoField PK; Preserve exact PK | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| action_time | instant required | none / None | Native action timestamp; Preserve UTC instant | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| user_id | fk:Account required | none / None | Acting administrator; Native actor FK; privileged access | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| content_type_id | fk:ContentType optional | NULL / None | Native acted-on model; Nullable per framework | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| object_id | text optional | NULL / None | Native target string key; May represent UUID/integer; not arbitrary FK | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| object_repr | varchar(200) required | empty string / None | Native target display text; Sensitive content review/redaction on erasure | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| action_flag | smallint required | none / None | Native add/change/delete flag; 1,2,3 | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| change_message | text required | empty string / None | Native admin change detail; Do not infer insurer factual acceptance; erase sensitive copies | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |

Constraints: native Django semantics;privileged access;explicit erasure mapping.
Indexes: action_time;user_id.

## ContentCopy

Inventory of where a private assertion payload was copied or transformed. Access: private. Basis: OPS-01, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs / None | Stable row identity; Primary key; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "DEC-01"] |
| created_at | instant required | now / None | Row recording time; UTC; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "DEC-01"] |
| owner_id | fk:Account required | none / None | Account authorization boundary; Owner-bound relationships; no cross-owner targets | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| source_artifact_id | fk:Artifact required | none / None | Original private assertion/content lineage; Same owner | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| destination_artifact_id | fk:Artifact required | none / None | Stored derived artifact containing the content; Same owner | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| storage_kind | enum required | none / None | Physical copy class; postgres,original_storage,search_index,cache,queue,model_response,export,backup | postgres,original_storage,search_index,cache,queue,model_response,export,backup | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| locator | varchar(500) required | none / None | Opaque store/location or JSON-path identity; No copied medical value; authenticated resolver | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| state | enum required | present / None | Copy erasure state; present,redacted,erased,held | present,redacted,erased,held | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| generation | bigint required | 0 / None | Erasure/rebuild fencing generation; Nonnegative; stale workers cannot restore older generation | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |

Constraints: unique(source_artifact_id,destination_artifact_id,storage_kind,locator);material copy must register before publication/dispatch; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: source_artifact_id,state;destination_artifact_id.

## ExpenseAllocation

Original-backed allocation of an expense across package/time/scope boundaries. Access: private. Basis: CAL-02, CAL-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs / None | Stable row identity; Primary key; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02", "CAL-03"] |
| created_at | instant required | now / None | Row recording time; UTC; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02", "CAL-03"] |
| owner_id | fk:Account required | none / None | Account authorization boundary; Owner-bound relationships; no cross-owner targets | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| expense_id | fk:ExpenseLine required | none / None | Original bill line; Same owner | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| package_parent_id | fk:ExpenseLine optional | NULL / None | Containing package line if present; Same episode; no cycles | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| kind | enum required | none / None | Reason for allocation; included_in_package,separate_payable,excluded_component,time_split,scope_split | included_in_package,separate_payable,excluded_component,time_split,scope_split | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| amount | json:QuantityV1 required | none / None | Allocated money or unresolved amount; Finite portions reconcile to expense; unknown blocks precise allocation | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-01"] |
| service_extent | json:TemporalExtentV1 required | none / None | Portion service time; Inside source service extent when known | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| boundary_assertion_id | fk:FactAssertion optional | NULL / None | Clinical stabilization or other allocation boundary; Same person/owner; exact event provenance | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| effects | json:AllocationEffectsV1 required | none / None | Billing/admissibility/cap accounting membership; Separate booleans/unknown per role; no double allocation | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Original allocation authority; Required for verified allocation; otherwise explicit stipulation | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| status | enum required | none / None | Allocation certainty; stipulated,verified,unresolved | stipulated,verified,unresolved | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |

Constraints: no package cycles;sum of nonoverlapping finite allocations <= original amount; a portion may have multiple accounting roles but is counted once per role/pool;unknown residual is not zero; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; expense_id IS NULL OR owner_id IS NOT NULL; package_parent_id IS NULL OR owner_id IS NOT NULL; boundary_assertion_id IS NULL OR owner_id IS NOT NULL.
Indexes: expense_id;package_parent_id.

## Clinician

Original-backed clinician identity scoped independently of facility names. Access: public. Basis: OBS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs / None | Stable row identity; Primary key; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| created_at | instant required | now / None | Row recording time; UTC; immutable | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| name | varchar(250) required | none / None | Printed practitioner name; Not unique; no identity from name alone | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| registration_identifiers | json:IdentifiersV1 required | empty array / None | Medical registry identifiers and provenance; Issuer-scoped identity | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| speciality | varchar(200) optional | NULL / None | Reported specialty; Original-backed or unknown | null | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |

Constraints: no name-only automatic merge.
Indexes: name.

## SourceLinkObservation

Append-only observation of one hyperlink or attachment in an immutable original; many origins may point to the same URL. Access: mixed. Basis: INS-01, INS-04, OPS-03.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | null | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | null | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| parent_acquisition_id | fk:Acquisition required | none / None | Response in which this exact link was observed; Requires preserved original body; same scope/owner | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| target_locator_id | fk:SourceLocator required | none / None | Resolved destination URL identity; Same scope/owner; does not replace observed raw href | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| original_locator | json:OriginalLocatorV1 required | none / None | Exact element, JSON pointer, text range or PDF region containing link; Must resolve in parent acquisition original bytes | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| raw_href | text required | none / None | Exact link/attachment value from original; Preserve escapes and relative form; no URL reconstruction treated as observed | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| observed_label | text required | none / None | Exact label attached to the link in source; May be empty for unlabeled link; mismatched title retained | null | {"value": "Happy Family Floater - 2021", "authentic": true, "source": "../registers/oriental-original-links-r5.json", "locator": "exact CMS row name; attachment filename remains separate"} | ["INS-01", "INS-04"] |
| record_key | varchar(500) optional | NULL / None | Original source row or attachment identity; Observed value only; not product identity | null | {"value": "82", "authentic": true, "source": "../registers/oriental-original-links-r5.json", "locator": "CMS row id 82, attachment id 17252; source c99a5f06375b45fa18dcc80eecf7c5ca4f4b4cb6f6b86927bd91f0000776452d"} | ["INS-01", "INS-04"] |
| relation_kind | enum required | none / None | How the original presents this link; hyperlink,attachment,redirect_reference,other | hyperlink,attachment,redirect_reference,other | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| observed_at | instant required | none / None | When this observation was made; UTC; not policy effective date or CMS attachment update time | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| resolver_version | varchar(120) required | none / None | Version of deterministic href resolution and original locator interpretation; Immutable reproducible implementation identifier | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04", "OPS-03"] |
| review_status | enum required | none / None | Whether the source observation was checked; unreviewed,verified,conflicted,rejected | unreviewed,verified,conflicted,rejected | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| review_reason | text optional | NULL / None | Evidence and reason for observation status; Conflict reason mandatory when conflicted; immutable | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |
| supersedes_id | fk:SourceLinkObservation optional | NULL / None | Prior observation corrected by this append-only observation; Same owner; preserve raw prior source; no cyclic lineage | null | No authentic private or generated identity inspected; synthetic fixture required. | ["INS-04"] |

Constraints: unique(id,owner_id);owner_id immutable; append-only observations; correction creates a new observation referencing supersedes_id without erasing observed label/href; parent acquisition must have a preserved acquired_original blob matching original_locator.blob_sha256; target_locator.url equals resolution of raw_href against parent acquisition final_url using recorded resolver_version; observe target does not prove target identity; all containment/source-link relationships require exact owner scope; supersession acyclic and only corrects same observation lineage; review status never overwrites conflicting attachment labels or implies historical applicability.
Indexes: target_locator_id,observed_at; parent_acquisition_id,record_key; unique(id,owner_id).

## ClaimEvent

A claim-process event, or mandatory hospitalization notice before any claim exists, with exact actor, recipient and evidence time. Access: private. Basis: INS-09, CUS-02, CAL-02, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CUS-02", "CAL-02", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs every private value; Required immutable owner; no NULL-to-public conversion | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim optional | NULL / None | Exact claim involved; absent only for a pre-claim hospitalization notice; Same owner; when present its episode and contract revision match this event | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| episode_id | fk:TreatmentEpisode required | none / None | Treatment episode that the communication or payment concerns; Same owner and exact claim lineage | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| contract_revision_id | fk:ContractRevision required | none / None | Personal contract revision to which this event was addressed; Same owner; matches claim when claim_id is present | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| event_key | uuid required | none / None | Stable identity of one real-world event across corrections; Same owner, episode, contract and event lineage for every revision | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 / count | Append-only revision number for that event; Positive; revision 1 has no supersedes_id; later revision is predecessor plus one | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| kind | enum required | none / None | Actual procedural event; events do not imply contractual admissibility; hospitalization_notice,claim_submitted,claim_received,document_requested,document_received,documentation_complete,documentation_incomplete,decision_issued,payment_made,payment_received,claim_due_confirmed,communication_received | hospitalization_notice,claim_submitted,claim_received,document_requested,document_received,documentation_complete,documentation_incomplete,decision_issued,payment_made,payment_received,claim_due_confirmed,communication_received | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| occurred_at | json:TemporalExtentV1 required | none / temporal extent | Actual event time, date or explicitly uncertain interval; Preserve precision and timezone; receipt by insurer/TPA differs from upload, dispatch or recording time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| sender | json:ClaimPartyV1 required | none / None | Party sending or performing the event; Validate exact party identity and owner; role alone does not establish delegated authority | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| recipient | json:ClaimPartyV1 required | none / None | Party receiving the communication or payment; An insurer receipt is not inferred from customer upload or TPA receipt without governing authority | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| certainty | enum required | reported / None | Evidence status of this event revision; reported,verified,disputed,retracted | reported,verified,disputed,retracted | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Exact event evidence, distinct from the rule describing a deadline; Compatible owner; event verification requires actual event proof, not merely a generic policy clause | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_message_id | fk:Message optional | NULL / None | Customer report or correction of this event; Same owner; may establish reported status but is not self-verifying insurer receipt | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| related_event_id | fk:ClaimEvent optional | NULL / None | Specific request, dispatch or other event connected to this one; Same owner and claim/episode/contract; event relationships acyclic; does not imply receipt or completion | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| documentation | json:ClaimDocumentationV1 optional | NULL / None | Explicit completeness assessment and exact requirement/receipt revisions; Required for documentation_complete/incomplete; referenced records belong to this claim; empty arrays are not proof no documents are needed | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimEvent optional | NULL / None | Previous version corrected by this event record; Same owner/event_key/claim/episode/contract/kind; acyclic; at most one successor | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |

Constraints: unique(owner_id,event_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; At least one source_span_id or source_message_id is required; claim_id required except hospitalization_notice; pre-claim notices bind episode and contract without manufacturing a submitted Claim; All cross-record claim/episode/contract identity checks use deferred constraint triggers and target key-share locks; documentation_complete requires documentation.status complete; documentation_incomplete requires incomplete or disputed; other event kinds cannot carry a completeness conclusion; Verified documentation completeness requires the exact active necessary requirements, matched receipts, original/accepted exception rules and recipient authority; ambiguity remains disputed; it is not inferred from number of uploaded files; Corrections invalidate dependent calculations/decisions; related pre-claim notice can later be linked by a new claim-bound communication without rewriting the historical notice; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules.
Indexes: claim_id,kind,created_at; episode_id,contract_revision_id,kind; owner_id,event_key,revision.

## ClaimDocumentRequirement

An immutable claim-specific version of a required or disputed document and the authority for its necessity or accepted form. Access: private. Basis: INS-09, INS-04, CUS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "INS-04", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs every private value; Required immutable owner; no NULL-to-public conversion | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none / None | Claim whose documentary condition is assessed; Same owner and exact claim lineage | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| requirement_key | varchar(160) required | none / None | Stable identity of one document requirement within the claim; Never use a filename alone; same key through corrections | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 / count | Requirement revision number; Positive; supersession increments by one | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| document_kind | varchar(160) required | none / None | Registered required evidence category; Examples from originals include discharge summary, bills and treating records; category is not proof supplied | null | {"value": "original bills", "authentic": true, "source": "../registers/independent-original-inventory-star-ssf-r6.json", "locator": "V.17 original claim-document requirement"} | ["INS-09"] |
| necessity | enum required | unknown / None | Adjudicated necessity; requests alone do not establish every item is contractually necessary; required,conditional,not_required,disputed,unknown | required,conditional,not_required,disputed,unknown | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| condition | json:PredicateV1 optional | NULL / None | Exact conditions under which the requirement applies; Required when necessity is conditional; unknown inputs keep necessity unresolved | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| accepted_form | enum required | unspecified / None | Required or accepted documentary form and certification scope; original,certified_copy,ordinary_copy,electronic,unspecified | original,certified_copy,ordinary_copy,electronic,unspecified | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| request_event_id | fk:ClaimEvent optional | NULL / None | Specific insurer or TPA request event, if any; Same claim; kind document_requested; authority/recipient checked independently | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| rule_id | fk:Rule optional | NULL / None | Applicable original-backed document requirement or exception; Public or same-owner rule; matches selected contract scope; full dependencies required | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| authority_span_id | fk:EvidenceSpan optional | NULL / None | Exact clause, certification requirement or accepted written exception; Compatible owner; required with verified necessity/form unless rule evidence supplies it | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| reason | text required | none / None | Why this requirement is necessary, conditional or disputed; Nonempty; preserve certification exceptions and unresolved request authority | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimDocumentRequirement optional | NULL / None | Prior requirement version; Same owner, claim and requirement_key; acyclic single-successor chain | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| certainty | enum required | reported / None | Evidence strength of the assessed necessity and accepted form; reported,verified,disputed | reported,verified,disputed | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(claim_id,requirement_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; At least one request_event_id, rule_id or authority_span_id is required; conditional necessity requires condition; other necessity states cannot imply unconditional document completeness; Every revision is immutable; changing necessity/form does not erase a past request or receipt; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Verified necessity/form requires applicable original or accepted exception authority, not merely the existence of a document request. Reported or disputed necessity blocks verified completeness until resolved.
Indexes: claim_id,necessity; claim_id,requirement_key,revision.

## ClaimDocumentReceipt

A specific delivery of a document to a named claim-processing recipient; repeats and corrected receipt times remain distinct. Access: private. Basis: INS-09, INS-04, CUS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "INS-04", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs every private value; Required immutable owner; no NULL-to-public conversion | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none / None | Claim receiving this document; Same owner and exact claim lineage | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| receipt_event_id | fk:ClaimEvent required | none / None | Exact receipt event and recipient; Same claim; kind document_received; occurred_at is receipt time, not local upload time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| requirement_id | fk:ClaimDocumentRequirement optional | NULL / None | Exact requirement version this delivery may satisfy; Same claim; NULL means unclassified or unsolicited document, not no requirement | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| document_id | fk:DocumentRevision optional | NULL / None | Exact delivered original bytes if acquired; Same owner for private claim documents; NULL allowed when only reported delivery is known | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| description | text required | none / None | Reported document identity when bytes or filename alone are insufficient; Do not invent missing original bytes or a final document identity | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| delivered_form | enum required | unknown / None | Actual delivered form; compared with accepted form; original,certified_copy,ordinary_copy,electronic,unknown | original,certified_copy,ordinary_copy,electronic,unknown | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| assessment | enum required | unassessed / None | Whether this delivery satisfies the named requirement; matched,insufficient,disputed,unassessed | matched,insufficient,disputed,unassessed | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| assessment_span_id | fk:EvidenceSpan optional | NULL / None | Proof of certification, acceptance or deficiency; Compatible owner; required for verified acceptance/deficiency where it is not in receipt-event evidence | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimDocumentReceipt optional | NULL / None | Prior classification or identity correction of the same delivery; Same owner/claim and receipt event lineage; preserves earlier evidence; at most one successor | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 / count | Version of this logical delivery or payment assertion; Positive; first version has no supersedes; successor increments by one | null | No authentic private/database value established; proposal representation only. | ["INS-09"] |
| receipt_key | uuid required | none / None | Stable identity of one delivered item across classification or timing corrections; Distinct items in one batch have distinct keys; retries reuse the same owner/key/revision | null | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(owner_id,receipt_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; Matched assessment requires a named applicable requirement and evidence of correct form/content; a reported delivery with no actual content remains unassessed unless authenticated acceptance explicitly establishes sufficiency; Receipt time lives only on its referenced immutable ClaimEvent revision; retransmission is a distinct event, not an overwrite; No completion or last-necessary-document date is inferred until exact requirement and receipt revisions are assessed together; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Supersession keeps owner/claim/receipt_key and receipt event logical lineage; changing classification creates a new version even when document_id and requirement_id remain unchanged; Multiple unclassified documents in one batch may have distinct receipt_keys even when document_id and requirement_id are both NULL.
Indexes: claim_id,requirement_id; receipt_event_id; document_id.

## ClaimPayment

An evidenced claim disbursement or reversal, retaining actual payment timing and separate indemnity, interest and other components. Access: private. Basis: INS-09, CAL-01, CAL-03, DEC-01.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CAL-01", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs every private value; Required immutable owner; no NULL-to-public conversion | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none / None | Claim whose liability this payment addresses; Same owner and exact claim lineage | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payment_key | varchar(200) required | none / None | Stable owner-scoped identity for this payment transaction; Unique per owner; retries reuse identity, separate partial payments do not | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payment_event_id | fk:ClaimEvent required | none / None | Evidenced payment execution or receipt event; Same claim; payment_made or payment_received; event source establishes actual time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| kind | enum required | disbursement / None | Payment or explicitly evidenced reversal; disbursement,reversal | disbursement,reversal | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payee | json:ClaimPartyV1 required | none / None | Actual recipient, distinct from proposer/insured by default; Must match payment event recipient when known; a nominee/representative requires accepted authority | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| total | json:QuantityV1 required | none / money | Total transferred amount; Known finite nonnegative money; currency required; unknown transfer must remain an event until established | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| indemnity | json:QuantityV1 required | none / money | Principal claim-payment component; Finite nonnegative same-currency money or explicit unknown; not automatically total | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| interest | json:QuantityV1 required | none / money | Separate interest component; Finite nonnegative same-currency money or explicit unknown; zero only if explicitly established | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| other | json:QuantityV1 required | none / money | Other separately classified payment component; Finite nonnegative same-currency money or explicit unknown; no unsupported deduction inference | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| transaction_reference | text optional | NULL / None | Original transaction reference if available; Owner-scoped encrypted field; never log raw value | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_span_id | fk:EvidenceSpan required | none / None | Actual payment amount/component evidence; Compatible owner; payment event and span must establish this transaction | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| reverses_id | fk:ClaimPayment optional | NULL / None | Original payment transaction partially or fully reversed; Same claim/payee/currency; noncyclic; direction reversal only; aggregate reversals cannot exceed original amounts | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 / count | Version of this logical delivery or payment assertion; Positive; first version has no supersedes; successor increments by one | null | No authentic private/database value established; proposal representation only. | ["INS-09"] |
| supersedes_id | fk:ClaimPayment optional | NULL / None | Corrected assertion about the same actual payment, distinct from a physical reversal; Same owner/claim/payment_key; one successor; revision increments; preserve exact prior event/amount provenance | null | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(owner_id,payment_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; Known components must sum exactly to total; partial unknown components remain unknown rather than balancing inventions; kind reversal iff reverses_id is present; source payment and accumulated reversals are locked before validation; Each partial payment has distinct event, recipient and transaction identity; current claim status is not payment evidence; Indemnity alone can feed UsageEntry cover-payment postings; interest/other are not insured-sum consumption or threshold accumulation; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Correcting a recorded amount/time/payee appends a same-key version and invalidates dependent ledger/decision inputs; it does not invent a bank reversal. kind reversal represents a separate evidenced financial transaction; Select one current version per payment_key for current accounting; historical reports retain exact prior versions. Revalidation/reposting uses bookkeeping reversal entries under the same logical-payment lock, preventing old and corrected versions being counted twice.
Indexes: claim_id,payment_event_id; reverses_id; owner_id,payment_key.

## InventoryRevision

A sealed, reproducible original-reading inventory snapshot with its counting protocol, scope and unresolved denominator status. Access: public. Basis: INS-04, OPS-03, OPS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-03", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| revision_key | varchar(160) required | none / None | Unique externally reportable inventory revision identifier; Unique; immutable after seal | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| previous_id | fk:InventoryRevision optional | NULL / None | Previous sealed inventory revision; Public; same scope lineage or explicitly documented scope expansion; acyclic ancestry | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| scope | json:InventoryScopeV1 required | none / None | Exact originals, insurer scope and unread/connected regions; All referenced originals public; scope closure is independent of parser output | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| counting_protocol | json:InventoryCountingProtocolV1 required | none / None | Approved segmentation, table-cell and hierarchy counting policy; Immutable protocol at seal; candidates are not an approved denominator | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| source_manifest_sha256 | char(64) required | none / None | Digest of source original identities and independent reading inputs; SHA256 of canonical source_manifest JSON; each source original hash must equal the referenced public document bytes | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| reader_identity | varchar(150) required | none / None | Independent original assessor identity; Not the extraction process being scored | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| state | enum required | draft / None | Frozen inventory state and whether a denominator is established; draft,sealed_unmeasured,sealed_measured | draft,sealed_unmeasured,sealed_measured | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| sealed_at | instant optional | NULL / instant | Time immutable membership and lineage were sealed; Required for sealed states; NULL only in draft; not source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| manifest_sha256 | char(64) optional | NULL / None | Digest of exact members, lineage and counting protocol; Required before seal; canonical referenced identities/content, not only aggregate count | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| source_manifest | json:InventorySourceManifestV1 required | none / None | Retrievable exact original/candidate membership manifest, not an opaque hash; Every document and instance key resolves to an immutable original reading; schema forbids benchmark/customer answers; source_manifest_sha256 hashes its canonical JSON | null | No authentic private/database value established; proposal representation only. | ["INS-04", "OPS-07"] |

Constraints: unique(revision_key); Sealed revisions, memberships and lineage are immutable; any segmentation/count/scope correction creates a descendant revision; sealed_measured requires complete_original_closure, approved counting protocol, resolved hierarchy/segmentation, no candidate/disputed membership and complete required original scope; otherwise seal as unmeasured; The seal transaction locks the revision and all member/lineage inputs; target updates or late inserts into a sealed revision are rejected; No benchmark questions or expected answers are stored in inventory revisions; Every source-manifest occurrence must have an explicit current membership or an adjudicated split/merge lineage whose source is retained; omitting a difficult candidate cannot reduce the denominator; Additional independent_atomic_segment items require original-backed lineage to manifested occurrences. Sealed_measured requires complete source/page coverage, not merely resolution of the rows someone inserted; Empty source manifests or missing occurrence coverage may be retained in draft/sealed_unmeasured. A measured zero requires explicit original-backed complete-scope proof; an empty input list is never such proof..
Indexes: previous_id; state,sealed_at.

## InventoryMembership

An original source occurrence or independently adjudicated atomic segment as counted, excluded or unresolved in one exact inventory revision. Access: public. Basis: INS-04, OPS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| inventory_revision_id | fk:InventoryRevision required | none / None | Exact inventory snapshot containing this assessment; Public; draft insertion only | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| item_id | fk:RuleInventoryItem required | none / None | Stable original occurrence or atomic segment being adjudicated; Public; original document belongs to revision scope | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| disposition | enum required | candidate / None | Explicit membership/segmentation outcome; candidate,included,excluded,structural_only,superseded,disputed | candidate,included,excluded,structural_only,superseded,disputed | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| count_weight | integer optional | NULL / count | Denominator contribution in this exact revision; NULL for candidate/disputed; 1 for included atomic instance; 0 for excluded/structural_only/superseded; never default an unresolved candidate to one | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| scope | json:InventoryScopeV1 required | none / None | Variant, source and rule-scope inclusion basis; Subset of revision scope; scope changes require new membership in a new revision | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| source_span_ids | json:UuidListV1 required | none / None | All independently read passages including continuations; Nonempty unique public EvidenceSpan IDs; primary item span included; connected originals explicitly declared | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| reason | text required | none / None | Segmentation, hierarchy or exclusion adjudication; Nonempty; unresolved clinical qualifier/duplicate interpretation remains explicit | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| adjudicator_identity | varchar(150) required | none / None | Independent person/process making this segmentation assessment; Not downstream parser or model self-review identity | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| previous_membership_id | fk:InventoryMembership optional | NULL / None | Same item as assessed in an earlier sealed revision; Same item; earlier revision in ancestor chain; split/merge uses InventoryLineage instead | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| content_sha256 | char(64) required | none / None | Canonical immutable membership content digest; Verified when sealing revision | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |

Constraints: unique(inventory_revision_id,item_id); Included instances have count_weight 1; candidate/disputed NULL; all noncounted dispositions zero; Sealed membership cannot be changed/deleted; predecessor remains part of its original historical manifest; A printed qualifier may remain structural_only or disputed; it must not be normalized into an independently covered procedure without original-backed adjudication.
Indexes: inventory_revision_id,disposition; item_id,inventory_revision_id.

## InventoryLineage

Explicit independent adjudication of source splitting, merging, qualifiers and repeated printed occurrences, without erasing original identities. Access: public. Basis: INS-04, OPS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| inventory_revision_id | fk:InventoryRevision required | none / None | Revision in which this relation was adjudicated; Public; all destination members in this revision | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| adjudication_key | varchar(160) required | none / None | Groups all edges of one split, merge or hierarchy decision; Stable within revision; every group has one relation kind and consistent reason | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| from_membership_id | fk:InventoryMembership required | none / None | Prior or parent source membership; Same revision or sealed ancestor; public; no future revision | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| to_membership_id | fk:InventoryMembership required | none / None | Resulting segment, qualifier or repeated occurrence; In this revision; public; never same member as source | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| kind | enum required | none / None | Adjudicated relation; source occurrences remain separate identities; split,merge,qualifies,semantic_duplicate,restates | split,merge,qualifies,semantic_duplicate,restates | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| source_span_ids | json:UuidListV1 required | none / None | Exact source evidence for the adjudication; Nonempty unique public spans; include source and destination passages | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| reason | text required | none / None | Why segmentation or semantic grouping is justified; Do not deduplicate clinical spellings or separately printed numbers without independent justification | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| adjudicator_identity | varchar(150) required | none / None | Independent original-reading adjudicator; Immutable; differs from downstream candidate extractor | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |

Constraints: unique(inventory_revision_id,from_membership_id,to_membership_id,kind); No cycles for split/merge/qualifies/restates; semantic_duplicate edges have a unique unordered endpoint pair within the revision; they do not themselves collapse source occurrence counts; Split groups require one source and at least two destinations; merge groups require at least two sources and one destination; cross-document merge cannot silently remove independently counted original occurrences; Source parent remains candidate/structural/superseded as appropriate; a segmentation relation alone does not decide count_weight; No change to any edge after revision seal.
Indexes: inventory_revision_id,adjudication_key; from_membership_id; to_membership_id.

## RuleInventorySupport

An immutable independent assessment that a specific curated rule and its dependency closure support one exact counted original member. Access: public. Basis: INS-04, OPS-03, OPS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-03", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| membership_id | fk:InventoryMembership required | none / None | Exact inventory member being evaluated; Public; belongs to a sealed revision | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| rule_id | fk:Rule required | none / None | Exact original-backed rule revision and mandatory dependency closure; Public rule only; do not use private customer/evaluation answers as original coverage | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| outcome | enum required | unresolved / None | Independent support assessment; supported,partial,unsupported,unresolved | supported,partial,unsupported,unresolved | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| support_span_ids | json:UuidListV1 required | none / None | Original support passages checked by reviewer; Nonempty unique public spans; resolve original member and connected restrictions | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| reviewer_identity | varchar(150) required | none / None | Independent reviewer of this support claim; Not the extraction/model candidate author self-certification | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| reviewed_at | instant required | none / instant | When this exact assessment was made; UTC immutable; not insurer effective date | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| reason | text required | none / None | Support boundaries, missing predicates and conflicts; Supported means all material member predicates and mandatory dependencies are covered; partial records cannot be added together to invent complete support | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| supersedes_id | fk:RuleInventorySupport optional | NULL / None | Prior support assessment corrected by this assessment; Same membership; exact replacement rule may differ; preserve old reports; at most one successor and no cycle | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| content_sha256 | char(64) required | none / None | Canonical immutable review digest; Checked when linking a coverage report | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |

Constraints: Immutable review rows; corrections append a successor; unique(supersedes_id) WHERE supersedes_id IS NOT NULL; One rule can support many original occurrences through separate reviews; each included member receives at most one numerator credit in a report; Public-only membership/rule/span checks enforce independence and owner scope.
Indexes: membership_id,outcome; rule_id; reviewed_at.

## CoverageReportSupport

The frozen member-to-support selection used to reproduce the numerator of one historical coverage report. Access: public. Basis: OPS-03, OPS-07.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-03", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| coverage_report_id | fk:CoverageReport required | none / None | Historical measured or partial coverage report; Public; immutable after report finalization | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| membership_id | fk:InventoryMembership required | none / None | Single original member counted in this report; Must belong to report.inventory_revision_id and disposition included | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| support_id | fk:RuleInventorySupport required | none / None | Exact immutable supported assessment selected for this member; Same membership; outcome supported; its rule and full dependencies present and validated in the report corpus | null | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |

Constraints: unique(coverage_report_id,membership_id); CoverageReport.supported_instances equals distinct linked memberships, never number of matching rules or table hits; No insertion/update/deletion after coverage_report.finalized_at is set; finalized report hash covers sorted support rows and exact sealed inventory manifest; Unsupported/partial/unresolved reviews cannot enter numerator; missing corpus validation leaves report unmeasured or partial.
Indexes: support_id; membership_id.

## TermsComponent

An original-backed component slot in a specific public combi edition; component legal identity and benefits remain separate. Access: public. Basis: INS-10.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; never reused | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp / instant | Assertion insertion time, separate from contractual effective time; UTC; immutable | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| wrapper_terms_id | fk:TermsRevision required | none / None | Exact public combi edition defining this component slot; Required typed identity; no inferred association | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| slot_code | varchar(80) required | none / None | Stable slot within this wrapper edition; Nonempty lowercase identifier; unique within wrapper terms | null | health or life; design-assigned codes for original COMBI13-A, not insurer-issued codes | ["INS-10"] |
| component_product_id | fk:Product required | none / None | Separately issued component product and issuer; Required typed identity; no inferred association | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| component_terms_id | fk:TermsRevision optional | NULL / None | Independently established component edition, if available; When present, terms.product_id equals component_product_id; wrapper naming a UIN alone does not establish complete component wording | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| asserted_component_uin | varchar(100) optional | NULL / None | Identifier explicitly asserted by the wrapper source; NULL means not stated, not no UIN; compare independently with resolved component edition; mismatch blocks verification | null | Health Premier ZUKHLIP25054V052425; Kotak Term Plan107N005V06, source26c72de9… COMBI13-A | ["INS-10"] |
| role | enum required | unresolved / None | Component role; does not expand the selected medical-insurer roster; medical,life,other,unresolved | medical,life,other,unresolved | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_kind | enum required | unresolved / None | Whether this wrapper requires or permits the component; required,optional,conditional,unresolved | required,optional,conditional,unresolved | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_rule_id | fk:Rule optional | NULL / None | Connected selection condition for conditional membership; Rule.owner_id NULL and rule.terms_id equals wrapper_terms_id; required when selection_kind is conditional | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan required | none / None | Original supporting wrapper/component association; Required typed identity; no inferred association | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| status | enum required | unresolved / None | Association review state; reviewed identity does not mean complete component terms; unresolved,reviewed,conflict | unresolved,reviewed,conflict | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| supersedes_id | fk:TermsComponent optional | NULL / None | Prior association from an earlier wrapper edition; Acyclic, same wrapper product and slot_code; a published wrapper edition is immutable | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(wrapper_terms_id,slot_code); component_terms_id, when present, belongs to component_product_id; asserted UIN disagreement sets conflict and blocks affected publication; conditional membership requires a public same-wrapper selection rule; All source spans and linked rules are public; do not manufacture a separately issued component wording from a wrapper title; Published component edges are immutable; changing an edge creates a new wrapper terms edition and invalidates dependent artifacts; No composition cycle, including cycles through resolved component terms; closure is checked before publication.
Indexes: wrapper_terms_id,slot_code; component_product_id,component_terms_id; supersedes_id.

## ContractBundle

Stable owned identity for a package of component policies, without inventing a third policy contract or sole issuer. Access: private. Basis: INS-10, OPS-01, CUS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; never reused | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp / instant | Assertion insertion time, separate from contractual effective time; UTC; immutable | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Owner governing all private bundle records; Immutable owner; never nulled to publish private records | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| label | varchar(250) required | none / None | Owner-facing package label; Nonempty; not unique and not proof of legal identity | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| external_reference | varchar(200) optional | NULL / None | Issuer package reference if actually supplied; Encrypted; NULL when unavailable; do not manufacture a wrapper policy number | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| current_revision_id | fk:ContractBundleRevision optional | NULL / None | Current accepted bundle interpretation; Deferred check: referenced revision.bundle_id equals this bundle id; CAS under bundle row lock and expected revision; never points across bundles | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(id,owner_id); immutable owner; Current revision pointer targets a revision of this same bundle and owner; updates are fenced by expected revision; No global unique external reference; private erasure includes revisions, membership, subject facts, artifacts and all copies; current_revision_id can target only a sealed revision with matching owner and bundle_id; head CAS checks expected prior revision..
Indexes: owner_id,created_at; owner_id,current_revision_id.

## ContractBundleRevision

Immutable owner-scoped interpretation of a package version, component membership and status, retained when customer facts or sources change. Access: private. Basis: INS-10, DEC-01, OPS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; never reused | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp / instant | Assertion insertion time, separate from contractual effective time; UTC; immutable | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Owner governing all private bundle records; Immutable owner; never nulled to publish private records | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| bundle_id | fk:ContractBundle required | none / None | Stable package being interpreted; Required typed identity; no inferred association | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| revision | bigint required | none / None | Monotonic bundle revision; Positive; unique(bundle_id,revision); previous revision is current at creation | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| wrapper_configuration_id | fk:Configuration optional | NULL / None | Selected public wrapper version/options if resolved; Configuration.terms_id is the parent of every member TermsComponent; unresolved configuration blocks verified composition | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| previous_id | fk:ContractBundleRevision optional | NULL / None | Previous immutable interpretation; Same bundle; exactly preceding revision; acyclic | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| membership_state | enum required | unresolved / None | Whether actual component membership is known; stipulated is research-only; unresolved,partial,stipulated,verified | unresolved,partial,stipulated,verified | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| status | enum required | unresolved / None | Package status assertion; never inferred from explanation of a cancellation consequence; proposed,in_force,expired,cancelled,separated,unresolved | proposed,in_force,expired,cancelled,separated,unresolved | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Issued package evidence, when supplied; Required for verified issued-package assertion; public sample letters do not prove private acceptance | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| sealed_at | timestamptz optional | NULL / instant | End of the short atomic revision construction transaction; NULL during construction only; immutable after sealing; every persisted revision must be sealed at deferred commit validation | null | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| membership_sha256 | char(64) optional | NULL / None | Digest of canonical exact wrapper configuration and complete ordered member records; Lowercase64hex; required with sealed_at. Recomputed before sealing; changing any membership input requires a new revision. | null | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| seal_format_version | smallint required | 1 / None | Version of canonical package-member serialization; Positive; currently1 only. Format1 hashes UTF-8 JSON with sorted keys, member rows ordered by terms_component_id/id, timestamps normalized to UTC ISO8601, identifiers as strings and no floating numbers; includes all committed member fields and wrapper_configuration_id. | null | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |

Constraints: unique(id,owner_id); owner immutable; unique(bundle_id,revision); Verified membership requires wrapper configuration, private issued evidence and exactly one resolved member disposition for every required/selected applicable slot; conditional/unknown selection blocks closure; Stipulated membership is allowed only in explicit research fixtures and never production verified acceptance; A verified cancelled status requires insurer-event evidence; a request, rule consequence or model response alone is insufficient; Sealing members and moving bundle current_revision pointer occur atomically in one short transaction; old turns cannot advance the pointer; Previous and current revision ownership and bundle lineage checked by deferred constraint triggers under key-share and bundle row locks; CHECK((sealed_at IS NULL)=(membership_sha256 IS NULL)); seal_format_version=1. Deferred commit trigger rejects any persisted unsealed revision, including a revision not yet referenced by the bundle head.; A parent-row-locking trigger guards every member INSERT/UPDATE/DELETE. It rejects mutation of sealed membership, including late insertion, and prevents races with sealing. Authorized erasure uses its separately privileged audited path.; Only the unsealed-to-sealed transition is allowed during construction. After sealing all revision fields are immutable; unsealing is prohibited. Current head can target only a sealed same-bundle revision.; At seal time, validate component/issuer/owner/edition closure and hash exact member data; unresolved or partial interpretation may be sealed with explicit missing members but cannot become verified by sealing..
Indexes: bundle_id,revision DESC; owner_id,status; wrapper_configuration_id.

## ContractBundleMember

Maps one public package slot to one actual same-owner policy revision, preserving component-specific insured membership and explicit missing or unselected slots. Access: private. Basis: INS-10, CUS-01, CUS-02.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; never reused | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp / instant | Assertion insertion time, separate from contractual effective time; UTC; immutable | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Owner governing all private bundle records; Immutable owner; never nulled to publish private records | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| bundle_revision_id | fk:ContractBundleRevision required | none / None | Exact immutable package interpretation; Required typed identity; no inferred association | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| terms_component_id | fk:TermsComponent required | none / None | Public component slot, including separate issuer identity; Required typed identity; no inferred association | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| contract_revision_id | fk:ContractRevision optional | NULL / None | Actual owned issued component policy revision, if established; Resolved policy configuration belongs to TermsComponent.component_product_id and, when fixed, component_terms_id; underlying PolicyContract.insurer_id matches component issuer | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_status | enum required | unresolved / None | Membership disposition; missing is explicit, not fabricated cover; unresolved,required_missing,selected_unverified,selected_stipulated,selected_verified,not_selected | unresolved,required_missing,selected_unverified,selected_stipulated,selected_verified,not_selected | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Issued evidence for the component membership; Required private evidence for selected_verified or verified not_selected; a public specimen is insufficient | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_fact_id | fk:FactAssertion optional | NULL / None | Attributed customer assertion when documentary proof is absent; Fact subject is this bundle, component contract or an insured person; trace to current fact snapshot; cannot promote unverified to verified | null | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(id,owner_id); owner immutable; unique(bundle_revision_id,terms_component_id); All member TermsComponent.wrapper_terms_id match bundle wrapper configuration terms; selected_verified requires contract_revision_id and private membership evidence; selected_stipulated requires explicit research fixture; required_missing/not_selected require contract_revision_id NULL; A required component cannot be not_selected; conditional disposition requires its resolved selection rule; All private links enforce composite owner FK and deferred lineage checks on both source and target changes; Members are immutable after revision sealing; changes create a new bundle revision. ContractMember records, not package identity, determine who is insured on each component; Default reject two selected slots in one bundle revision whose ContractRevision.contract_id is the same underlying PolicyContract, even if their revision IDs differ. Deferred check joins underlying contract IDs under parent and contract key-share locks. Any exception requires an explicit reviewed same-wrapper rule with exact slot pair; no implicit exception from matching dates or names..
Indexes: bundle_revision_id,selection_status; contract_revision_id; terms_component_id.
