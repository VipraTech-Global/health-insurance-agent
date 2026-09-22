# Final application field dictionary

Revision: `discussion-r25-final-review`

This is the field-level authority for the application proposal. The design is ready for human review and is not implemented.

## Account

Logical authentication principal implemented by the retained accounts.User(AbstractUser) model.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| email | varchar(254) required | none | Login identity | Unique exact existing email; no silent normalization merge | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| password | varchar(128) required | none | Django encoded password and algorithm marker | Preserve encoded bytes; never hash an existing hash | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-06"] |
| last_login | instant optional | NULL | Last successful login | UTC; preserve legacy value | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_superuser | boolean required | false | Global administration privilege | Authorized changes only | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_staff | boolean required | false | Administration interface access | Authorized changes only | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_active | boolean required | true | Whether login is permitted | Deleted account cannot be active | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| first_name | varchar(150) required | empty string | Optional display given name | No medical use | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| last_name | varchar(150) required | empty string | Optional display surname | No insured identity inference | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| date_joined | instant required | now | Original account creation | Preserve during migration | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| deleted_at | instant optional | NULL | Deletion completion marker | No retained personal content after completed deletion without hold | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| erasure_generation | bigint required | 0 | Fence work started before erasure | Monotonic; workers compare before storing/publishing | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "OPS-02"] |

Constraints: email unique; id immutable; username disabled; email is USERNAME_FIELD; native AbstractUser authentication, group and permission semantics retained; date_joined is the account creation timestamp

Indexes: email unique B-tree

## Person

A minimal owner-scoped human label; medical, role and identity assertions live in sourced fact records.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| display_name | varchar(200) required | empty string | Customer supplied label | Blank allowed; customer-facing label only; not a deduplication key or verified legal identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |

Constraints: unique(id,owner_id); owner_id immutable; display_name is not an identity or deduplication key

Indexes: owner_id

## PersonRelationship

Directional relationship between two owner-scoped people, separate from proposed or issued policy membership.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| from_person_id | fk:Person required | none | Person whose relationship is described | Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| to_person_id | fk:Person required | none | Related person | Same owner; not self | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| relationship_type | enum required | none | How to_person relates to from_person | spouse,parent,child,parent_in_law,sibling,guardian,dependent,other; other requires explanation in source assertion | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| source_statement_id | fk:CustomerStatement required | none | Exact customer statement supporting the relationship | Same owner and conversation context; subjects match from_person/to_person | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| valid_from | date optional | NULL | First date the relationship applies when materially known | ISO date; NULL means not established or not material | date | Synthetic design fixture only; no real customer value included. | ["CUS-01", "INS-03"] |
| valid_to | date optional | NULL | Last date the relationship applies when materially known | ISO date; NULL means open or not established; cannot precede valid_from | date | Synthetic design fixture only; no real customer value included. | ["CUS-01", "INS-03"] |

Constraints: from_person_id differs from to_person_id; from_person_id and to_person_id have the same immutable owner_id as the relationship; valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from; source assertion has the same owner and matching people; unique(owner_id,from_person_id,to_person_id,relationship_type,valid_from,valid_to) with NULLS NOT DISTINCT; unique(id,owner_id); owner_id immutable

Indexes: owner_id,from_person_id; owner_id,to_person_id; owner_id,relationship_type

## Conversation

Persistent conversation and its current accepted state.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| title | varchar(200) required | empty string | History list label | No automatic sensitive diagnosis in title | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| current_profile_revision_id | fk:CustomerProfileRevision optional | NULL | Current customer fact/requirement checkpoint | Same conversation and matching revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| status | enum required | open | Conversation lifecycle | open,archived,deleting,deleted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| updated_at | instant required | now | Most recent durable interaction | Monotonic per transaction | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| preferred_language | varchar(35) optional | NULL | Customer communication locale | BCP47; not a medical fact | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |

Constraints: unique(id,owner_id); profile revision pointer belongs to this conversation; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/statement/fact-type/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; current_profile_revision_id IS NULL OR owner_id IS NOT NULL

Indexes: owner_id,updated_at DESC

## Message

Immutable submitted or published conversational content.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Parent history | Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| sequence | bigint required | none | Durable ordering in conversation | Positive; allocated under conversation lock | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| role | enum required | none | Speaker role | customer,adviser,system | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| content | text required | none | Exact displayed message | Size bound proposed 100000 characters; encrypted storage | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| origin | enum required | none | How content entered history | text,voice_transcription,document_import,system,migration | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| client_request_id | uuid optional | NULL | Submission idempotency identifier | Unique per owner when nonnull | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| payload_commitment | char(64) required | none | Keyed commitment used to reject an idempotency-key collision with different submitted content | 64 lowercase hex characters produced by the versioned server HMAC key; never a raw content hash | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| submitted_at | instant required | none | Original receipt time | UTC; not rewritten on retry | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| recommendation_id | fk:Recommendation optional | NULL | Structured recommendation published by this adviser message | Same owner/conversation; unique when nonnull | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| redacted_at | instant optional | NULL | Content erasure event | Content and copies cleared atomically or deletion job blocks access | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |

Constraints: unique(conversation_id,sequence); unique(owner_id,client_request_id) where nonnull; recommendation_id is NULL or identifies a recommendation owned by the same account and conversation; authorized erasure replaces content with a fixed tombstone, sets redacted_at and invalidates all ConversationMessageChunk rows; payload_commitment is a keyed HMAC and cannot be used as a public content hash; unique(id,owner_id); owner_id immutable

Indexes: conversation_id,sequence; turn_id

## ConversationMessageChunk

Replaceable private lexical/semantic index for an exact section of one immutable conversation message.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Parent history | Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| message_id | fk:Message required | none | Exact immutable source message | Same owner and conversation; message not redacted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "RET-01"] |
| chunk_index | integer required | none | Zero-based section order within the message | Nonnegative; deterministic for one index revision | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| start_offset | integer required | none | Starting character offset in the original message | Nonnegative and less than end_offset | Unicode code-point offset | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| end_offset | integer required | none | Exclusive ending character offset in the original message | At most source content length and greater than start_offset | Unicode code-point offset | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| lexical_vector | tsvector required | derived | PostgreSQL full-text representation for exact-term search | Rebuildable private derivative; language configuration belongs to index_revision | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| embedding | vector(1024) optional | NULL | Local BGE-M3 semantic-search derivative | Only qualified 1024-dimensional local adapter output; no benchmark material | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| index_revision | varchar(160) required | none | Chunking, tokenizer and embedding version | Immutable revision-qualified identifier | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01", "OPS-06"] |
| content_commitment | char(64) required | none | Keyed commitment to the exact private source slice and index revision | Versioned HMAC; changes when source text or index revision changes | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| invalidated_at | instant optional | NULL | When this replaceable derivative stopped being eligible for retrieval | Required when source message is redacted or index revision is retired | instant | Synthetic design fixture only; no real customer value included. | ["CUS-02", "OPS-01"] |

Constraints: unique(message_id,chunk_index,index_revision); owner_id and conversation_id match the source Message; 0 <= start_offset < end_offset <= source message content length; current accepted CustomerProfileRevision overrides conflicting historical-message retrieval; redacted source messages make every chunk ineligible before content erasure

Indexes: conversation_id,message_id,chunk_index; GIN lexical_vector; HNSW embedding vector_cosine_ops WHERE embedding IS NOT NULL AND invalidated_at IS NULL; owner_id,conversation_id,invalidated_at

## CustomerStatement

A meaningful source span inside one customer message, retained so unusual or unresolved information cannot be silently dropped.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| source_message_id | fk:Message required | none | Immutable message containing this statement | Customer-role message; same owner; offsets must lie within content | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| start_offset | integer required | none | Starting character in source message | Zero-based Unicode code-point offset; nonnegative and less than end_offset | Unicode code-point offset | Synthetic: 0 | ["CUS-02", "CUS-03", "RET-01"] |
| end_offset | integer required | none | Exclusive ending character in source message | At most source content length and greater than start_offset | Unicode code-point offset | Synthetic: 20 | ["CUS-02", "CUS-03", "RET-01"] |
| subject_person_id | fk:Person optional | NULL | Person the statement concerns when person-specific | Same owner; null for conversation/purchase-wide or unresolved subject | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| kind | enum required | none | Initial semantic category | fact,intended_insured,requirement,preference,question,correction,context,other | None | Synthetic: fact | ["CUS-02", "CUS-03", "RET-01"] |
| status | enum required | pending | Whether the meaningful span has been handled | pending,mapped,clarification_required,ignored_with_reason | None | Synthetic: mapped | ["CUS-02", "CUS-03", "RET-01"] |
| resolution_note | text optional | NULL | Reason a statement needs clarification or is ignored | Required for clarification_required and ignored_with_reason; absent for mapped | None | Synthetic: exact hospital branch is unclear. | ["CUS-02", "CUS-03", "RET-01"] |

Constraints: 0 <= start_offset < end_offset <= source Message content length; source Message must have role customer and the same owner; subject_person_id, when set, has the same owner; resolution_note required exactly for clarification_required or ignored_with_reason; decision-relevant statements must become mapped or clarification_required before advice is ready; statement stores offsets, not a duplicate copy of Message.content; unique(id,owner_id); owner_id immutable

Indexes: source_message_id,start_offset,end_offset; owner_id,status; subject_person_id,kind

## CustomerProfileRevision

Small immutable checkpoint created only when customer facts or requirements change.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "DEC-01", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Conversation whose customer state changed | Same owner; one linear revision sequence per conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "DEC-01", "OPS-02"] |
| revision | bigint required | none | Sequential customer-state revision number | Positive; allocated while locking the Conversation; immutable | None | Synthetic: 3 | ["CUS-02", "DEC-01", "OPS-02"] |

Constraints: unique(conversation_id,revision); revision is positive and monotonic within conversation; facts and requirements for the revision are inserted in the same transaction before Conversation.current_profile_revision_id changes; ordinary chat without a fact or requirement change creates no revision; unique(id,owner_id); owner_id immutable

Indexes: conversation_id,revision DESC

## CustomerFact

One validated version of a customer fact; active historical state is reconstructed by logical key and profile revision.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| introduced_in_revision_id | fk:CustomerProfileRevision required | none | Profile revision that introduced this version | Same owner and source-statement conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| source_statement_id | fk:CustomerStatement required | none | Exact customer statement supporting this fact | Mapped statement in the same owner and revision conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| logical_key | uuid required | uuid4 for the first version; reuse for corrections | Stable identity of one logical fact across corrections | Same logical key remains within one owner, conversation, subject and fact type | None | Synthetic UUID shared by age corrections. | ["CUS-02", "CUS-03", "INS-06"] |
| fact_type | varchar(100) required | none | Reviewed semantic meaning of value | Must exist in the versioned code-controlled FactType registry; AI cannot create codes | None | Synthetic: person.age_reported | ["CUS-02", "CUS-03", "INS-06"] |
| schema_version | positive_integer required | none | Exact validator used for value | Registered for fact_type; historical validators remain readable | None | Synthetic: 1 | ["CUS-02", "CUS-03", "INS-06"] |
| value | json:FactValueV1 required | none | Typed known, unknown or not-applicable value | Closed schema selected by fact_type and schema_version; units and precision explicit | None | Synthetic: {"state":"known","kind":"quantity","value":"64","unit":"year"} | ["CUS-02", "CUS-03", "INS-06"] |
| status | enum required | reported | Customer acceptance state of this version | reported,confirmed,disputed,retracted | None | Synthetic: reported | ["CUS-02", "CUS-03", "INS-06"] |

Constraints: append-only except authorized erasure; source statement and introduced revision share owner and conversation; fact_type registry determines person/conversation subject, cardinality, schema, units and sensitivity; all versions of logical_key retain owner, conversation, subject and fact_type; latest version at or before a requested revision is active unless retracted; multiple active logical keys for a scalar subject/fact_type are an unresolved conflict; unknown and not_applicable are explicit value states and never become zero; unique(id,owner_id); owner_id immutable

Indexes: introduced_in_revision_id; owner_id,logical_key,introduced_in_revision_id; owner_id,fact_type; GIN value

## CustomerRequirement

One atomic mandatory, preferred or informational condition used to filter, rank or explain policy configurations.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| introduced_in_revision_id | fk:CustomerProfileRevision required | none | Profile revision that introduced this version | Same owner and source-statement conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| source_statement_id | fk:CustomerStatement required | none | Exact statement supporting this requirement | Requirement or preference statement in same owner and conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| logical_key | uuid required | uuid4 for first version; reuse for corrections | Stable identity of one requirement across corrections | Same logical key remains within one owner, conversation, criterion and scope | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| criterion | varchar(120) required | none | Policy outcome the customer wants tested | Must exist in reviewed comparison-criterion registry | None | Synthetic: claim.copay_percent | ["CUS-01", "CUS-03", "RET-01"] |
| operator | enum required | none | Comparison to apply to policy outcome | equals,not_equals,less_than_or_equal,greater_than_or_equal,includes,excludes,is_available,is_not_available,minimize,maximize; registry restricts per criterion | None | Synthetic: equals | ["CUS-01", "CUS-03", "RET-01"] |
| target_value | json:FactValueV1 optional | NULL | Desired boundary or value | Required except for minimize/maximize; type and unit fixed by criterion | None | Synthetic: {"state":"known","kind":"quantity","value":"0","unit":"ratio"} | ["CUS-01", "CUS-03", "RET-01"] |
| priority | enum required | none | Whether failure excludes or only ranks a configuration | mandatory,preferred,informational | None | Synthetic: mandatory | ["CUS-01", "CUS-03", "RET-01"] |
| scope | enum required | none | People or purchase to which this requirement applies | entire_purchase,all_intended_insured,person | None | Synthetic: person | ["CUS-01", "CUS-03", "RET-01"] |
| subject_person_id | fk:Person optional | NULL | Exact person for person-scoped requirement | Required exactly when scope=person; same owner and conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| status | enum required | reported | Customer acceptance state of this version | reported,confirmed,disputed,withdrawn | None | Synthetic: reported | ["CUS-01", "CUS-03", "RET-01"] |

Constraints: append-only except authorized erasure; source statement and introduced revision share owner and conversation; criterion registry determines permitted operators, value schema and units; subject_person_id required exactly for scope person and null otherwise; target_value required except for minimize and maximize; all versions of logical_key retain owner, conversation, criterion and scope; latest version at or before a requested revision is active unless withdrawn; one source statement may create separate atomic person-scoped requirements without a joining table; unique(id,owner_id); owner_id immutable

Indexes: introduced_in_revision_id; owner_id,logical_key,introduced_in_revision_id; owner_id,criterion,priority; subject_person_id,criterion; GIN target_value

## AdviceRequest

One customer advice goal spanning any number of clarification messages; execution attempts later pin exact profile revisions.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Conversation containing the customer goal | Same owner | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| source_statement_id | fk:CustomerStatement required | none | Statement that initiated this advice goal | Same owner and conversation; normally question, requirement or context | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| request_type | enum required | none | Buying/comparison goal, including comparison with existing cover | purchase_recommendation,product_comparison,coverage_question,renewal_review,portability_review | None | Synthetic: purchase_recommendation | ["CUS-01", "CUS-03", "RET-01"] |
| status | enum required | open | Whether the customer goal remains active | open,fulfilled,cancelled | None | Synthetic: open | ["CUS-01", "CUS-03", "RET-01"] |

Constraints: source statement and conversation share owner and conversation; ten information-gathering messages may still serve one AdviceRequest; processing state and failures belong to Turn/ModelAttempt, not this customer goal; each Turn references the exact CustomerProfileRevision it evaluates; unique(id,owner_id); owner_id immutable

Indexes: conversation_id,created_at DESC; owner_id,status; request_type,status

## Insurer

One insurer in the approved research roster and the issuer identity used by products and official documents.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| name | varchar(250) required | none | Full official insurer name | Nonempty; unique in the active research roster | None | Care Health Insurance Limited | ["INS-01", "INS-04"] |

Constraints: name unique; id and created_at inherited from approved abstract base models

Indexes: name unique B-tree

## DiscoveryRun

One autonomous Codex session tasked with discovering public documents for one insurer.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| insurer_id | fk:Insurer required | none | Insurer whose sources the run investigates | Required; one insurer per run; comparison sources may still mention others | None | Synthetic design example; no customer value used. | ["INS-01", "INS-04"] |
| instructions | text required | none | Exact discovery task supplied to Codex | Nonempty; retained verbatim; it describes the requested search and does not constrain reachable sites | None | Find all current and historical health-insurance documents for Care, including official and useful independent sources. | ["INS-04", "OPS-03"] |
| session_id | varchar(250) required | none | Codex session identity used for continuation and audit | Nonempty; unique; immutable after the session starts | None | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| model_name | varchar(160) required | none | Observed Codex model used for the run | Record the actual model identity; no silent substitution | None | gpt-6-astra | ["OPS-03", "OPS-04"] |
| completed_at | instant optional | NULL | When the run reached a terminal state | UTC; required for completed, failed or cancelled; completion does not assert source completeness | instant | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| status | enum required | queued | Run lifecycle | queued, running, completed, failed or cancelled | None | completed | ["INS-04", "OPS-03"] |
| error_summary | text optional | NULL | Safe explanation of a failed run | Required when failed; no credentials or private browser state | None | Browser session ended before attachments were inspected. | ["OPS-03"] |

Constraints: session_id unique; terminal status requires completed_at; failed requires error_summary; completed means the assigned session finished; it never proves all documents were found

Indexes: insurer_id,created_at DESC; status,created_at

## SourceURL

One unique public web address discovered by Codex, independent of how often or where it was observed.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| url | text required | none | Exact usable source URL | Unique; bounded to 8192 characters; no insurer-domain allowlist | None | https://careinsurance.com/example/policy-wording.pdf | ["INS-04", "OPS-03"] |
| source_type | enum required | unknown | Who operates the location, used as provenance rather than a browsing restriction | insurer_site, regulator_site, government_site, independent_site, archive, other or unknown | None | insurer_site | ["INS-04", "DEC-01"] |

Constraints: url unique; source_type is evidence metadata and never an autonomous-browsing allowlist

Indexes: url unique B-tree; source_type

## SourceObservation

One retained occasion on which a Codex discovery run encountered a source URL.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| discovery_run_id | fk:DiscoveryRun required | none | Codex run that made the observation | Required | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| source_url_id | fk:SourceURL required | none | URL encountered by the run | Required; many observations may point to the same URL | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| found_in_capture_id | fk:SourceCapture optional | NULL | Previously captured page or register containing the link | Optional; when present it must precede this observation | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| observation_type | enum required | other | How Codex encountered the URL | search_result, page_link, attachment, document_register, sitemap, known_url or other | None | attachment | ["INS-04"] |
| label_or_context | text optional | NULL | Useful visible label, snippet or surrounding context | Preserve useful source wording; do not place the downloaded document text here | None | Download Policy Terms and Conditions | ["INS-04"] |
| disposition | enum required | unresolved | Whether the observed URL belongs in the research scope | relevant, irrelevant or unresolved | None | relevant | ["INS-02", "INS-04"] |
| disposition_reason | text optional | NULL | Why the observation was excluded or remains unresolved | Required for irrelevant; retained so later runs do not repeat a known exclusion | None | Document concerns travel insurance rather than medical-expense cover. | ["INS-02", "INS-04"] |

Constraints: irrelevant requires disposition_reason; observations are retained even when irrelevant; found_in_capture_id cannot point to a later capture

Indexes: discovery_run_id,created_at; source_url_id,created_at; disposition

## SourceCapture

One attempt by a Codex discovery run to preserve the content currently returned by a source URL.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| discovery_run_id | fk:DiscoveryRun required | none | Run responsible for this capture attempt | Required | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| source_url_id | fk:SourceURL required | none | URL whose content was requested | Required | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| completed_at | instant optional | NULL | When the capture succeeded or failed | UTC; required for captured or failed | instant | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| status | enum required | running | Capture lifecycle | running, captured or failed | None | captured | ["INS-04", "OPS-03"] |
| http_status | smallint optional | NULL | HTTP response status when Codex or its browser exposes one | 100 through 599; optional because browser capture may not expose it | None | 200 | ["INS-04", "OPS-03"] |
| original_file_id | fk:OriginalFile optional | NULL | Exact bytes preserved by a successful capture | Required when captured; public file with matching stored bytes | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| document_version_id | fk:DocumentVersion optional | NULL | Document edition identified from the captured content | Set only after identification; captures of the same edition may share one version | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| error_summary | text optional | NULL | Safe reason a capture failed | Required when failed; no credentials or browser secrets | None | Access denied after browser navigation. | ["OPS-03"] |

Constraints: captured requires original_file_id and completed_at; failed requires error_summary and completed_at; running has no completed_at; the same URL may have many captures over time; multiple URLs may capture the same OriginalFile

Indexes: source_url_id,created_at DESC; discovery_run_id,status; document_version_id; original_file_id

## OriginalFile

Content-addressed exact bytes preserved from a public source or private customer upload.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account optional | NULL | Owner of a private file; NULL for public corpus files | Owner immutable; public files have NULL; private deduplication stays within the owner | None | No authentic customer identity or document value inspected. | ["OPS-01"] |
| sha256 | char(64) required | none | Cryptographic identity of the exact bytes | Lowercase hexadecimal; verified on write and integrity read | None | cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb | ["INS-04", "OPS-03"] |
| storage_key | varchar(500) required | none | Opaque private object-storage location | Unique; never expose a direct filesystem path | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-01"] |
| byte_size | bigint required | none | Exact stored byte length | Nonnegative and equal to stored object length | bytes | 2483921 | ["INS-04", "OPS-03"] |
| media_type | varchar(150) required | none | Detected actual media type | Derived from content rather than trusted filename extension | None | application/pdf | ["INS-04", "OPS-03"] |
| availability | enum required | available | Whether preserved bytes may currently be used | available, quarantined or deleted | None | available | ["INS-04", "OPS-01"] |
| last_verified_at | instant required | now | Most recent successful hash-integrity check | UTC; verification recomputes SHA-256 from stored bytes | instant | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |

Constraints: unique(owner_id,sha256) NULLS NOT DISTINCT; storage_key unique and namespaced by public corpus or owning account; owner_id NULL means public corpus; non-NULL means private and can never be changed to NULL; SourceCapture may reference only a public file; CustomerUploadedDocument must reference a same-owner private file; deleted private content cannot be read or reintroduced by a worker, restore or index rebuild

Indexes: sha256; owner_id,availability

## CustomerUploadedDocument

One private document supplied by a customer, separate from its content-addressed bytes.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "INS-03", "OPS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| original_file_id | fk:OriginalFile required | none | Exact private bytes supplied by the customer | OriginalFile.owner_id equals owner_id and its digest verifies before use | None | Synthetic design example only; no real customer identity included. | ["CUS-02", "INS-03", "OPS-01"] |
| source_message_id | fk:Message optional | NULL | Conversation message through which the file was supplied | Same owner; NULL for an authorized non-message import | None | Intentionally no real customer or authentication identity inspected or included. | ["CUS-02", "OPS-01"] |
| display_name | varchar(300) optional | NULL | Encrypted customer-facing filename or label | Never used as document identity; sanitize before display | None | star-policy-schedule.pdf (synthetic) | ["CUS-02", "OPS-01"] |
| kind | enum required | other | Buying/comparison document category; claim packs, receipts and treatment bills are outside scope | offer,quote,policy_schedule,endorsement,member_certificate,other | None | policy_schedule (synthetic) | ["INS-03"] |
| review_status | enum required | received | Whether the private document can be understood and used | received,readable,classified,unusable,conflicted | None | classified (synthetic) | ["CUS-02", "INS-03", "OPS-01"] |

Constraints: unique(id,owner_id); owner_id immutable; original_file_id points to a private OriginalFile owned by the same account; display_name is encrypted and is never a document-identity key

Indexes: owner_id,created_at; owner_id,kind,review_status; original_file_id

## DocumentSeries

Stable identity of one continuing publication across editions, such as a product policy wording.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| issuer_id | fk:Insurer optional | NULL | Insurer that issued the publication | NULL for regulator, government or independent publications | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| name | text required | none | Stable human-readable series name | Nonempty; do not put the edition year in this field | None | Care Supreme Policy Wording | ["INS-02", "INS-04"] |
| kind | enum required | other | Document category | policy_wording, customer_information_sheet, prospectus, endorsement, premium_table, provider_list, regulation, notice, comparison, web_page or other | None | policy_wording | ["INS-02", "INS-04"] |
| authority | enum required | unknown | Who authored or issued the claims inside the document | insurer_issued, regulator_issued, government_issued, independent_analysis or unknown | None | insurer_issued | ["INS-02", "DEC-01"] |
| relevance | enum required | unresolved | Relationship of the captured content to CoverGuide's medical-expense scope | relevant, supporting, unrelated or unresolved | None | relevant | ["INS-02", "INS-04"] |

Constraints: issuer_id required when authority is insurer_issued; independent_analysis does not become contractual authority because an insurer is discussed

Indexes: issuer_id,kind; authority,relevance; name

## DocumentVersion

One identified edition within a DocumentSeries, with evidence-backed dates and explicit supersession.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| document_series_id | fk:DocumentSeries required | none | Publication series containing this edition | Required | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| version_label | varchar(200) optional | NULL | Printed edition or version label | Original-backed; acquisition date is not a version label | None | Version 3 - 2025 | ["INS-02"] |
| identifiers | json:IdentifiersV1 required | empty array | Printed UINs and other document identifiers | Retain multiple or conflicting printed identifiers; never silently select one | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| language | varchar(35) optional | NULL | Printed document language | BCP47 code or NULL when unresolved | None | en-IN | ["INS-02"] |
| published_on | date optional | NULL | Printed publication date | Original-backed; never substitute capture date | calendar date | 2025-04-01 | ["INS-02", "INS-04"] |
| effective_from | date optional | NULL | First applicability date when established | Original-backed inclusive date; NULL means unknown | calendar date | 2025-04-01 | ["INS-02", "INS-03"] |
| effective_to | date optional | NULL | Last applicability date when established | Original-backed inclusive date; NULL means unknown, not unlimited | calendar date | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| supersedes_id | fk:DocumentVersion optional | NULL | Earlier edition explicitly replaced by this edition | Same DocumentSeries; acyclic; evidence required before verified status | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| review_status | enum required | unreviewed | Confidence in edition identity and applicability metadata | unreviewed, identified, verified or conflicted | None | verified | ["INS-02", "INS-04"] |

Constraints: supersedes_id belongs to the same DocumentSeries and is acyclic; effective_to is on or after effective_from; is_latest is derived and never stored; latest discovered, latest published and currently applicable remain distinct

Indexes: document_series_id,published_on DESC; document_series_id,effective_from,effective_to; review_status

## DocumentPage

One physical PDF page and its explicit review state, including pages on which extraction failed.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| original_file_id | fk:OriginalFile required | none | Exact PDF containing this page | File media type must be PDF | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| page_number | integer required | none | One-based physical page number | At least 1 and no greater than the preserved PDF page count | page | 37 | ["INS-04"] |
| printed_label | varchar(80) optional | NULL | Page label printed inside the document | May differ from physical page_number | None | Page 34 of 52 | ["INS-04"] |
| review_state | enum required | unread | How completely this physical page has been inspected | unread, text_read, visually_reviewed, fully_reviewed or unresolved | None | fully_reviewed | ["INS-04", "OPS-03"] |

Constraints: unique(original_file_id,page_number); non-PDF originals do not create DocumentPage rows; page dimensions and rotation are read from preserved PDF bytes rather than duplicated here

Indexes: original_file_id,page_number; review_state

## EvidenceSpan

One exact passage, table cell, footnote or region from either a public capture or private customer upload.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source publication or effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| source_capture_id | fk:SourceCapture optional | NULL | Public web capture supplying this evidence | Exactly one of source_capture_id or customer_uploaded_document_id is set | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| customer_uploaded_document_id | fk:CustomerUploadedDocument optional | NULL | Private customer upload supplying this evidence | Exactly one of source_capture_id or customer_uploaded_document_id is set | None | Synthetic private schedule upload identity only. | ["CUS-02", "INS-03", "OPS-01"] |
| page_id | fk:DocumentPage optional | NULL | Physical PDF page containing the evidence | Required for PDF locators; page OriginalFile must match the selected public capture or private upload | None | Synthetic design example; no customer value used. | ["INS-04"] |
| section_label | varchar(200) optional | NULL | Printed section or table label | Preserve the source wording | None | Pre-existing Disease Waiting Period | ["INS-04", "RET-01"] |
| quote | text required | none | Exact extracted or visually transcribed source text | Must resolve from the preserved bytes and locator; no paraphrase | None | Synthetic design example; no customer value used. | ["INS-04", "DEC-01"] |
| context | json:EvidenceContextV1 required | empty object | Headings, table axes, units, footnotes and connected passages required to interpret the quote | Closed versioned structure; retain material qualifiers | None | Synthetic design example; no customer value used. | ["INS-04", "DEC-01"] |
| method | enum required | none | How the passage was read | native_text, ocr_verified, manual_visual, html or json | None | native_text | ["INS-04", "OPS-03"] |
| verification | enum required | unverified | Independent verification state | unverified, text_verified, visually_verified, reviewed or failed | None | reviewed | ["INS-04", "DEC-01"] |
| locator | json:OriginalLocatorV1 required | none | Exact PDF region, HTML selector, JSON pointer or text range | Must resolve exactly against the OriginalFile reached through the selected evidence source | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |

Constraints: exactly one of source_capture_id or customer_uploaded_document_id is set; source capture is captured and mapped to a DocumentVersion; PDF evidence requires a page from the same OriginalFile; non-PDF evidence has no page_id; quote must resolve from immutable captured bytes and locator; verification does not by itself establish semantic entailment

Indexes: source_capture_id; page_id,section_label; verification; customer_uploaded_document_id

## Product

Stable insurer product family, independent of policy editions, named variants and optional additions.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| insurer_id | fk:Insurer required | none | Insurer offering the product | Required; a package component retains its own insurer | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| name | varchar(250) required | none | Official product-family name | Nonempty; not globally unique; edition years belong to PolicyVersion | None | Care Supreme | ["INS-01", "INS-02"] |
| benefit_type | enum required | unresolved | How the product pays benefits | medical_indemnity, fixed_benefit, hybrid, addon or unresolved | None | medical_indemnity | ["INS-01", "INS-05"] |
| lifecycle_status | enum required | unresolved | Whether the product is sold or retained only historically | open, withdrawn, renewal_only, historical or unresolved | None | open | ["INS-01", "INS-03"] |
| recommendation_role | enum required | unresolved | How CoverGuide may use the product in advice | primary_policy, supplementary, reference_only, excluded or unresolved | None | primary_policy | ["INS-01", "DEC-01"] |
| identity_evidence_id | fk:EvidenceSpan required | none | Exact original passage establishing product identity | Required reviewed evidence; a comparison name alone cannot establish official identity | None | Synthetic design example; no customer value used. | ["INS-01", "INS-04"] |

Constraints: no global unique-name assumption; identity_evidence_id required; recommendation_role and benefit_type remain distinct

Indexes: insurer_id,name; benefit_type,lifecycle_status,recommendation_role

## PolicyVersion

One complete legal terms package for a Product, assembled from every applicable governing document.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| product_id | fk:Product required | none | Product governed by this policy version | Required | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| uin | varchar(100) optional | NULL | Curated resolved product UIN | Original-backed; conflicts remain unresolved rather than silently selected | None | CHIHLIP25047V012425 | ["INS-02", "INS-05"] |
| version_label | varchar(200) optional | NULL | Printed or curated policy edition label | Original-backed; source capture date is not an edition label | None | 2025 edition | ["INS-02"] |
| publication_status | enum required | draft | Curation and publication state | draft, reviewed, published, superseded or blocked | None | reviewed | ["INS-04", "OPS-03"] |
| supersedes_id | fk:PolicyVersion optional | NULL | Earlier legal terms package replaced by this one | Same Product; acyclic; evidence required before publication | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| applicability | json:ApplicabilityV1 required | none | Dates, issue or renewal events and other boundaries selecting this policy version | Closed typed structure; unknown material bounds block affected advice | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03", "INS-05"] |

Constraints: supersedes_id belongs to the same Product and is acyclic; publication requires all required PolicyVersionDocument rows and material dependencies; a newer discovered document does not automatically change applicability

Indexes: product_id,publication_status; product_id,uin; product_id,supersedes_id

## PolicyVersionDocument

Membership, role, conditional applicability and proven precedence of one DocumentVersion in a PolicyVersion.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| policy_version_id | fk:PolicyVersion required | none | Policy version whose legal document bundle includes this document | Required | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| document_version_id | fk:DocumentVersion required | none | Exact source-document edition | Required; must have at least one successful SourceCapture before reviewed use | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| role | enum required | none | Legal or explanatory role of the document | base_wording, customer_information_sheet, prospectus, endorsement, regulatory_modification, referenced_schedule or other_dependency | None | base_wording | ["INS-02", "INS-04"] |
| required_for_policy | boolean required | true | Whether the policy version is incomplete without this applicable document | False only when applicability explains the limited role | None | True | ["INS-04", "INS-05"] |
| applicability | json:ApplicabilityV1 required | none | Conditions under which this document participates in the policy version | No universal newest-document priority | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| precedence_evidence_id | fk:EvidenceSpan optional | NULL | Exact clause proving that this document controls another | NULL means no precedence has been proven | None | Synthetic design example; no customer value used. | ["INS-04", "INS-05"] |

Constraints: unique(policy_version_id,document_version_id,role); contractual roles require insurer-issued or regulator-issued authority; independent analysis can only be supporting discovery material; required applicable documents must be present before publication; precedence is never inferred from download date

Indexes: policy_version_id,role; document_version_id

## ProductVariant

One insurer-defined base variant and its allowed sums insured, deductibles, room categories and family choices.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| policy_version_id | fk:PolicyVersion required | none | Policy version governing the variant | Required | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| name | varchar(200) required | Default | Official variant name or Default when the product has no named tier | Nonempty; no coverage inferred from the name | None | Gold | ["INS-01", "INS-03"] |
| choices | json:ConfigurationV1 required | none | Allowed sum insured, deductible, room, family and other base selectors | Typed values and units; describes allowed choices rather than one row per combination | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| availability | json:ApplicabilityV1 required | none | Sale, renewal, age, territory and insured-person conditions | Unresolved availability is not an exclusion | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| identity_evidence_id | fk:EvidenceSpan required | none | Original passage establishing the variant and its selectors | Required reviewed evidence | None | Synthetic design example; no customer value used. | ["INS-03", "INS-04"] |

Constraints: unique(policy_version_id,name); products without a named tier use exactly one Default variant; choices do not represent a customer selection

Indexes: policy_version_id,name

## ProductOption

One optional or mandatory add-on, rider or election available with a ProductVariant.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC; immutable; not a source effective date | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| product_variant_id | fk:ProductVariant required | none | Base variant on which the option is available | Required | None | Synthetic design example; no customer value used. | ["INS-01", "INS-03"] |
| option_policy_version_id | fk:PolicyVersion optional | NULL | Separate policy terms for the option when they exist | Optional because some options are fully defined inside the base policy version | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| name | varchar(200) required | none | Official option name | Nonempty; unique within the variant | None | Claim Shield | ["INS-01", "INS-03"] |
| selection_kind | enum required | optional | Whether the customer may omit the option | optional or mandatory | None | optional | ["INS-03"] |
| conditions | json:ApplicabilityV1 required | none | Eligibility, dates, dependencies and incompatible selections | Closed typed conditions; incompatibility belongs here rather than in an overloaded status | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| identity_evidence_id | fk:EvidenceSpan required | none | Exact original passage establishing the option | Required reviewed evidence | None | Synthetic design example; no customer value used. | ["INS-03", "INS-04"] |

Constraints: unique(product_variant_id,name); option_policy_version_id does not by itself mean the option was selected by a customer

Indexes: product_variant_id,name; option_policy_version_id

## CustomerPolicy

Stable identity of one insurer-issued customer policy or customer-specific offer.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| policy_number | encrypted_varchar(200) optional | NULL | Insurer-issued policy identifier | Owner-scoped and encrypted; not assumed globally unique | None | SH-12345 (synthetic) | ["INS-03", "OPS-01"] |
| insurer_id | fk:Insurer required | none | Insurer that issued the policy or personal offer | Required before creating a structured customer-policy record | None | Synthetic design example only; no real customer identity included. | ["INS-03"] |
| proposer_id | fk:Person optional | NULL | Person named as proposer or policyholder | Same owner; proposer, payer and insured people remain distinct | None | Intentionally no real customer or authentication identity inspected or included. | ["CUS-01", "INS-03"] |
| payer_id | fk:Person optional | NULL | Person paying the premium | Same owner; proposer, payer and insured people remain distinct | None | Intentionally no real customer or authentication identity inspected or included. | ["CUS-01", "INS-03"] |
| coverage_type | enum required | unresolved | How insured people share the issued cover | individual,family_floater,group_member,unresolved | None | family_floater (synthetic) | ["INS-03", "INS-07"] |
| lifecycle_status | enum required | unresolved | Current state of the customer-specific policy relationship | offered,active,lapsed,expired,cancelled,declined,unresolved | None | active (synthetic) | ["INS-03", "INS-08"] |
| group_master_reference | encrypted_varchar(250) optional | NULL | Employer or master-policy reference for group membership | Allowed only for group_member; it does not prove individual membership | None | EMP-GRP-77 (synthetic) | ["INS-03", "INS-07", "OPS-01"] |

Constraints: unique(id,owner_id); owner_id immutable; proposer_id and payer_id have the same owner_id; group_master_reference is allowed only when coverage_type=group_member; public recommendations do not create CustomerPolicy rows

Indexes: owner_id,insurer_id; owner_id,lifecycle_status

## CustomerPolicyRevision

One exact set of insurer-issued customer selections applying during a defined interval.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| customer_policy_id | fk:CustomerPolicy required | none | Customer policy whose exact issued terms this revision records | Same owner | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03", "INS-07"] |
| revision_number | positive_integer required | none | Monotonic revision order within the customer policy | At least 1; unique within customer_policy_id | count | 2 (synthetic) | ["INS-02", "INS-03", "INS-07"] |
| product_variant_id | fk:ProductVariant optional | NULL | Public product variant matched to the issued cover | May remain NULL while unresolved; required for verified variant-specific advice | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03", "INS-07"] |
| policy_term | daterange optional | NULL | Full insurer renewal term containing this revision | Nonempty when present; required for an active verified policy | None | [2026-01-01,2027-01-01) (synthetic) | ["INS-07", "INS-08"] |
| effective_during | daterange optional | NULL | Interval during which this exact issued revision controls | Nonempty and contained in policy_term when both are known | None | [2026-07-01,2027-01-01) (synthetic endorsement revision) | ["INS-02", "INS-03", "INS-07"] |
| selected_choices | json:CustomerPolicySelectionV1 required | {'choices': [], 'unresolved_keys': []} | Actual issued sum insured, deductible, room and other base selections | Strict versioned structure; contains no members or ProductOption selections | None | Synthetic: sum_insured INR 1000000, deductible INR 0, room_category single_private_room. | ["INS-02", "INS-03", "INS-07"] |
| selection_evidence_id | fk:EvidenceSpan optional | NULL | Private schedule passage supporting the base selections | Required before verification unless each selected choice has other exact evidence | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03", "INS-07"] |
| verification_status | enum required | reported | Confidence that this revision matches the insurer-issued cover | reported,verified,conflicted | None | verified (synthetic) | ["INS-02", "INS-03", "INS-07"] |

Constraints: unique(customer_policy_id,revision_number); unique(id,owner_id); owner_id immutable; verified revisions for one CustomerPolicy cannot have unresolved overlapping effective_during ranges; effective_during is contained by policy_term when both are known; product_variant insurer matches CustomerPolicy insurer when verification_status=verified

Indexes: customer_policy_id,revision_number; GiST policy_term; GiST effective_during

## PolicyMember

One person actually covered under one customer policy revision.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Exact issued policy revision providing this membership | Same owner | None | Synthetic design example only; no real customer identity included. | ["CUS-01", "INS-03", "INS-07"] |
| person_id | fk:Person required | none | Person actually covered by this policy revision | Same owner; a family relationship alone never creates membership | None | Intentionally no real customer or authentication identity inspected or included. | ["CUS-01", "INS-03", "INS-07"] |
| covered_during | daterange required | none | Person-specific insured interval | Nonempty; contained by the revision policy_term when that term is known | None | [2026-04-01,2027-01-01) (synthetic) | ["CUS-01", "INS-03", "INS-07"] |
| member_identifier | encrypted_varchar(160) optional | NULL | Insurer member or certificate identifier | Encrypted and owner-scoped; not a person deduplication key | None | MEM-002 (synthetic) | ["INS-03", "OPS-01"] |
| evidence_span_id | fk:EvidenceSpan optional | NULL | Schedule or member-certificate passage proving membership | Required when verification_status=verified | None | Synthetic design example only; no real customer identity included. | ["CUS-01", "INS-03", "INS-07"] |
| verification_status | enum required | reported | Whether actual policy membership is established | reported,verified,conflicted | None | verified (synthetic) | ["CUS-01", "INS-03", "INS-07"] |

Constraints: unique(id,owner_id); owner_id immutable; no overlapping duplicate verified membership for the same customer policy and person; covered_during is nonempty and consistent with the revision term; family role is read from PersonRelationship and is not duplicated here

Indexes: customer_policy_revision_id,person_id; owner_id,person_id; GiST covered_during

## CustomerPolicyOption

One customer-specific selected, declined or unresolved ProductOption decision.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Exact customer policy revision whose option choice is recorded | Same owner | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03"] |
| product_option_id | fk:ProductOption required | none | Public option offered by the matched product variant | Must belong to customer revision product_variant_id when that variant is resolved | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03"] |
| selection_status | enum required | unresolved | Whether this customer selected the option | selected,declined,unresolved | None | selected (synthetic maternity option) | ["INS-02", "INS-03"] |
| evidence_span_id | fk:EvidenceSpan optional | NULL | Private offer or schedule passage supporting the option decision | Required for a verified selected or declined state | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03"] |
| verification_status | enum required | reported | Reliability of this customer-specific option selection | reported,verified,conflicted | None | verified (synthetic) | ["INS-02", "INS-03"] |

Constraints: unique(customer_policy_revision_id,product_option_id); unique(id,owner_id); owner_id immutable; verified selected or declined rows require exact private evidence; ProductOption belongs to the revision ProductVariant when that variant is resolved

Indexes: customer_policy_revision_id,selection_status; product_option_id

## CustomerPolicyFact

One document-backed structured fact about a particular customer's issued policy revision.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | UTC; changes only with a stored field change | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Required and immutable | None | Synthetic design example only; no real customer value included. | ["OPS-01"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Exact issued revision to which the fact belongs | Same owner | None | Synthetic design example only; no real customer value included. | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| person_id | fk:Person optional | NULL | Affected insured when the fact is person-specific | Same owner; NULL means policy or shared-cover scope | None | Synthetic design example only; no real customer value included. | ["INS-03", "INS-07"] |
| fact_type | varchar(100) required | none | Finite code-controlled meaning of this issued-policy fact | personal_copay,personal_exclusion,premium_loading,waiting_period_change,waiver,additional_cover,continuity_credit,other_issued_term; AI output cannot create a new type | None | personal_copay (synthetic) | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| value | json:CustomerPolicyFactValueV1 required | none | Strict typed value selected by fact_type | Application validator selects the matching closed schema; personal terms use RuleV1, additional cover uses typed amount/start/scope, and continuity uses typed duration/amount/benefit scope | None | Synthetic 20 percent diabetes co-pay rule. | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| related_customer_policy_id | fk:CustomerPolicy optional | NULL | Prior policy supplying history when this is continuity credit | Required only for continuity_credit and must have the same owner | None | Synthetic design example only; no real customer value included. | ["INS-07", "INS-08"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact private offer, schedule or endorsement passage | Private evidence upload belongs to owner; public wording alone cannot establish a customer-specific fact | None | Synthetic design example only; no real customer value included. | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| verification_status | enum required | extracted | Review state of the structured policy fact | extracted,verified,conflicted | None | verified (synthetic) | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| supersedes_id | fk:CustomerPolicyFact optional | NULL | Earlier incorrect interpretation replaced by this row | Same owner and customer policy revision; acyclic; one direct successor | None | Synthetic design example only; no real customer value included. | ["CUS-02", "INS-03"] |

Constraints: unique(id,owner_id); owner_id immutable; evidence_span_id resolves through a CustomerUploadedDocument owned by owner_id; fact_type selects exactly one closed CustomerPolicyFactValueV1 branch; related_customer_policy_id is required only for continuity_credit; supersedes_id is same-owner, same-revision, acyclic and has at most one successor; customer statements without insurer evidence remain CustomerFact rows and do not create verified CustomerPolicyFact rows

Indexes: customer_policy_revision_id,fact_type,person_id; related_customer_policy_id; GIN value jsonb_path_ops; supersedes_id unique where nonnull

## PolicyRule

One immutable, reviewed condition, benefit, restriction or calculation instruction from a public policy version.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| policy_version_id | fk:PolicyVersion required | none | Exact public policy version containing the rule | Required public PolicyVersion; immutable after creation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| rule_key | varchar(160) required | none | Stable readable identity for this logical rule within the policy version | Nonempty controlled key; a correction keeps the key and supersedes the earlier row | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| rule_type | enum required | none | Controlled category used for retrieval and validation | definition,eligibility,coverage,exclusion,exception,waiting_period,limit,deduction,accumulation,restoration,calculation,precedence,operational_right | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| body | json:RuleV1 required | none | Closed structured conditions, required inputs, effects and optional table definition | RuleV1; three-valued evaluation; rule_type and table semantics validated; stored text is never executable | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| review_status | enum required | draft | Whether the complete rule and all required evidence may be used | draft,verified,blocked,superseded | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| supersedes_id | fk:PolicyRule optional | NULL | Earlier interpretation corrected by this immutable row | Same policy_version_id and rule_key; acyclic; at most one successor | None | Synthetic correction link only; no invented insurer value. | ["INS-04", "OPS-06"] |

Constraints: public only; no customer owner field; immutable after creation; verified requires sufficient required PolicyRuleEvidence and verified required PolicyRuleLink closure; body validates against RuleV1 and the selected rule_type; supersedes_id has the same policy_version_id and rule_key, is acyclic and has at most one successor; only a verified unsuperseded rule may enter a new KnowledgeRelease

Indexes: policy_version_id,rule_type,review_status; policy_version_id,rule_key; body GIN jsonb_path_ops for registered input and output keys

## PolicyRuleEvidence

One exact public source passage supporting, defining, restricting or contradicting a policy rule.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| policy_rule_id | fk:PolicyRule required | none | Structured policy rule supported or restricted | Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact public original passage | EvidenceSpan must be public and resolve to the applicable policy-version document set | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| role | enum required | none | How passage relates to rule | supports,defines,restricts,excepts,contradicts,precedence,table_header,table_cell,footnote | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| is_required | boolean required | true | Whether omitting this passage makes the rule unsafe to verify | Omission blocks affected rule | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |

Constraints: unique(policy_rule_id,evidence_span_id,role); evidence_span_id must be public and applicable to policy_rule_id.policy_version_id; verified PolicyRule requires all required evidence links to be present and independently reviewed as part of the rule review

Indexes: policy_rule_id,role; evidence_span_id

## PolicyRuleLink

A reviewed connection requiring two policy rules to be interpreted together.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| from_policy_rule_id | fk:PolicyRule required | none | Rule whose interpretation requires another rule | Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| to_policy_rule_id | fk:PolicyRule required | none | Definition, exception, prerequisite or calculation rule that must also load | Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| link_type | enum required | none | Meaning of the rule connection | definition,prerequisite,exception,overrides,calculation_input,scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |

Constraints: unique(from_policy_rule_id,to_policy_rule_id,link_type); no self link; both rules belong to the same PolicyVersion unless a later explicitly reviewed cross-version use is introduced; calculation_input and overrides links are acyclic; verified source rule requires its mandatory link closure to resolve to verified rules

Indexes: from_policy_rule_id,link_type; to_policy_rule_id

## PolicyRuleTableCell

One original-backed result selected by the complete axes declared in a policy rule body.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| policy_rule_id | fk:PolicyRule required | none | Table-lookup policy rule declaring the axes and result meaning | Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| selectors | json:TableSelectorsV1 required | none | Exact value for every axis declared by the parent rule body | Exactly all declared axes; quantity/code types match | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| value | json:ExpressionV1 required | none | Typed amount, limit, reference or expression returned by this cell | Up to SI is bounded by SI, not unlimited | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact original cell geometry and transcription | Public EvidenceSpan applicable to the parent rule's policy version | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |

Constraints: unique(policy_rule_id,selectors); selectors provide every declared axis exactly once and no undeclared axis; overlapping selector ranges block parent rule verification; headers and footnotes are required PolicyRuleEvidence links on the parent rule

Indexes: policy_rule_id; selectors GIN jsonb_path_ops

## ProviderLocation

One exact public hospital or healthcare-facility branch identity used for network matching.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| facility_name | varchar(300) required | none | Printed name of the exact facility or branch | Nonempty; never sufficient by itself for automatic identity merge | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| organization_name | varchar(250) optional | NULL | Parent healthcare organization when separately established | Unknown cannot match all branches | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| address | text optional | NULL | Original-backed branch address | No fuzzy automatic merge | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| city | varchar(150) optional | NULL | Branch city | Not customer residence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| postal_code | varchar(20) optional | NULL | Branch postcode | Country-specific validation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| country_code | char(2) required | IN | ISO3166 country | Explicit country for territory comparisons | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| external_identifiers | json:IdentifiersV1 required | empty array | Insurer or registry branch identifiers with provenance | Issuer scoped; conflicts preserved | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| identity_status | enum required | unresolved | Branch identity resolution | unresolved,verified,conflicted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| supersedes_id | fk:ProviderLocation optional | NULL | Earlier branch identity corrected by this immutable row | Acyclic; at most one successor; correction evidence required | None | Synthetic identity correction only; no invented provider identity. | ["OBS-02", "OPS-06"] |

Constraints: no name-only uniqueness or automatic merge; verified requires a supported external identifier or sufficiently specific name-and-address evidence; supersedes_id is acyclic and has at most one successor

Indexes: city,postal_code; external_identifiers GIN; facility_name

## ProviderNetworkSnapshot

One dated, scoped insurer network source or directory query, including a zero-result or failed check.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| insurer_id | fk:Insurer required | none | Insurer whose provider network or exclusion source was checked | Required for network_membership,exclusion,restricted_network,authorization; optional for clinician participation/search scope; NULL permitted for insurer-independent wheelchair_access | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| product_variant_id | fk:ProductVariant optional | NULL | Product-specific or restricted network variant when the source establishes one | NULL is insurer-wide only if original supports | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| source_capture_id | fk:SourceCapture required | none | Preserved directory, PDF, API response or failed retrieval attempt | Public source capture; exact bytes or explicit failure retained | None | No authentic new network capture invented for the design. | ["OBS-02", "INS-04", "OPS-03"] |
| scope | json:ProviderNetworkScopeV1 required | none | Exact geography, network tier, service and query filters checked | Closed ProviderNetworkScopeV1; no unstated expansion of scope | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| observed_at | instant required | none | When the provider status was checked or represented | Required source-observation instant; distinct from database creation and document publication | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| completeness | enum required | unknown | What absence from this exact result can establish | complete_for_scope,partial,unknown,failed | None | No authentic completeness claim established; examples are synthetic. | ["OBS-02", "OPS-03"] |
| scope_evidence_id | fk:EvidenceSpan optional | NULL | Exact heading or source statement establishing the snapshot scope | Public EvidenceSpan from source_capture_id when available; may be NULL for failed capture | None | No authentic field value established; synthetic scope examples only. | ["OBS-02", "INS-04"] |

Constraints: product_variant_id, when present, belongs to insurer_id; complete_for_scope requires successful source capture, closed traversal and explicit scope evidence; failed capture cannot imply provider absence; immutable; a later directory check creates another snapshot

Indexes: insurer_id,observed_at DESC; product_variant_id,observed_at DESC; scope GIN

## ProviderNetworkEntry

One exact facility branch status printed in one immutable provider-network snapshot.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| provider_network_snapshot_id | fk:ProviderNetworkSnapshot required | none | Exact dated insurer directory or list containing this entry | Required public snapshot | None | Synthetic snapshot reference only. | ["OBS-02", "INS-04"] |
| provider_location_id | fk:ProviderLocation required | none | Exact hospital or healthcare-facility branch | Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| network_status | enum required | none | Status explicitly represented by the source | network,restricted,excluded,unknown | None | Synthetic status only; no current hospital status asserted. | ["OBS-02"] |
| restrictions | json:NetworkRestrictionsV1 required | none | Entry-specific service, tier or other restrictions, including explicit none or unknown | Closed NetworkRestrictionsV1 backed by the same source | None | Synthetic restriction structure only. | ["OBS-02", "INS-04"] |
| effective_from | date optional | NULL | Source-stated first applicable date | No date inferred from download time | calendar date | No authentic date established for a provider entry. | ["OBS-02"] |
| effective_to | date optional | NULL | Source-stated last applicable date | On or after effective_from when both known | calendar date | No authentic date established for a provider entry. | ["OBS-02"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact directory row or exclusion-list passage | Public EvidenceSpan from the parent snapshot source capture | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |

Constraints: unique(provider_network_snapshot_id,provider_location_id,network_status); effective_to is not before effective_from; an entry establishes only its printed network status; cashless authorization and claim payment remain separate

Indexes: provider_network_snapshot_id,network_status; provider_location_id

## Quote

One immutable, evidence-backed personal insurer quote for an exact customer profile and product selection.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| profile_revision_id | fk:CustomerProfileRevision required | none | Exact customer profile used for this quote observation | Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| product_variant_id | fk:ProductVariant required | none | Public product variant used for the quote | Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| quoted_selection | json:AcceptedSelectionV1 required | none | People, option selections, SI and deductible | Typed IDs/quantities; no default acceptance | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| insurer_quote_reference | varchar(200) optional | NULL | Issuer quote reference where supplied | Owner-scoped; encrypted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| issued_at | instant optional | NULL | Issuer quote time | Source-supported | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| valid_until | instant optional | NULL | Offer expiry | Unknown not indefinite | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| total | json:QuantityV1 required | none | Verified payable total or explicit unknown | Money; components reconcile before finite validated total | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| coverage_term | json:TemporalExtentV1 required | none | Quoted insurance term | Distinct from payment frequency | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| price_breakdown | json:QuotePriceBreakdownV1 required | none | Closed ordered base, option, loading, discount, tax and fee breakdown | QuotePriceBreakdownV1; item evidence belongs to owner_id and source quote | None | Synthetic breakdown only; no customer quote invented. | ["OBS-01", "CAL-01", "INS-04"] |
| payment_schedule | json:QuotePaymentScheduleV1 required | none | Quoted instalment amounts and dates or explicit unavailable state | QuotePaymentScheduleV1; no inferred payment receipt or policy activation | None | Synthetic schedule only; no customer quote invented. | ["OBS-01", "CAL-01", "INS-04"] |
| source_evidence_id | fk:EvidenceSpan required | none | Exact private insurer quote evidence | EvidenceSpan resolves through a CustomerUploadedDocument owned by owner_id | None | No real customer quote evidence inspected. | ["OBS-01", "INS-04", "OPS-01"] |

Constraints: unique(id,owner_id); owner_id immutable; all person, option and evidence references inside JSON belong to owner_id or the quoted public product variant; created only from adequate insurer quote evidence; reported verbal price remains CustomerFact; profile correction or quote expiry invalidates current reuse without rewriting the historical quote; quote acceptance does not create in-force cover; issued cover uses CustomerPolicy

Indexes: owner_id,profile_revision_id; owner_id,product_variant_id,valid_until; total GIN; payment_schedule GIN

## KnowledgeRelease

Immutable set of reviewed policy rules that the buying adviser may use together.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| release_number | bigint required | none | Human-readable knowledge release number | Positive and unique | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| state | enum required | draft | Publication state | draft,ready,published,retired,blocked | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| supported_scope | json:CapabilityScopeV1 required | none | Exact insurers, request types, rule types and known gaps supported by this release | Closed CapabilityScopeV1; unresolved or blocked capability remains explicit | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| manifest_sha256 | char(64) required | none | Digest of the exact rule membership and supported scope | Recomputed and verified before publication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| published_at | instant optional | NULL | Atomic publication event | Single publication transaction | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| previous_release_id | fk:KnowledgeRelease optional | NULL | Immediately preceding published knowledge release | Acyclic | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |

Constraints: release_number unique and positive; published releases and their member rows are immutable; manifest_sha256 equals canonical membership plus supported_scope; published_at is required exactly when state is published or retired; previous_release_id is acyclic and points to an earlier release

Indexes: state,release_number DESC; published_at DESC

## KnowledgeReleaseRule

Includes one exact reviewed policy rule in one knowledge release.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| knowledge_release_id | fk:KnowledgeRelease required | none | Immutable knowledge release | Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| policy_rule_id | fk:PolicyRule required | none | Exact reviewed policy rule available to the adviser | Public; reviewed | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |

Constraints: unique(knowledge_release_id,policy_rule_id); policy rule is verified, has exact evidence and all mandatory linked rules are included before publication; rows are immutable after their release is published

Indexes: knowledge_release_id,policy_rule_id unique; policy_rule_id

## KnowledgeChannel

Selects the current published knowledge release for one application environment.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | timestamptz required | now | When the selected release last changed | Updated atomically with current_release_id and generation | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| name | varchar(80) required | none | Application environment name | Unique configured name such as production, review or pilot | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| current_release_id | fk:KnowledgeRelease optional | NULL | Published release currently used in this environment | NULL before first publication; otherwise target state is published | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| generation | bigint required | 0 | Monotonic compare-and-swap number preventing lost publication updates | Monotonic | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |

Constraints: name unique; current_release_id is NULL or points to a published release; generation changes atomically with current_release_id

Indexes: name unique; current_release_id

## PolicySearchChunk

Replaceable public search index text for one exact section of a policy document.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| document_version_id | fk:DocumentVersion required | none | Exact public document edition indexed by this chunk | Required public DocumentVersion | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| evidence_span_ids | json:UuidListV1 required | none | Ordered exact public evidence spans covered by this chunk | Every ID exists and belongs to document_version_id; validated before retrieval | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| text | text required | none | Searchable derivative text from the exact evidence spans | Never treated as independent original truth | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| lexical_vector | tsvector required | derived | PostgreSQL lexical-search representation | Rebuildable; language configuration version recorded | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| embedding | vector(1024) optional | NULL | Optional local BGE-M3 semantic-search vector | Only qualified1024-dim adapter output; no evaluation material | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| index_version | varchar(160) required | none | Chunking, tokenizer and embedding implementation version | Immutable identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| chunk_sha256 | char(64) required | none | Fingerprint of text, evidence ordering and index version | Canonical SHA-256; unique within document and index version | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |

Constraints: unique(document_version_id,index_version,chunk_sha256); all evidence_span_ids resolve to public spans in document_version_id; derivative text and vectors never replace the original evidence spans; retrieval eligibility is obtained by joining current KnowledgeReleaseRule rows through PolicyRuleEvidence

Indexes: document_version_id,index_version; GIN lexical_vector; HNSW embedding vector_cosine_ops WHERE embedding IS NOT NULL

## Recommendation

One saved buying/comparison result for an exact customer profile and published policy-knowledge release.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn required | none | Owning processing turn | Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| advice_request_id | fk:AdviceRequest required | none | Customer advice goal answered | Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| profile_revision_id | fk:CustomerProfileRevision required | none | Exact customer profile evaluated | Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| knowledge_release_id | fk:KnowledgeRelease required | none | Exact published policy-knowledge release used for this answer | Required published release; immutable after answer publication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| outcome | enum required | none | Buyer-advice result state | completed,conditional,clarification_required,insufficient_evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| supersedes_id | fk:Recommendation optional | NULL | Earlier recommendation replaced after a correction or later comparison | Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |

Constraints: unique(turn_id); turn, advice request and profile revision belong to the same owner and conversation; knowledge_release_id is published and immutable; supersedes_id has the same owner and advice request and is acyclic; technical failure is stored on Turn and does not create a Recommendation; completed or conditional publication requires no unsupported critical RecommendationStatement; unique(id,owner_id); owner_id immutable

Indexes: owner_id,advice_request_id,created_at DESC; turn_id unique; supersedes_id

## PolicyCandidateAssessment

One exact public policy configuration evaluated for the customer, including exclusions and uncertain candidates.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| recommendation_id | fk:Recommendation required | none | Parent buying/comparison result | Same owner | None | Synthetic design example only; no real customer value inspected. | ["DEC-01", "OPS-01"] |
| product_variant_id | fk:ProductVariant required | none | Public policy variant evaluated | Variant is eligible for recommendation scope or explicitly retained as excluded | None | Synthetic design example only; no real customer value inspected. | ["INS-01", "INS-02", "INS-03", "DEC-01"] |
| evaluated_selection | json:AcceptedSelectionV1 required | none | Exact people, options and quantities evaluated | Closed selection; referenced people share owner and options belong to variant | None | Synthetic design example only; no real customer value inspected. | ["INS-03", "INS-05", "DEC-01"] |
| selection_commitment | char(64) required | none | Keyed canonical commitment distinguishing two private evaluated selections | Versioned HMAC over the closed evaluated_selection payload | None | Synthetic design example only; no real customer value inspected. | ["DEC-01", "OPS-06"] |
| disposition | enum required | none | How this candidate finished the comparison | recommended,alternative,eligible,excluded,conditional,insufficient_evidence | None | Synthetic design example only; no real customer value inspected. | ["INS-01", "INS-02", "DEC-01"] |
| rank | integer optional | NULL | Customer-facing order when the recommendation ranks candidates | Positive; NULL for excluded or unranked candidates; no unexplained score | None | Synthetic design example only; no real customer value inspected. | ["DEC-01"] |
| quote_id | fk:Quote optional | NULL | Exact personal quote used for price comparison | Same owner and profile revision; selection matches candidate; unexpired at evaluation or explicitly historical | None | Synthetic design example only; no real customer value inspected. | ["OBS-02", "DEC-01"] |

Constraints: unique(recommendation_id,product_variant_id,selection_sha256); rank IS NULL OR rank > 0; recommended and alternative ranks are unique within recommendation when nonnull; quote_id is NULL or matches owner, profile revision, variant and evaluated selection; no opaque numeric recommendation score is stored; unique(id,owner_id); owner_id immutable

Indexes: recommendation_id,rank; product_variant_id; quote_id

## PolicyRequirementMatch

How one policy candidate performs against one exact customer requirement.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable row identity | Primary key; immutable | None | Synthetic design example only; no real customer value inspected. | ["DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this match was recorded | UTC; immutable | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Customer account owning this private comparison | Required; immutable | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| candidate_assessment_id | fk:PolicyCandidateAssessment required | none | Policy configuration being compared | Same owner | None | Synthetic design example only; no real customer value inspected. | ["DEC-01"] |
| customer_requirement_id | fk:CustomerRequirement required | none | Exact requirement version tested | Same owner; active in recommendation profile revision | None | Synthetic design example only; no real customer value inspected. | ["CUS-03", "DEC-01"] |
| outcome | enum required | none | Whether the policy satisfies the requirement | meets,partly_meets,does_not_meet,unknown,not_applicable | None | Synthetic design example only; no real customer value inspected. | ["INS-01", "INS-02", "DEC-01"] |
| comparison_value | json:TypedValueV1 optional | NULL | Structured policy value compared with the customer's target | Unit and state are explicit; unknown differs from zero and not applicable | None | Synthetic design example only; no real customer value inspected. | ["CUS-03", "CAL-03", "DEC-01"] |
| provider_network_entry_id | fk:ProviderNetworkEntry optional | NULL | Exact dated facility result used for a hospital requirement | Entry belongs to the assessed insurer/variant scope; absence does not imply non-network unless snapshot is complete | None | Synthetic design example only; no real customer value inspected. | ["OBS-01", "DEC-01"] |

Constraints: unique(candidate_assessment_id,customer_requirement_id); requirement is active in the pinned customer profile revision; unknown and not_applicable require an explanatory RecommendationStatement; unique(id,owner_id); owner_id immutable

Indexes: candidate_assessment_id,outcome; customer_requirement_id; provider_network_entry_id

## InformationNeed

One missing customer fact, requirement or document confirmation that should be asked before stronger advice.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable row identity | Primary key; immutable | None | Synthetic design example only; no real customer value inspected. | ["CUS-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When the gap was recorded | UTC; immutable | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Customer account owning this private gap | Required; immutable | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| recommendation_id | fk:Recommendation required | none | Result that identified the missing information | Same owner | None | Synthetic design example only; no real customer value inspected. | ["DEC-01"] |
| subject_person_id | fk:Person optional | NULL | Person the missing information concerns | Same owner; NULL only for purchase-wide information | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03"] |
| need_kind | enum required | none | Kind of information required | fact,requirement,document_confirmation | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03"] |
| information_key | varchar(120) required | none | Reviewed code-controlled fact, requirement or document key | Must exist in the matching approved registry; AI cannot invent keys | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-01"] |
| reason | text required | none | Why the missing information affects filtering or comparison | Specific and customer-readable; no unsupported policy conclusion | None | Synthetic design example only; no real customer value inspected. | ["DEC-01"] |
| priority | enum required | none | How much the gap affects advice | required,important,optional | None | Synthetic design example only; no real customer value inspected. | ["CUS-03", "DEC-01"] |
| status | enum required | open | Progress of this clarification | open,asked,resolved,waived,unavailable | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "OPS-02"] |
| asked_in_message_id | fk:Message optional | NULL | Adviser message that asked the focused question | Same owner/conversation; required when status is asked | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "OPS-02"] |
| resolved_in_profile_revision_id | fk:CustomerProfileRevision optional | NULL | Customer profile revision containing the accepted answer | Same conversation; required when status is resolved | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03"] |

Constraints: unique(recommendation_id,subject_person_id,need_kind,information_key) NULLS NOT DISTINCT; asked requires asked_in_message_id; resolved requires resolved_in_profile_revision_id; required open, asked or unavailable needs prevent a completed recommendation; information_key is code-controlled and AI output cannot extend the registry; unique(id,owner_id); owner_id immutable

Indexes: recommendation_id,status,priority; owner_id,subject_person_id,status; asked_in_message_id

## RecommendationStatement

One independently checkable customer-facing statement in a buying recommendation.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| recommendation_id | fk:Recommendation required | none | Parent recommendation | Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| ordinal | integer required | none | Claim order | Positive | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| candidate_assessment_id | fk:PolicyCandidateAssessment optional | NULL | Candidate this statement concerns | Same recommendation and owner | None | Synthetic design example only; no real customer value inspected. | ["DEC-01"] |
| requirement_match_id | fk:PolicyRequirementMatch optional | NULL | Requirement result this statement explains | Same recommendation and owner | None | Synthetic design example only; no real customer value inspected. | ["CUS-03", "DEC-01"] |
| information_need_id | fk:InformationNeed optional | NULL | Clarification gap this statement explains | Same recommendation and owner | None | Synthetic design example only; no real customer value inspected. | ["CUS-03", "DEC-01"] |
| calculation_id | fk:Calculation optional | NULL | Exact deterministic calculation supporting this statement | Same owner and advice request | None | Synthetic design example only; no real customer value inspected. | ["CAL-04", "DEC-01"] |
| text | text required | none | Exact supported assertion | Scope restricted to cited evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| statement_type | enum required | none | Customer-facing statement category | customer_context,eligibility,requirement_match,benefit,restriction,price,provider,calculation,limitation,next_step | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| critical | boolean required | true | Material correctness flag | Eligibility/calculation/privacy claims critical | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| support_status | enum required | unverified | Whether this statement has adequate support | supported,partly_supported,unsupported,customer_profile_supported | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |

Constraints: unique(recommendation_id,ordinal); at most one of candidate_assessment_id, requirement_match_id and information_need_id is nonnull; none means recommendation-wide; requirement_match and information_need targets belong to the same recommendation; unsupported critical statement blocks publication; calculation statement requires calculation_id; unique(id,owner_id); owner_id immutable

Indexes: recommendation_id,ordinal; candidate_assessment_id; requirement_match_id; information_need_id; calculation_id

## RecommendationCitation

Exact original policy passage supporting, restricting or conflicting with one recommendation statement.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| recommendation_statement_id | fk:RecommendationStatement required | none | Customer-facing statement being evidenced | Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact original passage, table cell or footnote | Public or same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| policy_rule_id | fk:PolicyRule optional | NULL | Interpreted policy rule connecting original to claim | Exact corpus revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| role | enum required | none | Support relationship | supports,restricts,excepts,conflicts,assumption_source | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| ordinal | integer required | none | Display order | Positive | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |

Constraints: unique(recommendation_statement_id,evidence_span_id,role); policy_rule_id is NULL only for direct source facts that need no interpreted policy rule; policy_rule_id when present is in the recommendation's KnowledgeRelease and is supported by evidence_span_id; private evidence is accessible only to the same owner; public evidence requires citation access; unique(id,owner_id); owner_id immutable

Indexes: recommendation_statement_id,ordinal; evidence_span_id; policy_rule_id

## Calculation

One immutable deterministic calculation with exact inputs, operation order, assumptions and result.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | Synthetic design example only; no real customer value included. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | Synthetic design example only; no real customer value included. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this private row | Immutable; all private relationships enforce the same owner | None | Intentionally no real customer or authentication identity included. | ["OPS-01"] |
| advice_request_id | fk:AdviceRequest required | none | Customer question requiring this calculation | Same owner | None | Synthetic design example only; no real customer value included. | ["CAL-01", "CAL-02", "DEC-01"] |
| calculation_type | varchar(120) required | none | Reviewed calculation kind used to select the deterministic evaluator | Finite code-controlled registry; AI output cannot create a type | None | claim_payable_amount (synthetic) | ["CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| engine_version | varchar(120) required | none | Exact qualified deterministic evaluator build | Immutable and resolvable to deployed code | None | claim-engine-1.0 (synthetic) | ["CAL-01", "CAL-02", "CAL-03", "OPS-06"] |
| inputs | json:CalculationInputsV1 required | none | Exact values, units and record/evidence references used | All required inputs present or explicitly unknown; no binary floating point | None | Synthetic design example only; no real customer value included. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| operations | json:CalculationOperationsV1 required | none | Ordered typed operations with intermediate results and policy support | Unique step keys; explicit rounding, units, rule IDs and evidence IDs | None | Synthetic design example only; no real customer value included. | ["CAL-01", "CAL-02", "CAL-03", "CAL-04", "DEC-01"] |
| result | json:TypedValueV1 required | none | Final computed value or explicit unknown/not-applicable result | Reproduces exactly from inputs and operations | None | Synthetic design example only; no real customer value included. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| assumptions | json:AssumptionsV1 required | [] | Material hypothetical or unresolved premises | Empty when none; every unresolved assumption describes its effect | None | Synthetic design example only; no real customer value included. | ["CAL-01", "CAL-02", "DEC-01"] |
| status | enum required | none | Whether deterministic evaluation completed | complete,blocked,failed; blocked is used for missing material inputs | None | complete (synthetic) | ["CAL-01", "CAL-02", "DEC-01"] |

Constraints: unique(id,owner_id); owner_id immutable; advice_request_id shares owner_id; append-only after creation; complete requires a replayable result and no unresolved material input; blocked preserves unknown inputs and assumptions; it does not invent a result; operation ordering, percentage base, rounding and units are explicit; policy rule and evidence references resolve to the exact applicable versions

Indexes: advice_request_id,created_at DESC; owner_id,calculation_type,status; GIN inputs; GIN operations

## Turn

One durable, idempotent and cancellable customer-message processing request.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | timestamptz required | now | Last durable state change | UTC; updated on state or lease change | instant | Synthetic operational example only; no real customer value inspected. | ["OPS-02", "OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Persistent context | Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| request_id | uuid required | none | Idempotent customer request | Unique per owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| input_message_id | fk:Message required | none | Persisted customer input | Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| starting_profile_revision_id | fk:CustomerProfileRevision optional | NULL | Previously accepted customer profile when this input message was durably accepted | NULL for a first message; otherwise same owner and conversation and equal to the accepted profile at durable turn creation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| state | enum required | queued | Durable processing outcome | queued,running,cancel_requested,cancelled,completed,failed,stale | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| lease_token | uuid optional | NULL | Current worker fencing token | Required when running; changes on recovery | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| lease_until | instant optional | NULL | Lease expiry | UTC; expired worker cannot publish | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| deadline | instant required | none | Bounded turn deadline | After creation | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| cancelled_at | instant optional | NULL | Accepted cancellation event | Does not erase committed customer facts | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| error_code | varchar(100) optional | NULL | Explicit technical failure | Safe bounded code, no raw provider secrets | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| route_commitment | char(64) required | empty only for pre-amendment rows | Keyed commitment over both immutable interactive-role bindings | HMAC; set before enqueue; immutable once set; new turns require exactly both roles | None | Synthetic operational example only; no real customer value inspected. | ["OPS-02", "OPS-04", "OPS-06"] |

Constraints: unique(owner_id,request_id); input message and optional starting profile belong to the same owner and conversation; every newly accepted turn has exactly one fact_interpretation and one recommendation_answer binding before enqueue; route_commitment is immutable once set; running requires a current lease token and lease_until; only the current lease token may publish; completed requires a Recommendation whose profile_revision_id is the final evaluated revision; technical failure creates none; a newer concurrent profile makes the result stale unless the publication transaction proves its correction lineage is compatible; unique(id,owner_id); owner_id immutable

Indexes: owner_id,conversation_id,created_at DESC; state,lease_until; owner_id,request_id unique

## TurnRouteBinding

One immutable exact route and passed qualification captured for an interactive role before a turn is queued.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable row identity | Primary key; immutable; never reused | None | Synthetic operational example only; no real customer value inspected. | ["OPS-02", "OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When the route was pinned | UTC; immutable | instant | Synthetic operational example only; no real customer value inspected. | ["OPS-06"] |
| turn_id | fk:Turn required | none | Accepted turn that owns the binding | Exactly two per new turn; immutable | None | Synthetic operational example only; no real customer value inspected. | ["OPS-02", "OPS-04"] |
| role | enum required | none | Interactive operation | fact_interpretation,recommendation_answer | None | fact_interpretation (synthetic) | ["OPS-04"] |
| route_id | fk:ModelRoute required | none | Exact immutable route revision | Active when called; must match all captured route fields | None | Synthetic operational example only; no real customer value inspected. | ["OPS-04"] |
| qualification_id | fk:ModelQualification required | none | Exact passed qualification | Same route and role/schema; current schema hash; passed exact-identity capabilities | None | Synthetic operational example only; no real customer value inspected. | ["OPS-04"] |
| requested_model | varchar(160) required | none | Exact requested provider/model ID | Must equal the bound route | None | gemini/gemini-3.5-flash-lite (operator configuration example) | ["OPS-04"] |
| expected_model | varchar(160) required | none | Exact model ID expected in the response | Must equal observed_model for a passed binding | None | gemini-3.5-flash-lite (operator configuration example) | ["OPS-04"] |
| observed_model | varchar(160) required | none | Model ID observed during qualification | Exact equality with expected_model | None | gemini-3.5-flash-lite (operator configuration example) | ["OPS-04"] |
| endpoint_profile | varchar(120) required | none | Secret-free endpoint identity | Interactive relay or loopback OmniRoute profile only | None | omniroute-loopback (operator configuration example) | ["OPS-04"] |
| adapter_version | varchar(120) required | none | Strict transport implementation identity | Must equal the bound route | None | strict-relay-v2/1 (implementation example) | ["OPS-04"] |
| route_configuration_sha256 | char(64) required | none | Digest of endpoint/model/adapter configuration | Lowercase hex; must equal the bound route | None | Synthetic operational example only; no real customer value inspected. | ["OPS-04"] |
| schema_sha256 | char(64) required | none | Digest of the exact output schema qualified | Lowercase hex; must equal the bound qualification and current schema | None | Synthetic operational example only; no real customer value inspected. | ["OPS-04"] |

Constraints: unique(turn_id,role); insert-only; exact route and qualification FKs use PROTECT; expected_model equals observed_model; any disabled route, failed/missing qualification, schema/configuration/identity mismatch or route-commitment mismatch fails closed; retries copy the original bindings and never switch provider, model or endpoint

Indexes: turn_id,role unique; route_id; qualification_id

## TurnEvent

One immutable ordered UI event that reconnecting clients can replay without repeating inference.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn required | none | Owning work item | Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| sequence | bigint required | none | Monotonic replay cursor | Positive | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| event_type | enum required | none | Durable UI event kind | queued,started,clarification,progress,recommendation,cancelled,failed,stale | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| payload | json:TurnEventV1 required | none | Safe UI event content/reference | Strict kind union; no raw model chain-of-thought or private-other-owner IDs | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |

Constraints: unique(turn_id,sequence); append-only except authorized erasure; payload matches event_type and contains no hidden reasoning or another owner identity; unique(id,owner_id); owner_id immutable

Indexes: turn_id,sequence; owner_id,created_at DESC

## Outbox

Reliable typed dispatch record committed with the work that Celery or publication must deliver.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | timestamptz required | now | Last delivery-state change | UTC | instant | Synthetic operational example only; no real customer value inspected. | ["OPS-02", "OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| event_type | enum required | none | Typed dispatch operation | turn_dispatch,document_processing,knowledge_publication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| turn_id | fk:Turn optional | NULL | Customer turn to dispatch | Same owner; present only for turn_dispatch | None | Synthetic operational example only; no real customer value inspected. | ["OPS-02"] |
| processing_job_id | fk:ProcessingJob optional | NULL | Document job to dispatch | Owner matches when private; present only for document_processing | None | Synthetic operational example only; no real customer value inspected. | ["OPS-02", "OPS-03"] |
| knowledge_release_id | fk:KnowledgeRelease optional | NULL | Knowledge release publication event | Present only for knowledge_publication | None | Synthetic operational example only; no real customer value inspected. | ["OPS-03"] |
| idempotency_key | varchar(200) required | none | Stable delivery deduplication key | Unique within topic | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| state | enum required | pending | Delivery state | pending,leased,delivered,failed | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| attempt_count | integer required | 0 | Explicit dispatch tries | Nonnegative | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| available_at | instant required | now | Earliest retry time | Backoff explicit | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| lease_until | instant optional | NULL | Dispatcher recovery lease | Required when leased | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| last_error_code | varchar(100) optional | NULL | Safe transport failure | Failed cannot silently disappear | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |

Constraints: exactly one of turn_id, processing_job_id and knowledge_release_id is nonnull and matches event_type; unique(event_type,idempotency_key); created in the same transaction as its target work; leased requires lease_until; delivered rows are immutable; no copied customer or policy payload

Indexes: state,available_at; event_type,idempotency_key unique; turn_id; processing_job_id; knowledge_release_id

## ModelRoute

One exact secret-free CLIProxyAPI/Codex route configuration.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| route_key | varchar(120) required | none | Stable route identity | Unique revision-qualified name | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| endpoint_profile | varchar(120) required | none | Secret-free configured relay reference | Shared CLIProxyAPI strict /v1/responses; no credentials here | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| requested_model | varchar(160) required | none | Exact required model identity | No silent fallback | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| adapter_version | varchar(120) required | none | Strict adapter implementation identity | Immutable | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| configuration_sha256 | char(64) required | none | Secret-free model/adapter settings digest | Changes require new qualification | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| disabled_at | instant optional | NULL | When this immutable route revision stopped accepting new work | NULL while selectable; one-way disable | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |

Constraints: route_key unique; route settings immutable; changes create a new route revision; credentials are never stored; disabled route cannot start new attempts

Indexes: route_key unique; disabled_at

## ModelQualification

One completed test of an exact route against one application schema and capability set.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | Qualification completion time | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| route_id | fk:ModelRoute required | none | Qualified route revision | Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| schema_name | enum required | none | Actual use schema | fact_interpretation,policy_extraction,policy_review,recommendation_answer | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| schema_sha256 | char(64) required | none | Exact tested JSON schema | Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| observed_model | varchar(160) required | none | Actual returned model identity | Must exactly satisfy strict identity policy | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| capabilities | json:QualificationV1 required | none | Context/image/structured output checks used | Measured capability, test inputs hashes, results and limits | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| result | enum required | none | Qualification outcome | passed,failed | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |

Constraints: unique(route_id,schema_name,schema_sha256,created_at); passed requires exact expected model identity and all mandatory capability probes; route or schema changes require a new qualification

Indexes: route_id,schema_name,created_at DESC; result

## ModelAttempt

One actual CLIProxyAPI/Codex call with explicit identity, timing, usage and failure.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn optional | NULL | Adviser call context | Exactly one turn or processing job | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| processing_job_id | fk:ProcessingJob optional | NULL | Corpus call context | Exactly one turn or processing job | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| qualification_id | fk:ModelQualification required | none | Qualified exact route/schema | Must be passed/current for attempted use | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| attempt_number | integer required | none | Explicit call ordinal | Positive; no hidden retries | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| started_at | instant required | none | Request start | UTC | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| completed_at | instant optional | NULL | Provider completion | At or after start | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| observed_model | varchar(160) optional | NULL | Actual response identity | Mismatch => technical failure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| status | enum required | started | Provider call result | started,succeeded,timeout,transport_error,schema_error,identity_error,cancelled,indeterminate | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| usage | json:UsageV1 required | none | Reported token counts and measured latency | Unknown usage explicit; never estimated as reported | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| error_code | varchar(100) optional | NULL | Safe operational failure category | No raw credentials or inherited environment | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| request_commitment | char(64) required | none | Keyed commitment to the private canonical request | Versioned HMAC; request content is not recoverable from this value | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| response_storage_key | varchar(500) optional | NULL | Encrypted retained structured response location when retention is necessary | Owner-scoped; no credentials or hidden reasoning; NULL after erasure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| response_storage_sha256 | char(64) optional | NULL | SHA-256 of the encrypted bytes at response_storage_key | Required with response_storage_key; validates stored ciphertext, not low-entropy plaintext | None | Synthetic operational example only; no real customer value inspected. | ["OPS-04", "OPS-06"] |

Constraints: exactly one of turn_id and processing_job_id is nonnull; qualification must be passed for the exact schema and active route; attempt numbers are positive and unique within parent; completed_at is at or after started_at; retained responses obey owner deletion; no hidden reasoning retention; unique(id,owner_id); owner_id immutable

Indexes: turn_id,attempt_number; processing_job_id,attempt_number; qualification_id; status,created_at

## ProcessingJob

One resumable public-policy or private-upload classification, reading, extraction, validation or independent-review task.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | timestamptz required | now | Last state or lease change | UTC | instant | Synthetic operational example only; no real customer value inspected. | ["OPS-02", "OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| source_capture_id | fk:SourceCapture optional | NULL | Public captured source being processed | Successful capture with preserved bytes; owner_id NULL | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| customer_uploaded_document_id | fk:CustomerUploadedDocument optional | NULL | Private customer document being processed | Same owner; never enters public knowledge | None | Synthetic operational example only; no real customer value inspected. | ["CUS-02", "INS-04", "OPS-01"] |
| stage | enum required | none | Replaceable processing step | classify,read,ocr,extract,validate,independent_review,reconcile | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| adapter_version | varchar(160) required | none | Reader/model pipeline identity | Original inventory workflow separately identified | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| input_commitment | char(64) required | none | Keyed commitment to the exact private/public input bytes and parameters | Versioned HMAC for private jobs; public jobs may additionally reference OriginalFile.sha256 | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| attempt_number | integer required | 1 | Initial or targeted retry | 1..3 for automated extract/review cycle | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| parent_job_id | fk:ProcessingJob optional | NULL | Previous targeted attempt | Same document/stage; no cycle | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| state | enum required | queued | Recoverable stage status | queued,running,succeeded,failed,blocked,cancelled | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| lease_token | uuid optional | NULL | Stale-worker fencing identity | Rotate on retry/recovery | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| lease_until | instant optional | NULL | Worker recovery deadline | Running requires fencing via lease token | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| result_storage_key | varchar(500) optional | NULL | Encrypted operational result location | Not contractual evidence; owner-scoped when private | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| result_storage_sha256 | char(64) optional | NULL | SHA-256 of encrypted operational-result bytes | Required with result_storage_key; validates stored ciphertext | None | Synthetic operational example only; no real customer value inspected. | ["OPS-03", "OPS-06"] |
| issues | json:ProcessingIssuesV1 required | empty array | Omissions/errors and targeted retry requirements | Material unresolved issues block affected capabilities | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| error_code | varchar(100) optional | NULL | Explicit technical failure | Safe bounded value | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |

Constraints: exactly one of source_capture_id and customer_uploaded_document_id is nonnull; public input requires owner_id NULL; private input requires matching owner_id; unique(input target,stage,input_sha256,attempt_number); attempt_number is 1..3 for automated extraction/review; running requires lease token and lease_until; independent_review issues determine whether affected policy rules can publish; operational output is never original contractual evidence

Indexes: state,lease_until; source_capture_id,stage,attempt_number; customer_uploaded_document_id,stage,attempt_number; parent_job_id

## ConsentRecord

One requested, granted or revoked record for CoverGuide processing consent. A requested row is not a grant.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When the consent request or action was recorded | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| person_id | fk:Person optional | NULL | Person whose data/action consent concerns | Same owner; authority separately established | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "CUS-01"] |
| consent_type | enum required | none | Approved internal processing purpose | privacy_terms,health_data_processing,document_processing | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| notice_version | varchar(80) required | none | Exact privacy/consent notice accepted | Nonempty immutable version identifier | None | Synthetic design example only; no real customer value inspected. | ["OPS-01", "OPS-06"] |
| capture_method | enum required | none | How the grant was captured | web_checkbox,conversation,uploaded_document,migration | None | Synthetic design example only; no real customer value inspected. | ["OPS-01", "OPS-06"] |
| status | enum required | requested | Consent state | requested,granted,revoked | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| source_message_id | fk:Message optional | NULL | Exact customer authorization | Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| revoked_at | instant optional | NULL | Withdrawal event | Pending dispatch must recheck | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |

Constraints: requested records may be created to present a notice but confer no permission; granted requires an actual captured customer action and conversation capture requires source_message_id; migrations must not fabricate granted status; person and message share owner; revoked requires revoked_at; requested and granted require revoked_at NULL; no ABHA creation, external medical sharing or representation authority is implied; unique(id,owner_id); owner_id immutable

Indexes: owner_id,consent_type,created_at DESC; owner_id,person_id,consent_type; source_message_id

## DeletionRequest

One durable customer request to erase an account, conversation, upload or selected disclosure and its derived private copies.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | Deletion request receipt time | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | timestamptz required | now | Last workflow-state change | UTC | instant | Synthetic design example only; no real customer value inspected. | ["OPS-02", "OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| scope | json:DeletionScopeV1 required | none | Account/conversation/person/artifact deletion targets | Closed owned target types only; includes derived private copies and in-flight work | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| state | enum required | pending | Erasure progress | pending,running,completed,failed | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| completed_at | instant optional | NULL | Verified erasure completion | Requires all required stores/caches/jobs checked | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| verification | json:DeletionVerificationV1 required | none | Store-level erasure evidence without medical values | Private originals, derived indexes, responses, queues, backups/tombstone policy | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| error_code | varchar(100) optional | NULL | Explicit erasure failure | No false completed flag | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |

Constraints: completed requires completed_at and successful store-level verification; failed requires error_code; scope contains only resources owned by owner_id; account erasure fences old workers before content removal; no legal-hold state is assumed; unique(id,owner_id); owner_id immutable

Indexes: owner_id,created_at DESC; state,updated_at

## AuditEvent

Minimal append-only record of sensitive-data access, publication, deletion and administration without copied customer medical text.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When the audited operation occurred | UTC storage; immutable; not a source effective date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| actor_id | fk:Account optional | NULL | Authenticated actor if retained | Pseudonymize/erase according to approved retention | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| operation | varchar(100) required | none | Authorized action category | Registered allowlist | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| object_kind | varchar(100) required | none | Target resource type | Registered allowlist | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| object_id | uuid optional | NULL | Target identity if retention allows | No raw content | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| outcome | enum required | none | Action result | allowed,denied,succeeded,failed | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| metadata | json:AuditMetadataV1 required | empty object | Safe request/revision/error metadata | Allowlist IDs/counts/codes; no diagnoses, tokens or payload excerpts | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |

Constraints: metadata uses a closed allowlist of identifiers, revisions, counts and safe error codes; no diagnoses, message text, secrets or provider payloads; append-only until the approved retention period expires; owner is required for a private target; unique(id,owner_id); owner_id immutable

Indexes: owner_id,created_at DESC; actor_id,created_at DESC; operation,created_at DESC; object_kind,object_id

## PolicyPackageComponent

One original-backed component slot in a public packaged policy, used to compare which separately issued product supplies medical or supplementary cover.

| Field | Type / required | Default | Purpose | Validation | Units | Example | Basis |
|---|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | Primary key; never reused | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp | Assertion insertion time, separate from contractual effective time | UTC; immutable | instant | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| package_policy_version_id | fk:PolicyVersion required | none | Exact packaged-policy version defining this component | Required typed identity; no inferred association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| slot_key | varchar(80) required | none | Stable component position within this package version | Nonempty lowercase identifier; unique within wrapper terms | None | health or life; design-assigned codes for original COMBI13-A, not insurer-issued codes | ["INS-10"] |
| component_product_id | fk:Product optional | NULL | Separately issued component product when identified | Required for reviewed association; NULL is allowed only while unresolved/conflicting | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| component_policy_version_id | fk:PolicyVersion optional | NULL | Exact component policy version when independently established | When present, terms.product_id equals component_product_id; wrapper naming a UIN alone does not establish complete component wording | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| asserted_component_uin | varchar(100) optional | NULL | Identifier explicitly asserted by the wrapper source | NULL means not stated, not no UIN; compare independently with resolved component edition; mismatch blocks verification | None | Health Premier ZUKHLIP25054V052425; Kotak Term Plan107N005V06, source26c72de9… COMBI13-A | ["INS-10"] |
| role | enum required | unresolved | Component role; does not expand the selected medical-insurer roster | medical,life,other,unresolved | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_kind | enum required | unresolved | Whether this wrapper requires or permits the component | required,optional,conditional,unresolved | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_policy_rule_id | fk:PolicyRule optional | NULL | Connected selection condition for conditional membership | Rule.owner_id NULL and rule.terms_id equals wrapper_terms_id; required when selection_kind is conditional | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact original support for the package/component association | Required typed identity; no inferred association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| review_status | enum required | unresolved | Association review outcome | unresolved,reviewed,conflict,excluded | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(package_policy_version_id,slot_key); reviewed requires component_product_id and evidence_span_id; component_policy_version belongs to component_product; conditional selection requires a same-package PolicyRule; conflicting asserted UIN blocks affected recommendation capability; package composition is acyclic; history comes from PolicyVersion; no duplicate component self-supersession

Indexes: package_policy_version_id,slot_key unique; component_product_id; component_policy_version_id; selection_policy_rule_id
