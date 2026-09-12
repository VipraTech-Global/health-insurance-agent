# Field dictionary — proposed revision 11

Batches 1 through 4 are approved. Later batches and the complete database design remain under review.

## Account

Logical authentication principal implemented by the retained accounts.User(AbstractUser) model. Access: framework_private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| email | varchar(254) required | none / None | Login identity; Unique exact existing email; no silent normalization merge | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| password | varchar(128) required | none / None | Django encoded password and algorithm marker; Preserve encoded bytes; never hash an existing hash | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-06"] |
| last_login | instant optional | NULL / instant | Last successful login; UTC; preserve legacy value | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_superuser | boolean required | false / None | Global administration privilege; Authorized changes only | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_staff | boolean required | false / None | Administration interface access; Authorized changes only | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_active | boolean required | true / None | Whether login is permitted; Deleted account cannot be active | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| first_name | varchar(150) required | empty string / None | Optional display given name; No medical use | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| last_name | varchar(150) required | empty string / None | Optional display surname; No insured identity inference | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| date_joined | instant required | now / instant | Original account creation; Preserve during migration | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| deleted_at | instant optional | NULL / instant | Deletion completion marker; No retained personal content after completed deletion without hold | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| erasure_generation | bigint required | 0 / None | Fence work started before erasure; Monotonic; workers compare before storing/publishing | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "OPS-02"] |

Constraints: email unique; id immutable; username disabled; email is USERNAME_FIELD; native AbstractUser authentication, group and permission semantics retained; date_joined is the account creation timestamp.
Indexes: email unique B-tree.

## AIPreference

One-to-one user AI route preference kept outside authentication columns. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| user_id | fk:Account required | none / None | Account whose AI preference this is; Primary key and one-to-one owner boundary | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-04", "OPS-06"] |
| route_id | fk:ModelRoute optional | NULL / None | Preserved user-selected qualified AI route; Selection retained even if route disabled; ordinary users may invoke only separately qualified active route; never auto-fallback | None | No authentic private or generated identity inspected; synthetic fixture required. | ["OPS-04", "OPS-06"] |
| updated_at | instant required | now / instant | When the preference last changed; UTC; preserve pilot value during migration; changes only when the preference changes | None | No authentic private or generated identity inspected; synthetic fixture required. | ["OPS-04", "OPS-06"] |

Constraints: user_id primary key and one-to-one; disabled or unqualified selected route produces an explicit operational result; no silent fallback.
Indexes: user_id primary key; route_id.

## Person

A minimal owner-scoped human label; medical, role and identity assertions live in sourced fact records. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| display_name | varchar(200) required | empty string / None | Customer supplied label; Blank allowed; customer-facing label only; not a deduplication key or verified legal identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |

Constraints: unique(id,owner_id); owner_id immutable; display_name is not an identity or deduplication key.
Indexes: owner_id.

## PersonRelationship

Directional relationship between two owner-scoped people, separate from proposed or issued policy membership. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| from_person_id | fk:Person required | none / None | Person whose relationship is described; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| to_person_id | fk:Person required | none / None | Related person; Same owner; not self | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| relationship_type | enum required | none / None | How to_person relates to from_person; spouse,parent,child,parent_in_law,sibling,guardian,dependent,other; other requires explanation in source assertion | s, p, o, u, s, e, ,, p, a, r, e, n, t, ,, c, h, i, l, d, ,, p, a, r, e, n, t, _, i, n, _, l, a, w, ,, s, i, b, l, i, n, g, ,, g, u, a, r, d, i, a, n, ,, d, e, p, e, n, d, e, n, t, ,, o, t, h, e, r | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| source_statement_id | fk:CustomerStatement required | none / None | Exact customer statement supporting the relationship; Same owner and conversation context; subjects match from_person/to_person | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| valid_from | date optional | NULL / date | First date the relationship applies when materially known; ISO date; NULL means not established or not material | None | Synthetic design fixture only; no real customer value included. | ["CUS-01", "INS-03"] |
| valid_to | date optional | NULL / date | Last date the relationship applies when materially known; ISO date; NULL means open or not established; cannot precede valid_from | None | Synthetic design fixture only; no real customer value included. | ["CUS-01", "INS-03"] |

Constraints: from_person_id differs from to_person_id; from_person_id and to_person_id have the same immutable owner_id as the relationship; valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from; source assertion has the same owner and matching people; unique(owner_id,from_person_id,to_person_id,relationship_type,valid_from,valid_to) with NULLS NOT DISTINCT; unique(id,owner_id); owner_id immutable.
Indexes: owner_id,from_person_id; owner_id,to_person_id; owner_id,relationship_type.

## Conversation

Persistent conversation and its current accepted state. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| title | varchar(200) required | empty string / None | History list label; No automatic sensitive diagnosis in title | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| current_profile_revision_id | fk:CustomerProfileRevision optional | NULL / None | Current customer fact/requirement checkpoint; Same conversation and matching revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| status | enum required | open / None | Conversation lifecycle; open,archived,deleting,deleted | o, p, e, n, ,, a, r, c, h, i, v, e, d, ,, d, e, l, e, t, i, n, g, ,, d, e, l, e, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| updated_at | instant required | now / instant | Most recent durable interaction; Monotonic per transaction | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| preferred_language | varchar(35) optional | NULL / None | Customer communication locale; BCP47; not a medical fact | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |

Constraints: unique(id,owner_id); profile revision pointer belongs to this conversation; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/statement/fact-type/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; current_profile_revision_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,updated_at DESC.

## Message

Immutable submitted or published conversational content. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Parent history; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| sequence | bigint required | none / None | Durable ordering in conversation; Positive; allocated under conversation lock | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| role | enum required | none / None | Speaker role; customer,adviser,system | c, u, s, t, o, m, e, r, ,, a, d, v, i, s, e, r, ,, s, y, s, t, e, m | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| content | text required | none / None | Exact displayed message; Size bound proposed 100000 characters; encrypted storage | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| origin | enum required | none / None | How content entered history; text,voice_transcription,document_import,system,migration | t, e, x, t, ,, v, o, i, c, e, _, t, r, a, n, s, c, r, i, p, t, i, o, n, ,, d, o, c, u, m, e, n, t, _, i, m, p, o, r, t, ,, s, y, s, t, e, m, ,, m, i, g, r, a, t, i, o, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| client_request_id | uuid optional | NULL / None | Submission idempotency identifier; Unique per owner when nonnull | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| payload_sha256 | char(64) required | none / None | Hash of canonical submitted payload; Lowercase SHA256; compare duplicate request contents | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| submitted_at | instant required | none / instant | Original receipt time; UTC; not rewritten on retry | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| turn_id | fk:Turn optional | NULL / None | Processing turn producing or consuming message; Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| answer_id | fk:Decision optional | NULL / None | Published answer artifact; Same conversation; adviser output only | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| redacted_at | instant optional | NULL / instant | Content erasure event; Content and copies cleared atomically or deletion job blocks access | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |

Constraints: unique(conversation_id,sequence); unique(owner_id,client_request_id) where nonnull; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; turn_id IS NULL OR owner_id IS NOT NULL; answer_id IS NULL OR owner_id IS NOT NULL.
Indexes: conversation_id,sequence; turn_id.

## ConversationMessageChunk

Replaceable private lexical/semantic index for an exact section of one immutable conversation message. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Parent history; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| message_id | fk:Message required | none / None | Exact immutable source message; Same owner and conversation; message not redacted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "RET-01"] |
| chunk_index | integer required | none / None | Zero-based section order within the message; Nonnegative; deterministic for one index revision | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| start_offset | integer required | none / Unicode code-point offset | Starting character offset in the original message; Nonnegative and less than end_offset | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| end_offset | integer required | none / Unicode code-point offset | Exclusive ending character offset in the original message; At most source content length and greater than start_offset | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| lexical_vector | tsvector required | derived / None | PostgreSQL full-text representation for exact-term search; Rebuildable private derivative; language configuration belongs to index_revision | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| embedding | vector(1024) optional | NULL / None | Local BGE-M3 semantic-search derivative; Only qualified 1024-dimensional local adapter output; no benchmark material | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| index_revision | varchar(160) required | none / None | Chunking, tokenizer and embedding version; Immutable revision-qualified identifier | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01", "OPS-06"] |
| content_sha256 | char(64) required | none / None | Fingerprint of exact source slice and index revision; Lowercase SHA256; recomputed before exact text is supplied | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| invalidated_at | instant optional | NULL / instant | When this replaceable derivative stopped being eligible for retrieval; Required when source message is redacted or index revision is retired | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "OPS-01"] |

Constraints: unique(message_id,chunk_index,index_revision); owner_id and conversation_id match the source Message; 0 <= start_offset < end_offset <= source message content length; current accepted CustomerProfileRevision overrides conflicting historical-message retrieval; redacted source messages make every chunk ineligible before content erasure.
Indexes: conversation_id,message_id,chunk_index; GIN lexical_vector; HNSW embedding vector_cosine_ops WHERE embedding IS NOT NULL AND invalidated_at IS NULL; owner_id,conversation_id,invalidated_at.

## CustomerStatement

A meaningful source span inside one customer message, retained so unusual or unresolved information cannot be silently dropped. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| source_message_id | fk:Message required | none / None | Immutable message containing this statement; Customer-role message; same owner; offsets must lie within content | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| start_offset | integer required | none / Unicode code-point offset | Starting character in source message; Zero-based Unicode code-point offset; nonnegative and less than end_offset | None | Synthetic: 0 | ["CUS-02", "CUS-03", "RET-01"] |
| end_offset | integer required | none / Unicode code-point offset | Exclusive ending character in source message; At most source content length and greater than start_offset | None | Synthetic: 20 | ["CUS-02", "CUS-03", "RET-01"] |
| subject_person_id | fk:Person optional | NULL / None | Person the statement concerns when person-specific; Same owner; null for conversation/purchase-wide or unresolved subject | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| kind | enum required | none / None | Initial semantic category; fact,intended_insured,requirement,preference,question,correction,context,other | f, a, c, t, ,, i, n, t, e, n, d, e, d, _, i, n, s, u, r, e, d, ,, r, e, q, u, i, r, e, m, e, n, t, ,, p, r, e, f, e, r, e, n, c, e, ,, q, u, e, s, t, i, o, n, ,, c, o, r, r, e, c, t, i, o, n, ,, c, o, n, t, e, x, t, ,, o, t, h, e, r | Synthetic: fact | ["CUS-02", "CUS-03", "RET-01"] |
| status | enum required | pending / None | Whether the meaningful span has been handled; pending,mapped,clarification_required,ignored_with_reason | p, e, n, d, i, n, g, ,, m, a, p, p, e, d, ,, c, l, a, r, i, f, i, c, a, t, i, o, n, _, r, e, q, u, i, r, e, d, ,, i, g, n, o, r, e, d, _, w, i, t, h, _, r, e, a, s, o, n | Synthetic: mapped | ["CUS-02", "CUS-03", "RET-01"] |
| resolution_note | text optional | NULL / None | Reason a statement needs clarification or is ignored; Required for clarification_required and ignored_with_reason; absent for mapped | None | Synthetic: exact hospital branch is unclear. | ["CUS-02", "CUS-03", "RET-01"] |

Constraints: 0 <= start_offset < end_offset <= source Message content length; source Message must have role customer and the same owner; subject_person_id, when set, has the same owner; resolution_note required exactly for clarification_required or ignored_with_reason; decision-relevant statements must become mapped or clarification_required before advice is ready; statement stores offsets, not a duplicate copy of Message.content; unique(id,owner_id); owner_id immutable.
Indexes: source_message_id,start_offset,end_offset; owner_id,status; subject_person_id,kind.

## CustomerProfileRevision

Small immutable checkpoint created only when customer facts or requirements change. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "DEC-01", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Conversation whose customer state changed; Same owner; one linear revision sequence per conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "DEC-01", "OPS-02"] |
| revision | bigint required | none / None | Sequential customer-state revision number; Positive; allocated while locking the Conversation; immutable | None | Synthetic: 3 | ["CUS-02", "DEC-01", "OPS-02"] |

Constraints: unique(conversation_id,revision); revision is positive and monotonic within conversation; facts and requirements for the revision are inserted in the same transaction before Conversation.current_profile_revision_id changes; ordinary chat without a fact or requirement change creates no revision; unique(id,owner_id); owner_id immutable.
Indexes: conversation_id,revision DESC.

## CustomerFact

One validated version of a customer fact; active historical state is reconstructed by logical key and profile revision. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| introduced_in_revision_id | fk:CustomerProfileRevision required | none / None | Profile revision that introduced this version; Same owner and source-statement conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| source_statement_id | fk:CustomerStatement required | none / None | Exact customer statement supporting this fact; Mapped statement in the same owner and revision conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| logical_key | uuid required | uuid4 for the first version; reuse for corrections / None | Stable identity of one logical fact across corrections; Same logical key remains within one owner, conversation, subject and fact type | None | Synthetic UUID shared by age corrections. | ["CUS-02", "CUS-03", "INS-06"] |
| fact_type | varchar(100) required | none / None | Reviewed semantic meaning of value; Must exist in the versioned code-controlled FactType registry; AI cannot create codes | None | Synthetic: person.age_reported | ["CUS-02", "CUS-03", "INS-06"] |
| schema_version | positive_integer required | none / None | Exact validator used for value; Registered for fact_type; historical validators remain readable | None | Synthetic: 1 | ["CUS-02", "CUS-03", "INS-06"] |
| value | json:FactValueV1 required | none / None | Typed known, unknown or not-applicable value; Closed schema selected by fact_type and schema_version; units and precision explicit | None | Synthetic: {"state":"known","kind":"quantity","value":"64","unit":"year"} | ["CUS-02", "CUS-03", "INS-06"] |
| status | enum required | reported / None | Customer acceptance state of this version; reported,confirmed,disputed,retracted | r, e, p, o, r, t, e, d, ,, c, o, n, f, i, r, m, e, d, ,, d, i, s, p, u, t, e, d, ,, r, e, t, r, a, c, t, e, d | Synthetic: reported | ["CUS-02", "CUS-03", "INS-06"] |

Constraints: append-only except authorized erasure; source statement and introduced revision share owner and conversation; fact_type registry determines person/conversation subject, cardinality, schema, units and sensitivity; all versions of logical_key retain owner, conversation, subject and fact_type; latest version at or before a requested revision is active unless retracted; multiple active logical keys for a scalar subject/fact_type are an unresolved conflict; unknown and not_applicable are explicit value states and never become zero; unique(id,owner_id); owner_id immutable.
Indexes: introduced_in_revision_id; owner_id,logical_key,introduced_in_revision_id; owner_id,fact_type; GIN value.

## CustomerRequirement

One atomic mandatory, preferred or informational condition used to filter, rank or explain policy configurations. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| introduced_in_revision_id | fk:CustomerProfileRevision required | none / None | Profile revision that introduced this version; Same owner and source-statement conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| source_statement_id | fk:CustomerStatement required | none / None | Exact statement supporting this requirement; Requirement or preference statement in same owner and conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| logical_key | uuid required | uuid4 for first version; reuse for corrections / None | Stable identity of one requirement across corrections; Same logical key remains within one owner, conversation, criterion and scope | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| criterion | varchar(120) required | none / None | Policy outcome the customer wants tested; Must exist in reviewed comparison-criterion registry | None | Synthetic: claim.copay_percent | ["CUS-01", "CUS-03", "RET-01"] |
| operator | enum required | none / None | Comparison to apply to policy outcome; equals,not_equals,less_than_or_equal,greater_than_or_equal,includes,excludes,is_available,is_not_available,minimize,maximize; registry restricts per criterion | e, q, u, a, l, s, ,, n, o, t, _, e, q, u, a, l, s, ,, l, e, s, s, _, t, h, a, n, _, o, r, _, e, q, u, a, l, ,, g, r, e, a, t, e, r, _, t, h, a, n, _, o, r, _, e, q, u, a, l, ,, i, n, c, l, u, d, e, s, ,, e, x, c, l, u, d, e, s, ,, i, s, _, a, v, a, i, l, a, b, l, e, ,, i, s, _, n, o, t, _, a, v, a, i, l, a, b, l, e, ,, m, i, n, i, m, i, z, e, ,, m, a, x, i, m, i, z, e | Synthetic: equals | ["CUS-01", "CUS-03", "RET-01"] |
| target_value | json:FactValueV1 optional | NULL / None | Desired boundary or value; Required except for minimize/maximize; type and unit fixed by criterion | None | Synthetic: {"state":"known","kind":"quantity","value":"0","unit":"ratio"} | ["CUS-01", "CUS-03", "RET-01"] |
| priority | enum required | none / None | Whether failure excludes or only ranks a configuration; mandatory,preferred,informational | m, a, n, d, a, t, o, r, y, ,, p, r, e, f, e, r, r, e, d, ,, i, n, f, o, r, m, a, t, i, o, n, a, l | Synthetic: mandatory | ["CUS-01", "CUS-03", "RET-01"] |
| scope | enum required | none / None | People or purchase to which this requirement applies; entire_purchase,all_intended_insured,person | e, n, t, i, r, e, _, p, u, r, c, h, a, s, e, ,, a, l, l, _, i, n, t, e, n, d, e, d, _, i, n, s, u, r, e, d, ,, p, e, r, s, o, n | Synthetic: person | ["CUS-01", "CUS-03", "RET-01"] |
| subject_person_id | fk:Person optional | NULL / None | Exact person for person-scoped requirement; Required exactly when scope=person; same owner and conversation | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| status | enum required | reported / None | Customer acceptance state of this version; reported,confirmed,disputed,withdrawn | r, e, p, o, r, t, e, d, ,, c, o, n, f, i, r, m, e, d, ,, d, i, s, p, u, t, e, d, ,, w, i, t, h, d, r, a, w, n | Synthetic: reported | ["CUS-01", "CUS-03", "RET-01"] |

Constraints: append-only except authorized erasure; source statement and introduced revision share owner and conversation; criterion registry determines permitted operators, value schema and units; subject_person_id required exactly for scope person and null otherwise; target_value required except for minimize and maximize; all versions of logical_key retain owner, conversation, criterion and scope; latest version at or before a requested revision is active unless withdrawn; one source statement may create separate atomic person-scoped requirements without a joining table; unique(id,owner_id); owner_id immutable.
Indexes: introduced_in_revision_id; owner_id,logical_key,introduced_in_revision_id; owner_id,criterion,priority; subject_person_id,criterion; GIN target_value.

## AdviceRequest

One customer advice goal spanning any number of clarification messages; execution attempts later pin exact profile revisions. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Required; immutable; related private rows must have the same owner | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Conversation containing the customer goal; Same owner | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| source_statement_id | fk:CustomerStatement required | none / None | Statement that initiated this advice goal; Same owner and conversation; normally question, requirement or context | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| request_type | enum required | none / None | Requested advice scope; purchase_recommendation,product_comparison,coverage_question,claim_explanation,renewal_review,portability_review | p, u, r, c, h, a, s, e, _, r, e, c, o, m, m, e, n, d, a, t, i, o, n, ,, p, r, o, d, u, c, t, _, c, o, m, p, a, r, i, s, o, n, ,, c, o, v, e, r, a, g, e, _, q, u, e, s, t, i, o, n, ,, c, l, a, i, m, _, e, x, p, l, a, n, a, t, i, o, n, ,, r, e, n, e, w, a, l, _, r, e, v, i, e, w, ,, p, o, r, t, a, b, i, l, i, t, y, _, r, e, v, i, e, w | Synthetic: purchase_recommendation | ["CUS-01", "CUS-03", "RET-01"] |
| status | enum required | open / None | Whether the customer goal remains active; open,fulfilled,cancelled | o, p, e, n, ,, f, u, l, f, i, l, l, e, d, ,, c, a, n, c, e, l, l, e, d | Synthetic: open | ["CUS-01", "CUS-03", "RET-01"] |

Constraints: source statement and conversation share owner and conversation; ten information-gathering messages may still serve one AdviceRequest; processing state and failures belong to Turn/ModelAttempt, not this customer goal; each Turn references the exact CustomerProfileRevision it evaluates; unique(id,owner_id); owner_id immutable.
Indexes: conversation_id,created_at DESC; owner_id,status; request_type,status.

## Insurer

One insurer in the approved research roster and the issuer identity used by products and official documents. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| name | varchar(250) required | none / None | Full official insurer name; Nonempty; unique in the active research roster | None | Care Health Insurance Limited | ["INS-01", "INS-04"] |

Constraints: name unique; id and created_at inherited from approved abstract base models.
Indexes: name unique B-tree.

## DiscoveryRun

One autonomous Codex session tasked with discovering public documents for one insurer. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When mutable metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| insurer_id | fk:Insurer required | none / None | Insurer whose sources the run investigates; Required; one insurer per run; comparison sources may still mention others | None | Synthetic design example; no customer value used. | ["INS-01", "INS-04"] |
| instructions | text required | none / None | Exact discovery task supplied to Codex; Nonempty; retained verbatim; it describes the requested search and does not constrain reachable sites | None | Find all current and historical health-insurance documents for Care, including official and useful independent sources. | ["INS-04", "OPS-03"] |
| session_id | varchar(250) required | none / None | Codex session identity used for continuation and audit; Nonempty; unique; immutable after the session starts | None | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| model_name | varchar(160) required | none / None | Observed Codex model used for the run; Record the actual model identity; no silent substitution | None | gpt-6-astra | ["OPS-03", "OPS-04"] |
| completed_at | instant optional | NULL / instant | When the run reached a terminal state; UTC; required for completed, failed or cancelled; completion does not assert source completeness | None | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| status | enum required | queued / None | Run lifecycle; queued, running, completed, failed or cancelled | queued, running, completed, failed, cancelled | completed | ["INS-04", "OPS-03"] |
| error_summary | text optional | NULL / None | Safe explanation of a failed run; Required when failed; no credentials or private browser state | None | Browser session ended before attachments were inspected. | ["OPS-03"] |

Constraints: session_id unique; terminal status requires completed_at; failed requires error_summary; completed means the assigned session finished; it never proves all documents were found.
Indexes: insurer_id,created_at DESC; status,created_at.

## SourceURL

One unique public web address discovered by Codex, independent of how often or where it was observed. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When mutable metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| url | text required | none / None | Exact usable source URL; Unique; bounded to 8192 characters; no insurer-domain allowlist | None | https://careinsurance.com/example/policy-wording.pdf | ["INS-04", "OPS-03"] |
| source_type | enum required | unknown / None | Who operates the location, used as provenance rather than a browsing restriction; insurer_site, regulator_site, government_site, independent_site, archive, other or unknown | insurer_site, regulator_site, government_site, independent_site, archive, other, unknown | insurer_site | ["INS-04", "DEC-01"] |

Constraints: url unique; source_type is evidence metadata and never an autonomous-browsing allowlist.
Indexes: url unique B-tree; source_type.

## SourceObservation

One retained occasion on which a Codex discovery run encountered a source URL. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| discovery_run_id | fk:DiscoveryRun required | none / None | Codex run that made the observation; Required | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| source_url_id | fk:SourceURL required | none / None | URL encountered by the run; Required; many observations may point to the same URL | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| found_in_capture_id | fk:SourceCapture optional | NULL / None | Previously captured page or register containing the link; Optional; when present it must precede this observation | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| observation_type | enum required | other / None | How Codex encountered the URL; search_result, page_link, attachment, document_register, sitemap, known_url or other | search_result, page_link, attachment, document_register, sitemap, known_url, other | attachment | ["INS-04"] |
| label_or_context | text optional | NULL / None | Useful visible label, snippet or surrounding context; Preserve useful source wording; do not place the downloaded document text here | None | Download Policy Terms and Conditions | ["INS-04"] |
| disposition | enum required | unresolved / None | Whether the observed URL belongs in the research scope; relevant, irrelevant or unresolved | relevant, irrelevant, unresolved | relevant | ["INS-02", "INS-04"] |
| disposition_reason | text optional | NULL / None | Why the observation was excluded or remains unresolved; Required for irrelevant; retained so later runs do not repeat a known exclusion | None | Document concerns travel insurance rather than medical-expense cover. | ["INS-02", "INS-04"] |

Constraints: irrelevant requires disposition_reason; observations are retained even when irrelevant; found_in_capture_id cannot point to a later capture.
Indexes: discovery_run_id,created_at; source_url_id,created_at; disposition.

## SourceCapture

One attempt by a Codex discovery run to preserve the content currently returned by a source URL. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When mutable metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| discovery_run_id | fk:DiscoveryRun required | none / None | Run responsible for this capture attempt; Required | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| source_url_id | fk:SourceURL required | none / None | URL whose content was requested; Required | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| completed_at | instant optional | NULL / instant | When the capture succeeded or failed; UTC; required for captured or failed | None | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| status | enum required | running / None | Capture lifecycle; running, captured or failed | running, captured, failed | captured | ["INS-04", "OPS-03"] |
| http_status | smallint optional | NULL / None | HTTP response status when Codex or its browser exposes one; 100 through 599; optional because browser capture may not expose it | None | 200 | ["INS-04", "OPS-03"] |
| original_file_id | fk:OriginalFile optional | NULL / None | Exact bytes preserved by a successful capture; Required when captured; public file with matching stored bytes | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| document_version_id | fk:DocumentVersion optional | NULL / None | Document edition identified from the captured content; Set only after identification; captures of the same edition may share one version | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| error_summary | text optional | NULL / None | Safe reason a capture failed; Required when failed; no credentials or browser secrets | None | Access denied after browser navigation. | ["OPS-03"] |

Constraints: captured requires original_file_id and completed_at; failed requires error_summary and completed_at; running has no completed_at; the same URL may have many captures over time; multiple URLs may capture the same OriginalFile.
Indexes: source_url_id,created_at DESC; discovery_run_id,status; document_version_id; original_file_id.

## OriginalFile

Content-addressed exact bytes preserved from a public source or private customer upload. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When mutable metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account optional | NULL / None | Owner of a private file; NULL for public corpus files; Owner immutable; public files have NULL; private deduplication stays within the owner | None | No authentic customer identity or document value inspected. | ["OPS-01"] |
| sha256 | char(64) required | none / None | Cryptographic identity of the exact bytes; Lowercase hexadecimal; verified on write and integrity read | None | cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb | ["INS-04", "OPS-03"] |
| storage_key | varchar(500) required | none / None | Opaque private object-storage location; Unique; never expose a direct filesystem path | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-01"] |
| byte_size | bigint required | none / bytes | Exact stored byte length; Nonnegative and equal to stored object length | None | 2483921 | ["INS-04", "OPS-03"] |
| media_type | varchar(150) required | none / None | Detected actual media type; Derived from content rather than trusted filename extension | None | application/pdf | ["INS-04", "OPS-03"] |
| availability | enum required | available / None | Whether preserved bytes may currently be used; available, quarantined or deleted | available, quarantined, deleted | available | ["INS-04", "OPS-01"] |
| last_verified_at | instant required | now / instant | Most recent successful hash-integrity check; UTC; verification recomputes SHA-256 from stored bytes | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |

Constraints: unique(owner_id,sha256) NULLS NOT DISTINCT; storage_key unique; owner_id immutable; deleted private content cannot be read.
Indexes: sha256; owner_id,availability.

## DocumentSeries

Stable identity of one continuing publication across editions, such as a product policy wording. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When mutable metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| issuer_id | fk:Insurer optional | NULL / None | Insurer that issued the publication; NULL for regulator, government or independent publications | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| name | text required | none / None | Stable human-readable series name; Nonempty; do not put the edition year in this field | None | Care Supreme Policy Wording | ["INS-02", "INS-04"] |
| kind | enum required | other / None | Document category; policy_wording, customer_information_sheet, prospectus, endorsement, premium_table, provider_list, regulation, notice, comparison, web_page or other | policy_wording, customer_information_sheet, prospectus, endorsement, premium_table, provider_list, regulation, notice, comparison, web_page, other | policy_wording | ["INS-02", "INS-04"] |
| authority | enum required | unknown / None | Who authored or issued the claims inside the document; insurer_issued, regulator_issued, government_issued, independent_analysis or unknown | insurer_issued, regulator_issued, government_issued, independent_analysis, unknown | insurer_issued | ["INS-02", "DEC-01"] |
| relevance | enum required | unresolved / None | Relationship of the captured content to CoverGuide's medical-expense scope; relevant, supporting, unrelated or unresolved | relevant, supporting, unrelated, unresolved | relevant | ["INS-02", "INS-04"] |

Constraints: issuer_id required when authority is insurer_issued; independent_analysis does not become contractual authority because an insurer is discussed.
Indexes: issuer_id,kind; authority,relevance; name.

## DocumentVersion

One identified edition within a DocumentSeries, with evidence-backed dates and explicit supersession. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When mutable metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| document_series_id | fk:DocumentSeries required | none / None | Publication series containing this edition; Required | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| version_label | varchar(200) optional | NULL / None | Printed edition or version label; Original-backed; acquisition date is not a version label | None | Version 3 - 2025 | ["INS-02"] |
| identifiers | json:IdentifiersV1 required | empty array / None | Printed UINs and other document identifiers; Retain multiple or conflicting printed identifiers; never silently select one | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| language | varchar(35) optional | NULL / None | Printed document language; BCP47 code or NULL when unresolved | None | en-IN | ["INS-02"] |
| published_on | date optional | NULL / calendar date | Printed publication date; Original-backed; never substitute capture date | None | 2025-04-01 | ["INS-02", "INS-04"] |
| effective_from | date optional | NULL / calendar date | First applicability date when established; Original-backed inclusive date; NULL means unknown | None | 2025-04-01 | ["INS-02", "INS-03"] |
| effective_to | date optional | NULL / calendar date | Last applicability date when established; Original-backed inclusive date; NULL means unknown, not unlimited | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| supersedes_id | fk:DocumentVersion optional | NULL / None | Earlier edition explicitly replaced by this edition; Same DocumentSeries; acyclic; evidence required before verified status | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| review_status | enum required | unreviewed / None | Confidence in edition identity and applicability metadata; unreviewed, identified, verified or conflicted | unreviewed, identified, verified, conflicted | verified | ["INS-02", "INS-04"] |

Constraints: supersedes_id belongs to the same DocumentSeries and is acyclic; effective_to is on or after effective_from; is_latest is derived and never stored; latest discovered, latest published and currently applicable remain distinct.
Indexes: document_series_id,published_on DESC; document_series_id,effective_from,effective_to; review_status.

## DocumentPage

One physical PDF page and its explicit review state, including pages on which extraction failed. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When mutable metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| original_file_id | fk:OriginalFile required | none / None | Exact PDF containing this page; File media type must be PDF | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| page_number | integer required | none / page | One-based physical page number; At least 1 and no greater than the preserved PDF page count | None | 37 | ["INS-04"] |
| printed_label | varchar(80) optional | NULL / None | Page label printed inside the document; May differ from physical page_number | None | Page 34 of 52 | ["INS-04"] |
| review_state | enum required | unread / None | How completely this physical page has been inspected; unread, text_read, visually_reviewed, fully_reviewed or unresolved | unread, text_read, visually_reviewed, fully_reviewed, unresolved | fully_reviewed | ["INS-04", "OPS-03"] |

Constraints: unique(original_file_id,page_number); non-PDF originals do not create DocumentPage rows; page dimensions and rotation are read from preserved PDF bytes rather than duplicated here.
Indexes: original_file_id,page_number; review_state.

## EvidenceSpan

One exact passage, table cell, footnote or region supporting a policy or operational claim. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source publication or effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| source_capture_id | fk:SourceCapture required | none / None | Exact URL, capture time, bytes and identified document edition used as evidence; Capture must be successful and have a document_version_id | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| page_id | fk:DocumentPage optional | NULL / None | Physical PDF page containing the evidence; Required for PDF locators; page file must match the capture's OriginalFile; NULL for HTML or JSON | None | Synthetic design example; no customer value used. | ["INS-04"] |
| section_label | varchar(200) optional | NULL / None | Printed section or table label; Preserve the source wording | None | Pre-existing Disease Waiting Period | ["INS-04", "RET-01"] |
| quote | text required | none / None | Exact extracted or visually transcribed source text; Must resolve from the preserved bytes and locator; no paraphrase | None | Synthetic design example; no customer value used. | ["INS-04", "DEC-01"] |
| context | json:EvidenceContextV1 required | empty object / None | Headings, table axes, units, footnotes and connected passages required to interpret the quote; Closed versioned structure; retain material qualifiers | None | Synthetic design example; no customer value used. | ["INS-04", "DEC-01"] |
| method | enum required | none / None | How the passage was read; native_text, ocr_verified, manual_visual, html or json | native_text, ocr_verified, manual_visual, html, json | native_text | ["INS-04", "OPS-03"] |
| verification | enum required | unverified / None | Independent verification state; unverified, text_verified, visually_verified, reviewed or failed | unverified, text_verified, visually_verified, reviewed, failed | reviewed | ["INS-04", "DEC-01"] |
| locator | json:OriginalLocatorV1 required | none / None | Exact PDF region, HTML selector, JSON pointer or text range; Must resolve unambiguously against source_capture.original_file_id; PDF geometry is stored only here | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |

Constraints: source capture is captured and mapped to a DocumentVersion; PDF evidence requires a page from the same OriginalFile; non-PDF evidence has no page_id; quote must resolve from immutable captured bytes and locator; verification does not by itself establish semantic entailment.
Indexes: source_capture_id; page_id,section_label; verification.

## Product

Stable insurer product family, independent of policy editions, named variants and optional additions. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When curated metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| insurer_id | fk:Insurer required | none / None | Insurer offering the product; Required; a package component retains its own insurer | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| name | varchar(250) required | none / None | Official product-family name; Nonempty; not globally unique; edition years belong to PolicyVersion | None | Care Supreme | ["INS-01", "INS-02"] |
| benefit_type | enum required | unresolved / None | How the product pays benefits; medical_indemnity, fixed_benefit, hybrid, addon or unresolved | medical_indemnity, fixed_benefit, hybrid, addon, unresolved | medical_indemnity | ["INS-01", "INS-05"] |
| lifecycle_status | enum required | unresolved / None | Whether the product is sold or retained only historically; open, withdrawn, renewal_only, historical or unresolved | open, withdrawn, renewal_only, historical, unresolved | open | ["INS-01", "INS-03"] |
| recommendation_role | enum required | unresolved / None | How CoverGuide may use the product in advice; primary_policy, supplementary, reference_only, excluded or unresolved | primary_policy, supplementary, reference_only, excluded, unresolved | primary_policy | ["INS-01", "DEC-01"] |
| identity_evidence_id | fk:EvidenceSpan required | none / None | Exact original passage establishing product identity; Required reviewed evidence; a comparison name alone cannot establish official identity | None | Synthetic design example; no customer value used. | ["INS-01", "INS-04"] |

Constraints: no global unique-name assumption; identity_evidence_id required; recommendation_role and benefit_type remain distinct.
Indexes: insurer_id,name; benefit_type,lifecycle_status,recommendation_role.

## PolicyVersion

One complete legal terms package for a Product, assembled from every applicable governing document. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When curated metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| product_id | fk:Product required | none / None | Product governed by this policy version; Required | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| uin | varchar(100) optional | NULL / None | Curated resolved product UIN; Original-backed; conflicts remain unresolved rather than silently selected | None | CHIHLIP25047V012425 | ["INS-02", "INS-05"] |
| version_label | varchar(200) optional | NULL / None | Printed or curated policy edition label; Original-backed; source capture date is not an edition label | None | 2025 edition | ["INS-02"] |
| publication_status | enum required | draft / None | Curation and publication state; draft, reviewed, published, superseded or blocked | draft, reviewed, published, superseded, blocked | reviewed | ["INS-04", "OPS-03"] |
| supersedes_id | fk:PolicyVersion optional | NULL / None | Earlier legal terms package replaced by this one; Same Product; acyclic; evidence required before publication | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| applicability | json:ApplicabilityV1 required | none / None | Dates, issue or renewal events and other boundaries selecting this policy version; Closed typed structure; unknown material bounds block affected advice | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03", "INS-05"] |

Constraints: supersedes_id belongs to the same Product and is acyclic; publication requires all required PolicyVersionDocument rows and material dependencies; a newer discovered document does not automatically change applicability.
Indexes: product_id,publication_status; product_id,uin; product_id,supersedes_id.

## PolicyVersionDocument

Membership, role, conditional applicability and proven precedence of one DocumentVersion in a PolicyVersion. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| policy_version_id | fk:PolicyVersion required | none / None | Policy version whose legal document bundle includes this document; Required | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| document_version_id | fk:DocumentVersion required | none / None | Exact source-document edition; Required; must have at least one successful SourceCapture before reviewed use | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| role | enum required | none / None | Legal or explanatory role of the document; base_wording, customer_information_sheet, prospectus, endorsement, regulatory_modification, referenced_schedule or other_dependency | base_wording, customer_information_sheet, prospectus, endorsement, regulatory_modification, referenced_schedule, other_dependency | base_wording | ["INS-02", "INS-04"] |
| required_for_policy | boolean required | true / None | Whether the policy version is incomplete without this applicable document; False only when applicability explains the limited role | None | true | ["INS-04", "INS-05"] |
| applicability | json:ApplicabilityV1 required | none / None | Conditions under which this document participates in the policy version; No universal newest-document priority | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| precedence_evidence_id | fk:EvidenceSpan optional | NULL / None | Exact clause proving that this document controls another; NULL means no precedence has been proven | None | Synthetic design example; no customer value used. | ["INS-04", "INS-05"] |

Constraints: unique(policy_version_id,document_version_id,role); required applicable documents must be present before publication; precedence is never inferred from download date.
Indexes: policy_version_id,role; document_version_id.

## ProductVariant

One insurer-defined base variant and its allowed sums insured, deductibles, room categories and family choices. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When curated metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| policy_version_id | fk:PolicyVersion required | none / None | Policy version governing the variant; Required | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| name | varchar(200) required | Default / None | Official variant name or Default when the product has no named tier; Nonempty; no coverage inferred from the name | None | Gold | ["INS-01", "INS-03"] |
| choices | json:ConfigurationV1 required | none / None | Allowed sum insured, deductible, room, family and other base selectors; Typed values and units; describes allowed choices rather than one row per combination | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| availability | json:ApplicabilityV1 required | none / None | Sale, renewal, age, territory and insured-person conditions; Unresolved availability is not an exclusion | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| identity_evidence_id | fk:EvidenceSpan required | none / None | Original passage establishing the variant and its selectors; Required reviewed evidence | None | Synthetic design example; no customer value used. | ["INS-03", "INS-04"] |

Constraints: unique(policy_version_id,name); products without a named tier use exactly one Default variant; choices do not represent a customer selection.
Indexes: policy_version_id,name.

## ProductOption

One optional or mandatory add-on, rider or election available with a ProductVariant. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC; immutable; not a source effective date | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now / instant | When curated metadata or lifecycle state last changed; UTC; changes only with a stored field change | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| product_variant_id | fk:ProductVariant required | none / None | Base variant on which the option is available; Required | None | Synthetic design example; no customer value used. | ["INS-01", "INS-03"] |
| option_policy_version_id | fk:PolicyVersion optional | NULL / None | Separate policy terms for the option when they exist; Optional because some options are fully defined inside the base policy version | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| name | varchar(200) required | none / None | Official option name; Nonempty; unique within the variant | None | Claim Shield | ["INS-01", "INS-03"] |
| selection_kind | enum required | optional / None | Whether the customer may omit the option; optional or mandatory | optional, mandatory | optional | ["INS-03"] |
| conditions | json:ApplicabilityV1 required | none / None | Eligibility, dates, dependencies and incompatible selections; Closed typed conditions; incompatibility belongs here rather than in an overloaded status | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| identity_evidence_id | fk:EvidenceSpan required | none / None | Exact original passage establishing the option; Required reviewed evidence | None | Synthetic design example; no customer value used. | ["INS-03", "INS-04"] |

Constraints: unique(product_variant_id,name); option_policy_version_id does not by itself mean the option was selected by a customer.
Indexes: product_variant_id,name; option_policy_version_id.

## PolicyContract

A customer policy relationship; proposed cover remains a separate status. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| policy_number | varchar(200) optional | NULL / None | Issued identifier; Encrypted; not globally unique | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| insurer_id | fk:Insurer required | none / None | Issuing insurer; Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| proposer_id | fk:Person optional | NULL / None | Named proposer; Same owner; unknown distinct from buyer | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| payer_id | fk:Person optional | NULL / None | Premium payer; Same owner; need not be insured | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| kind | enum required | none / None | Individual or group relationship; individual,floater,group_member | i, n, d, i, v, i, d, u, a, l, ,, f, l, o, a, t, e, r, ,, g, r, o, u, p, _, m, e, m, b, e, r | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| status | enum required | proposed / None | Contract acceptance state; proposed,offered,accepted,in_force,expired,cancelled,declined,unresolved | p, r, o, p, o, s, e, d, ,, o, f, f, e, r, e, d, ,, a, c, c, e, p, t, e, d, ,, i, n, _, f, o, r, c, e, ,, e, x, p, i, r, e, d, ,, c, a, n, c, e, l, l, e, d, ,, d, e, c, l, i, n, e, d, ,, u, n, r, e, s, o, l, v, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| acceptance_span_id | fk:EvidenceSpan optional | NULL / None | Issuer acceptance evidence; Required before asserted acceptance | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |
| group_master_reference | varchar(250) optional | NULL / None | Employer/master policy identifier; Group member only; not member-cover proof | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-07", "INS-08"] |

Constraints: owner protected; status assertion requires evidence; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; proposer_id IS NULL OR owner_id IS NOT NULL; payer_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,insurer_id; owner_id,status.

## ContractRevision

Exact selected and individually endorsed terms for one contract interval. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_id | fk:PolicyContract required | none / None | Owned policy; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| revision | integer required | none / count | Contract revision sequence; Positive | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| configuration_id | fk:ProductVariant required | none / None | Selected public variant; No automatic latest terms | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| valid_during | daterange required | none / None | Coverage applicability interval; Explicit lower/upper bounds; no inferred midnight coverage rule | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| issued_at | instant optional | NULL / instant | Insurer issue event; Original-supported | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| received_at | instant optional | NULL / instant | Customer receipt event for rights clocks; Independent of issuance | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| schedule_document_id | fk:DocumentVersion optional | NULL / None | Personal issued schedule; Same owner; required for verified in-force configuration | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| selection | json:AcceptedSelectionV1 required | none / None | Accepted options, person scope and sums; Strict IDs and evidence; distinguish unknown option status | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| status | enum required | unverified / None | Applicability assessment; unverified,verified,conflicted,superseded | u, n, v, e, r, i, f, i, e, d, ,, v, e, r, i, f, i, e, d, ,, c, o, n, f, l, i, c, t, e, d, ,, s, u, p, e, r, s, e, d, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| previous_id | fk:ContractRevision optional | NULL / None | Prior accepted revision; Same contract; acyclic | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |

Constraints: unique(contract_id,revision); overlap allowed only with explicit transition/endorsement scope resolution; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; contract_id IS NULL OR owner_id IS NOT NULL; previous_id IS NULL OR owner_id IS NOT NULL.
Indexes: contract_id,revision; GiST valid_during.

## ContractMember

Actual named insured membership and individual commencement. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_revision_id | fk:ContractRevision required | none / None | Issued revision; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| person_id | fk:Person required | none / None | Insured person; Same owner | None | Intentionally no real customer/authentication values inspected or included. | ["CUS-01", "INS-03", "INS-07"] |
| role | enum required | none / None | Membership role; self,spouse,child,parent,other | s, e, l, f, ,, s, p, o, u, s, e, ,, c, h, i, l, d, ,, p, a, r, e, n, t, ,, o, t, h, e, r | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| valid_during | daterange required | none / None | Member coverage interval; Birth, addition, termination and renewal distinguished | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| membership_span_id | fk:EvidenceSpan optional | NULL / None | Member certificate/schedule proof; Required for verified membership | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| status | enum required | unverified / None | Membership certainty; proposed,verified,unverified,terminated | p, r, o, p, o, s, e, d, ,, v, e, r, i, f, i, e, d, ,, u, n, v, e, r, i, f, i, e, d, ,, t, e, r, m, i, n, a, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| member_identifier | varchar(160) optional | NULL / None | Insurer employee/member certificate ID; Encrypted; owner-scoped | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |

Constraints: No overlapping duplicate verified membership for the same contract_revision_id and person_id; valid_during is nonempty. ContractRevision defines the policy scope.; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate exact referenced identities and lineage. FOR KEY SHARE protects immutable referenced keys only; it does not serialize membership-set checks.; contract_revision_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL; Every ContractMember INSERT/UPDATE/DELETE locks all affected ContractRevision parent rows FOR UPDATE in deterministic ID order before modifying membership, including both old and new parents on a move. Under READ COMMITTED, run deferred overlap validation in a fresh statement after acquiring the locks, considering committed rows and this transaction. Restrict writes to this protocol; bulk imports and authorized erasure also follow it. No network or model call while holding these locks..
Indexes: contract_revision_id,person_id; GiST valid_during.

## IndividualTerm

Accepted underwriting modification scoped to people and benefits. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_revision_id | fk:ContractRevision required | none / None | Personal configuration; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| person_id | fk:Person optional | NULL / None | Affected insured if person-specific; Required when rule scope is person | None | Intentionally no real customer/authentication values inspected or included. | ["INS-03", "INS-05", "INS-06"] |
| kind | enum required | none / None | Individual modification; exclusion,copay,loading,waiver,waiting_change,other_endorsement | e, x, c, l, u, s, i, o, n, ,, c, o, p, a, y, ,, l, o, a, d, i, n, g, ,, w, a, i, v, e, r, ,, w, a, i, t, i, n, g, _, c, h, a, n, g, e, ,, o, t, h, e, r, _, e, n, d, o, r, s, e, m, e, n, t | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| rule_body | json:RuleV1 required | none / None | Typed conditional personal effect; Must identify override target and exact scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| status | enum required | proposed / None | Acceptance of personal term; proposed,offered,accepted,rejected,unresolved | p, r, o, p, o, s, e, d, ,, o, f, f, e, r, e, d, ,, a, c, c, e, p, t, e, d, ,, r, e, j, e, c, t, e, d, ,, u, n, r, e, s, o, l, v, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| evidence_span_id | fk:EvidenceSpan required | none / None | Original offer/accepted endorsement; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |
| valid_during | daterange required | none / None | Effective term interval; Must intersect covered membership | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-03", "INS-05", "INS-06"] |

Constraints: accepted modification requires issuer evidence and accepted configuration; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; contract_revision_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: contract_revision_id,person_id,kind.

## CoverageLayer

Original, enhanced, bonus or restored cover with separate clocks. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_revision_id | fk:ContractRevision required | none / None | Personal policy interval; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| person_id | fk:Person optional | NULL / None | Individual layer subject; NULL for shared pool; Scope required in limit_scope | None | Intentionally no real customer/authentication values inspected or included. | ["INS-07", "CAL-03", "CAL-04"] |
| kind | enum required | none / None | Cover origin; base,enhancement,bonus,recharge,restoration | b, a, s, e, ,, e, n, h, a, n, c, e, m, e, n, t, ,, b, o, n, u, s, ,, r, e, c, h, a, r, g, e, ,, r, e, s, t, o, r, a, t, i, o, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| amount | json:QuantityV1 required | none / None | Nominal cover for this layer; Money or dependent expression; not headline total | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| inception | date optional | NULL / calendar date | Layer clock start; Unknown retained | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| limit_scope | json:LimitScopeV1 required | none / None | Person/family/year/body-part/benefit scope; Explicit reset and member identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Issued layer/bonus evidence; Unverified status if absent | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |
| status | enum required | unverified / None | Layer validity; stipulated,unverified,verified,exhausted | s, t, i, p, u, l, a, t, e, d, ,, u, n, v, e, r, i, f, i, e, d, ,, v, e, r, i, f, i, e, d, ,, e, x, h, a, u, s, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "CAL-03", "CAL-04"] |

Constraints: layer amounts nonnegative where finite; no inferred sum-insured consumption from copay; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; contract_revision_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: contract_revision_id,kind,person_id.

## ContinuityCredit

Accepted prior history credited to an amount, person and benefit. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| layer_id | fk:CoverageLayer required | none / None | Receiving cover layer; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| prior_contract_id | fk:PolicyContract required | none / None | Historical source contract; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| person_id | fk:Person required | none / None | Person receiving credit; Same owner | None | Intentionally no real customer/authentication values inspected or included. | ["INS-07", "INS-08"] |
| credit_kind | enum required | none / None | Specific continuity measure; ped_wait,specific_wait,moratorium,bonus | p, e, d, _, w, a, i, t, ,, s, p, e, c, i, f, i, c, _, w, a, i, t, ,, m, o, r, a, t, o, r, i, u, m, ,, b, o, n, u, s | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| period | json:DurationV1 required | none / None | Accepted credited duration; Calendar versus elapsed units explicit | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| amount_scope | json:QuantityV1 required | none / None | Cover extent receiving credit; Money; unknown cannot mean whole SI | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| accepted_span_id | fk:EvidenceSpan optional | NULL / None | Receiving insurer acceptance; Required when status accepted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |
| status | enum required | requested / None | Credit assessment state; requested,accepted,disputed,unresolved | r, e, q, u, e, s, t, e, d, ,, a, c, c, e, p, t, e, d, ,, d, i, s, p, u, t, e, d, ,, u, n, r, e, s, o, l, v, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-07", "INS-08"] |

Constraints: no blanket personless continuity boolean; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; layer_id IS NULL OR owner_id IS NOT NULL; prior_contract_id IS NULL OR owner_id IS NOT NULL; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: layer_id,person_id,credit_kind.

## PolicyEvent

Dated policy and rights events with original receipt provenance. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| contract_id | fk:PolicyContract optional | NULL / None | Policy relationship; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| kind | enum required | none / None | Event type; issue,receipt,renewal_due,premium_paid,instalment_due,cancellation_notice,withdrawal_notice,port_request_received,port_information_received,group_exit,claim_notified,cancellation_enquiry,cancellation_requested,cancellation_received,cancellation_accepted,coverage_terminated,refund_calculated,refund_paid,refund_received,cancellation_declined,refund_reversed | i, s, s, u, e, ,, r, e, c, e, i, p, t, ,, r, e, n, e, w, a, l, _, d, u, e, ,, p, r, e, m, i, u, m, _, p, a, i, d, ,, i, n, s, t, a, l, m, e, n, t, _, d, u, e, ,, c, a, n, c, e, l, l, a, t, i, o, n, _, n, o, t, i, c, e, ,, w, i, t, h, d, r, a, w, a, l, _, n, o, t, i, c, e, ,, p, o, r, t, _, r, e, q, u, e, s, t, _, r, e, c, e, i, v, e, d, ,, p, o, r, t, _, i, n, f, o, r, m, a, t, i, o, n, _, r, e, c, e, i, v, e, d, ,, g, r, o, u, p, _, e, x, i, t, ,, c, l, a, i, m, _, n, o, t, i, f, i, e, d, ,, c, a, n, c, e, l, l, a, t, i, o, n, _, e, n, q, u, i, r, y, ,, c, a, n, c, e, l, l, a, t, i, o, n, _, r, e, q, u, e, s, t, e, d, ,, c, a, n, c, e, l, l, a, t, i, o, n, _, r, e, c, e, i, v, e, d, ,, c, a, n, c, e, l, l, a, t, i, o, n, _, a, c, c, e, p, t, e, d, ,, c, o, v, e, r, a, g, e, _, t, e, r, m, i, n, a, t, e, d, ,, r, e, f, u, n, d, _, c, a, l, c, u, l, a, t, e, d, ,, r, e, f, u, n, d, _, p, a, i, d, ,, r, e, f, u, n, d, _, r, e, c, e, i, v, e, d, ,, c, a, n, c, e, l, l, a, t, i, o, n, _, d, e, c, l, i, n, e, d, ,, r, e, f, u, n, d, _, r, e, v, e, r, s, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| occurred_at | json:TemporalExtentV1 required | none / None | Actual event time/date and precision; Timezone and uncertain interval retained | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| amount | json:QuantityV1 optional | NULL / None | Payment/debt/refund if event includes money; Typed money; missing not zero | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Documentary event proof; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| source_message_id | fk:Message optional | NULL / None | Customer event assertion; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| status | enum required | reported / None | Evidence certainty; reported,verified,disputed | r, e, p, o, r, t, e, d, ,, v, e, r, i, f, i, e, d, ,, d, i, s, p, u, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| related_event_id | fk:PolicyEvent optional | NULL / None | Receipt/payment connected event; Same owner and exact PolicyContract ID or ContractBundleRevision ID, subject to event-specific relationship checks. An explicitly linked source/receiving port contract is permitted only for the documented portability relation. Refusal links the relevant request; refund_reversed links the exact prior refund_paid event and validates its remaining balance under target locks. No arbitrary cross-policy or cross-package linkage. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| bundle_revision_id | fk:ContractBundleRevision optional | NULL / None | Exact package interpretation for a package-level receipt/request/event; Exactly one of contract_id or bundle_revision_id is set; retain revision even after membership correction | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| sender | json:PolicyEventPartyV1 required | {'kind': 'unknown', 'reason': 'Not established'} / None | Party making the evidenced communication or payment; Typed identity; person belongs to owner; insurer is the targeted contract issuer or one of the exact package component issuers. Unknown party cannot substantiate verified insurer receipt, acceptance, termination or payment. | None | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| recipient | json:PolicyEventPartyV1 required | {'kind': 'unknown', 'reason': 'Not established'} / None | Party receiving the evidenced communication or payment; Typed identity; person belongs to owner; insurer is the targeted contract issuer or one of the exact package component issuers. Unknown party cannot substantiate verified insurer receipt, acceptance, termination or payment. | None | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| authority_span_id | fk:EvidenceSpan optional | NULL / None | Authority of an insurer delegate to receive or decide for the target contract/package; Required for a TPA or other delegated authority before event can be verified; same owner or public agreement with exact issuer/scope/period; not established by a TPA name alone | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-10", "INS-08"] |

Constraints: at least one provenance source; port clocks use actual relevant receipt; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; contract_id IS NULL OR owner_id IS NOT NULL; source_message_id IS NULL OR owner_id IS NOT NULL; related_event_id IS NULL OR owner_id IS NOT NULL; num_nonnulls(contract_id,bundle_revision_id)=1; related events have same owner but do not imply shared contract or confirmed cancellation; Event kinds distinguish enquiry, requested, received, accepted, effective termination, calculated refund, paid refund and received refund. Legacy cancellation_notice is ambiguous and cannot be promoted without a new attributed specific event.; verified cancellation_received requires evidenced authorized insurer recipient; verified cancellation_accepted/coverage_terminated/refund_paid require evidenced authorized issuer sender, exact target, and authoritative source_span_id. Customer message or model explanation alone is insufficient.; refund_paid and refund_received are separate events; amount must state actual currency/value or remain explicitly unknown; no completed-refund claim from a calculated amount.; Sender/recipient typed references enforce owner and exact targeted component issuer set; a delegated party requires authority_span_id. Events record observations and do not dispatch external actions.; A verified cancellation_declined event requires authoritative issuer evidence; it does not imply coverage termination. It references the relevant request through related_event_id.; A verified refund_reversed event requires authoritative payment/reversal evidence and related_event_id targeting the exact prior refund_paid event with the same owner and contract or bundle revision. Store an actual reversal amount or explicit unknown; reject reversal above the remaining unreversed amount under event/target locks when amounts are known. Refund reversal never reinstates insurance cover by inference..
Indexes: contract_id,kind.

## Rule

Immutable original-backed condition or calculation instruction. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| terms_id | fk:PolicyVersion optional | NULL / None | Public product edition; Required for product rule; absent for general legal scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| rule_key | varchar(160) required | none / None | Stable logical rule identity; Unique within revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| revision | integer required | 1 / count | Rule representation revision; Positive; changed body creates new row | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| kind | enum required | none / None | Rule purpose; definition,grant,eligibility,exclusion,exception,waiting,limit,deduction,accumulation,precedence,operational_right | d, e, f, i, n, i, t, i, o, n, ,, g, r, a, n, t, ,, e, l, i, g, i, b, i, l, i, t, y, ,, e, x, c, l, u, s, i, o, n, ,, e, x, c, e, p, t, i, o, n, ,, w, a, i, t, i, n, g, ,, l, i, m, i, t, ,, d, e, d, u, c, t, i, o, n, ,, a, c, c, u, m, u, l, a, t, i, o, n, ,, p, r, e, c, e, d, e, n, c, e, ,, o, p, e, r, a, t, i, o, n, a, l, _, r, i, g, h, t | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| body | json:RuleV1 required | none / None | Versioned typed conditions and effects; Strict AST; no executable strings; unit and dependency validation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| body_sha256 | char(64) required | none / None | Canonical rule digest; Recompute before publication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| critical | boolean required | true / None | Whether unsupported use can materially harm advice; Reviewer may downgrade only with reason | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| review_state | enum required | draft / None | Rule approval state; draft,reviewed,blocked,published,superseded | d, r, a, f, t, ,, r, e, v, i, e, w, e, d, ,, b, l, o, c, k, e, d, ,, p, u, b, l, i, s, h, e, d, ,, s, u, p, e, r, s, e, d, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| inventory_item_id | fk:RuleInventoryItem optional | NULL / None | Optional original occurrence pointer for legacy/draft convenience; Not sufficient for numerator credit; exact counted-member support must be recorded by RuleInventorySupport | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-07"] |

Constraints: unique(owner_id,terms_id,rule_key,revision) NULLS NOT DISTINCT; public product rules have NULL owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: terms_id,kind,review_state; body GIN for registered filter keys.

## RuleEvidence

Claim-to-original support including exceptions and contradiction. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| rule_id | fk:Rule required | none / None | Curated rule; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| span_id | fk:EvidenceSpan required | none / None | Exact original passage; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| role | enum required | none / None | How passage relates to rule; supports,defines,restricts,excepts,contradicts,precedence,table_header,table_cell,footnote | s, u, p, p, o, r, t, s, ,, d, e, f, i, n, e, s, ,, r, e, s, t, r, i, c, t, s, ,, e, x, c, e, p, t, s, ,, c, o, n, t, r, a, d, i, c, t, s, ,, p, r, e, c, e, d, e, n, c, e, ,, t, a, b, l, e, _, h, e, a, d, e, r, ,, t, a, b, l, e, _, c, e, l, l, ,, f, o, o, t, n, o, t, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| mandatory | boolean required | true / None | Whether this passage is needed to justify use; Omission blocks affected rule | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| review_status | enum required | unreviewed / None | Semantic entailment review; unreviewed,supported,unsupported,unresolved | u, n, r, e, v, i, e, w, e, d, ,, s, u, p, p, o, r, t, e, d, ,, u, n, s, u, p, p, o, r, t, e, d, ,, u, n, r, e, s, o, l, v, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |

Constraints: unique(rule_id,span_id,role); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: rule_id; span_id.

## RuleDependency

Explicit connected-rule closure and direction. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| from_rule_id | fk:Rule required | none / None | Rule needing the dependency; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| to_rule_id | fk:Rule required | none / None | Required connected rule; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| kind | enum required | none / None | Dependency semantics; definition,prerequisite,exception,override,calculation_input,scope | d, e, f, i, n, i, t, i, o, n, ,, p, r, e, r, e, q, u, i, s, i, t, e, ,, e, x, c, e, p, t, i, o, n, ,, o, v, e, r, r, i, d, e, ,, c, a, l, c, u, l, a, t, i, o, n, _, i, n, p, u, t, ,, s, c, o, p, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| scope | json:ApplicabilityV1 required | none / None | When edge is mandatory; Explicit unknown conditions retained | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| precedence_span_id | fk:EvidenceSpan optional | NULL / None | Original evidence authorizing override; Required for override; no last-write-wins | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |

Constraints: no self dependency; calculation/override cycles rejected; definition cycles bounded and flagged; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: from_rule_id,kind; to_rule_id.

## RuleIssue

Missing evidence, contradiction or unread original region blocking capabilities. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentVersion optional | NULL / None | Affected original; At least document or rule | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| rule_id | fk:Rule optional | NULL / None | Affected rule; At least document or rule | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| kind | enum required | none / None | Unresolved matter; missing_original,unread_region,conflict,ambiguous_boundary,identity_conflict,unsupported_transcription,missing_dependency | m, i, s, s, i, n, g, _, o, r, i, g, i, n, a, l, ,, u, n, r, e, a, d, _, r, e, g, i, o, n, ,, c, o, n, f, l, i, c, t, ,, a, m, b, i, g, u, o, u, s, _, b, o, u, n, d, a, r, y, ,, i, d, e, n, t, i, t, y, _, c, o, n, f, l, i, c, t, ,, u, n, s, u, p, p, o, r, t, e, d, _, t, r, a, n, s, c, r, i, p, t, i, o, n, ,, m, i, s, s, i, n, g, _, d, e, p, e, n, d, e, n, c, y | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| severity | enum required | material / None | Impact on affected use; material,nonmaterial | m, a, t, e, r, i, a, l, ,, n, o, n, m, a, t, e, r, i, a, l | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| description | text required | none / None | Precise unresolved dependency and consequence; Nonempty; no generic unknown substituted for known facts | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| required_action | text required | none / None | Evidence needed to resolve issue; Specific original/interpretation request | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| status | enum required | open / None | Review resolution state; open,resolved,accepted_nonmaterial | o, p, e, n, ,, r, e, s, o, l, v, e, d, ,, a, c, c, e, p, t, e, d, _, n, o, n, m, a, t, e, r, i, a, l | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| resolution_span_id | fk:EvidenceSpan optional | NULL / None | Authoritative resolution proof; Required for source-based resolution | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |
| resolved_at | instant optional | NULL / instant | Resolution event; Required when resolved | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05", "OPS-03"] |

Constraints: material open issue blocks affected publication; do not delete historical issue; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: status,severity; rule_id; document_id.

## RuleInventoryItem

Immutable original source occurrence or independently derived atomic segment; its final count membership belongs to a sealed InventoryRevision. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| document_id | fk:DocumentVersion required | none / None | Original independently inventoried; Public | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| span_id | fk:EvidenceSpan required | none / None | Exact independently read rule location; Same document or connected span | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| instance_key | varchar(200) required | none / None | Original rule instance identity; Unique within original; separate per relevant variant/limit scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| scope | json:InventoryScopeV1 required | none / None | Relevance, insurer and count membership; Explicit inclusion/exclusion basis and connected-page coverage | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| reader_identity | varchar(150) required | none / None | Independent assessor identity; Not extraction process identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| review_state | enum required | unreviewed / None | Initial independent reading/transcription confidence of this immutable source occurrence; unreviewed,confirmed,disputed; not final denominator membership; that belongs to InventoryMembership | u, n, r, e, v, i, e, w, e, d, ,, c, o, n, f, i, r, m, e, d, ,, d, i, s, p, u, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "OPS-03"] |
| count_weight | integer optional | NULL / count | Preserved initial count suggestion, never an authoritative denominator contribution; NULL means no initial suggestion; nonnegative historical suggestion only. Coverage must use sealed InventoryMembership.count_weight instead | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-07"] |
| occurrence_kind | enum required | none / None | What this stable original identity denotes; printed_assertion,printed_table_cell,printed_qualifier,independent_atomic_segment | p, r, i, n, t, e, d, _, a, s, s, e, r, t, i, o, n, ,, p, r, i, n, t, e, d, _, t, a, b, l, e, _, c, e, l, l, ,, p, r, i, n, t, e, d, _, q, u, a, l, i, f, i, e, r, ,, i, n, d, e, p, e, n, d, e, n, t, _, a, t, o, m, i, c, _, s, e, g, m, e, n, t | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |

Constraints: unique(document_id,instance_key); inventory origin independent of candidate extraction; Original document/key/span and initial reading content are immutable; new segmentation creates new item identities linked by InventoryLineage; Initial review_state/count_weight cannot enter a coverage denominator; parser output cannot create independent inventory identities.
Indexes: document_id,review_state.

## Provider

Legal hospital organization and exact branch identity. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| legal_name | varchar(300) required | none / None | Provider organization name; Not a unique key | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| branch_name | varchar(250) optional | NULL / None | Specific facility branch; Unknown cannot match all branches | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| address | text optional | NULL / None | Original-backed branch address; No fuzzy automatic merge | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| city | varchar(150) optional | NULL / None | Branch city; Not customer residence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| postal_code | varchar(20) optional | NULL / None | Branch postcode; Country-specific validation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| country_code | char(2) required | IN / None | ISO3166 country; Explicit country for territory comparisons | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| external_identifiers | json:IdentifiersV1 required | empty array / None | Insurer/registry provider codes with provenance; Issuer scoped; conflicts preserved | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| identity_status | enum required | unresolved / None | Branch identity resolution; unresolved,verified,conflicted | u, n, r, e, s, o, l, v, e, d, ,, v, e, r, i, f, i, e, d, ,, c, o, n, f, l, i, c, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |

Constraints: no name-only uniqueness; verified external identity keys scoped by issuer.
Indexes: city,postal_code; external_identifiers GIN.

## ProviderObservation

Dated insurer- and service-specific hospital status. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| provider_id | fk:Provider required | none / None | Exact facility branch; Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| insurer_id | fk:Insurer optional | NULL / None | Insurer reporting status; Required for network_membership,exclusion,restricted_network,authorization; optional for clinician participation/search scope; NULL permitted for insurer-independent wheelchair_access | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| configuration_id | fk:ProductVariant optional | NULL / None | Restricted product scope; NULL is insurer-wide only if original supports | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| service_scope | json:ProviderScopeV1 required | none / None | Treatment, network tier and geographic scope; Explicit all/selected/unknown values | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| status | enum required | unknown / None | Legacy-style summary only for network/exclusion observations; kind/value are authoritative; network,nonnetwork,restricted,excluded,unknown,not_applicable | n, e, t, w, o, r, k, ,, n, o, n, n, e, t, w, o, r, k, ,, r, e, s, t, r, i, c, t, e, d, ,, e, x, c, l, u, d, e, d, ,, u, n, k, n, o, w, n, ,, n, o, t, _, a, p, p, l, i, c, a, b, l, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| observed_at | instant required | none / instant | Observation date; Not future guarantee | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| valid_during | json:TemporalExtentV1 required | none / None | Original stated validity if any; Unknown validity distinct from observation time | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| span_id | fk:EvidenceSpan required | none / None | Original dated directory/notice evidence; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| supersedes_id | fk:ProviderObservation optional | NULL / None | Prior status observation; Same branch/insurer/scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| kind | enum required | none / None | Independent observed provider property; network_membership,exclusion,restricted_network,wheelchair_access,clinician_participation,authorization,search_completeness | n, e, t, w, o, r, k, _, m, e, m, b, e, r, s, h, i, p, ,, e, x, c, l, u, s, i, o, n, ,, r, e, s, t, r, i, c, t, e, d, _, n, e, t, w, o, r, k, ,, w, h, e, e, l, c, h, a, i, r, _, a, c, c, e, s, s, ,, c, l, i, n, i, c, i, a, n, _, p, a, r, t, i, c, i, p, a, t, i, o, n, ,, a, u, t, h, o, r, i, z, a, t, i, o, n, ,, s, e, a, r, c, h, _, c, o, m, p, l, e, t, e, n, e, s, s | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| value | json:ObservationValueV1 required | none / None | Typed observed value and evidence certainty; Boolean/code/unknown plus source completeness; absence of hit not false | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| clinician_id | fk:Clinician optional | NULL / None | Named specialist participation subject; Required for clinician_participation; otherwise NULL | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| search_coverage | json:SearchCoverageV1 required | none / None | Scope and completeness of the observed directory/query; Exact source revision, query, pagination and completeness; unmeasured if unknown | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |

Constraints: immutable history; overlapping contradictory observations produce issue; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; network/exclusion/restricted_network/authorization kinds require insurer_id;clinician_participation requires clinician_id;wheelchair_access can be branch-wide with insurer_id NULL;configuration requires its matching insurer.
Indexes: provider_id,insurer_id,observed_at DESC; configuration_id.

## Quote

Private insurer offer bound to exact people, facts and configuration. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Comparison context; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| profile_revision_id | fk:CustomerProfileRevision required | none / None | Exact customer profile used for this quote observation; Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| configuration_id | fk:ProductVariant required | none / None | Quoted public options basis; Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| quoted_selection | json:AcceptedSelectionV1 required | none / None | People, option selections, SI and deductible; Typed IDs/quantities; no default acceptance | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| insurer_quote_id | varchar(200) optional | NULL / None | Issuer quote identifier; Owner-scoped; encrypted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| issued_at | instant optional | NULL / instant | Issuer quote time; Source-supported | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| valid_until | instant optional | NULL / instant | Offer expiry; Unknown not indefinite | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| status | enum required | unverified / None | Offer/acceptance state; unverified,offered,accepted,expired,declined,invalidated | u, n, v, e, r, i, f, i, e, d, ,, o, f, f, e, r, e, d, ,, a, c, c, e, p, t, e, d, ,, e, x, p, i, r, e, d, ,, d, e, c, l, i, n, e, d, ,, i, n, v, a, l, i, d, a, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| source_document_id | fk:DocumentVersion required | none / None | Original quote; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| total | json:QuantityV1 required | none / None | Verified payable total or explicit unknown; Money; components reconcile before finite validated total | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| coverage_term | json:TemporalExtentV1 required | none / None | Quoted insurance term; Distinct from payment frequency | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |

Constraints: fact correction invalidates reuse; accepted quote alone not in-force policy; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; profile_revision_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,conversation_id,status; valid_until.

## QuoteComponent

A source-backed premium, loading, discount or tax component. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| quote_id | fk:Quote required | none / None | Owned quote; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| sequence | integer required | none / count | Calculation/order on source quote; Positive | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| kind | enum required | none / None | Premium component; base,addon,loading,discount,tax,fee,instalment_charge | b, a, s, e, ,, a, d, d, o, n, ,, l, o, a, d, i, n, g, ,, d, i, s, c, o, u, n, t, ,, t, a, x, ,, f, e, e, ,, i, n, s, t, a, l, m, e, n, t, _, c, h, a, r, g, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| amount | json:QuantityV1 required | none / None | Money or explicit unknown amount; Signed only discount/refund; currency consistent | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| basis | json:ExpressionV1 optional | NULL / None | Original rate/base calculation when given; Strict typed expression; no assumed tax rate | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| span_id | fk:EvidenceSpan required | none / None | Exact quote/tax evidence; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| applies_to | json:ComponentScopeV1 required | none / None | Person, option or component base IDs; Explicit set; no implicit total premium basis | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |

Constraints: unique(quote_id,sequence); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; quote_id IS NULL OR owner_id IS NOT NULL.
Indexes: quote_id,sequence.

## PaymentScheduleItem

Quoted or issued instalment schedule with distinct debt status. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| quote_id | fk:Quote optional | NULL / None | Quoted schedule parent; Exactly one quote or contract | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| contract_id | fk:PolicyContract optional | NULL / None | Issued schedule parent; Exactly one quote or contract | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| sequence | integer required | none / count | Payment ordinal; Positive | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| amount | json:QuantityV1 required | none / None | Payable amount; Money; unknown explicit | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| due_on | date optional | NULL / calendar date | Scheduled due date; Unknown distinct from paid | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| paid_event_id | fk:PolicyEvent optional | NULL / None | Actual receipt evidence; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| span_id | fk:EvidenceSpan required | none / None | Original instalment terms; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |

Constraints: exactly one parent; unique(parent,sequence) with two partial constraints; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; quote_id IS NULL OR owner_id IS NOT NULL; contract_id IS NULL OR owner_id IS NOT NULL; paid_event_id IS NULL OR owner_id IS NOT NULL.
Indexes: quote_id,sequence; contract_id,due_on.

## TreatmentEpisode

Actual or synthetic treatment event, separate from insurer claim. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| person_id | fk:Person required | none / None | Treated insured subject; Same owner | None | Intentionally no real customer/authentication values inspected or included. | ["INS-06", "CAL-02", "CAL-03"] |
| provider_id | fk:Provider optional | NULL / None | Facility branch; Unresolved branch remains NULL | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| started_at | json:TemporalExtentV1 required | none / None | Admission/treatment date with precision; Date-only not invented timestamp | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| ended_at | json:TemporalExtentV1 required | none / None | Discharge or unknown end; Cannot precede start when both known | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| setting | enum required | unknown / None | Treatment setting; inpatient,daycare,outpatient,home,ayush,unknown | i, n, p, a, t, i, e, n, t, ,, d, a, y, c, a, r, e, ,, o, u, t, p, a, t, i, e, n, t, ,, h, o, m, e, ,, a, y, u, s, h, ,, u, n, k, n, o, w, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| clinical_facts | json:ClinicalFactsV1 required | none / None | Diagnosis/advice/procedure assertion IDs; References owned facts; no AI diagnosis inferred | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| last_related_consultation | date optional | NULL / calendar date | Illness episode reference event; Original/customer provenance required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| provenance | enum required | reported / None | Event certainty; reported,documented,case_stipulated | r, e, p, o, r, t, e, d, ,, d, o, c, u, m, e, n, t, e, d, ,, c, a, s, e, _, s, t, i, p, u, l, a, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| source_document_id | fk:DocumentVersion optional | NULL / None | Treatment original; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |

Constraints: temporal consistency; person ownership; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; person_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,person_id; provider_id.

## ExpenseLine

Item-level billed expense with clinical and event association. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| episode_id | fk:TreatmentEpisode required | none / None | Treatment event; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| line_number | integer required | none / count | Invoice line identity; Positive | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| label | text required | none / None | Original bill description; Do not overwrite with normalized classification | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| category | enum required | unknown / None | Reviewed cost classification; room,icu,medicine,procedure,implant,diagnostic,consultation,ambulance,consumable,other,unknown | r, o, o, m, ,, i, c, u, ,, m, e, d, i, c, i, n, e, ,, p, r, o, c, e, d, u, r, e, ,, i, m, p, l, a, n, t, ,, d, i, a, g, n, o, s, t, i, c, ,, c, o, n, s, u, l, t, a, t, i, o, n, ,, a, m, b, u, l, a, n, c, e, ,, c, o, n, s, u, m, a, b, l, e, ,, o, t, h, e, r, ,, u, n, k, n, o, w, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| service_on | date optional | NULL / calendar date | Expense service date; Needed for pre/post membership | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| amount | json:QuantityV1 required | none / None | Gross billed money; Nonnegative finite or unknown | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| quantity | json:QuantityV1 optional | NULL / None | Days or other billed units; Unit explicit; not inferred from dates alone | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| relatedness_fact_id | fk:CustomerFact optional | NULL / None | Customer fact supporting relatedness where customer-supplied; Same owner; clinical relation not date proximity alone | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| span_id | fk:EvidenceSpan optional | NULL / None | Original bill line evidence; Required for documented amount | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| service_extent | json:TemporalExtentV1 required | none / None | Actual service interval and timestamp precision; Date-only remains uncertain around stabilization instant; no invented midnight | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |

Constraints: unique(episode_id,line_number); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; episode_id IS NULL OR owner_id IS NOT NULL; relatedness_fact_id IS NULL OR owner_id IS NOT NULL.
Indexes: episode_id,line_number; category.

## Claim

An insurer claim for an episode under one specific contract. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| episode_id | fk:TreatmentEpisode required | none / None | Treatment event; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| contract_revision_id | fk:ContractRevision required | none / None | Claimed personal terms; Same owner; treatment applicability checked | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| insurer_claim_id | varchar(200) optional | NULL / None | Issuer claim identifier; Encrypted; insurer/owner scoped | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| kind | enum required | none / None | Claim process type; cashless,reimbursement,preauthorization | c, a, s, h, l, e, s, s, ,, r, e, i, m, b, u, r, s, e, m, e, n, t, ,, p, r, e, a, u, t, h, o, r, i, z, a, t, i, o, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| status | enum required | reported / None | Observed insurer outcome; reported,pending,authorized,part_paid,paid,repudiated,withdrawn,unresolved | r, e, p, o, r, t, e, d, ,, p, e, n, d, i, n, g, ,, a, u, t, h, o, r, i, z, e, d, ,, p, a, r, t, _, p, a, i, d, ,, p, a, i, d, ,, r, e, p, u, d, i, a, t, e, d, ,, w, i, t, h, d, r, a, w, n, ,, u, n, r, e, s, o, l, v, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| submitted_at | instant optional | NULL / instant | Convenience summary of the currently accepted submission event; May be NULL; authoritative history is ClaimEvent claim_submitted/claim_received with exact recipient; derive only from a selected verified event and do not replace receipt clocks | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| settlement_document_id | fk:DocumentVersion optional | NULL / None | Insurer outcome original; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| primary_claim_id | fk:Claim optional | NULL / None | First indemnity insurer selection for balance coordination; Same episode/owner; no cycle | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |

Constraints: authorization not final entitlement; no duplicate recovery by summing separate claims; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; episode_id IS NULL OR owner_id IS NOT NULL; contract_revision_id IS NULL OR owner_id IS NOT NULL; primary_claim_id IS NULL OR owner_id IS NOT NULL.
Indexes: episode_id,contract_revision_id; owner_id,status.

## ClaimLineAssessment

Per-insurer expense treatment with distinct monetary roles. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| claim_id | fk:Claim required | none / None | Insurer-specific claim; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| expense_id | fk:ExpenseLine required | none / None | Bill item being assessed; Same episode | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| status | enum required | unknown / None | Item admissibility; admissible,inadmissible,conditional,unknown | a, d, m, i, s, s, i, b, l, e, ,, i, n, a, d, m, i, s, s, i, b, l, e, ,, c, o, n, d, i, t, i, o, n, a, l, ,, u, n, k, n, o, w, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| admissible_amount | json:QuantityV1 required | none / None | Expense after contract exclusions/limits; Money; unknown propagation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| threshold_amount | json:QuantityV1 required | none / None | Contribution to deductible accumulation; Separate from admissible/payment | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| cover_consumption | json:QuantityV1 required | none / None | Consumption of relevant cover pool; Not inferred from insurer paid amount | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| paid_amount | json:QuantityV1 required | none / None | Actual insurer payment if known; Separate from estimated payable | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| reason | text required | none / None | Specific inclusion/exclusion reason; Must cite applicable rule or insurer settlement | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| rule_id | fk:Rule optional | NULL / None | Governing rule when curated; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| span_id | fk:EvidenceSpan optional | NULL / None | Original settlement or contract proof; At least rule or span for supported status | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| revision | integer required | 1 / None | Immutable item-assessment revision; Positive; never overwrite earlier assessment | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03", "DEC-01"] |
| supersedes_id | fk:ClaimLineAssessment optional | NULL / None | Earlier assessment corrected by this revision; Same claim/expense; lower revision; acyclic | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03"] |

Constraints: expense belongs to claim episode; unknown is not zero; unique(claim_id,expense_id,revision);supersession is a single nonbranching chain;current selection is latest accepted revision as of decision profile revision; usage entries reference exact immutable assessment revision;correction posts reversals/new entries rather than edits; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; claim_id IS NULL OR owner_id IS NOT NULL; expense_id IS NULL OR owner_id IS NOT NULL; supersedes_id IS NULL OR owner_id IS NOT NULL.
Indexes: claim_id,expense_id.

## UsageEntry

Append-only signed utilization or reversal for a scoped pool. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| layer_id | fk:CoverageLayer required | none / None | Cover/limit pool; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| claim_line_id | fk:ClaimLineAssessment optional | NULL / None | Claim item causing use; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| kind | enum required | none / None | Accounting role; reserve,admissible_threshold,cover_use,payment,reversal,bonus_award,bonus_withdrawal | r, e, s, e, r, v, e, ,, a, d, m, i, s, s, i, b, l, e, _, t, h, r, e, s, h, o, l, d, ,, c, o, v, e, r, _, u, s, e, ,, p, a, y, m, e, n, t, ,, r, e, v, e, r, s, a, l, ,, b, o, n, u, s, _, a, w, a, r, d, ,, b, o, n, u, s, _, w, i, t, h, d, r, a, w, a, l | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| amount | json:QuantityV1 required | none / None | Signed posted quantity; Finite money; reversals point to original | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| scope | json:LimitScopeV1 required | none / None | Exact person/illness/year/body-part scope; No cross-year aggregation unless original authorizes | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| posted_at | instant required | none / instant | Ledger posting time; Immutable | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| occurred_on | date required | none / calendar date | Underlying policy event date; Not posting date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| reverses_id | fk:UsageEntry optional | NULL / None | Entry corrected or released; Same pool/scope; reversal sum cannot exceed original | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Insurer usage or bonus evidence; Unverified reservations distinctly labelled | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| posting_key | uuid required | none / None | Stable source-event/component posting identity; Unique per owner across all posting kinds; stored before worker dispatch | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03", "OPS-02"] |
| policy_event_id | fk:PolicyEvent optional | NULL / None | Source policy event for nonclaim postings; Same owner; optional if exact claim-line revision is provenance | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03"] |
| claim_payment_id | fk:ClaimPayment optional | NULL / None | Exact disbursement that funds an insurer-payment ledger posting; Same owner and claim as claim_line_id; only indemnity component; optional for legacy/unverified/nonpayment entries | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CAL-03"] |

Constraints: append-only; finite quantities only; unique(owner_id,posting_key);posting_key generated from durable source-event action and component identity;retry reuses key; one explicit source event or claim-line revision;atomic reversal sum locks original entry and prevents over-reversal; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; layer_id IS NULL OR owner_id IS NOT NULL; claim_line_id IS NULL OR owner_id IS NOT NULL; reverses_id IS NULL OR owner_id IS NOT NULL; policy_event_id IS NULL OR owner_id IS NOT NULL; New verified payment postings require claim_payment_id; aggregate non-reversed postings cannot exceed the known indemnity of that payment; interest and other amounts never consume cover; Claim payment corrections/reversals create new evidenced transactions and ledger reversals rather than changing historical UsageEntry amounts.
Indexes: layer_id,occurred_on; claim_line_id; reverses_id.

## CorpusRevision

Immutable published knowledge manifest. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| sequence | bigint required | none / None | Corpus release sequence; Positive unique | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| manifest_sha256 | char(64) required | none / None | Digest of exact member set and dependencies; Verified before publication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| state | enum required | draft / None | Publication state; draft,validated,published,retired,blocked | d, r, a, f, t, ,, v, a, l, i, d, a, t, e, d, ,, p, u, b, l, i, s, h, e, d, ,, r, e, t, i, r, e, d, ,, b, l, o, c, k, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| validated_at | instant optional | NULL / instant | Independent closure/coverage validation; Required before publish | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| published_at | instant optional | NULL / instant | Atomic publication event; Single publication transaction | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| previous_id | fk:CorpusRevision optional | NULL / None | Previous published corpus; Acyclic | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| coverage_report_id | fk:CoverageReport optional | NULL / None | Independent inventory completeness measurements; Unknown denominators explicitly block coverage claim | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |

Constraints: sequence unique; sealed member set immutable.
Indexes: state,sequence DESC.

## CorpusMember

Exact terms and rule revisions included in a corpus. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| corpus_id | fk:CorpusRevision required | none / None | Immutable publication; Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| rule_id | fk:Rule required | none / None | Exact curated rule revision; Public; reviewed | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| terms_id | fk:PolicyVersion optional | NULL / None | Applicable product edition; Must match rule when product-bound | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| capabilities | json:CapabilityScopeV1 required | none / None | Supported intents, insurers and rule scopes; Unknown/blocked capability never silently included | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |

Constraints: unique(corpus_id,rule_id); all mandatory dependencies present.
Indexes: corpus_id,terms_id; rule_id.

## CorpusPointer

Atomic current corpus selection for one publication channel. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| channel | varchar(80) required | none / None | Publication channel; production,review,pilot; explicit allowlist | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| corpus_id | fk:CorpusRevision required | none / None | Selected immutable corpus; Published/validated as required by channel | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| generation | bigint required | 0 / None | Compare-and-swap publication revision; Monotonic | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| changed_at | instant required | now / instant | Pointer update time; Atomic with durable invalidation event | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |

Constraints: channel unique; production target must be published.
Indexes: channel unique.

## SearchChunk

Replaceable searchable derivative with exact original coverage. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentVersion required | none / None | Source edition; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| span_ids | json:UuidListV1 required | none / None | Ordered evidence spans in chunk; All IDs exist and belong to original/owner; validated closure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| text | text required | none / None | Retrieval derivative text; Never treated as independent original truth | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| lexical_vector | tsvector required | derived / None | PostgreSQL text-search representation; Rebuildable; language configuration version recorded | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| embedding | vector(1024) optional | NULL / None | BGE-M3 dense vector derivative; Only qualified1024-dim adapter output; no evaluation material | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| index_revision | varchar(160) required | none / None | Tokenizer, embedding and chunking version; Immutable identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| corpus_id | fk:CorpusRevision required | none / None | Corpus under which retrieval is allowed; Member source and access checks precede ranking | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| chunk_sha256 | char(64) required | none / None | Derivative content fingerprint; Hash includes text/span ordering/index revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |

Constraints: unique(owner_id,corpus_id,index_revision,chunk_sha256) NULLS NOT DISTINCT; private owner filters before retrieval; equal private derivatives are separate owner records;public corpus cannot include private chunks; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: Public corpus BM25 via qualified pg_textsearch 1.4.0, version-qualified index and corpus/document filters; Private search uses owner-prefiltered deterministic BM25 in the replaceable retrieval adapter until private index isolation is proven; GIN lexical_vector is only lexical fallback/diagnostics and never labelled BM25; HNSW embedding vector_cosine_ops for public corpus; exact cosine over owner-prefiltered private candidates; document_id.

## Artifact

Stable dependency identity for immutable inputs and outputs. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| kind | enum required | none / None | Typed artifact class; customer_statement,customer_fact,customer_requirement,message,customer_profile_revision,terms,rule,document,quote,provider_observation,decision,calculation,model_qualification,corpus,search_chunk,processing_output,model_response,contract_revision,individual_term,coverage_layer,usage_entry,claim_event,claim_document_requirement,claim_document_receipt,claim_payment,inventory_item,inventory_revision,inventory_membership,inventory_lineage,inventory_support,coverage_report,terms_component,contract_bundle_revision,contract_bundle_member,policy_event | c, u, s, t, o, m, e, r, _, s, t, a, t, e, m, e, n, t, ,, c, u, s, t, o, m, e, r, _, f, a, c, t, ,, c, u, s, t, o, m, e, r, _, r, e, q, u, i, r, e, m, e, n, t, ,, m, e, s, s, a, g, e, ,, c, u, s, t, o, m, e, r, _, p, r, o, f, i, l, e, _, r, e, v, i, s, i, o, n, ,, t, e, r, m, s, ,, r, u, l, e, ,, d, o, c, u, m, e, n, t, ,, q, u, o, t, e, ,, p, r, o, v, i, d, e, r, _, o, b, s, e, r, v, a, t, i, o, n, ,, d, e, c, i, s, i, o, n, ,, c, a, l, c, u, l, a, t, i, o, n, ,, m, o, d, e, l, _, q, u, a, l, i, f, i, c, a, t, i, o, n, ,, c, o, r, p, u, s, ,, s, e, a, r, c, h, _, c, h, u, n, k, ,, p, r, o, c, e, s, s, i, n, g, _, o, u, t, p, u, t, ,, m, o, d, e, l, _, r, e, s, p, o, n, s, e, ,, c, o, n, t, r, a, c, t, _, r, e, v, i, s, i, o, n, ,, i, n, d, i, v, i, d, u, a, l, _, t, e, r, m, ,, c, o, v, e, r, a, g, e, _, l, a, y, e, r, ,, u, s, a, g, e, _, e, n, t, r, y, ,, c, l, a, i, m, _, e, v, e, n, t, ,, c, l, a, i, m, _, d, o, c, u, m, e, n, t, _, r, e, q, u, i, r, e, m, e, n, t, ,, c, l, a, i, m, _, d, o, c, u, m, e, n, t, _, r, e, c, e, i, p, t, ,, c, l, a, i, m, _, p, a, y, m, e, n, t, ,, i, n, v, e, n, t, o, r, y, _, i, t, e, m, ,, i, n, v, e, n, t, o, r, y, _, r, e, v, i, s, i, o, n, ,, i, n, v, e, n, t, o, r, y, _, m, e, m, b, e, r, s, h, i, p, ,, i, n, v, e, n, t, o, r, y, _, l, i, n, e, a, g, e, ,, i, n, v, e, n, t, o, r, y, _, s, u, p, p, o, r, t, ,, c, o, v, e, r, a, g, e, _, r, e, p, o, r, t, ,, t, e, r, m, s, _, c, o, m, p, o, n, e, n, t, ,, c, o, n, t, r, a, c, t, _, b, u, n, d, l, e, _, r, e, v, i, s, i, o, n, ,, c, o, n, t, r, a, c, t, _, b, u, n, d, l, e, _, m, e, m, b, e, r, ,, p, o, l, i, c, y, _, e, v, e, n, t | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| object_id | uuid required | none / None | Typed target row UUID; Deferred constraint trigger resolves kind to exact allowed table and matching owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| content_sha256 | char(64) required | none / None | Immutable target digest; Verified on registration | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| validity | enum required | current / None | Whether valid for current reuse; current,stale,blocked,erased | c, u, r, r, e, n, t, ,, s, t, a, l, e, ,, b, l, o, c, k, e, d, ,, e, r, a, s, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| invalidated_at | instant optional | NULL / instant | First invalidation event; Historical target remains readable only if authorized | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |

Constraints: unique(kind,object_id); typed target existence and owner trigger; no arbitrary table names; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; New claim artifact kinds resolve to exact owner-bound ClaimEvent/ClaimDocumentRequirement/ClaimDocumentReceipt/ClaimPayment; inventory/coverage artifact kinds resolve only to public immutable inventory/review/report rows.
Indexes: kind,object_id; validity.

## Dependency

Input dependency used for replay and selective invalidation. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| dependent_id | fk:Artifact required | none / None | Computed artifact; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| input_id | fk:Artifact required | none / None | Exact input artifact; Public or same owner; never another owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| purpose | enum required | none / None | Why input is necessary; facts,applicability,rule,evidence,quote,provider,model,corpus | f, a, c, t, s, ,, a, p, p, l, i, c, a, b, i, l, i, t, y, ,, r, u, l, e, ,, e, v, i, d, e, n, c, e, ,, q, u, o, t, e, ,, p, r, o, v, i, d, e, r, ,, m, o, d, e, l, ,, c, o, r, p, u, s | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| material | boolean required | true / None | Whether invalidity blocks dependent reuse; False needs recorded nonmaterial reason | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| reason | text required | none / None | Specific dependency scope; No generic undocumented edge | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |

Constraints: unique(dependent_id,input_id,purpose); no self/cycles in computed graph; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: input_id; dependent_id.

## Decision

Validated adviser outcome for exact inputs and evidence. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Customer context; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| turn_id | fk:Turn required | none / None | Owning processing turn; Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| advice_request_id | fk:AdviceRequest required | none / None | Customer advice goal answered; Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| profile_revision_id | fk:CustomerProfileRevision required | none / None | Exact customer profile evaluated; Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| corpus_id | fk:CorpusRevision required | none / None | Immutable knowledge inputs; Published allowed corpus | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| outcome | enum required | none / None | Answer completeness state; complete,conditional,clarification,insufficient_evidence,technical_failure | c, o, m, p, l, e, t, e, ,, c, o, n, d, i, t, i, o, n, a, l, ,, c, l, a, r, i, f, i, c, a, t, i, o, n, ,, i, n, s, u, f, f, i, c, i, e, n, t, _, e, v, i, d, e, n, c, e, ,, t, e, c, h, n, i, c, a, l, _, f, a, i, l, u, r, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| answer_text | text required | none / None | Validated rendered answer; Citations resolve; no unsupported critical claims | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| scope | json:DecisionScopeV1 required | none / None | Precisely answered question and unresolved remainder; Conditional calculation not full entitlement | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| validation | json:ValidationV1 required | none / None | Claim support and material correctness results; Failed critical check prevents publication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| published_at | instant optional | NULL / instant | User-visible publication time; Fact revision/current turn still matches under lock | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| validity | enum required | current / None | Current replay validity; current,stale,blocked,erased | c, u, r, r, e, n, t, ,, s, t, a, l, e, ,, b, l, o, c, k, e, d, ,, e, r, a, s, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| supersedes_id | fk:Decision optional | NULL / None | Prior answer revised by correction; Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |

Constraints: one published decision per successful turn; publication fact CAS; critical errors block; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; conversation_id IS NULL OR owner_id IS NOT NULL; turn_id IS NULL OR owner_id IS NOT NULL; advice_request_id IS NULL OR owner_id IS NOT NULL; profile_revision_id IS NULL OR owner_id IS NOT NULL; supersedes_id IS NULL OR owner_id IS NOT NULL.
Indexes: conversation_id,created_at DESC; turn_id; validity.

## DecisionClaim

One independently supported statement or candidate disposition. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| decision_id | fk:Decision required | none / None | Answer artifact; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| ordinal | integer required | none / count | Claim order; Positive | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| text | text required | none / None | Exact supported assertion; Scope restricted to cited evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| kind | enum required | none / None | Statement type; fact,eligibility,exclusion,calculation,comparison,clarification,limitation | f, a, c, t, ,, e, l, i, g, i, b, i, l, i, t, y, ,, e, x, c, l, u, s, i, o, n, ,, c, a, l, c, u, l, a, t, i, o, n, ,, c, o, m, p, a, r, i, s, o, n, ,, c, l, a, r, i, f, i, c, a, t, i, o, n, ,, l, i, m, i, t, a, t, i, o, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| critical | boolean required | true / None | Material correctness flag; Eligibility/calculation/privacy claims critical | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| support | enum required | unverified / None | Evidence validation result; supported,conditional,unsupported,conflicted | s, u, p, p, o, r, t, e, d, ,, c, o, n, d, i, t, i, o, n, a, l, ,, u, n, s, u, p, p, o, r, t, e, d, ,, c, o, n, f, l, i, c, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| candidate_configuration_id | fk:ProductVariant optional | NULL / None | Candidate to which statement applies; No market-wide extrapolation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| missing_dependency | text optional | NULL / None | Precise unresolved condition and effect; Required for conflicted/conditional when material | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |

Constraints: unique(decision_id,ordinal); unsupported critical claim cannot publish; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; decision_id IS NULL OR owner_id IS NOT NULL.
Indexes: decision_id,ordinal.

## ClaimCitation

Original support attached to one answer claim. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| claim_id | fk:DecisionClaim required | none / None | Supported statement; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| span_id | fk:EvidenceSpan required | none / None | Exact original citation target; Public or same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| role | enum required | none / None | Support relationship; supports,restricts,excepts,conflicts,assumption_source | s, u, p, p, o, r, t, s, ,, r, e, s, t, r, i, c, t, s, ,, e, x, c, e, p, t, s, ,, c, o, n, f, l, i, c, t, s, ,, a, s, s, u, m, p, t, i, o, n, _, s, o, u, r, c, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| rule_id | fk:Rule optional | NULL / None | Interpreted rule connecting original to claim; Exact corpus revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| ordinal | integer required | none / count | Display order; Positive | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |

Constraints: unique(claim_id,span_id,role); all cited originals accessible to owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; claim_id IS NULL OR owner_id IS NOT NULL.
Indexes: claim_id,ordinal; span_id.

## Calculation

Independent deterministic result with complete trace. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| decision_id | fk:Decision required | none / None | Owning answer; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| label | varchar(200) required | none / None | Calculation purpose; No entitlement implication beyond scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| engine_version | varchar(120) required | none / None | Deterministic evaluator identity; Immutable qualified build | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| expression | json:ExpressionV1 required | none / None | Typed calculation AST; No eval strings; no hidden operation order | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| inputs | json:CalculationInputsV1 required | none / None | Values, units and assertion/span references; Complete required inputs or explicit unknown | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| result | json:TypedValueV1 required | none / None | Computed result or unknown; Finite Decimal money; never binary float | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| trace | json:CalculationTraceV1 required | none / None | Ordered intermediate results and rule applications; Reproducible from stored inputs | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| assumptions | json:AssumptionsV1 required | none / None | Explicit hypothetical and unresolved premises; Synthetic not issuer acceptance | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| scope | enum required | none / None | Meaning of result; hypothetical,threshold_only,conditional_payable,verified_entitlement | h, y, p, o, t, h, e, t, i, c, a, l, ,, t, h, r, e, s, h, o, l, d, _, o, n, l, y, ,, c, o, n, d, i, t, i, o, n, a, l, _, p, a, y, a, b, l, e, ,, v, e, r, i, f, i, e, d, _, e, n, t, i, t, l, e, m, e, n, t | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| verified_by | varchar(160) optional | NULL / None | Independent method/reviewer identifier; Required for curated benchmark oracle, not model self-assertion | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |

Constraints: deterministic hash/replay check; complete result requires known inputs; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; decision_id IS NULL OR owner_id IS NOT NULL.
Indexes: decision_id.

## Turn

Durable unit of customer work owned by a worker. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none / None | Persistent context; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| request_id | uuid required | none / None | Idempotent customer request; Unique per owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| payload_sha256 | char(64) required | none / None | Canonical request hash; Same request different hash => conflict | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| input_message_id | fk:Message required | none / None | Persisted customer input; Same conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| expected_revision | bigint required | none / None | Requested accepted fact revision; CAS before dispatch/publication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| profile_revision_id | fk:CustomerProfileRevision required | none / None | Exact customer profile fixed before dispatch; Same conversation and expected revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| state | enum required | queued / None | Durable processing outcome; queued,running,cancel_requested,cancelled,completed,failed,stale | q, u, e, u, e, d, ,, r, u, n, n, i, n, g, ,, c, a, n, c, e, l, _, r, e, q, u, e, s, t, e, d, ,, c, a, n, c, e, l, l, e, d, ,, c, o, m, p, l, e, t, e, d, ,, f, a, i, l, e, d, ,, s, t, a, l, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| lease_token | uuid optional | NULL / None | Current worker fencing token; Required when running; changes on recovery | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| lease_until | instant optional | NULL / instant | Lease expiry; UTC; expired worker cannot publish | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| deadline | instant required | none / instant | Bounded turn deadline; After creation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| cancelled_at | instant optional | NULL / instant | Accepted cancellation event; Does not erase committed customer facts | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| error_code | varchar(100) optional | NULL / None | Explicit technical failure; Safe bounded code, no raw provider secrets | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |

Constraints: unique(owner_id,request_id); one active turn per conversation or explicitly serialized revisions; fenced publication; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; input_message_id IS NULL OR owner_id IS NOT NULL; profile_revision_id IS NULL OR owner_id IS NOT NULL.
Indexes: state,lease_until; conversation_id,created_at.

## TurnEvent

Durable ordered stream event reused by reconnecting clients. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn required | none / None | Owning work item; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| sequence | bigint required | none / None | Monotonic replay cursor; Positive | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| kind | enum required | none / None | Durable event class; queued,started,clarification,progress,decision,cancelled,failed,stale | q, u, e, u, e, d, ,, s, t, a, r, t, e, d, ,, c, l, a, r, i, f, i, c, a, t, i, o, n, ,, p, r, o, g, r, e, s, s, ,, d, e, c, i, s, i, o, n, ,, c, a, n, c, e, l, l, e, d, ,, f, a, i, l, e, d, ,, s, t, a, l, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| payload | json:TurnEventV1 required | none / None | Safe UI event content/reference; Strict kind union; no raw model chain-of-thought or private-other-owner IDs | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| recorded_at | instant required | now / instant | Event commit time; Not generated on reconnect | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |

Constraints: unique(turn_id,sequence); append-only except authorized erasure; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; turn_id IS NULL OR owner_id IS NOT NULL.
Indexes: turn_id,sequence.

## Outbox

Transactional dispatch/event publication awaiting delivery. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| topic | enum required | none / None | Dispatch destination; turn,processing,invalidation,deletion,publication | t, u, r, n, ,, p, r, o, c, e, s, s, i, n, g, ,, i, n, v, a, l, i, d, a, t, i, o, n, ,, d, e, l, e, t, i, o, n, ,, p, u, b, l, i, c, a, t, i, o, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| aggregate_id | uuid required | none / None | Typed target key determined by topic; Trigger validates topic target and owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| idempotency_key | varchar(200) required | none / None | Stable delivery deduplication key; Unique within topic | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| payload | json:OutboxPayloadV1 required | none / None | Minimal dispatch reference; No copied medical values; target ID and generation only | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| state | enum required | pending / None | Delivery state; pending,leased,delivered,failed | p, e, n, d, i, n, g, ,, l, e, a, s, e, d, ,, d, e, l, i, v, e, r, e, d, ,, f, a, i, l, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| attempt_count | integer required | 0 / count | Explicit dispatch tries; Nonnegative | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| available_at | instant required | now / instant | Earliest retry time; Backoff explicit | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| lease_until | instant optional | NULL / instant | Dispatcher recovery lease; Required when leased | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| last_error_code | varchar(100) optional | NULL / None | Safe transport failure; Failed cannot silently disappear | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |

Constraints: unique(topic,idempotency_key); persist in same transaction as work; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: state,available_at; lease_until.

## ModelRoute

Exact immutable shared relay/model route configuration. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| route_key | varchar(120) required | none / None | Stable route identity; Unique revision-qualified name | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| endpoint_profile | varchar(120) required | none / None | Secret-free configured relay reference; Shared CLIProxyAPI strict /v1/responses; no credentials here | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| requested_model | varchar(160) required | none / None | Exact required model identity; No silent fallback | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| adapter_version | varchar(120) required | none / None | Strict adapter implementation identity; Immutable | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| configuration_sha256 | char(64) required | none / None | Secret-free model/adapter settings digest; Changes require new qualification | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| status | enum required | unqualified / None | User availability; unqualified,qualified,disabled | u, n, q, u, a, l, i, f, i, e, d, ,, q, u, a, l, i, f, i, e, d, ,, d, i, s, a, b, l, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |

Constraints: route_key unique; immutable route revisions.
Indexes: status,route_key.

## ModelQualification

Evidence of actual schema and capability qualification. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| route_id | fk:ModelRoute required | none / None | Qualified route revision; Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| schema_name | enum required | none / None | Actual use schema; fact_interpretation,extraction,review,answer | f, a, c, t, _, i, n, t, e, r, p, r, e, t, a, t, i, o, n, ,, e, x, t, r, a, c, t, i, o, n, ,, r, e, v, i, e, w, ,, a, n, s, w, e, r | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| schema_sha256 | char(64) required | none / None | Exact tested JSON schema; Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| observed_model | varchar(160) required | none / None | Actual returned model identity; Must exactly satisfy strict identity policy | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| capabilities | json:QualificationV1 required | none / None | Context/image/structured output checks used; Measured capability, test inputs hashes, results and limits | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| qualified_at | instant required | none / instant | Qualification time; UTC | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| result | enum required | none / None | Qualification outcome; passed,failed,expired | p, a, s, s, e, d, ,, f, a, i, l, e, d, ,, e, x, p, i, r, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| artifact_sha256 | char(64) required | none / None | Stored qualification evidence digest; Reproducible private-safe evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |

Constraints: route/schema/capability changes invalidate prior qualification.
Indexes: route_id,schema_name,qualified_at DESC.

## ModelAttempt

Every provider call, failure and usage record. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn optional | NULL / None | Adviser call context; Exactly one turn or processing job | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| processing_job_id | fk:ProcessingJob optional | NULL / None | Corpus call context; Exactly one turn or processing job | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| qualification_id | fk:ModelQualification required | none / None | Qualified exact route/schema; Must be passed/current for attempted use | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| attempt_number | integer required | none / count | Explicit call ordinal; Positive; no hidden retries | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| started_at | instant required | none / instant | Request start; UTC | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| completed_at | instant optional | NULL / instant | Provider completion; At or after start | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| observed_model | varchar(160) optional | NULL / None | Actual response identity; Mismatch => technical failure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| status | enum required | started / None | Provider call result; started,succeeded,timeout,transport_error,schema_error,identity_error,cancelled,indeterminate | s, t, a, r, t, e, d, ,, s, u, c, c, e, e, d, e, d, ,, t, i, m, e, o, u, t, ,, t, r, a, n, s, p, o, r, t, _, e, r, r, o, r, ,, s, c, h, e, m, a, _, e, r, r, o, r, ,, i, d, e, n, t, i, t, y, _, e, r, r, o, r, ,, c, a, n, c, e, l, l, e, d, ,, i, n, d, e, t, e, r, m, i, n, a, t, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| usage | json:UsageV1 required | none / None | Reported token counts and measured latency; Unknown usage explicit; never estimated as reported | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| error_code | varchar(100) optional | NULL / None | Safe operational failure category; No raw credentials or inherited environment | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| request_sha256 | char(64) required | none / None | Canonical request fingerprint; No benchmark inputs in implementation store | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| response_artifact_key | varchar(500) optional | NULL / None | Private safely retained structured response; Owner access and deletion; no hidden reasoning retention | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |

Constraints: exactly one parent; attempt state cannot swallow operational failure; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; turn_id IS NULL OR owner_id IS NOT NULL.
Indexes: turn_id,attempt_number; processing_job_id,attempt_number; status.

## ProcessingJob

Resumable original reading/extraction/review task. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentVersion required | none / None | Preserved input original; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| stage | enum required | none / None | Replaceable processing step; classify,read,ocr,extract,validate,independent_review,reconcile | c, l, a, s, s, i, f, y, ,, r, e, a, d, ,, o, c, r, ,, e, x, t, r, a, c, t, ,, v, a, l, i, d, a, t, e, ,, i, n, d, e, p, e, n, d, e, n, t, _, r, e, v, i, e, w, ,, r, e, c, o, n, c, i, l, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| adapter_version | varchar(160) required | none / None | Reader/model pipeline identity; Original inventory workflow separately identified | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| input_sha256 | char(64) required | none / None | Input bytes/parameters digest; Stable retry identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| attempt_number | integer required | 1 / count | Initial or targeted retry; 1..3 for automated extract/review cycle | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| parent_job_id | fk:ProcessingJob optional | NULL / None | Previous targeted attempt; Same document/stage; no cycle | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| state | enum required | queued / None | Recoverable stage status; queued,running,succeeded,failed,blocked,cancelled | q, u, e, u, e, d, ,, r, u, n, n, i, n, g, ,, s, u, c, c, e, e, d, e, d, ,, f, a, i, l, e, d, ,, b, l, o, c, k, e, d, ,, c, a, n, c, e, l, l, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| lease_until | instant optional | NULL / instant | Worker recovery deadline; Running requires fencing via lease token | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| lease_token | uuid optional | NULL / None | Stale-worker fencing identity; Rotate on retry/recovery | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| result_blob_id | fk:OriginalFile optional | NULL / None | Preserved processing result file pending the later processing-artifact review; Never treat a processing result as contractual original evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| issues | json:ProcessingIssuesV1 required | empty array / None | Omissions/errors and targeted retry requirements; Material unresolved issues block affected capabilities | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| error_code | varchar(100) optional | NULL / None | Explicit technical failure; Safe bounded value | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |

Constraints: unique(document_id,stage,input_sha256,attempt_number); initial plus2 targeted retries; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; result_blob_id is an operational result file and can never establish contractual source truth.
Indexes: state,lease_until; document_id,stage.

## CoverageReport

Measured original-inventory coverage, with unknown denominator explicit. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| corpus_id | fk:CorpusRevision optional | NULL / None | Assessed curated publication; May be prepublication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| insurer_id | fk:Insurer optional | NULL / None | Per-insurer or overall measurement; NULL means overall only with explicit scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| inventory_revision | varchar(160) required | none / None | Human-readable mirror of the referenced inventory revision key; Must equal inventory_revision_id.revision_key; never authoritative by itself | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-07"] |
| relevant_instances | bigint optional | NULL / None | Verified denominator; NULL unmeasured; zero requires complete scope proof | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| supported_instances | bigint required | 0 / None | Matched reviewed numerator; Nonnegative count of exact CoverageReportSupport memberships; <= known denominator; partial support never earns a credit | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-07"] |
| status | enum required | unmeasured / None | Measurement completeness; unmeasured,partial,measured | u, n, m, e, a, s, u, r, e, d, ,, p, a, r, t, i, a, l, ,, m, e, a, s, u, r, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| scope | json:InventoryScopeV1 required | none / None | Documents/pages/variants included and excluded; All required originals must be accounted for | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| report_sha256 | char(64) optional | NULL / None | Independent audit artifact fingerprint; NULL while draft; required canonical report/support/inventory digest at finalization; immutable thereafter | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-05"] |
| inventory_revision_id | fk:InventoryRevision required | none / None | Exact sealed independent inventory snapshot underlying denominator and numerator; Public; required even for unmeasured reports; same scope as report; no unbound version string | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| finalized_at | instant optional | NULL / instant | Time the exact inventory and support selection was frozen; NULL means draft; set once when hash and membership counts have been validated | None | No authentic private/database value established; proposal representation only. | ["OPS-07"] |

Constraints: measured requires known complete denominator; NULL denominator cannot yield percentage; inventory_revision_id must name a sealed revision; measured requires sealed_measured and full relevant scope; otherwise relevant_instances stays NULL; Known denominator equals sum of included membership weights in exact declared report scope; do not count candidates or structural rows; Finalized report is immutable; report_sha256 covers inventory manifest, exact scope, corpus identity and selected CoverageReportSupport identities; No numerator from a parser-derived inventory or private/evaluation rule; general aggregate evaluation status is not inventory evidence; finalized_at IS NULL iff report_sha256 IS NULL; draft reports are not acceptance evidence and cannot be used by a published CorpusRevision; Finalization transaction locks report, exact support rows, sealed inventory and corpus validation inputs; all are checked before setting finalized_at and report_sha256 atomically.
Indexes: corpus_id,insurer_id.

## ReviewRecord

Independent review and its bounded approval scope. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| artifact_id | fk:Artifact required | none / None | Exact reviewed immutable target; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewer_account_id | fk:Account optional | NULL / None | Human reviewer if applicable; Retain anonymous role after permitted deletion | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewer_identity | varchar(160) required | none / None | Independent human/agent/version role; Not implementer self-certification when independence required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| scope | text required | none / None | What was and was not checked; Precise original/code/schema boundaries | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| outcome | enum required | none / None | Review disposition; approved,rejected,changes_requested,incomplete | a, p, p, r, o, v, e, d, ,, r, e, j, e, c, t, e, d, ,, c, h, a, n, g, e, s, _, r, e, q, u, e, s, t, e, d, ,, i, n, c, o, m, p, l, e, t, e | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| findings | json:ReviewFindingsV1 required | none / None | Material findings and resolution evidence; No silent dismissal | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewed_at | instant required | none / instant | Review time; UTC | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |

Constraints: review does not imply design/cutover authorization; immutable; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: artifact_id,reviewed_at DESC.

## ConsentRecord

Specific customer authorization and revocation history. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| person_id | fk:Person optional | NULL / None | Person whose data/action consent concerns; Same owner; authority separately established | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "CUS-01"] |
| purpose | enum required | none / None | Consent scope; medical_share,abha_creation,optional_processing,representation | m, e, d, i, c, a, l, _, s, h, a, r, e, ,, a, b, h, a, _, c, r, e, a, t, i, o, n, ,, o, p, t, i, o, n, a, l, _, p, r, o, c, e, s, s, i, n, g, ,, r, e, p, r, e, s, e, n, t, a, t, i, o, n | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| recipient | varchar(250) optional | NULL / None | Specific authorized recipient; Required for medical_share | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| instance_key | uuid required | none / None | Single consent transaction identity; Per-instance sharing consent; not blanket ABHA permission | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| status | enum required | requested / None | Consent state; requested,granted,revoked,expired | r, e, q, u, e, s, t, e, d, ,, g, r, a, n, t, e, d, ,, r, e, v, o, k, e, d, ,, e, x, p, i, r, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| source_message_id | fk:Message optional | NULL / None | Exact customer authorization; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Documented authority/consent; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| valid_until | instant optional | NULL / instant | Explicit expiry; Unknown is not perpetual authorization | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| revoked_at | instant optional | NULL / instant | Withdrawal event; Pending dispatch must recheck | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |

Constraints: granted requires explicit provenance; instance_key unique within owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; person_id IS NULL OR owner_id IS NOT NULL; source_message_id IS NULL OR owner_id IS NOT NULL.
Indexes: owner_id,purpose,status.

## DeletionRequest

Durable erasure workflow and approved scope. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| scope | json:DeletionScopeV1 required | none / None | Account/conversation/person/artifact deletion targets; Owned IDs only; derived copies included | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| requested_at | instant required | none / instant | Request receipt; UTC | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| state | enum required | pending / None | Erasure progress; pending,blocked_by_hold,running,completed,failed | p, e, n, d, i, n, g, ,, b, l, o, c, k, e, d, _, b, y, _, h, o, l, d, ,, r, u, n, n, i, n, g, ,, c, o, m, p, l, e, t, e, d, ,, f, a, i, l, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| completed_at | instant optional | NULL / instant | Verified erasure completion; Requires all required stores/caches/jobs checked | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| verification | json:DeletionVerificationV1 required | none / None | Store-level erasure evidence without medical values; Private originals, derived indexes, responses, queues, backups/tombstone policy | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| error_code | varchar(100) optional | NULL / None | Explicit erasure failure; No false completed flag | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |

Constraints: completed requires verification of all scope targets; account record anonymized/purged after final receipt policy; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: owner_id,state.

## RetentionHold

Explicit approved exception to deletion; no invented retention period. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| deletion_request_id | fk:DeletionRequest required | none / None | Affected deletion; Same owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| scope | json:DeletionScopeV1 required | none / None | Precisely retained subset; Minimum necessary; access restricted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| basis | text required | none / None | Verified legal/contractual basis; Requires authoritative reviewed evidence; not model assertion | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| approved_by_id | fk:Account optional | NULL only after authorized actor erasure / None | Authorized human decision; Authorized human at creation; signed minimal review receipt retained after actor erasure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| expires_at | instant required | none / instant | Bounded hold expiry/review date; No indefinite default | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| released_at | instant optional | NULL / instant | Hold release; Triggers remaining erasure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |

Constraints: hold cannot retain unrelated targets; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; deletion_request_id IS NULL OR owner_id IS NOT NULL.
Indexes: deletion_request_id; expires_at.

## AuditEvent

Minimal authorization and lifecycle audit without copied medical values. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| actor_id | fk:Account optional | NULL / None | Authenticated actor if retained; Pseudonymize/erase according to approved retention | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| operation | varchar(100) required | none / None | Authorized action category; Registered allowlist | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| object_kind | varchar(100) required | none / None | Target resource type; Registered allowlist | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| object_id | uuid optional | NULL / None | Target identity if retention allows; No raw content | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| occurred_at | instant required | now / instant | Audit event time; Append-only until approved retention purge | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| outcome | enum required | none / None | Action result; allowed,denied,succeeded,failed | a, l, l, o, w, e, d, ,, d, e, n, i, e, d, ,, s, u, c, c, e, e, d, e, d, ,, f, a, i, l, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| metadata | json:AuditMetadataV1 required | empty object / None | Safe request/revision/error metadata; Allowlist IDs/counts/codes; no diagnoses, tokens or payload excerpts | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |

Constraints: no personal content in metadata; append-only with explicit retention purge; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: owner_id,occurred_at; operation,occurred_at.

## LegacyMapping

Lossless migration identity and unresolved semantic translations. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| source_table | varchar(150) required | none / None | Pilot model/table; Allowlisted frozen source manifest | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| source_key | varchar(250) required | none / None | Original PK/compound identity; Preserve exact UUID/string representation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| source_sha256 | char(64) required | none / None | Canonical preserved record fingerprint; Hash sensitive content only within private audit boundary | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| target_kind | varchar(150) optional | NULL / None | Approved replacement target; Registered mapping type | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| target_id | json:TargetKeyV1 optional | NULL / None | Replacement identity; Tagged UUID, integer or opaque string key; target_kind resolves native table and owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| status | enum required | preserved_unmapped / None | Translation safety; preserved_unmapped,mapped,quarantined,erased | p, r, e, s, e, r, v, e, d, _, u, n, m, a, p, p, e, d, ,, m, a, p, p, e, d, ,, q, u, a, r, a, n, t, i, n, e, d, ,, e, r, a, s, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| reason | text required | none / None | Mapping evidence or unsafe limitation; No guessed fact subject or version | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| migration_run_key | varchar(160) required | none / None | Rehearsal/cutover manifest identity; No implicit live migration | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| archive_blob_id | fk:OriginalFile required | none / None | Preserved exact legacy source-record payload; Same owner as the migrated record; hash matches the archived payload | None | No authentic private value inspected; see synthetic worked examples. | ["OPS-06"] |

Constraints: unique(migration_run_key,source_table,source_key); unmapped source payload kept in private immutable archive; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; archive_blob_id retains the exact legacy payload with matching owner;an archive is not contractual source evidence;erased source payload cannot reimport.
Indexes: migration_run_key,status; target_kind,target_id.

## AuthGroup

Existing Django privilege group identity. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native Django primary key, not UUID | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| name | varchar(150) required | none / None | Permission group name; Unique; no inferred privilege promotion | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: name unique.
Indexes: name unique.

## AuthPermission

Django model permission identity preserved semantically. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native Django primary key, not UUID | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| codename | varchar(100) required | none / None | Permission operation; Unique per content type | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| name | varchar(255) required | none / None | Human-readable permission label; Not authorization key | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| content_type_id | fk:ContentType required | none / None | Native Permission content-type relationship; Native django_content_type FK; do not flatten into fields | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "OPS-06"] |

Constraints: unique(content_type_id,codename);native AutoField primary key.
Indexes: content_type_id,codename.

## AccountGroup

Explicit account group membership. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | bigint required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native pilot user through-table BigAutoField; preserve exact PK | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| user_id | fk:Account required | none / None | Native user_id through-table FK, logically the account owner; Native Account FK; not a second physical owner_id column | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| group_id | fk:AuthGroup required | none / None | Granted privilege group; Authorized administration only | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(user_id,group_id).
Indexes: user_id,group_id.

## AccountPermission

Explicit account permission grant. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | bigint required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native pilot user through-table BigAutoField; preserve exact PK | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| user_id | fk:Account required | none / None | Native user_id through-table FK, logically the account owner; Native Account FK; not a second physical owner_id column | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| permission_id | fk:AuthPermission required | none / None | Granted model permission; Authorized administration only | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(user_id,permission_id).
Indexes: user_id,permission_id.

## GroupPermission

Permission granted to a group. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows / None | Stable row identity; Native Django primary key, not UUID | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| group_id | fk:AuthGroup required | none / None | Privilege group; Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| permission_id | fk:AuthPermission required | none / None | Granted operation; Required | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(group_id,permission_id).
Indexes: group_id,permission_id.

## AuthSession

Existing signed Django session retained with compatible settings. Access: framework_private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| session_key | varchar(40) required | none / None | Django session primary lookup key; Unique; secret; not exposed in reports | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| session_data | text required | none / None | Django signed session payload; Preserve encoding/signature configuration; never log | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-06"] |
| expire_date | instant required | none / instant | Session expiry; UTC; expired sessions excluded | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: session_key primary key; native signed Django semantics; authenticated session resolves account before private data retrieval.
Indexes: session_key unique; expire_date.

## RuleTable

Original-backed table with semantic axes, not unlabelled numeric arrays. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| rule_id | fk:Rule required | none / None | Rule containing table lookup; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| table_key | varchar(160) required | none / None | Stable lookup identifier; Unique within rule | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| axes | json:TableAxesV1 required | none / None | Named selector definitions and exact source headers; SI and deductible axes distinct even with same currency | None | Star Gold III.J uses sum_insured_inr; Silver II.E uses deductible_inr, original physical pages3-4. | ["CAL-04", "INS-04", "INS-05"] |
| result_unit | varchar(80) required | none / None | Dimension of returned cell; Registered quantity unit | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| scope | json:LimitScopeV1 required | none / None | Per-treatment/person/period extent; Original-supported | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| header_span_ids | json:UuidListV1 required | none / None | Original header and continuation-page context; Required nonempty; validated span IDs | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| state | enum required | partial / None | Table reading completeness; partial,complete,conflicted | p, a, r, t, i, a, l, ,, c, o, m, p, l, e, t, e, ,, c, o, n, f, l, i, c, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |

Constraints: unique(rule_id,table_key); complete requires every original axis/cell/footnote inventoried; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: rule_id,table_key.

## RuleTableCell

One value and its complete selector/footnote context. Access: mixed.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration / None | Stable row identity; Primary key; immutable; never reused | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this row was first recorded; UTC storage; immutable; not a source effective date | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none / None | Account whose authorization governs this row; Composite owner foreign keys on private relationships; mixed rows require public/private scope check | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| table_id | fk:RuleTable required | none / None | Semantic table; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| selectors | json:TableSelectorsV1 required | none / None | Axis values selecting this cell; Exactly all declared axes; quantity/code types match | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| selector_sha256 | char(64) required | none / None | Canonical selector identity; Unique within table | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| value | json:ExpressionV1 required | none / None | Finite amount, SI reference or other supported expression; Up to SI is bounded by SI, not unlimited | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| cell_span_id | fk:EvidenceSpan required | none / None | Original cell geometry/transcription; Compatible owner | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| footnote_span_ids | json:UuidListV1 required | empty array / None | All applicable footnotes; Empty means verified none only if table review complete | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| review_state | enum required | unreviewed / None | Independent cell review; unreviewed,verified,conflicted | u, n, r, e, v, i, e, w, e, d, ,, v, e, r, i, f, i, e, d, ,, c, o, n, f, l, i, c, t, e, d | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |

Constraints: unique(table_id,selector_sha256); overlapping selector ranges cannot publish unresolved; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: table_id,selector_sha256.

## ContentType

Native Django model content-type identity. Access: framework_private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | native sequence / None | Native AutoField primary key; Preserve exact PK | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| app_label | varchar(100) required | none / None | Application label; Part of natural key | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| model | varchar(100) required | none / None | Model name; Part of natural key | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |

Constraints: primary key(id);unique(app_label,model).
Indexes: app_label,model.

## AdminLogEntry

Preserved Django administration audit, with privacy review of free text. Access: framework_private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | integer required | native sequence / None | Native LogEntry AutoField PK; Preserve exact PK | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| action_time | instant required | none / None | Native action timestamp; Preserve UTC instant | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| user_id | fk:Account required | none / None | Acting administrator; Native actor FK; privileged access | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| content_type_id | fk:ContentType optional | NULL / None | Native acted-on model; Nullable per framework | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| object_id | text optional | NULL / None | Native target string key; May represent UUID/integer; not arbitrary FK | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| object_repr | varchar(200) required | empty string / None | Native target display text; Sensitive content review/redaction on erasure | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| action_flag | smallint required | none / None | Native add/change/delete flag; 1,2,3 | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| change_message | text required | empty string / None | Native admin change detail; Do not infer insurer factual acceptance; erase sensitive copies | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |

Constraints: native Django semantics;privileged access;explicit erasure mapping.
Indexes: action_time;user_id.

## ContentCopy

Inventory of where a private assertion payload was copied or transformed. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs / None | Stable row identity; Primary key; immutable | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "DEC-01"] |
| created_at | instant required | now / None | Row recording time; UTC; immutable | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "DEC-01"] |
| owner_id | fk:Account required | none / None | Account authorization boundary; Owner-bound relationships; no cross-owner targets | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| source_artifact_id | fk:Artifact required | none / None | Original private assertion/content lineage; Same owner | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| destination_artifact_id | fk:Artifact required | none / None | Stored derived artifact containing the content; Same owner | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| storage_kind | enum required | none / None | Physical copy class; postgres,original_storage,search_index,cache,queue,model_response,export,backup | p, o, s, t, g, r, e, s, ,, o, r, i, g, i, n, a, l, _, s, t, o, r, a, g, e, ,, s, e, a, r, c, h, _, i, n, d, e, x, ,, c, a, c, h, e, ,, q, u, e, u, e, ,, m, o, d, e, l, _, r, e, s, p, o, n, s, e, ,, e, x, p, o, r, t, ,, b, a, c, k, u, p | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| locator | varchar(500) required | none / None | Opaque store/location or JSON-path identity; No copied medical value; authenticated resolver | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| state | enum required | present / None | Copy erasure state; present,redacted,erased,held | p, r, e, s, e, n, t, ,, r, e, d, a, c, t, e, d, ,, e, r, a, s, e, d, ,, h, e, l, d | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| generation | bigint required | 0 / None | Erasure/rebuild fencing generation; Nonnegative; stale workers cannot restore older generation | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |

Constraints: unique(source_artifact_id,destination_artifact_id,storage_kind,locator);material copy must register before publication/dispatch; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes.
Indexes: source_artifact_id,state;destination_artifact_id.

## ExpenseAllocation

Original-backed allocation of an expense across package/time/scope boundaries. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs / None | Stable row identity; Primary key; immutable | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02", "CAL-03"] |
| created_at | instant required | now / None | Row recording time; UTC; immutable | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02", "CAL-03"] |
| owner_id | fk:Account required | none / None | Account authorization boundary; Owner-bound relationships; no cross-owner targets | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| expense_id | fk:ExpenseLine required | none / None | Original bill line; Same owner | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| package_parent_id | fk:ExpenseLine optional | NULL / None | Containing package line if present; Same episode; no cycles | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| kind | enum required | none / None | Reason for allocation; included_in_package,separate_payable,excluded_component,time_split,scope_split | i, n, c, l, u, d, e, d, _, i, n, _, p, a, c, k, a, g, e, ,, s, e, p, a, r, a, t, e, _, p, a, y, a, b, l, e, ,, e, x, c, l, u, d, e, d, _, c, o, m, p, o, n, e, n, t, ,, t, i, m, e, _, s, p, l, i, t, ,, s, c, o, p, e, _, s, p, l, i, t | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| amount | json:QuantityV1 required | none / None | Allocated money or unresolved amount; Finite portions reconcile to expense; unknown blocks precise allocation | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-01"] |
| service_extent | json:TemporalExtentV1 required | none / None | Portion service time; Inside source service extent when known | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| boundary_fact_id | fk:CustomerFact optional | NULL / None | Customer fact supporting the allocation boundary when customer-supplied; Same person/owner; exact event provenance | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| effects | json:AllocationEffectsV1 required | none / None | Billing/admissibility/cap accounting membership; Separate booleans/unknown per role; no double allocation | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Original allocation authority; Required for verified allocation; otherwise explicit stipulation | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| status | enum required | none / None | Allocation certainty; stipulated,verified,unresolved | s, t, i, p, u, l, a, t, e, d, ,, v, e, r, i, f, i, e, d, ,, u, n, r, e, s, o, l, v, e, d | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |

Constraints: no package cycles;sum of nonoverlapping finite allocations <= original amount; a portion may have multiple accounting roles but is counted once per role/pool;unknown residual is not zero; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; expense_id IS NULL OR owner_id IS NOT NULL; package_parent_id IS NULL OR owner_id IS NOT NULL; boundary_fact_id IS NULL OR owner_id IS NOT NULL.
Indexes: expense_id;package_parent_id.

## Clinician

Original-backed clinician identity scoped independently of facility names. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs / None | Stable row identity; Primary key; immutable | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| created_at | instant required | now / None | Row recording time; UTC; immutable | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| name | varchar(250) required | none / None | Printed practitioner name; Not unique; no identity from name alone | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| registration_identifiers | json:IdentifiersV1 required | empty array / None | Medical registry identifiers and provenance; Issuer-scoped identity | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| speciality | varchar(200) optional | NULL / None | Reported specialty; Original-backed or unknown | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |

Constraints: no name-only automatic merge.
Indexes: name.

## ClaimEvent

A claim-process event, or mandatory hospitalization notice before any claim exists, with exact actor, recipient and evidence time. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CUS-02", "CAL-02", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs every private value; Required immutable owner; no NULL-to-public conversion | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim optional | NULL / None | Exact claim involved; absent only for a pre-claim hospitalization notice; Same owner; when present its episode and contract revision match this event | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| episode_id | fk:TreatmentEpisode required | none / None | Treatment episode that the communication or payment concerns; Same owner and exact claim lineage | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| contract_revision_id | fk:ContractRevision required | none / None | Personal contract revision to which this event was addressed; Same owner; matches claim when claim_id is present | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| event_key | uuid required | none / None | Stable identity of one real-world event across corrections; Same owner, episode, contract and event lineage for every revision | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 / count | Append-only revision number for that event; Positive; revision 1 has no supersedes_id; later revision is predecessor plus one | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| kind | enum required | none / None | Actual procedural event; events do not imply contractual admissibility; hospitalization_notice,claim_submitted,claim_received,document_requested,document_received,documentation_complete,documentation_incomplete,decision_issued,payment_made,payment_received,claim_due_confirmed,communication_received | h, o, s, p, i, t, a, l, i, z, a, t, i, o, n, _, n, o, t, i, c, e, ,, c, l, a, i, m, _, s, u, b, m, i, t, t, e, d, ,, c, l, a, i, m, _, r, e, c, e, i, v, e, d, ,, d, o, c, u, m, e, n, t, _, r, e, q, u, e, s, t, e, d, ,, d, o, c, u, m, e, n, t, _, r, e, c, e, i, v, e, d, ,, d, o, c, u, m, e, n, t, a, t, i, o, n, _, c, o, m, p, l, e, t, e, ,, d, o, c, u, m, e, n, t, a, t, i, o, n, _, i, n, c, o, m, p, l, e, t, e, ,, d, e, c, i, s, i, o, n, _, i, s, s, u, e, d, ,, p, a, y, m, e, n, t, _, m, a, d, e, ,, p, a, y, m, e, n, t, _, r, e, c, e, i, v, e, d, ,, c, l, a, i, m, _, d, u, e, _, c, o, n, f, i, r, m, e, d, ,, c, o, m, m, u, n, i, c, a, t, i, o, n, _, r, e, c, e, i, v, e, d | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| occurred_at | json:TemporalExtentV1 required | none / temporal extent | Actual event time, date or explicitly uncertain interval; Preserve precision and timezone; receipt by insurer/TPA differs from upload, dispatch or recording time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| sender | json:ClaimPartyV1 required | none / None | Party sending or performing the event; Validate exact party identity and owner; role alone does not establish delegated authority | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| recipient | json:ClaimPartyV1 required | none / None | Party receiving the communication or payment; An insurer receipt is not inferred from customer upload or TPA receipt without governing authority | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| certainty | enum required | reported / None | Evidence status of this event revision; reported,verified,disputed,retracted | r, e, p, o, r, t, e, d, ,, v, e, r, i, f, i, e, d, ,, d, i, s, p, u, t, e, d, ,, r, e, t, r, a, c, t, e, d | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Exact event evidence, distinct from the rule describing a deadline; Compatible owner; event verification requires actual event proof, not merely a generic policy clause | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_message_id | fk:Message optional | NULL / None | Customer report or correction of this event; Same owner; may establish reported status but is not self-verifying insurer receipt | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| related_event_id | fk:ClaimEvent optional | NULL / None | Specific request, dispatch or other event connected to this one; Same owner and claim/episode/contract; event relationships acyclic; does not imply receipt or completion | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| documentation | json:ClaimDocumentationV1 optional | NULL / None | Explicit completeness assessment and exact requirement/receipt revisions; Required for documentation_complete/incomplete; referenced records belong to this claim; empty arrays are not proof no documents are needed | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimEvent optional | NULL / None | Previous version corrected by this event record; Same owner/event_key/claim/episode/contract/kind; acyclic; at most one successor | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |

Constraints: unique(owner_id,event_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; At least one source_span_id or source_message_id is required; claim_id required except hospitalization_notice; pre-claim notices bind episode and contract without manufacturing a submitted Claim; All cross-record claim/episode/contract identity checks use deferred constraint triggers and target key-share locks; documentation_complete requires documentation.status complete; documentation_incomplete requires incomplete or disputed; other event kinds cannot carry a completeness conclusion; Verified documentation completeness requires the exact active necessary requirements, matched receipts, original/accepted exception rules and recipient authority; ambiguity remains disputed; it is not inferred from number of uploaded files; Corrections invalidate dependent calculations/decisions; related pre-claim notice can later be linked by a new claim-bound communication without rewriting the historical notice; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules.
Indexes: claim_id,kind,created_at; episode_id,contract_revision_id,kind; owner_id,event_key,revision.

## ClaimDocumentRequirement

An immutable claim-specific version of a required or disputed document and the authority for its necessity or accepted form. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "INS-04", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs every private value; Required immutable owner; no NULL-to-public conversion | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none / None | Claim whose documentary condition is assessed; Same owner and exact claim lineage | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| requirement_key | varchar(160) required | none / None | Stable identity of one document requirement within the claim; Never use a filename alone; same key through corrections | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 / count | Requirement revision number; Positive; supersession increments by one | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| document_kind | varchar(160) required | none / None | Registered required evidence category; Examples from originals include discharge summary, bills and treating records; category is not proof supplied | None | {"value": "original bills", "authentic": true, "source": "../registers/independent-original-inventory-star-ssf-r6.json", "locator": "V.17 original claim-document requirement"} | ["INS-09"] |
| necessity | enum required | unknown / None | Adjudicated necessity; requests alone do not establish every item is contractually necessary; required,conditional,not_required,disputed,unknown | r, e, q, u, i, r, e, d, ,, c, o, n, d, i, t, i, o, n, a, l, ,, n, o, t, _, r, e, q, u, i, r, e, d, ,, d, i, s, p, u, t, e, d, ,, u, n, k, n, o, w, n | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| condition | json:PredicateV1 optional | NULL / None | Exact conditions under which the requirement applies; Required when necessity is conditional; unknown inputs keep necessity unresolved | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| accepted_form | enum required | unspecified / None | Required or accepted documentary form and certification scope; original,certified_copy,ordinary_copy,electronic,unspecified | o, r, i, g, i, n, a, l, ,, c, e, r, t, i, f, i, e, d, _, c, o, p, y, ,, o, r, d, i, n, a, r, y, _, c, o, p, y, ,, e, l, e, c, t, r, o, n, i, c, ,, u, n, s, p, e, c, i, f, i, e, d | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| request_event_id | fk:ClaimEvent optional | NULL / None | Specific insurer or TPA request event, if any; Same claim; kind document_requested; authority/recipient checked independently | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| rule_id | fk:Rule optional | NULL / None | Applicable original-backed document requirement or exception; Public or same-owner rule; matches selected contract scope; full dependencies required | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| authority_span_id | fk:EvidenceSpan optional | NULL / None | Exact clause, certification requirement or accepted written exception; Compatible owner; required with verified necessity/form unless rule evidence supplies it | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| reason | text required | none / None | Why this requirement is necessary, conditional or disputed; Nonempty; preserve certification exceptions and unresolved request authority | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimDocumentRequirement optional | NULL / None | Prior requirement version; Same owner, claim and requirement_key; acyclic single-successor chain | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| certainty | enum required | reported / None | Evidence strength of the assessed necessity and accepted form; reported,verified,disputed | r, e, p, o, r, t, e, d, ,, v, e, r, i, f, i, e, d, ,, d, i, s, p, u, t, e, d | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(claim_id,requirement_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; At least one request_event_id, rule_id or authority_span_id is required; conditional necessity requires condition; other necessity states cannot imply unconditional document completeness; Every revision is immutable; changing necessity/form does not erase a past request or receipt; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Verified necessity/form requires applicable original or accepted exception authority, not merely the existence of a document request. Reported or disputed necessity blocks verified completeness until resolved.
Indexes: claim_id,necessity; claim_id,requirement_key,revision.

## ClaimDocumentReceipt

A specific delivery of a document to a named claim-processing recipient; repeats and corrected receipt times remain distinct. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "INS-04", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs every private value; Required immutable owner; no NULL-to-public conversion | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none / None | Claim receiving this document; Same owner and exact claim lineage | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| receipt_event_id | fk:ClaimEvent required | none / None | Exact receipt event and recipient; Same claim; kind document_received; occurred_at is receipt time, not local upload time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| requirement_id | fk:ClaimDocumentRequirement optional | NULL / None | Exact requirement version this delivery may satisfy; Same claim; NULL means unclassified or unsolicited document, not no requirement | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| document_id | fk:DocumentVersion optional | NULL / None | Exact delivered original bytes if acquired; Same owner for private claim documents; NULL allowed when only reported delivery is known | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| description | text required | none / None | Reported document identity when bytes or filename alone are insufficient; Do not invent missing original bytes or a final document identity | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| delivered_form | enum required | unknown / None | Actual delivered form; compared with accepted form; original,certified_copy,ordinary_copy,electronic,unknown | o, r, i, g, i, n, a, l, ,, c, e, r, t, i, f, i, e, d, _, c, o, p, y, ,, o, r, d, i, n, a, r, y, _, c, o, p, y, ,, e, l, e, c, t, r, o, n, i, c, ,, u, n, k, n, o, w, n | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| assessment | enum required | unassessed / None | Whether this delivery satisfies the named requirement; matched,insufficient,disputed,unassessed | m, a, t, c, h, e, d, ,, i, n, s, u, f, f, i, c, i, e, n, t, ,, d, i, s, p, u, t, e, d, ,, u, n, a, s, s, e, s, s, e, d | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| assessment_span_id | fk:EvidenceSpan optional | NULL / None | Proof of certification, acceptance or deficiency; Compatible owner; required for verified acceptance/deficiency where it is not in receipt-event evidence | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimDocumentReceipt optional | NULL / None | Prior classification or identity correction of the same delivery; Same owner/claim and receipt event lineage; preserves earlier evidence; at most one successor | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 / count | Version of this logical delivery or payment assertion; Positive; first version has no supersedes; successor increments by one | None | No authentic private/database value established; proposal representation only. | ["INS-09"] |
| receipt_key | uuid required | none / None | Stable identity of one delivered item across classification or timing corrections; Distinct items in one batch have distinct keys; retries reuse the same owner/key/revision | None | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(owner_id,receipt_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; Matched assessment requires a named applicable requirement and evidence of correct form/content; a reported delivery with no actual content remains unassessed unless authenticated acceptance explicitly establishes sufficiency; Receipt time lives only on its referenced immutable ClaimEvent revision; retransmission is a distinct event, not an overwrite; No completion or last-necessary-document date is inferred until exact requirement and receipt revisions are assessed together; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Supersession keeps owner/claim/receipt_key and receipt event logical lineage; changing classification creates a new version even when document_id and requirement_id remain unchanged; Multiple unclassified documents in one batch may have distinct receipt_keys even when document_id and requirement_id are both NULL.
Indexes: claim_id,requirement_id; receipt_event_id; document_id.

## ClaimPayment

An evidenced claim disbursement or reversal, retaining actual payment timing and separate indemnity, interest and other components. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CAL-01", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Account whose authorization governs every private value; Required immutable owner; no NULL-to-public conversion | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none / None | Claim whose liability this payment addresses; Same owner and exact claim lineage | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payment_key | varchar(200) required | none / None | Stable owner-scoped identity for this payment transaction; Identifies one logical payment per owner and is shared by its correction revisions; unique(owner_id,payment_key,revision). Retries reuse the same version identity; separate partial payments have distinct logical keys. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payment_event_id | fk:ClaimEvent required | none / None | Evidenced payment execution or receipt event; Same claim; payment_made or payment_received; event source establishes actual time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| kind | enum required | disbursement / None | Payment or explicitly evidenced reversal; disbursement,reversal | d, i, s, b, u, r, s, e, m, e, n, t, ,, r, e, v, e, r, s, a, l | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payee | json:ClaimPartyV1 required | none / None | Actual recipient, distinct from proposer/insured by default; Must match payment event recipient when known; a nominee/representative requires accepted authority | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| total | json:QuantityV1 required | none / money | Total transferred amount; Known finite nonnegative money; currency required; unknown transfer must remain an event until established | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| indemnity | json:QuantityV1 required | none / money | Principal claim-payment component; Finite nonnegative same-currency money or explicit unknown; not automatically total | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| interest | json:QuantityV1 required | none / money | Separate interest component; Finite nonnegative same-currency money or explicit unknown; zero only if explicitly established | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| other | json:QuantityV1 required | none / money | Other separately classified payment component; Finite nonnegative same-currency money or explicit unknown; no unsupported deduction inference | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| transaction_reference | text optional | NULL / None | Original transaction reference if available; Owner-scoped encrypted field; never log raw value | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_span_id | fk:EvidenceSpan required | none / None | Actual payment amount/component evidence; Compatible owner; payment event and span must establish this transaction | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| reverses_id | fk:ClaimPayment optional | NULL / None | Original payment transaction partially or fully reversed; Same owner, exact claim and currency; noncyclic; kind reversal only. Payee is the actual reversal recipient, not necessarily the original payee. Linked original and reversal events must evidence the reversed transaction and sender/recipient roles, including accepted delegated authority. Net current logical reversal versions cannot exceed the original current amount. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 / count | Version of this logical delivery or payment assertion; Positive; first version has no supersedes; successor increments by one | None | No authentic private/database value established; proposal representation only. | ["INS-09"] |
| supersedes_id | fk:ClaimPayment optional | NULL / None | Corrected assertion about the same actual payment, distinct from a physical reversal; Same owner/claim/payment_key; one successor; revision increments; preserve exact prior event/amount provenance | None | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(owner_id,payment_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; Known components must sum exactly to total; partial unknown components remain unknown rather than balancing inventions; kind reversal iff reverses_id is present; source payment and accumulated reversals are locked before validation; Each partial payment has distinct event, recipient and transaction identity; current claim status is not payment evidence; Indemnity alone can feed UsageEntry cover-payment postings; interest/other are not insured-sum consumption or threshold accumulation; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Correcting a recorded amount/time/payee appends a same-key version and invalidates dependent ledger/decision inputs; it does not invent a bank reversal. kind reversal represents a separate evidenced financial transaction; Select one current version per payment_key for current accounting; historical reports retain exact prior versions. Revalidation/reposting uses bookkeeping reversal entries under the same logical-payment lock, preventing old and corrected versions being counted twice; Every ClaimPayment insertion, correction or authorized erasure locks the exact Claim parent FOR UPDATE before reading or changing its payment set. Use READ COMMITTED with a fresh validation statement after acquiring the lock; validate current logical versions and net reversal balances together. A corrected original below established reversals cannot publish as consistent accounting until the discrepancy is explicitly resolved. Historical versions remain intact..
Indexes: claim_id,payment_event_id; reverses_id; owner_id,payment_key.

## InventoryRevision

A sealed, reproducible original-reading inventory snapshot with its counting protocol, scope and unresolved denominator status. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-03", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| revision_key | varchar(160) required | none / None | Unique externally reportable inventory revision identifier; Unique; immutable after seal | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| previous_id | fk:InventoryRevision optional | NULL / None | Previous sealed inventory revision; Public; same scope lineage or explicitly documented scope expansion; acyclic ancestry | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| scope | json:InventoryScopeV1 required | none / None | Exact originals, insurer scope and unread/connected regions; All referenced originals public; scope closure is independent of parser output | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| counting_protocol | json:InventoryCountingProtocolV1 required | none / None | Approved segmentation, table-cell and hierarchy counting policy; Immutable protocol at seal; candidates are not an approved denominator | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| source_manifest_sha256 | char(64) required | none / None | Digest of source original identities and independent reading inputs; SHA256 of canonical source_manifest JSON; each source original hash must equal the referenced public document bytes | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| reader_identity | varchar(150) required | none / None | Independent original assessor identity; Not the extraction process being scored | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| state | enum required | draft / None | Frozen inventory state and whether a denominator is established; draft,sealed_unmeasured,sealed_measured | d, r, a, f, t, ,, s, e, a, l, e, d, _, u, n, m, e, a, s, u, r, e, d, ,, s, e, a, l, e, d, _, m, e, a, s, u, r, e, d | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| sealed_at | instant optional | NULL / instant | Time immutable membership and lineage were sealed; Required for sealed states; NULL only in draft; not source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| manifest_sha256 | char(64) optional | NULL / None | Digest of exact members, lineage and counting protocol; Required before seal; canonical referenced identities/content, not only aggregate count | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| source_manifest | json:InventorySourceManifestV1 required | none / None | Retrievable exact original/candidate membership manifest, not an opaque hash; Every document and instance key resolves to an immutable original reading; schema forbids benchmark/customer answers; source_manifest_sha256 hashes its canonical JSON | None | No authentic private/database value established; proposal representation only. | ["INS-04", "OPS-07"] |

Constraints: unique(revision_key); Sealed revisions, memberships and lineage are immutable; any segmentation/count/scope correction creates a descendant revision; sealed_measured requires complete_original_closure, approved counting protocol, resolved hierarchy/segmentation, no candidate/disputed membership and complete required original scope; otherwise seal as unmeasured; The seal transaction locks the revision and all member/lineage inputs; target updates or late inserts into a sealed revision are rejected; No benchmark questions or expected answers are stored in inventory revisions; Every source-manifest occurrence must have an explicit current membership or an adjudicated split/merge lineage whose source is retained; omitting a difficult candidate cannot reduce the denominator; Additional independent_atomic_segment items require original-backed lineage to manifested occurrences. Sealed_measured requires complete source/page coverage, not merely resolution of the rows someone inserted; Empty source manifests or missing occurrence coverage may be retained in draft/sealed_unmeasured. A measured zero requires explicit original-backed complete-scope proof; an empty input list is never such proof..
Indexes: previous_id; state,sealed_at.

## InventoryMembership

An original source occurrence or independently adjudicated atomic segment as counted, excluded or unresolved in one exact inventory revision. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| inventory_revision_id | fk:InventoryRevision required | none / None | Exact inventory snapshot containing this assessment; Public; draft insertion only | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| item_id | fk:RuleInventoryItem required | none / None | Stable original occurrence or atomic segment being adjudicated; Public; original document belongs to revision scope | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| disposition | enum required | candidate / None | Explicit membership/segmentation outcome; candidate,included,excluded,structural_only,superseded,disputed | c, a, n, d, i, d, a, t, e, ,, i, n, c, l, u, d, e, d, ,, e, x, c, l, u, d, e, d, ,, s, t, r, u, c, t, u, r, a, l, _, o, n, l, y, ,, s, u, p, e, r, s, e, d, e, d, ,, d, i, s, p, u, t, e, d | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| count_weight | integer optional | NULL / count | Denominator contribution in this exact revision; NULL for candidate/disputed; 1 for included atomic instance; 0 for excluded/structural_only/superseded; never default an unresolved candidate to one | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| scope | json:InventoryScopeV1 required | none / None | Variant, source and rule-scope inclusion basis; Subset of revision scope; scope changes require new membership in a new revision | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| source_span_ids | json:UuidListV1 required | none / None | All independently read passages including continuations; Nonempty unique public EvidenceSpan IDs; primary item span included; connected originals explicitly declared | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| reason | text required | none / None | Segmentation, hierarchy or exclusion adjudication; Nonempty; unresolved clinical qualifier/duplicate interpretation remains explicit | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| adjudicator_identity | varchar(150) required | none / None | Independent person/process making this segmentation assessment; Not downstream parser or model self-review identity | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| previous_membership_id | fk:InventoryMembership optional | NULL / None | Same item as assessed in an earlier sealed revision; Same item; earlier revision in ancestor chain; split/merge uses InventoryLineage instead | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| content_sha256 | char(64) required | none / None | Canonical immutable membership content digest; Verified when sealing revision | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |

Constraints: unique(inventory_revision_id,item_id); Included instances have count_weight 1; candidate/disputed NULL; all noncounted dispositions zero; Sealed membership cannot be changed/deleted; predecessor remains part of its original historical manifest; A printed qualifier may remain structural_only or disputed; it must not be normalized into an independently covered procedure without original-backed adjudication.
Indexes: inventory_revision_id,disposition; item_id,inventory_revision_id.

## InventoryLineage

Explicit independent adjudication of source splitting, merging, qualifiers and repeated printed occurrences, without erasing original identities. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| inventory_revision_id | fk:InventoryRevision required | none / None | Revision in which this relation was adjudicated; Public; all destination members in this revision | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| adjudication_key | varchar(160) required | none / None | Groups all edges of one split, merge or hierarchy decision; Stable within revision; every group has one relation kind and consistent reason | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| from_membership_id | fk:InventoryMembership required | none / None | Prior or parent source membership; Same revision or sealed ancestor; public; no future revision | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| to_membership_id | fk:InventoryMembership required | none / None | Resulting segment, qualifier or repeated occurrence; In this revision; public; never same member as source | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| kind | enum required | none / None | Adjudicated relation; source occurrences remain separate identities; split,merge,qualifies,semantic_duplicate,restates | s, p, l, i, t, ,, m, e, r, g, e, ,, q, u, a, l, i, f, i, e, s, ,, s, e, m, a, n, t, i, c, _, d, u, p, l, i, c, a, t, e, ,, r, e, s, t, a, t, e, s | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| source_span_ids | json:UuidListV1 required | none / None | Exact source evidence for the adjudication; Nonempty unique public spans; include source and destination passages | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| reason | text required | none / None | Why segmentation or semantic grouping is justified; Do not deduplicate clinical spellings or separately printed numbers without independent justification | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| adjudicator_identity | varchar(150) required | none / None | Independent original-reading adjudicator; Immutable; differs from downstream candidate extractor | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |

Constraints: unique(inventory_revision_id,from_membership_id,to_membership_id,kind); No cycles for split/merge/qualifies/restates; semantic_duplicate edges have a unique unordered endpoint pair within the revision; they do not themselves collapse source occurrence counts; Split groups require one source and at least two destinations; merge groups require at least two sources and one destination; cross-document merge cannot silently remove independently counted original occurrences; Source parent remains candidate/structural/superseded as appropriate; a segmentation relation alone does not decide count_weight; No change to any edge after revision seal.
Indexes: inventory_revision_id,adjudication_key; from_membership_id; to_membership_id.

## RuleInventorySupport

An immutable independent assessment that a specific curated rule and its dependency closure support one exact counted original member. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-03", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| membership_id | fk:InventoryMembership required | none / None | Exact inventory member being evaluated; Public; belongs to a sealed revision | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| rule_id | fk:Rule required | none / None | Exact original-backed rule revision and mandatory dependency closure; Public rule only; do not use private customer/evaluation answers as original coverage | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| outcome | enum required | unresolved / None | Independent support assessment; supported,partial,unsupported,unresolved | s, u, p, p, o, r, t, e, d, ,, p, a, r, t, i, a, l, ,, u, n, s, u, p, p, o, r, t, e, d, ,, u, n, r, e, s, o, l, v, e, d | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| support_span_ids | json:UuidListV1 required | none / None | Original support passages checked by reviewer; Nonempty unique public spans; resolve original member and connected restrictions | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-04", "OPS-07"] |
| reviewer_identity | varchar(150) required | none / None | Independent reviewer of this support claim; Not the extraction/model candidate author self-certification | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| reviewed_at | instant required | none / instant | When this exact assessment was made; UTC immutable; not insurer effective date | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| reason | text required | none / None | Support boundaries, missing predicates and conflicts; Supported means all material member predicates and mandatory dependencies are covered; partial records cannot be added together to invent complete support | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| supersedes_id | fk:RuleInventorySupport optional | NULL / None | Prior support assessment corrected by this assessment; Same membership; exact replacement rule may differ; preserve old reports; at most one successor and no cycle | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| content_sha256 | char(64) required | none / None | Canonical immutable review digest; Checked when linking a coverage report | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |

Constraints: Immutable review rows; corrections append a successor; unique(supersedes_id) WHERE supersedes_id IS NOT NULL; One rule can support many original occurrences through separate reviews; each included member receives at most one numerator credit in a report; Public-only membership/rule/span checks enforce independence and owner scope.
Indexes: membership_id,outcome; rule_id; reviewed_at.

## CoverageReportSupport

The frozen member-to-support selection used to reproduce the numerator of one historical coverage report. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; immutable; never reused | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-03", "OPS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion / instant | When this record was first stored; UTC immutable recording time; never substitute for event or source effective time | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| coverage_report_id | fk:CoverageReport required | none / None | Historical measured or partial coverage report; Public; immutable after report finalization | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| membership_id | fk:InventoryMembership required | none / None | Single original member counted in this report; Must belong to report.inventory_revision_id and disposition included | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |
| support_id | fk:RuleInventorySupport required | none / None | Exact immutable supported assessment selected for this member; Same membership; outcome supported; its rule and full dependencies present and validated in the report corpus | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-07"] |

Constraints: unique(coverage_report_id,membership_id); CoverageReport.supported_instances equals distinct linked memberships, never number of matching rules or table hits; No insertion/update/deletion after coverage_report.finalized_at is set; finalized report hash covers sorted support rows and exact sealed inventory manifest; Unsupported/partial/unresolved reviews cannot enter numerator; missing corpus validation leaves report unmeasured or partial.
Indexes: support_id; membership_id.

## TermsComponent

An original-backed component slot in a specific public combi edition; component legal identity and benefits remain separate. Access: public.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; never reused | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp / instant | Assertion insertion time, separate from contractual effective time; UTC; immutable | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| wrapper_terms_id | fk:PolicyVersion required | none / None | Exact public combi edition defining this component slot; Required typed identity; no inferred association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| slot_code | varchar(80) required | none / None | Stable slot within this wrapper edition; Nonempty lowercase identifier; unique within wrapper terms | None | health or life; design-assigned codes for original COMBI13-A, not insurer-issued codes | ["INS-10"] |
| component_product_id | fk:Product required | none / None | Separately issued component product and issuer; Required typed identity; no inferred association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| component_terms_id | fk:PolicyVersion optional | NULL / None | Independently established component edition, if available; When present, terms.product_id equals component_product_id; wrapper naming a UIN alone does not establish complete component wording | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| asserted_component_uin | varchar(100) optional | NULL / None | Identifier explicitly asserted by the wrapper source; NULL means not stated, not no UIN; compare independently with resolved component edition; mismatch blocks verification | None | Health Premier ZUKHLIP25054V052425; Kotak Term Plan107N005V06, source26c72de9… COMBI13-A | ["INS-10"] |
| role | enum required | unresolved / None | Component role; does not expand the selected medical-insurer roster; medical,life,other,unresolved | m, e, d, i, c, a, l, ,, l, i, f, e, ,, o, t, h, e, r, ,, u, n, r, e, s, o, l, v, e, d | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_kind | enum required | unresolved / None | Whether this wrapper requires or permits the component; required,optional,conditional,unresolved | r, e, q, u, i, r, e, d, ,, o, p, t, i, o, n, a, l, ,, c, o, n, d, i, t, i, o, n, a, l, ,, u, n, r, e, s, o, l, v, e, d | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_rule_id | fk:Rule optional | NULL / None | Connected selection condition for conditional membership; Rule.owner_id NULL and rule.terms_id equals wrapper_terms_id; required when selection_kind is conditional | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan required | none / None | Original supporting wrapper/component association; Required typed identity; no inferred association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| status | enum required | unresolved / None | Association review state; reviewed identity does not mean complete component terms; unresolved,reviewed,conflict | u, n, r, e, s, o, l, v, e, d, ,, r, e, v, i, e, w, e, d, ,, c, o, n, f, l, i, c, t | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| supersedes_id | fk:TermsComponent optional | NULL / None | Prior association from an earlier wrapper edition; Acyclic, same wrapper product and slot_code; a published wrapper edition is immutable | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(wrapper_terms_id,slot_code); component_terms_id, when present, belongs to component_product_id; asserted UIN disagreement sets conflict and blocks affected publication; conditional membership requires a public same-wrapper selection rule; All source spans and linked rules are public; do not manufacture a separately issued component wording from a wrapper title; Published component edges are immutable; changing an edge creates a new wrapper terms edition and invalidates dependent artifacts; No composition cycle, including cycles through resolved component terms; closure is checked before publication.
Indexes: wrapper_terms_id,slot_code; component_product_id,component_terms_id; supersedes_id.

## ContractBundle

Stable owned identity for a package of component policies, without inventing a third policy contract or sole issuer. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; never reused | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp / instant | Assertion insertion time, separate from contractual effective time; UTC; immutable | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Owner governing all private bundle records; Immutable owner; never nulled to publish private records | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| label | varchar(250) required | none / None | Owner-facing package label; Nonempty; not unique and not proof of legal identity | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| external_reference | varchar(200) optional | NULL / None | Issuer package reference if actually supplied; Encrypted; NULL when unavailable; do not manufacture a wrapper policy number | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| current_revision_id | fk:ContractBundleRevision optional | NULL / None | Current accepted bundle interpretation; Deferred check: referenced revision.bundle_id equals this bundle id; CAS under bundle row lock and expected revision; never points across bundles | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(id,owner_id); immutable owner; Current revision pointer targets a revision of this same bundle and owner; updates are fenced by expected revision; No global unique external reference; private erasure includes revisions, membership, subject facts, artifacts and all copies; current_revision_id can target only a sealed revision with matching owner and bundle_id; head CAS checks expected prior revision..
Indexes: owner_id,created_at; owner_id,current_revision_id.

## ContractBundleRevision

Immutable owner-scoped interpretation of a package version, component membership and status, retained when customer facts or sources change. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; never reused | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp / instant | Assertion insertion time, separate from contractual effective time; UTC; immutable | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Owner governing all private bundle records; Immutable owner; never nulled to publish private records | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| bundle_id | fk:ContractBundle required | none / None | Stable package being interpreted; Required typed identity; no inferred association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| revision | bigint required | none / None | Monotonic bundle revision; Positive; unique(bundle_id,revision); previous revision is current at creation | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| wrapper_configuration_id | fk:ProductVariant optional | NULL / None | Selected public wrapper version/options if resolved; ProductVariant.terms_id is the parent of every member TermsComponent; unresolved configuration blocks verified composition | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| previous_id | fk:ContractBundleRevision optional | NULL / None | Previous immutable interpretation; Same bundle; exactly preceding revision; acyclic | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| membership_state | enum required | unresolved / None | Whether actual component membership is known; stipulated is research-only; unresolved,partial,stipulated,verified | u, n, r, e, s, o, l, v, e, d, ,, p, a, r, t, i, a, l, ,, s, t, i, p, u, l, a, t, e, d, ,, v, e, r, i, f, i, e, d | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| status | enum required | unresolved / None | Package status assertion; never inferred from explanation of a cancellation consequence; proposed,in_force,expired,cancelled,separated,unresolved | p, r, o, p, o, s, e, d, ,, i, n, _, f, o, r, c, e, ,, e, x, p, i, r, e, d, ,, c, a, n, c, e, l, l, e, d, ,, s, e, p, a, r, a, t, e, d, ,, u, n, r, e, s, o, l, v, e, d | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Issued package evidence, when supplied; Required for verified issued-package assertion; public sample letters do not prove private acceptance | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| sealed_at | timestamptz optional | NULL / instant | End of the short atomic revision construction transaction; NULL during construction only; immutable after sealing; every persisted revision must be sealed at deferred commit validation | None | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| membership_sha256 | char(64) optional | NULL / None | Digest of canonical exact wrapper configuration and complete ordered member records; Lowercase64hex; required with sealed_at. Recomputed before sealing; changing any membership input requires a new revision. | None | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| seal_format_version | smallint required | 1 / None | Version of canonical package-member serialization; Positive; currently1 only. Format1 hashes UTF-8 JSON with sorted keys, member rows ordered by terms_component_id/id, timestamps normalized to UTC ISO8601, identifiers as strings and no floating numbers; includes all committed member fields and wrapper_configuration_id. | None | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |

Constraints: unique(id,owner_id); owner immutable; unique(bundle_id,revision); Verified membership requires wrapper configuration, private issued evidence and exactly one resolved member disposition for every required/selected applicable slot; conditional/unknown selection blocks closure; Stipulated membership is allowed only in explicit research fixtures and never production verified acceptance; A verified cancelled status requires insurer-event evidence; a request, rule consequence or model response alone is insufficient; Sealing members and moving bundle current_revision pointer occur atomically in one short transaction; old turns cannot advance the pointer; Previous and current revision ownership and bundle lineage checked by deferred constraint triggers under key-share and bundle row locks; CHECK((sealed_at IS NULL)=(membership_sha256 IS NULL)); seal_format_version=1. Deferred commit trigger rejects any persisted unsealed revision, including a revision not yet referenced by the bundle head.; A parent-row-locking trigger guards every member INSERT/UPDATE/DELETE. It rejects mutation of sealed membership, including late insertion, and prevents races with sealing. Authorized erasure uses its separately privileged audited path.; Only the unsealed-to-sealed transition is allowed during construction. After sealing all revision fields are immutable; unsealing is prohibited. Current head can target only a sealed same-bundle revision.; At seal time, validate component/issuer/owner/edition closure and hash exact member data; unresolved or partial interpretation may be sealed with explicit missing members but cannot become verified by sealing..
Indexes: bundle_id,revision DESC; owner_id,status; wrapper_configuration_id.

## ContractBundleMember

Maps one public package slot to one actual same-owner policy revision, preserving component-specific insured membership and explicit missing or unselected slots. Access: private.

| Field | Type / required | Default / units | Purpose and validation | Allowed values | Example | Requirement basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 / None | Stable immutable row identity; Primary key; never reused | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp / instant | Assertion insertion time, separate from contractual effective time; UTC; immutable | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none / None | Owner governing all private bundle records; Immutable owner; never nulled to publish private records | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| bundle_revision_id | fk:ContractBundleRevision required | none / None | Exact immutable package interpretation; Required typed identity; no inferred association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| terms_component_id | fk:TermsComponent required | none / None | Public component slot, including separate issuer identity; Required typed identity; no inferred association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| contract_revision_id | fk:ContractRevision optional | NULL / None | Actual owned issued component policy revision, if established; Resolved policy configuration belongs to TermsComponent.component_product_id and, when fixed, component_terms_id; underlying PolicyContract.insurer_id matches component issuer | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_status | enum required | unresolved / None | Membership disposition; missing is explicit, not fabricated cover; unresolved,required_missing,selected_unverified,selected_stipulated,selected_verified,not_selected | u, n, r, e, s, o, l, v, e, d, ,, r, e, q, u, i, r, e, d, _, m, i, s, s, i, n, g, ,, s, e, l, e, c, t, e, d, _, u, n, v, e, r, i, f, i, e, d, ,, s, e, l, e, c, t, e, d, _, s, t, i, p, u, l, a, t, e, d, ,, s, e, l, e, c, t, e, d, _, v, e, r, i, f, i, e, d, ,, n, o, t, _, s, e, l, e, c, t, e, d | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan optional | NULL / None | Issued evidence for the component membership; Required private evidence for selected_verified or verified not_selected; a public specimen is insufficient | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_fact_id | fk:CustomerFact optional | NULL / None | Attributed customer assertion when documentary proof is absent; Fact subject is this bundle, component contract or an insured person; trace to current customer profile revision; cannot promote unverified to verified | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(id,owner_id); owner immutable; unique(bundle_revision_id,terms_component_id); All member TermsComponent.wrapper_terms_id match bundle wrapper configuration terms; selected_verified requires contract_revision_id and private membership evidence; selected_stipulated requires explicit research fixture; required_missing/not_selected require contract_revision_id NULL; A required component cannot be not_selected; conditional disposition requires its resolved selection rule; All private links enforce composite owner FK and deferred lineage checks on both source and target changes; Members are immutable after revision sealing; changes create a new bundle revision. ContractMember records, not package identity, determine who is insured on each component; Default reject two selected slots in one bundle revision whose ContractRevision.contract_id is the same underlying PolicyContract, even if their revision IDs differ. Deferred check joins underlying contract IDs under parent and contract key-share locks. Any exception requires an explicit reviewed same-wrapper rule with exact slot pair; no implicit exception from matching dates or names..
Indexes: bundle_revision_id,selection_status; contract_revision_id; terms_component_id.
