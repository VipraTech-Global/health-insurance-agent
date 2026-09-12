# Field dictionary — proposed revision 14

Batches 1 through 7 are approved. Later batches and the complete database design remain under review.

## Account

Logical authentication principal implemented by the retained accounts.User(AbstractUser) model.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| email | varchar(254) required | none | Login identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| password | varchar(128) required | none | Django encoded password and algorithm marker | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-06"] |
| last_login | instant optional | NULL | Last successful login | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_superuser | boolean required | false | Global administration privilege | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_staff | boolean required | false | Administration interface access | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| is_active | boolean required | true | Whether login is permitted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| first_name | varchar(150) required | empty string | Optional display given name | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| last_name | varchar(150) required | empty string | Optional display surname | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| date_joined | instant required | now | Original account creation | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| deleted_at | instant optional | NULL | Deletion completion marker | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| erasure_generation | bigint required | 0 | Fence work started before erasure | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "OPS-02"] |

Constraints: email unique; id immutable; username disabled; email is USERNAME_FIELD; native AbstractUser authentication, group and permission semantics retained; date_joined is the account creation timestamp

Indexes: email unique B-tree

## AIPreference

One-to-one user AI route preference kept outside authentication columns.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| user_id | fk:Account required | none | Account whose AI preference this is | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-04", "OPS-06"] |
| route_id | fk:ModelRoute optional | NULL | Preserved user-selected qualified AI route | None | No authentic private or generated identity inspected; synthetic fixture required. | ["OPS-04", "OPS-06"] |
| updated_at | instant required | now | When the preference last changed | instant | No authentic private or generated identity inspected; synthetic fixture required. | ["OPS-04", "OPS-06"] |

Constraints: user_id primary key and one-to-one; disabled or unqualified selected route produces an explicit operational result; no silent fallback

Indexes: user_id primary key; route_id

## Person

A minimal owner-scoped human label; medical, role and identity assertions live in sourced fact records.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| display_name | varchar(200) required | empty string | Customer supplied label | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "CUS-02"] |

Constraints: unique(id,owner_id); owner_id immutable; display_name is not an identity or deduplication key

Indexes: owner_id

## PersonRelationship

Directional relationship between two owner-scoped people, separate from proposed or issued policy membership.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| from_person_id | fk:Person required | none | Person whose relationship is described | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| to_person_id | fk:Person required | none | Related person | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| relationship_type | enum required | none | How to_person relates to from_person Allowed: spouse,parent,child,parent_in_law,sibling,guardian,dependent,other. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| source_statement_id | fk:CustomerStatement required | none | Exact customer statement supporting the relationship | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03"] |
| valid_from | date optional | NULL | First date the relationship applies when materially known | date | Synthetic design fixture only; no real customer value included. | ["CUS-01", "INS-03"] |
| valid_to | date optional | NULL | Last date the relationship applies when materially known | date | Synthetic design fixture only; no real customer value included. | ["CUS-01", "INS-03"] |

Constraints: from_person_id differs from to_person_id; from_person_id and to_person_id have the same immutable owner_id as the relationship; valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from; source assertion has the same owner and matching people; unique(owner_id,from_person_id,to_person_id,relationship_type,valid_from,valid_to) with NULLS NOT DISTINCT; unique(id,owner_id); owner_id immutable

Indexes: owner_id,from_person_id; owner_id,to_person_id; owner_id,relationship_type

## Conversation

Persistent conversation and its current accepted state.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| title | varchar(200) required | empty string | History list label | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| current_profile_revision_id | fk:CustomerProfileRevision optional | NULL | Current customer fact/requirement checkpoint | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| status | enum required | open | Conversation lifecycle Allowed: open,archived,deleting,deleted. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| updated_at | instant required | now | Most recent durable interaction | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |
| preferred_language | varchar(35) optional | NULL | Customer communication locale | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02"] |

Constraints: unique(id,owner_id); profile revision pointer belongs to this conversation; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/statement/fact-type/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; current_profile_revision_id IS NULL OR owner_id IS NOT NULL

Indexes: owner_id,updated_at DESC

## Message

Immutable submitted or published conversational content.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Parent history | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| sequence | bigint required | none | Durable ordering in conversation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| role | enum required | none | Speaker role Allowed: customer,adviser,system. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| content | text required | none | Exact displayed message | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| origin | enum required | none | How content entered history Allowed: text,voice_transcription,document_import,system,migration. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| client_request_id | uuid optional | NULL | Submission idempotency identifier | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| payload_sha256 | char(64) required | none | Hash of canonical submitted payload | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| submitted_at | instant required | none | Original receipt time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| turn_id | fk:Turn optional | NULL | Processing turn producing or consuming message | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| answer_id | fk:Decision optional | NULL | Published answer artifact | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| redacted_at | instant optional | NULL | Content erasure event | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |

Constraints: unique(conversation_id,sequence); unique(owner_id,client_request_id) where nonnull; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; turn_id IS NULL OR owner_id IS NOT NULL; answer_id IS NULL OR owner_id IS NOT NULL

Indexes: conversation_id,sequence; turn_id

## ConversationMessageChunk

Replaceable private lexical/semantic index for an exact section of one immutable conversation message.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Parent history | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "OPS-02", "DEC-01"] |
| message_id | fk:Message required | none | Exact immutable source message | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "RET-01"] |
| chunk_index | integer required | none | Zero-based section order within the message | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| start_offset | integer required | none | Starting character offset in the original message | Unicode code-point offset | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| end_offset | integer required | none | Exclusive ending character offset in the original message | Unicode code-point offset | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| lexical_vector | tsvector required | derived | PostgreSQL full-text representation for exact-term search | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| embedding | vector(1024) optional | NULL | Local BGE-M3 semantic-search derivative | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| index_revision | varchar(160) required | none | Chunking, tokenizer and embedding version | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01", "OPS-06"] |
| content_sha256 | char(64) required | none | Fingerprint of exact source slice and index revision | None | Synthetic design fixture only; no real customer value included. | ["CUS-02", "RET-01"] |
| invalidated_at | instant optional | NULL | When this replaceable derivative stopped being eligible for retrieval | instant | Synthetic design fixture only; no real customer value included. | ["CUS-02", "OPS-01"] |

Constraints: unique(message_id,chunk_index,index_revision); owner_id and conversation_id match the source Message; 0 <= start_offset < end_offset <= source message content length; current accepted CustomerProfileRevision overrides conflicting historical-message retrieval; redacted source messages make every chunk ineligible before content erasure

Indexes: conversation_id,message_id,chunk_index; GIN lexical_vector; HNSW embedding vector_cosine_ops WHERE embedding IS NOT NULL AND invalidated_at IS NULL; owner_id,conversation_id,invalidated_at

## CustomerStatement

A meaningful source span inside one customer message, retained so unusual or unresolved information cannot be silently dropped.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| source_message_id | fk:Message required | none | Immutable message containing this statement | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| start_offset | integer required | none | Starting character in source message | Unicode code-point offset | Synthetic: 0 | ["CUS-02", "CUS-03", "RET-01"] |
| end_offset | integer required | none | Exclusive ending character in source message | Unicode code-point offset | Synthetic: 20 | ["CUS-02", "CUS-03", "RET-01"] |
| subject_person_id | fk:Person optional | NULL | Person the statement concerns when person-specific | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "RET-01"] |
| kind | enum required | none | Initial semantic category Allowed: fact,intended_insured,requirement,preference,question,correction,context,other. | None | Synthetic: fact | ["CUS-02", "CUS-03", "RET-01"] |
| status | enum required | pending | Whether the meaningful span has been handled Allowed: pending,mapped,clarification_required,ignored_with_reason. | None | Synthetic: mapped | ["CUS-02", "CUS-03", "RET-01"] |
| resolution_note | text optional | NULL | Reason a statement needs clarification or is ignored | None | Synthetic: exact hospital branch is unclear. | ["CUS-02", "CUS-03", "RET-01"] |

Constraints: 0 <= start_offset < end_offset <= source Message content length; source Message must have role customer and the same owner; subject_person_id, when set, has the same owner; resolution_note required exactly for clarification_required or ignored_with_reason; decision-relevant statements must become mapped or clarification_required before advice is ready; statement stores offsets, not a duplicate copy of Message.content; unique(id,owner_id); owner_id immutable

Indexes: source_message_id,start_offset,end_offset; owner_id,status; subject_person_id,kind

## CustomerProfileRevision

Small immutable checkpoint created only when customer facts or requirements change.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "DEC-01", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Conversation whose customer state changed | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "DEC-01", "OPS-02"] |
| revision | bigint required | none | Sequential customer-state revision number | None | Synthetic: 3 | ["CUS-02", "DEC-01", "OPS-02"] |

Constraints: unique(conversation_id,revision); revision is positive and monotonic within conversation; facts and requirements for the revision are inserted in the same transaction before Conversation.current_profile_revision_id changes; ordinary chat without a fact or requirement change creates no revision; unique(id,owner_id); owner_id immutable

Indexes: conversation_id,revision DESC

## CustomerFact

One validated version of a customer fact; active historical state is reconstructed by logical key and profile revision.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| introduced_in_revision_id | fk:CustomerProfileRevision required | none | Profile revision that introduced this version | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| source_statement_id | fk:CustomerStatement required | none | Exact customer statement supporting this fact | None | Synthetic design example only; no real customer value inspected. | ["CUS-02", "CUS-03", "INS-06"] |
| logical_key | uuid required | uuid4 for the first version; reuse for corrections | Stable identity of one logical fact across corrections | None | Synthetic UUID shared by age corrections. | ["CUS-02", "CUS-03", "INS-06"] |
| fact_type | varchar(100) required | none | Reviewed semantic meaning of value | None | Synthetic: person.age_reported | ["CUS-02", "CUS-03", "INS-06"] |
| schema_version | positive_integer required | none | Exact validator used for value | None | Synthetic: 1 | ["CUS-02", "CUS-03", "INS-06"] |
| value | json:FactValueV1 required | none | Typed known, unknown or not-applicable value | None | Synthetic: {"state":"known","kind":"quantity","value":"64","unit":"year"} | ["CUS-02", "CUS-03", "INS-06"] |
| status | enum required | reported | Customer acceptance state of this version Allowed: reported,confirmed,disputed,retracted. | None | Synthetic: reported | ["CUS-02", "CUS-03", "INS-06"] |

Constraints: append-only except authorized erasure; source statement and introduced revision share owner and conversation; fact_type registry determines person/conversation subject, cardinality, schema, units and sensitivity; all versions of logical_key retain owner, conversation, subject and fact_type; latest version at or before a requested revision is active unless retracted; multiple active logical keys for a scalar subject/fact_type are an unresolved conflict; unknown and not_applicable are explicit value states and never become zero; unique(id,owner_id); owner_id immutable

Indexes: introduced_in_revision_id; owner_id,logical_key,introduced_in_revision_id; owner_id,fact_type; GIN value

## CustomerRequirement

One atomic mandatory, preferred or informational condition used to filter, rank or explain policy configurations.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| introduced_in_revision_id | fk:CustomerProfileRevision required | none | Profile revision that introduced this version | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| source_statement_id | fk:CustomerStatement required | none | Exact statement supporting this requirement | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| logical_key | uuid required | uuid4 for first version; reuse for corrections | Stable identity of one requirement across corrections | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| criterion | varchar(120) required | none | Policy outcome the customer wants tested | None | Synthetic: claim.copay_percent | ["CUS-01", "CUS-03", "RET-01"] |
| operator | enum required | none | Comparison to apply to policy outcome Allowed: equals,not_equals,less_than_or_equal,greater_than_or_equal,includes,excludes,is_available,is_not_available,minimize,maximize. | None | Synthetic: equals | ["CUS-01", "CUS-03", "RET-01"] |
| target_value | json:FactValueV1 optional | NULL | Desired boundary or value | None | Synthetic: {"state":"known","kind":"quantity","value":"0","unit":"ratio"} | ["CUS-01", "CUS-03", "RET-01"] |
| priority | enum required | none | Whether failure excludes or only ranks a configuration Allowed: mandatory,preferred,informational. | None | Synthetic: mandatory | ["CUS-01", "CUS-03", "RET-01"] |
| scope | enum required | none | People or purchase to which this requirement applies Allowed: entire_purchase,all_intended_insured,person. | None | Synthetic: person | ["CUS-01", "CUS-03", "RET-01"] |
| subject_person_id | fk:Person optional | NULL | Exact person for person-scoped requirement | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| status | enum required | reported | Customer acceptance state of this version Allowed: reported,confirmed,disputed,withdrawn. | None | Synthetic: reported | ["CUS-01", "CUS-03", "RET-01"] |

Constraints: append-only except authorized erasure; source statement and introduced revision share owner and conversation; criterion registry determines permitted operators, value schema and units; subject_person_id required exactly for scope person and null otherwise; target_value required except for minimize and maximize; all versions of logical_key retain owner, conversation, criterion and scope; latest version at or before a requested revision is active unless withdrawn; one source statement may create separate atomic person-scoped requirements without a joining table; unique(id,owner_id); owner_id immutable

Indexes: introduced_in_revision_id; owner_id,logical_key,introduced_in_revision_id; owner_id,criterion,priority; subject_person_id,criterion; GIN target_value

## AdviceRequest

One customer advice goal spanning any number of clarification messages; execution attempts later pin exact profile revisions.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example only; no real customer value inspected. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Synthetic design example only; no real customer value inspected. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Conversation containing the customer goal | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| source_statement_id | fk:CustomerStatement required | none | Statement that initiated this advice goal | None | Synthetic design example only; no real customer value inspected. | ["CUS-01", "CUS-03", "RET-01"] |
| request_type | enum required | none | Requested advice scope Allowed: purchase_recommendation,product_comparison,coverage_question,claim_explanation,renewal_review,portability_review. | None | Synthetic: purchase_recommendation | ["CUS-01", "CUS-03", "RET-01"] |
| status | enum required | open | Whether the customer goal remains active Allowed: open,fulfilled,cancelled. | None | Synthetic: open | ["CUS-01", "CUS-03", "RET-01"] |

Constraints: source statement and conversation share owner and conversation; ten information-gathering messages may still serve one AdviceRequest; processing state and failures belong to Turn/ModelAttempt, not this customer goal; each Turn references the exact CustomerProfileRevision it evaluates; unique(id,owner_id); owner_id immutable

Indexes: conversation_id,created_at DESC; owner_id,status; request_type,status

## Insurer

One insurer in the approved research roster and the issuer identity used by products and official documents.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| name | varchar(250) required | none | Full official insurer name | None | Care Health Insurance Limited | ["INS-01", "INS-04"] |

Constraints: name unique; id and created_at inherited from approved abstract base models

Indexes: name unique B-tree

## DiscoveryRun

One autonomous Codex session tasked with discovering public documents for one insurer.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| insurer_id | fk:Insurer required | none | Insurer whose sources the run investigates | None | Synthetic design example; no customer value used. | ["INS-01", "INS-04"] |
| instructions | text required | none | Exact discovery task supplied to Codex | None | Find all current and historical health-insurance documents for Care, including official and useful independent sources. | ["INS-04", "OPS-03"] |
| session_id | varchar(250) required | none | Codex session identity used for continuation and audit | None | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| model_name | varchar(160) required | none | Observed Codex model used for the run | None | gpt-6-astra | ["OPS-03", "OPS-04"] |
| completed_at | instant optional | NULL | When the run reached a terminal state | instant | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| status | enum required | queued | Run lifecycle Allowed: ['queued', 'running', 'completed', 'failed', 'cancelled']. | None | completed | ["INS-04", "OPS-03"] |
| error_summary | text optional | NULL | Safe explanation of a failed run | None | Browser session ended before attachments were inspected. | ["OPS-03"] |

Constraints: session_id unique; terminal status requires completed_at; failed requires error_summary; completed means the assigned session finished; it never proves all documents were found

Indexes: insurer_id,created_at DESC; status,created_at

## SourceURL

One unique public web address discovered by Codex, independent of how often or where it was observed.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| url | text required | none | Exact usable source URL | None | https://careinsurance.com/example/policy-wording.pdf | ["INS-04", "OPS-03"] |
| source_type | enum required | unknown | Who operates the location, used as provenance rather than a browsing restriction Allowed: ['insurer_site', 'regulator_site', 'government_site', 'independent_site', 'archive', 'other', 'unknown']. | None | insurer_site | ["INS-04", "DEC-01"] |

Constraints: url unique; source_type is evidence metadata and never an autonomous-browsing allowlist

Indexes: url unique B-tree; source_type

## SourceObservation

One retained occasion on which a Codex discovery run encountered a source URL.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| discovery_run_id | fk:DiscoveryRun required | none | Codex run that made the observation | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| source_url_id | fk:SourceURL required | none | URL encountered by the run | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| found_in_capture_id | fk:SourceCapture optional | NULL | Previously captured page or register containing the link | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| observation_type | enum required | other | How Codex encountered the URL Allowed: ['search_result', 'page_link', 'attachment', 'document_register', 'sitemap', 'known_url', 'other']. | None | attachment | ["INS-04"] |
| label_or_context | text optional | NULL | Useful visible label, snippet or surrounding context | None | Download Policy Terms and Conditions | ["INS-04"] |
| disposition | enum required | unresolved | Whether the observed URL belongs in the research scope Allowed: ['relevant', 'irrelevant', 'unresolved']. | None | relevant | ["INS-02", "INS-04"] |
| disposition_reason | text optional | NULL | Why the observation was excluded or remains unresolved | None | Document concerns travel insurance rather than medical-expense cover. | ["INS-02", "INS-04"] |

Constraints: irrelevant requires disposition_reason; observations are retained even when irrelevant; found_in_capture_id cannot point to a later capture

Indexes: discovery_run_id,created_at; source_url_id,created_at; disposition

## SourceCapture

One attempt by a Codex discovery run to preserve the content currently returned by a source URL.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| discovery_run_id | fk:DiscoveryRun required | none | Run responsible for this capture attempt | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| source_url_id | fk:SourceURL required | none | URL whose content was requested | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| completed_at | instant optional | NULL | When the capture succeeded or failed | instant | Synthetic design example; no customer value used. | ["OPS-03", "OPS-06"] |
| status | enum required | running | Capture lifecycle Allowed: ['running', 'captured', 'failed']. | None | captured | ["INS-04", "OPS-03"] |
| http_status | smallint optional | NULL | HTTP response status when Codex or its browser exposes one | None | 200 | ["INS-04", "OPS-03"] |
| original_file_id | fk:OriginalFile optional | NULL | Exact bytes preserved by a successful capture | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| document_version_id | fk:DocumentVersion optional | NULL | Document edition identified from the captured content | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| error_summary | text optional | NULL | Safe reason a capture failed | None | Access denied after browser navigation. | ["OPS-03"] |

Constraints: captured requires original_file_id and completed_at; failed requires error_summary and completed_at; running has no completed_at; the same URL may have many captures over time; multiple URLs may capture the same OriginalFile

Indexes: source_url_id,created_at DESC; discovery_run_id,status; document_version_id; original_file_id

## OriginalFile

Content-addressed exact bytes preserved from a public source or private customer upload.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account optional | NULL | Owner of a private file; NULL for public corpus files | None | No authentic customer identity or document value inspected. | ["OPS-01"] |
| sha256 | char(64) required | none | Cryptographic identity of the exact bytes | None | cb0a27f2c9a15599a62560a56c01f6bc5554f3b3ab5e62c028293940980038bb | ["INS-04", "OPS-03"] |
| storage_key | varchar(500) required | none | Opaque private object-storage location | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-01"] |
| byte_size | bigint required | none | Exact stored byte length | bytes | 2483921 | ["INS-04", "OPS-03"] |
| media_type | varchar(150) required | none | Detected actual media type | None | application/pdf | ["INS-04", "OPS-03"] |
| availability | enum required | available | Whether preserved bytes may currently be used Allowed: ['available', 'quarantined', 'deleted']. | None | available | ["INS-04", "OPS-01"] |
| last_verified_at | instant required | now | Most recent successful hash-integrity check | instant | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |

Constraints: unique(owner_id,sha256) NULLS NOT DISTINCT; storage_key unique; owner_id immutable; deleted private content cannot be read

Indexes: sha256; owner_id,availability

## CustomerUploadedDocument

One private document supplied by a customer, separate from its content-addressed bytes.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-02", "INS-03", "OPS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| original_file_id | fk:OriginalFile required | none | Exact private bytes supplied by the customer | None | Synthetic design example only; no real customer identity included. | ["CUS-02", "INS-03", "OPS-01"] |
| source_message_id | fk:Message optional | NULL | Conversation message through which the file was supplied | None | Intentionally no real customer or authentication identity inspected or included. | ["CUS-02", "OPS-01"] |
| display_name | varchar(300) optional | NULL | Encrypted customer-facing filename or label | None | star-policy-schedule.pdf (synthetic) | ["CUS-02", "OPS-01"] |
| kind | enum required | other | Customer-document category Allowed: offer,policy_schedule,endorsement,member_certificate,receipt,claim_document,other. | None | policy_schedule (synthetic) | ["INS-03"] |
| review_status | enum required | received | Whether the private document can be understood and used Allowed: received,readable,classified,unusable,conflicted. | None | classified (synthetic) | ["CUS-02", "INS-03", "OPS-01"] |

Constraints: unique(id,owner_id); owner_id immutable; original_file_id points to a private OriginalFile owned by the same account; display_name is encrypted and is never a document-identity key

Indexes: owner_id,created_at; owner_id,kind,review_status; original_file_id

## DocumentSeries

Stable identity of one continuing publication across editions, such as a product policy wording.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| issuer_id | fk:Insurer optional | NULL | Insurer that issued the publication | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| name | text required | none | Stable human-readable series name | None | Care Supreme Policy Wording | ["INS-02", "INS-04"] |
| kind | enum required | other | Document category Allowed: ['policy_wording', 'customer_information_sheet', 'prospectus', 'endorsement', 'premium_table', 'provider_list', 'regulation', 'notice', 'comparison', 'web_page', 'other']. | None | policy_wording | ["INS-02", "INS-04"] |
| authority | enum required | unknown | Who authored or issued the claims inside the document Allowed: ['insurer_issued', 'regulator_issued', 'government_issued', 'independent_analysis', 'unknown']. | None | insurer_issued | ["INS-02", "DEC-01"] |
| relevance | enum required | unresolved | Relationship of the captured content to CoverGuide's medical-expense scope Allowed: ['relevant', 'supporting', 'unrelated', 'unresolved']. | None | relevant | ["INS-02", "INS-04"] |

Constraints: issuer_id required when authority is insurer_issued; independent_analysis does not become contractual authority because an insurer is discussed

Indexes: issuer_id,kind; authority,relevance; name

## DocumentVersion

One identified edition within a DocumentSeries, with evidence-backed dates and explicit supersession.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| document_series_id | fk:DocumentSeries required | none | Publication series containing this edition | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| version_label | varchar(200) optional | NULL | Printed edition or version label | None | Version 3 - 2025 | ["INS-02"] |
| identifiers | json:IdentifiersV1 required | empty array | Printed UINs and other document identifiers | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| language | varchar(35) optional | NULL | Printed document language | None | en-IN | ["INS-02"] |
| published_on | date optional | NULL | Printed publication date | calendar date | 2025-04-01 | ["INS-02", "INS-04"] |
| effective_from | date optional | NULL | First applicability date when established | calendar date | 2025-04-01 | ["INS-02", "INS-03"] |
| effective_to | date optional | NULL | Last applicability date when established | calendar date | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| supersedes_id | fk:DocumentVersion optional | NULL | Earlier edition explicitly replaced by this edition | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| review_status | enum required | unreviewed | Confidence in edition identity and applicability metadata Allowed: ['unreviewed', 'identified', 'verified', 'conflicted']. | None | verified | ["INS-02", "INS-04"] |

Constraints: supersedes_id belongs to the same DocumentSeries and is acyclic; effective_to is on or after effective_from; is_latest is derived and never stored; latest discovered, latest published and currently applicable remain distinct

Indexes: document_series_id,published_on DESC; document_series_id,effective_from,effective_to; review_status

## DocumentPage

One physical PDF page and its explicit review state, including pages on which extraction failed.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When mutable metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| original_file_id | fk:OriginalFile required | none | Exact PDF containing this page | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |
| page_number | integer required | none | One-based physical page number | page | 37 | ["INS-04"] |
| printed_label | varchar(80) optional | NULL | Page label printed inside the document | None | Page 34 of 52 | ["INS-04"] |
| review_state | enum required | unread | How completely this physical page has been inspected Allowed: ['unread', 'text_read', 'visually_reviewed', 'fully_reviewed', 'unresolved']. | None | fully_reviewed | ["INS-04", "OPS-03"] |

Constraints: unique(original_file_id,page_number); non-PDF originals do not create DocumentPage rows; page dimensions and rotation are read from preserved PDF bytes rather than duplicated here

Indexes: original_file_id,page_number; review_state

## EvidenceSpan

One exact passage, table cell, footnote or region from either a public capture or private customer upload.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| source_capture_id | fk:SourceCapture optional | NULL | Public web capture supplying this evidence | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| customer_uploaded_document_id | fk:CustomerUploadedDocument optional | NULL | Private customer upload supplying this evidence | None | Synthetic private schedule upload identity only. | ["CUS-02", "INS-03", "OPS-01"] |
| page_id | fk:DocumentPage optional | NULL | Physical PDF page containing the evidence | None | Synthetic design example; no customer value used. | ["INS-04"] |
| section_label | varchar(200) optional | NULL | Printed section or table label | None | Pre-existing Disease Waiting Period | ["INS-04", "RET-01"] |
| quote | text required | none | Exact extracted or visually transcribed source text | None | Synthetic design example; no customer value used. | ["INS-04", "DEC-01"] |
| context | json:EvidenceContextV1 required | empty object | Headings, table axes, units, footnotes and connected passages required to interpret the quote | None | Synthetic design example; no customer value used. | ["INS-04", "DEC-01"] |
| method | enum required | none | How the passage was read Allowed: ['native_text', 'ocr_verified', 'manual_visual', 'html', 'json']. | None | native_text | ["INS-04", "OPS-03"] |
| verification | enum required | unverified | Independent verification state Allowed: ['unverified', 'text_verified', 'visually_verified', 'reviewed', 'failed']. | None | reviewed | ["INS-04", "DEC-01"] |
| locator | json:OriginalLocatorV1 required | none | Exact PDF region, HTML selector, JSON pointer or text range | None | Synthetic design example; no customer value used. | ["INS-04", "OPS-03"] |

Constraints: exactly one of source_capture_id or customer_uploaded_document_id is set; source capture is captured and mapped to a DocumentVersion; PDF evidence requires a page from the same OriginalFile; non-PDF evidence has no page_id; quote must resolve from immutable captured bytes and locator; verification does not by itself establish semantic entailment

Indexes: source_capture_id; page_id,section_label; verification; customer_uploaded_document_id

## Product

Stable insurer product family, independent of policy editions, named variants and optional additions.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| insurer_id | fk:Insurer required | none | Insurer offering the product | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| name | varchar(250) required | none | Official product-family name | None | Care Supreme | ["INS-01", "INS-02"] |
| benefit_type | enum required | unresolved | How the product pays benefits Allowed: ['medical_indemnity', 'fixed_benefit', 'hybrid', 'addon', 'unresolved']. | None | medical_indemnity | ["INS-01", "INS-05"] |
| lifecycle_status | enum required | unresolved | Whether the product is sold or retained only historically Allowed: ['open', 'withdrawn', 'renewal_only', 'historical', 'unresolved']. | None | open | ["INS-01", "INS-03"] |
| recommendation_role | enum required | unresolved | How CoverGuide may use the product in advice Allowed: ['primary_policy', 'supplementary', 'reference_only', 'excluded', 'unresolved']. | None | primary_policy | ["INS-01", "DEC-01"] |
| identity_evidence_id | fk:EvidenceSpan required | none | Exact original passage establishing product identity | None | Synthetic design example; no customer value used. | ["INS-01", "INS-04"] |

Constraints: no global unique-name assumption; identity_evidence_id required; recommendation_role and benefit_type remain distinct

Indexes: insurer_id,name; benefit_type,lifecycle_status,recommendation_role

## PolicyVersion

One complete legal terms package for a Product, assembled from every applicable governing document.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| product_id | fk:Product required | none | Product governed by this policy version | None | Synthetic design example; no customer value used. | ["INS-01", "INS-02"] |
| uin | varchar(100) optional | NULL | Curated resolved product UIN | None | CHIHLIP25047V012425 | ["INS-02", "INS-05"] |
| version_label | varchar(200) optional | NULL | Printed or curated policy edition label | None | 2025 edition | ["INS-02"] |
| publication_status | enum required | draft | Curation and publication state Allowed: ['draft', 'reviewed', 'published', 'superseded', 'blocked']. | None | reviewed | ["INS-04", "OPS-03"] |
| supersedes_id | fk:PolicyVersion optional | NULL | Earlier legal terms package replaced by this one | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| applicability | json:ApplicabilityV1 required | none | Dates, issue or renewal events and other boundaries selecting this policy version | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03", "INS-05"] |

Constraints: supersedes_id belongs to the same Product and is acyclic; publication requires all required PolicyVersionDocument rows and material dependencies; a newer discovered document does not automatically change applicability

Indexes: product_id,publication_status; product_id,uin; product_id,supersedes_id

## PolicyVersionDocument

Membership, role, conditional applicability and proven precedence of one DocumentVersion in a PolicyVersion.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| policy_version_id | fk:PolicyVersion required | none | Policy version whose legal document bundle includes this document | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| document_version_id | fk:DocumentVersion required | none | Exact source-document edition | None | Synthetic design example; no customer value used. | ["INS-02", "INS-04"] |
| role | enum required | none | Legal or explanatory role of the document Allowed: ['base_wording', 'customer_information_sheet', 'prospectus', 'endorsement', 'regulatory_modification', 'referenced_schedule', 'other_dependency']. | None | base_wording | ["INS-02", "INS-04"] |
| required_for_policy | boolean required | true | Whether the policy version is incomplete without this applicable document | None | True | ["INS-04", "INS-05"] |
| applicability | json:ApplicabilityV1 required | none | Conditions under which this document participates in the policy version | None | Synthetic design example; no customer value used. | ["INS-02", "INS-05"] |
| precedence_evidence_id | fk:EvidenceSpan optional | NULL | Exact clause proving that this document controls another | None | Synthetic design example; no customer value used. | ["INS-04", "INS-05"] |

Constraints: unique(policy_version_id,document_version_id,role); required applicable documents must be present before publication; precedence is never inferred from download date

Indexes: policy_version_id,role; document_version_id

## ProductVariant

One insurer-defined base variant and its allowed sums insured, deductibles, room categories and family choices.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| policy_version_id | fk:PolicyVersion required | none | Policy version governing the variant | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| name | varchar(200) required | Default | Official variant name or Default when the product has no named tier | None | Gold | ["INS-01", "INS-03"] |
| choices | json:ConfigurationV1 required | none | Allowed sum insured, deductible, room, family and other base selectors | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| availability | json:ApplicabilityV1 required | none | Sale, renewal, age, territory and insured-person conditions | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| identity_evidence_id | fk:EvidenceSpan required | none | Original passage establishing the variant and its selectors | None | Synthetic design example; no customer value used. | ["INS-03", "INS-04"] |

Constraints: unique(policy_version_id,name); products without a named tier use exactly one Default variant; choices do not represent a customer selection

Indexes: policy_version_id,name

## ProductOption

One optional or mandatory add-on, rider or election available with a ProductVariant.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | Synthetic design example; no customer value used. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| product_variant_id | fk:ProductVariant required | none | Base variant on which the option is available | None | Synthetic design example; no customer value used. | ["INS-01", "INS-03"] |
| option_policy_version_id | fk:PolicyVersion optional | NULL | Separate policy terms for the option when they exist | None | Synthetic design example; no customer value used. | ["INS-02", "INS-03"] |
| name | varchar(200) required | none | Official option name | None | Claim Shield | ["INS-01", "INS-03"] |
| selection_kind | enum required | optional | Whether the customer may omit the option Allowed: ['optional', 'mandatory']. | None | optional | ["INS-03"] |
| conditions | json:ApplicabilityV1 required | none | Eligibility, dates, dependencies and incompatible selections | None | Synthetic design example; no customer value used. | ["INS-03", "INS-05"] |
| identity_evidence_id | fk:EvidenceSpan required | none | Exact original passage establishing the option | None | Synthetic design example; no customer value used. | ["INS-03", "INS-04"] |

Constraints: unique(product_variant_id,name); option_policy_version_id does not by itself mean the option was selected by a customer

Indexes: product_variant_id,name; option_policy_version_id

## CustomerPolicy

Stable identity of one insurer-issued customer policy or customer-specific offer.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| policy_number | encrypted_varchar(200) optional | NULL | Insurer-issued policy identifier | None | SH-12345 (synthetic) | ["INS-03", "OPS-01"] |
| insurer_id | fk:Insurer required | none | Insurer that issued the policy or personal offer | None | Synthetic design example only; no real customer identity included. | ["INS-03"] |
| proposer_id | fk:Person optional | NULL | Person named as proposer or policyholder | None | Intentionally no real customer or authentication identity inspected or included. | ["CUS-01", "INS-03"] |
| payer_id | fk:Person optional | NULL | Person paying the premium | None | Intentionally no real customer or authentication identity inspected or included. | ["CUS-01", "INS-03"] |
| coverage_type | enum required | unresolved | How insured people share the issued cover Allowed: individual,family_floater,group_member,unresolved. | None | family_floater (synthetic) | ["INS-03", "INS-07"] |
| lifecycle_status | enum required | unresolved | Current state of the customer-specific policy relationship Allowed: offered,active,lapsed,expired,cancelled,declined,unresolved. | None | active (synthetic) | ["INS-03", "INS-08"] |
| group_master_reference | encrypted_varchar(250) optional | NULL | Employer or master-policy reference for group membership | None | EMP-GRP-77 (synthetic) | ["INS-03", "INS-07", "OPS-01"] |

Constraints: unique(id,owner_id); owner_id immutable; proposer_id and payer_id have the same owner_id; group_master_reference is allowed only when coverage_type=group_member; public recommendations do not create CustomerPolicy rows

Indexes: owner_id,insurer_id; owner_id,lifecycle_status

## CustomerPolicyRevision

One exact set of insurer-issued customer selections applying during a defined interval.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| customer_policy_id | fk:CustomerPolicy required | none | Customer policy whose exact issued terms this revision records | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03", "INS-07"] |
| revision_number | positive_integer required | none | Monotonic revision order within the customer policy | count | 2 (synthetic) | ["INS-02", "INS-03", "INS-07"] |
| product_variant_id | fk:ProductVariant optional | NULL | Public product variant matched to the issued cover | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03", "INS-07"] |
| policy_term | daterange optional | NULL | Full insurer renewal term containing this revision | None | [2026-01-01,2027-01-01) (synthetic) | ["INS-07", "INS-08"] |
| effective_during | daterange optional | NULL | Interval during which this exact issued revision controls | None | [2026-07-01,2027-01-01) (synthetic endorsement revision) | ["INS-02", "INS-03", "INS-07"] |
| selected_choices | json:CustomerPolicySelectionV1 required | {'choices': [], 'unresolved_keys': []} | Actual issued sum insured, deductible, room and other base selections | None | Synthetic: sum_insured INR 1000000, deductible INR 0, room_category single_private_room. | ["INS-02", "INS-03", "INS-07"] |
| selection_evidence_id | fk:EvidenceSpan optional | NULL | Private schedule passage supporting the base selections | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03", "INS-07"] |
| verification_status | enum required | reported | Confidence that this revision matches the insurer-issued cover Allowed: reported,verified,conflicted. | None | verified (synthetic) | ["INS-02", "INS-03", "INS-07"] |

Constraints: unique(customer_policy_id,revision_number); unique(id,owner_id); owner_id immutable; verified revisions for one CustomerPolicy cannot have unresolved overlapping effective_during ranges; effective_during is contained by policy_term when both are known; product_variant insurer matches CustomerPolicy insurer when verification_status=verified

Indexes: customer_policy_id,revision_number; GiST policy_term; GiST effective_during

## PolicyMember

One person actually covered under one customer policy revision.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Exact issued policy revision providing this membership | None | Synthetic design example only; no real customer identity included. | ["CUS-01", "INS-03", "INS-07"] |
| person_id | fk:Person required | none | Person actually covered by this policy revision | None | Intentionally no real customer or authentication identity inspected or included. | ["CUS-01", "INS-03", "INS-07"] |
| covered_during | daterange required | none | Person-specific insured interval | None | [2026-04-01,2027-01-01) (synthetic) | ["CUS-01", "INS-03", "INS-07"] |
| member_identifier | encrypted_varchar(160) optional | NULL | Insurer member or certificate identifier | None | MEM-002 (synthetic) | ["INS-03", "OPS-01"] |
| evidence_span_id | fk:EvidenceSpan optional | NULL | Schedule or member-certificate passage proving membership | None | Synthetic design example only; no real customer identity included. | ["CUS-01", "INS-03", "INS-07"] |
| verification_status | enum required | reported | Whether actual policy membership is established Allowed: reported,verified,conflicted. | None | verified (synthetic) | ["CUS-01", "INS-03", "INS-07"] |

Constraints: unique(id,owner_id); owner_id immutable; no overlapping duplicate verified membership for the same customer policy and person; covered_during is nonempty and consistent with the revision term; family role is read from PersonRelationship and is not duplicated here

Indexes: customer_policy_revision_id,person_id; owner_id,person_id; GiST covered_during

## CustomerPolicyOption

One customer-specific selected, declined or unresolved ProductOption decision.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-02", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Exact customer policy revision whose option choice is recorded | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03"] |
| product_option_id | fk:ProductOption required | none | Public option offered by the matched product variant | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03"] |
| selection_status | enum required | unresolved | Whether this customer selected the option Allowed: selected,declined,unresolved. | None | selected (synthetic maternity option) | ["INS-02", "INS-03"] |
| evidence_span_id | fk:EvidenceSpan optional | NULL | Private offer or schedule passage supporting the option decision | None | Synthetic design example only; no real customer identity included. | ["INS-02", "INS-03"] |
| verification_status | enum required | reported | Reliability of this customer-specific option selection Allowed: reported,verified,conflicted. | None | verified (synthetic) | ["INS-02", "INS-03"] |

Constraints: unique(customer_policy_revision_id,product_option_id); unique(id,owner_id); owner_id immutable; verified selected or declined rows require exact private evidence; ProductOption belongs to the revision ProductVariant when that variant is resolved

Indexes: customer_policy_revision_id,selection_status; product_option_id

## CustomerPolicyFact

One document-backed structured fact about a particular customer's issued policy revision.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CUS-01", "INS-03", "INS-07", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| updated_at | instant required | now | When curated metadata or lifecycle state last changed | instant | Synthetic design example; no customer value used. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Synthetic design example only; no real customer value included. | ["OPS-01"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Exact issued revision to which the fact belongs | None | Synthetic design example only; no real customer value included. | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| person_id | fk:Person optional | NULL | Affected insured when the fact is person-specific | None | Synthetic design example only; no real customer value included. | ["INS-03", "INS-07"] |
| fact_type | varchar(100) required | none | Finite code-controlled meaning of this issued-policy fact Allowed: personal_copay,personal_exclusion,premium_loading,waiting_period_change,waiver,additional_cover,continuity_credit,other_issued_term. | None | personal_copay (synthetic) | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| value | json:CustomerPolicyFactValueV1 required | none | Strict typed value selected by fact_type | None | Synthetic 20 percent diabetes co-pay rule. | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| related_customer_policy_id | fk:CustomerPolicy optional | NULL | Prior policy supplying history when this is continuity credit | None | Synthetic design example only; no real customer value included. | ["INS-07", "INS-08"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact private offer, schedule or endorsement passage | None | Synthetic design example only; no real customer value included. | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| verification_status | enum required | extracted | Review state of the structured policy fact Allowed: extracted,verified,conflicted. | None | verified (synthetic) | ["INS-03", "INS-05", "INS-06", "INS-07", "INS-08", "CAL-03", "CAL-04"] |
| supersedes_id | fk:CustomerPolicyFact optional | NULL | Earlier incorrect interpretation replaced by this row | None | Synthetic design example only; no real customer value included. | ["CUS-02", "INS-03"] |

Constraints: unique(id,owner_id); owner_id immutable; evidence_span_id resolves through a CustomerUploadedDocument owned by owner_id; fact_type selects exactly one closed CustomerPolicyFactValueV1 branch; related_customer_policy_id is required only for continuity_credit; supersedes_id is same-owner, same-revision, acyclic and has at most one successor; customer statements without insurer evidence remain CustomerFact rows and do not create verified CustomerPolicyFact rows

Indexes: customer_policy_revision_id,fact_type,person_id; related_customer_policy_id; GIN value jsonb_path_ops; supersedes_id unique where nonnull

## PolicyEvent

One sourced real-world event in the timeline of a customer policy.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Synthetic design example only; no real customer value included. | ["OPS-01"] |
| customer_policy_id | fk:CustomerPolicy required | none | Customer policy affected by the event | None | Synthetic design example only; no real customer value included. | ["INS-07", "INS-08"] |
| event_type | varchar(100) required | none | Finite code-controlled real-world policy event Allowed: policy_issued,document_received,renewal_due,premium_due,premium_paid,portability_requested,portability_information_received,group_cover_ended,claim_notified,cancellation_requested,cancellation_received,cancellation_accepted,coverage_ended,refund_calculated,refund_paid,refund_received,refund_reversed,other. | None | cancellation_received (synthetic) | ["INS-07", "INS-08"] |
| occurred_at | json:TemporalExtentV1 required | none | Actual event time/date and precision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| amount | json:QuantityV1 optional | NULL | Payment/debt/refund if event includes money | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-08", "INS-07"] |
| source_evidence_id | fk:EvidenceSpan optional | NULL | Documentary proof of the event | None | Synthetic design example only; no real customer value included. | ["INS-07", "INS-08"] |
| source_message_id | fk:Message optional | NULL | Customer statement reporting the event | None | Synthetic design example only; no real customer value included. | ["CUS-02", "INS-08"] |
| verification_status | enum required | reported | Reliability of the event occurrence and date Allowed: reported,verified,disputed,retracted. | None | verified (synthetic) | ["INS-07", "INS-08"] |
| related_event_id | fk:PolicyEvent optional | NULL | Earlier event in the same real-world sequence | None | Synthetic design example only; no real customer value included. | ["INS-07", "INS-08"] |
| supersedes_event_id | fk:PolicyEvent optional | NULL | Earlier incorrect event record corrected by this row | None | Synthetic design example only; no real customer value included. | ["CUS-02", "INS-08"] |
| authority_evidence_id | fk:EvidenceSpan optional | NULL | Proof that a TPA or intermediary could receive or decide for the insurer | None | Synthetic design example only; no real customer value included. | ["INS-08"] |

Constraints: unique(id,owner_id); owner_id immutable; at least one of source_evidence_id or source_message_id is present; verified events require evidence adequate for the event type; an authorized intermediary requires authority_evidence_id before insurer receipt or decision is verified; related_event_id records a sequence relation; supersedes_event_id records correction and the two meanings cannot be substituted; supersedes_event_id is same-owner, same-policy, acyclic and has at most one successor; record creation never sends a request, accepts cancellation or causes payment; package-level events remain unresolved until the package models are reviewed

Indexes: customer_policy_id,event_type,occurred_at; owner_id,verification_status; related_event_id; supersedes_event_id unique where nonnull

## PolicyRule

One immutable, reviewed condition, benefit, restriction or calculation instruction from a public policy version.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| policy_version_id | fk:PolicyVersion required | none | Exact public policy version containing the rule | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| rule_key | varchar(160) required | none | Stable readable identity for this logical rule within the policy version | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| rule_type | enum required | none | Controlled category used for retrieval and validation Allowed: definition,eligibility,coverage,exclusion,exception,waiting_period,limit,deduction,accumulation,restoration,calculation,precedence,operational_right. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| body | json:RuleV1 required | none | Closed structured conditions, required inputs, effects and optional table definition | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| review_status | enum required | draft | Whether the complete rule and all required evidence may be used Allowed: draft,verified,blocked,superseded. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| supersedes_id | fk:PolicyRule optional | NULL | Earlier interpretation corrected by this immutable row | None | Synthetic correction link only; no invented insurer value. | ["INS-04", "OPS-06"] |

Constraints: public only; no customer owner field; immutable after creation; verified requires sufficient required PolicyRuleEvidence and verified required PolicyRuleLink closure; body validates against RuleV1 and the selected rule_type; supersedes_id has the same policy_version_id and rule_key, is acyclic and has at most one successor; only a verified unsuperseded rule may enter a new CorpusRevision

Indexes: policy_version_id,rule_type,review_status; policy_version_id,rule_key; body GIN jsonb_path_ops for registered input and output keys

## PolicyRuleEvidence

One exact public source passage supporting, defining, restricting or contradicting a policy rule.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| policy_rule_id | fk:PolicyRule required | none | Structured policy rule supported or restricted | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact public original passage | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| role | enum required | none | How passage relates to rule Allowed: supports,defines,restricts,excepts,contradicts,precedence,table_header,table_cell,footnote. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |
| is_required | boolean required | true | Whether omitting this passage makes the rule unsafe to verify | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "INS-05"] |

Constraints: unique(policy_rule_id,evidence_span_id,role); evidence_span_id must be public and applicable to policy_rule_id.policy_version_id; verified PolicyRule requires all required evidence links to be present and independently reviewed as part of the rule review

Indexes: policy_rule_id,role; evidence_span_id

## PolicyRuleLink

A reviewed connection requiring two policy rules to be interpreted together.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| from_policy_rule_id | fk:PolicyRule required | none | Rule whose interpretation requires another rule | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| to_policy_rule_id | fk:PolicyRule required | none | Definition, exception, prerequisite or calculation rule that must also load | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |
| link_type | enum required | none | Meaning of the rule connection Allowed: definition,prerequisite,exception,overrides,calculation_input,scope. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "RET-01"] |

Constraints: unique(from_policy_rule_id,to_policy_rule_id,link_type); no self link; both rules belong to the same PolicyVersion unless a later explicitly reviewed cross-version use is introduced; calculation_input and overrides links are acyclic; verified source rule requires its mandatory link closure to resolve to verified rules

Indexes: from_policy_rule_id,link_type; to_policy_rule_id

## PolicyRuleTableCell

One original-backed result selected by the complete axes declared in a policy rule body.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-05", "CAL-01", "CAL-02", "CAL-03", "CAL-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| policy_rule_id | fk:PolicyRule required | none | Table-lookup policy rule declaring the axes and result meaning | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04", "INS-05"] |
| selectors | json:TableSelectorsV1 required | none | Exact value for every axis declared by the parent rule body | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| value | json:ExpressionV1 required | none | Typed amount, limit, reference or expression returned by this cell | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |
| evidence_span_id | fk:EvidenceSpan required | none | Exact original cell geometry and transcription | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-04", "INS-04"] |

Constraints: unique(policy_rule_id,selectors); selectors provide every declared axis exactly once and no undeclared axis; overlapping selector ranges block parent rule verification; headers and footnotes are required PolicyRuleEvidence links on the parent rule

Indexes: policy_rule_id; selectors GIN jsonb_path_ops

## Provider

Legal hospital organization and exact branch identity.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| legal_name | varchar(300) required | none | Provider organization name | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| branch_name | varchar(250) optional | NULL | Specific facility branch | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| address | text optional | NULL | Original-backed branch address | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| city | varchar(150) optional | NULL | Branch city | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| postal_code | varchar(20) optional | NULL | Branch postcode | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| country_code | char(2) required | IN | ISO3166 country | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| external_identifiers | json:IdentifiersV1 required | empty array | Insurer/registry provider codes with provenance | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |
| identity_status | enum required | unresolved | Branch identity resolution Allowed: unresolved,verified,conflicted. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02"] |

Constraints: no name-only uniqueness; verified external identity keys scoped by issuer

Indexes: city,postal_code; external_identifiers GIN

## ProviderObservation

Dated insurer- and service-specific hospital status.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| provider_id | fk:Provider required | none | Exact facility branch | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| insurer_id | fk:Insurer optional | NULL | Insurer reporting status | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| configuration_id | fk:ProductVariant optional | NULL | Restricted product scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| service_scope | json:ProviderScopeV1 required | none | Treatment, network tier and geographic scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| status | enum required | unknown | Legacy-style summary only for network/exclusion observations; kind/value are authoritative Allowed: network,nonnetwork,restricted,excluded,unknown,not_applicable. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| observed_at | instant required | none | Observation date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| valid_during | json:TemporalExtentV1 required | none | Original stated validity if any | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| span_id | fk:EvidenceSpan required | none | Original dated directory/notice evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| supersedes_id | fk:ProviderObservation optional | NULL | Prior status observation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-02", "INS-05"] |
| kind | enum required | none | Independent observed provider property Allowed: network_membership,exclusion,restricted_network,wheelchair_access,clinician_participation,authorization,search_completeness. | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| value | json:ObservationValueV1 required | none | Typed observed value and evidence certainty | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| clinician_id | fk:Clinician optional | NULL | Named specialist participation subject | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| search_coverage | json:SearchCoverageV1 required | none | Scope and completeness of the observed directory/query | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |

Constraints: immutable history; overlapping contradictory observations produce issue; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; network/exclusion/restricted_network/authorization kinds require insurer_id;clinician_participation requires clinician_id;wheelchair_access can be branch-wide with insurer_id NULL;configuration requires its matching insurer

Indexes: provider_id,insurer_id,observed_at DESC; configuration_id

## Quote

Private insurer offer bound to exact people, facts and configuration.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Comparison context | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| profile_revision_id | fk:CustomerProfileRevision required | none | Exact customer profile used for this quote observation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| configuration_id | fk:ProductVariant required | none | Quoted public options basis | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| quoted_selection | json:AcceptedSelectionV1 required | none | People, option selections, SI and deductible | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| insurer_quote_id | varchar(200) optional | NULL | Issuer quote identifier | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| issued_at | instant optional | NULL | Issuer quote time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| valid_until | instant optional | NULL | Offer expiry | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| status | enum required | unverified | Offer/acceptance state Allowed: unverified,offered,accepted,expired,declined,invalidated. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| source_document_id | fk:DocumentVersion required | none | Original quote | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| total | json:QuantityV1 required | none | Verified payable total or explicit unknown | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |
| coverage_term | json:TemporalExtentV1 required | none | Quoted insurance term | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-03"] |

Constraints: fact correction invalidates reuse; accepted quote alone not in-force policy; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; profile_revision_id IS NULL OR owner_id IS NOT NULL

Indexes: owner_id,conversation_id,status; valid_until

## QuoteComponent

A source-backed premium, loading, discount or tax component.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| quote_id | fk:Quote required | none | Owned quote | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| sequence | integer required | none | Calculation/order on source quote | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| kind | enum required | none | Premium component Allowed: base,addon,loading,discount,tax,fee,instalment_charge. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| amount | json:QuantityV1 required | none | Money or explicit unknown amount | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| basis | json:ExpressionV1 optional | NULL | Original rate/base calculation when given | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| span_id | fk:EvidenceSpan required | none | Exact quote/tax evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |
| applies_to | json:ComponentScopeV1 required | none | Person, option or component base IDs | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "CAL-01", "CAL-02"] |

Constraints: unique(quote_id,sequence); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; quote_id IS NULL OR owner_id IS NOT NULL

Indexes: quote_id,sequence

## PaymentScheduleItem

Quoted or issued instalment schedule with distinct debt status.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| quote_id | fk:Quote optional | NULL | Quoted schedule parent | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| customer_policy_id | fk:CustomerPolicy optional | NULL | Issued schedule parent | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| sequence | integer required | none | Payment ordinal | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| amount | json:QuantityV1 required | none | Payable amount | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| due_on | date optional | NULL | Scheduled due date | calendar date | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| paid_event_id | fk:PolicyEvent optional | NULL | Actual receipt evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |
| span_id | fk:EvidenceSpan required | none | Original instalment terms | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OBS-01", "INS-08"] |

Constraints: exactly one parent; unique(parent,sequence) with two partial constraints; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; quote_id IS NULL OR owner_id IS NOT NULL; customer_policy_id IS NULL OR owner_id IS NOT NULL; paid_event_id IS NULL OR owner_id IS NOT NULL

Indexes: quote_id,sequence; customer_policy_id,due_on

## TreatmentEpisode

Actual or synthetic treatment event, separate from insurer claim.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| person_id | fk:Person required | none | Treated insured subject | None | Intentionally no real customer/authentication values inspected or included. | ["INS-06", "CAL-02", "CAL-03"] |
| provider_id | fk:Provider optional | NULL | Facility branch | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| started_at | json:TemporalExtentV1 required | none | Admission/treatment date with precision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| ended_at | json:TemporalExtentV1 required | none | Discharge or unknown end | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| setting | enum required | unknown | Treatment setting Allowed: inpatient,daycare,outpatient,home,ayush,unknown. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| clinical_facts | json:ClinicalFactsV1 required | none | Diagnosis/advice/procedure assertion IDs | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| last_related_consultation | date optional | NULL | Illness episode reference event | calendar date | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| provenance | enum required | reported | Event certainty Allowed: reported,documented,case_stipulated. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |
| source_document_id | fk:DocumentVersion optional | NULL | Treatment original | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-06", "CAL-02", "CAL-03"] |

Constraints: temporal consistency; person ownership; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; person_id IS NULL OR owner_id IS NOT NULL

Indexes: owner_id,person_id; provider_id

## ExpenseLine

Item-level billed expense with clinical and event association.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| episode_id | fk:TreatmentEpisode required | none | Treatment event | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| line_number | integer required | none | Invoice line identity | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| label | text required | none | Original bill description | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| category | enum required | unknown | Reviewed cost classification Allowed: room,icu,medicine,procedure,implant,diagnostic,consultation,ambulance,consumable,other,unknown. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| service_on | date optional | NULL | Expense service date | calendar date | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| amount | json:QuantityV1 required | none | Gross billed money | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| quantity | json:QuantityV1 optional | NULL | Days or other billed units | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| relatedness_fact_id | fk:CustomerFact optional | NULL | Customer fact supporting relatedness where customer-supplied | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| span_id | fk:EvidenceSpan optional | NULL | Original bill line evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03"] |
| service_extent | json:TemporalExtentV1 required | none | Actual service interval and timestamp precision | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |

Constraints: unique(episode_id,line_number); unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; episode_id IS NULL OR owner_id IS NOT NULL; relatedness_fact_id IS NULL OR owner_id IS NOT NULL

Indexes: episode_id,line_number; category

## Claim

An insurer claim for an episode under one specific contract.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| episode_id | fk:TreatmentEpisode required | none | Treatment event | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Claimed personal terms | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| insurer_claim_id | varchar(200) optional | NULL | Issuer claim identifier | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| kind | enum required | none | Claim process type Allowed: cashless,reimbursement,preauthorization. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| status | enum required | reported | Observed insurer outcome Allowed: reported,pending,authorized,part_paid,paid,repudiated,withdrawn,unresolved. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| submitted_at | instant optional | NULL | Convenience summary of the currently accepted submission event | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| settlement_document_id | fk:DocumentVersion optional | NULL | Insurer outcome original | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |
| primary_claim_id | fk:Claim optional | NULL | First indemnity insurer selection for balance coordination | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "INS-08"] |

Constraints: authorization not final entitlement; no duplicate recovery by summing separate claims; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; episode_id IS NULL OR owner_id IS NOT NULL; customer_policy_revision_id IS NULL OR owner_id IS NOT NULL; primary_claim_id IS NULL OR owner_id IS NOT NULL

Indexes: episode_id,customer_policy_revision_id; owner_id,status

## ClaimLineAssessment

Per-insurer expense treatment with distinct monetary roles.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| claim_id | fk:Claim required | none | Insurer-specific claim | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| expense_id | fk:ExpenseLine required | none | Bill item being assessed | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| status | enum required | unknown | Item admissibility Allowed: admissible,inadmissible,conditional,unknown. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| admissible_amount | json:QuantityV1 required | none | Expense after contract exclusions/limits | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| threshold_amount | json:QuantityV1 required | none | Contribution to deductible accumulation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| cover_consumption | json:QuantityV1 required | none | Consumption of relevant cover pool | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| paid_amount | json:QuantityV1 required | none | Actual insurer payment if known | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| reason | text required | none | Specific inclusion/exclusion reason | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| policy_rule_id | fk:PolicyRule optional | NULL | Governing policy rule when curated | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| span_id | fk:EvidenceSpan optional | NULL | Original settlement or contract proof | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-02", "CAL-03", "DEC-01"] |
| revision | integer required | 1 | Immutable item-assessment revision | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03", "DEC-01"] |
| supersedes_id | fk:ClaimLineAssessment optional | NULL | Earlier assessment corrected by this revision | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03"] |

Constraints: expense belongs to claim episode; unknown is not zero; unique(claim_id,expense_id,revision);supersession is a single nonbranching chain;current selection is latest accepted revision as of decision profile revision; usage entries reference exact immutable assessment revision;correction posts reversals/new entries rather than edits; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; claim_id IS NULL OR owner_id IS NOT NULL; expense_id IS NULL OR owner_id IS NOT NULL; supersedes_id IS NULL OR owner_id IS NOT NULL

Indexes: claim_id,expense_id

## UsageEntry

Append-only signed utilization or reversal for a scoped pool.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Policy revision whose base or additional cover pool is posted | None | Synthetic design example only; no real customer value included. | ["INS-07", "CAL-03", "CAL-04"] |
| customer_policy_fact_id | fk:CustomerPolicyFact optional | NULL | Specific additional-cover fact when this posting does not use base cover | None | Synthetic design example only; no real customer value included. | ["INS-07", "CAL-03", "CAL-04"] |
| claim_line_id | fk:ClaimLineAssessment optional | NULL | Claim item causing use | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| kind | enum required | none | Accounting role Allowed: reserve,admissible_threshold,cover_use,payment,reversal,bonus_award,bonus_withdrawal. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| amount | json:QuantityV1 required | none | Signed posted quantity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| scope | json:LimitScopeV1 required | none | Exact person/illness/year/body-part scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| posted_at | instant required | none | Ledger posting time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| occurred_on | date required | none | Underlying policy event date | calendar date | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| reverses_id | fk:UsageEntry optional | NULL | Entry corrected or released | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| source_span_id | fk:EvidenceSpan optional | NULL | Insurer usage or bonus evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-03", "CAL-04", "INS-07"] |
| posting_key | uuid required | none | Stable source-event/component posting identity | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03", "OPS-02"] |
| policy_event_id | fk:PolicyEvent optional | NULL | Source policy event for nonclaim postings | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-03"] |
| claim_payment_id | fk:ClaimPayment optional | NULL | Exact disbursement that funds an insurer-payment ledger posting | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CAL-03"] |

Constraints: append-only; finite quantities only; unique(owner_id,posting_key);posting_key generated from durable source-event action and component identity;retry reuses key; one explicit source event or claim-line revision;atomic reversal sum locks original entry and prevents over-reversal; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; customer_policy_revision_id IS NULL OR owner_id IS NOT NULL; claim_line_id IS NULL OR owner_id IS NOT NULL; reverses_id IS NULL OR owner_id IS NOT NULL; policy_event_id IS NULL OR owner_id IS NOT NULL; New verified payment postings require claim_payment_id; aggregate non-reversed postings cannot exceed the known indemnity of that payment; interest and other amounts never consume cover; Claim payment corrections/reversals create new evidenced transactions and ledger reversals rather than changing historical UsageEntry amounts; customer_policy_fact_id is NULL for base-cover postings and otherwise identifies an additional_cover fact in the same revision

Indexes: customer_policy_revision_id,occurred_on; claim_line_id; reverses_id

## CorpusRevision

Immutable published knowledge manifest.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| sequence | bigint required | none | Corpus release sequence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| manifest_sha256 | char(64) required | none | Digest of exact member set and dependencies | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| state | enum required | draft | Publication state Allowed: draft,validated,published,retired,blocked. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| validated_at | instant optional | NULL | Independent closure/coverage validation | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| published_at | instant optional | NULL | Atomic publication event | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |
| previous_id | fk:CorpusRevision optional | NULL | Previous published corpus | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01", "DEC-01"] |

Constraints: sequence unique; sealed member set immutable

Indexes: state,sequence DESC

## CorpusMember

Exact terms and rule revisions included in a corpus.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| corpus_id | fk:CorpusRevision required | none | Immutable publication | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| policy_rule_id | fk:PolicyRule required | none | Exact curated policy rule revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| terms_id | fk:PolicyVersion optional | NULL | Applicable product edition | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |
| capabilities | json:CapabilityScopeV1 required | none | Supported intents, insurers and rule scopes | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "RET-01"] |

Constraints: unique(corpus_id,rule_id); all mandatory dependencies present

Indexes: corpus_id,terms_id; rule_id

## CorpusPointer

Atomic current corpus selection for one publication channel.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| channel | varchar(80) required | none | Publication channel | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| corpus_id | fk:CorpusRevision required | none | Selected immutable corpus | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| generation | bigint required | 0 | Compare-and-swap publication revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| changed_at | instant required | now | Pointer update time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |

Constraints: channel unique; production target must be published

Indexes: channel unique

## SearchChunk

Replaceable searchable derivative with exact original coverage.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentVersion required | none | Source edition | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| span_ids | json:UuidListV1 required | none | Ordered evidence spans in chunk | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| text | text required | none | Retrieval derivative text | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| lexical_vector | tsvector required | derived | PostgreSQL text-search representation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| embedding | vector(1024) optional | NULL | BGE-M3 dense vector derivative | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| index_revision | varchar(160) required | none | Tokenizer, embedding and chunking version | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| corpus_id | fk:CorpusRevision required | none | Corpus under which retrieval is allowed | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |
| chunk_sha256 | char(64) required | none | Derivative content fingerprint | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["INS-04", "RET-01", "OPS-03"] |

Constraints: unique(owner_id,corpus_id,index_revision,chunk_sha256) NULLS NOT DISTINCT; private owner filters before retrieval; equal private derivatives are separate owner records;public corpus cannot include private chunks; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes

Indexes: Public corpus BM25 via qualified pg_textsearch 1.4.0, version-qualified index and corpus/document filters; Private search uses owner-prefiltered deterministic BM25 in the replaceable retrieval adapter until private index isolation is proven; GIN lexical_vector is only lexical fallback/diagnostics and never labelled BM25; HNSW embedding vector_cosine_ops for public corpus; exact cosine over owner-prefiltered private candidates; document_id

## Artifact

Stable dependency identity for immutable inputs and outputs.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| kind | enum required | none | Typed artifact class Allowed: customer_statement,customer_fact,customer_requirement,message,customer_profile_revision,terms,rule,document,quote,provider_observation,decision,calculation,model_qualification,corpus,search_chunk,processing_output,model_response,contract_revision,individual_term,coverage_layer,usage_entry,claim_event,claim_document_requirement,claim_document_receipt,claim_payment,inventory_item,inventory_revision,inventory_membership,inventory_lineage,inventory_support,coverage_report,terms_component,contract_bundle_revision,contract_bundle_member,policy_event. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| object_id | uuid required | none | Typed target row UUID | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| content_sha256 | char(64) required | none | Immutable target digest | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| validity | enum required | current | Whether valid for current reuse Allowed: current,stale,blocked,erased. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| invalidated_at | instant optional | NULL | First invalidation event | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |

Constraints: unique(kind,object_id); typed target existence and owner trigger; no arbitrary table names; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; New claim artifact kinds resolve to exact owner-bound ClaimEvent/ClaimDocumentRequirement/ClaimDocumentReceipt/ClaimPayment; inventory/coverage artifact kinds resolve only to public immutable inventory/review/report rows

Indexes: kind,object_id; validity

## Dependency

Input dependency used for replay and selective invalidation.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| dependent_id | fk:Artifact required | none | Computed artifact | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| input_id | fk:Artifact required | none | Exact input artifact | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| purpose | enum required | none | Why input is necessary Allowed: facts,applicability,rule,evidence,quote,provider,model,corpus. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| material | boolean required | true | Whether invalidity blocks dependent reuse | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |
| reason | text required | none | Specific dependency scope | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "OPS-03"] |

Constraints: unique(dependent_id,input_id,purpose); no self/cycles in computed graph; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes

Indexes: input_id; dependent_id

## Decision

Validated adviser outcome for exact inputs and evidence.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Customer context | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| turn_id | fk:Turn required | none | Owning processing turn | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| advice_request_id | fk:AdviceRequest required | none | Customer advice goal answered | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| profile_revision_id | fk:CustomerProfileRevision required | none | Exact customer profile evaluated | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| corpus_id | fk:CorpusRevision required | none | Immutable knowledge inputs | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| outcome | enum required | none | Answer completeness state Allowed: complete,conditional,clarification,insufficient_evidence,technical_failure. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| answer_text | text required | none | Validated rendered answer | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| scope | json:DecisionScopeV1 required | none | Precisely answered question and unresolved remainder | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| validation | json:ValidationV1 required | none | Claim support and material correctness results | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| published_at | instant optional | NULL | User-visible publication time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| validity | enum required | current | Current replay validity Allowed: current,stale,blocked,erased. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |
| supersedes_id | fk:Decision optional | NULL | Prior answer revised by correction | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "RET-01"] |

Constraints: one published decision per successful turn; publication fact CAS; critical errors block; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; Deferred constraint triggers validate conversation/subject/predicate/revision/contract lineage against referenced rows; FOR KEY SHARE locks and immutable target identities prevent races; see relationships-and-lifecycle.md; conversation_id IS NULL OR owner_id IS NOT NULL; turn_id IS NULL OR owner_id IS NOT NULL; advice_request_id IS NULL OR owner_id IS NOT NULL; profile_revision_id IS NULL OR owner_id IS NOT NULL; supersedes_id IS NULL OR owner_id IS NOT NULL

Indexes: conversation_id,created_at DESC; turn_id; validity

## DecisionClaim

One independently supported statement or candidate disposition.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| decision_id | fk:Decision required | none | Answer artifact | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| ordinal | integer required | none | Claim order | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| text | text required | none | Exact supported assertion | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| kind | enum required | none | Statement type Allowed: fact,eligibility,exclusion,calculation,comparison,clarification,limitation. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| critical | boolean required | true | Material correctness flag | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| support | enum required | unverified | Evidence validation result Allowed: supported,conditional,unsupported,conflicted. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| candidate_configuration_id | fk:ProductVariant optional | NULL | Candidate to which statement applies | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |
| missing_dependency | text optional | NULL | Precise unresolved condition and effect | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-05"] |

Constraints: unique(decision_id,ordinal); unsupported critical claim cannot publish; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; decision_id IS NULL OR owner_id IS NOT NULL

Indexes: decision_id,ordinal

## ClaimCitation

Original support attached to one answer claim.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| claim_id | fk:DecisionClaim required | none | Supported statement | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| span_id | fk:EvidenceSpan required | none | Exact original citation target | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| role | enum required | none | Support relationship Allowed: supports,restricts,excepts,conflicts,assumption_source. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| policy_rule_id | fk:PolicyRule optional | NULL | Interpreted policy rule connecting original to claim | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |
| ordinal | integer required | none | Display order | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["DEC-01", "INS-04"] |

Constraints: unique(claim_id,span_id,role); all cited originals accessible to owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; claim_id IS NULL OR owner_id IS NOT NULL

Indexes: claim_id,ordinal; span_id

## Calculation

Independent deterministic result with complete trace.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| decision_id | fk:Decision required | none | Owning answer | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| label | varchar(200) required | none | Calculation purpose | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| engine_version | varchar(120) required | none | Deterministic evaluator identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| expression | json:ExpressionV1 required | none | Typed calculation AST | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| inputs | json:CalculationInputsV1 required | none | Values, units and assertion/span references | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| result | json:TypedValueV1 required | none | Computed result or unknown | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| trace | json:CalculationTraceV1 required | none | Ordered intermediate results and rule applications | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| assumptions | json:AssumptionsV1 required | none | Explicit hypothetical and unresolved premises | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| scope | enum required | none | Meaning of result Allowed: hypothetical,threshold_only,conditional_payable,verified_entitlement. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |
| verified_by | varchar(160) optional | NULL | Independent method/reviewer identifier | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["CAL-01", "CAL-02", "CAL-03", "DEC-01"] |

Constraints: deterministic hash/replay check; complete result requires known inputs; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; decision_id IS NULL OR owner_id IS NOT NULL

Indexes: decision_id

## Turn

Durable unit of customer work owned by a worker.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| conversation_id | fk:Conversation required | none | Persistent context | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| request_id | uuid required | none | Idempotent customer request | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| payload_sha256 | char(64) required | none | Canonical request hash | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| input_message_id | fk:Message required | none | Persisted customer input | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| expected_revision | bigint required | none | Requested accepted fact revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| profile_revision_id | fk:CustomerProfileRevision required | none | Exact customer profile fixed before dispatch | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| state | enum required | queued | Durable processing outcome Allowed: queued,running,cancel_requested,cancelled,completed,failed,stale. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| lease_token | uuid optional | NULL | Current worker fencing token | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| lease_until | instant optional | NULL | Lease expiry | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| deadline | instant required | none | Bounded turn deadline | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| cancelled_at | instant optional | NULL | Accepted cancellation event | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |
| error_code | varchar(100) optional | NULL | Explicit technical failure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-04"] |

Constraints: unique(owner_id,request_id); one active turn per conversation or explicitly serialized revisions; fenced publication; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; conversation_id IS NULL OR owner_id IS NOT NULL; input_message_id IS NULL OR owner_id IS NOT NULL; profile_revision_id IS NULL OR owner_id IS NOT NULL

Indexes: state,lease_until; conversation_id,created_at

## TurnEvent

Durable ordered stream event reused by reconnecting clients.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn required | none | Owning work item | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| sequence | bigint required | none | Monotonic replay cursor | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| kind | enum required | none | Durable event class Allowed: queued,started,clarification,progress,decision,cancelled,failed,stale. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| payload | json:TurnEventV1 required | none | Safe UI event content/reference | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |
| recorded_at | instant required | now | Event commit time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02"] |

Constraints: unique(turn_id,sequence); append-only except authorized erasure; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; turn_id IS NULL OR owner_id IS NOT NULL

Indexes: turn_id,sequence

## Outbox

Transactional dispatch/event publication awaiting delivery.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| topic | enum required | none | Dispatch destination Allowed: turn,processing,invalidation,deletion,publication. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| aggregate_id | uuid required | none | Typed target key determined by topic | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| idempotency_key | varchar(200) required | none | Stable delivery deduplication key | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| payload | json:OutboxPayloadV1 required | none | Minimal dispatch reference | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| state | enum required | pending | Delivery state Allowed: pending,leased,delivered,failed. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| attempt_count | integer required | 0 | Explicit dispatch tries | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| available_at | instant required | now | Earliest retry time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| lease_until | instant optional | NULL | Dispatcher recovery lease | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |
| last_error_code | varchar(100) optional | NULL | Safe transport failure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-02", "OPS-03"] |

Constraints: unique(topic,idempotency_key); persist in same transaction as work; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes

Indexes: state,available_at; lease_until

## ModelRoute

Exact immutable shared relay/model route configuration.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| route_key | varchar(120) required | none | Stable route identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| endpoint_profile | varchar(120) required | none | Secret-free configured relay reference | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| requested_model | varchar(160) required | none | Exact required model identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| adapter_version | varchar(120) required | none | Strict adapter implementation identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| configuration_sha256 | char(64) required | none | Secret-free model/adapter settings digest | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| status | enum required | unqualified | User availability Allowed: unqualified,qualified,disabled. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |

Constraints: route_key unique; immutable route revisions

Indexes: status,route_key

## ModelQualification

Evidence of actual schema and capability qualification.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| route_id | fk:ModelRoute required | none | Qualified route revision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| schema_name | enum required | none | Actual use schema Allowed: fact_interpretation,extraction,review,answer. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| schema_sha256 | char(64) required | none | Exact tested JSON schema | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| observed_model | varchar(160) required | none | Actual returned model identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| capabilities | json:QualificationV1 required | none | Context/image/structured output checks used | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| qualified_at | instant required | none | Qualification time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| result | enum required | none | Qualification outcome Allowed: passed,failed,expired. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |
| artifact_sha256 | char(64) required | none | Stored qualification evidence digest | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04"] |

Constraints: route/schema/capability changes invalidate prior qualification

Indexes: route_id,schema_name,qualified_at DESC

## ModelAttempt

Every provider call, failure and usage record.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| turn_id | fk:Turn optional | NULL | Adviser call context | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| processing_job_id | fk:ProcessingJob optional | NULL | Corpus call context | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| qualification_id | fk:ModelQualification required | none | Qualified exact route/schema | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| attempt_number | integer required | none | Explicit call ordinal | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| started_at | instant required | none | Request start | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| completed_at | instant optional | NULL | Provider completion | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| observed_model | varchar(160) optional | NULL | Actual response identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| status | enum required | started | Provider call result Allowed: started,succeeded,timeout,transport_error,schema_error,identity_error,cancelled,indeterminate. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| usage | json:UsageV1 required | none | Reported token counts and measured latency | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| error_code | varchar(100) optional | NULL | Safe operational failure category | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| request_sha256 | char(64) required | none | Canonical request fingerprint | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |
| response_artifact_key | varchar(500) optional | NULL | Private safely retained structured response | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-04", "OPS-02"] |

Constraints: exactly one parent; attempt state cannot swallow operational failure; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; turn_id IS NULL OR owner_id IS NOT NULL

Indexes: turn_id,attempt_number; processing_job_id,attempt_number; status

## ProcessingJob

Resumable original reading/extraction/review task.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| document_id | fk:DocumentVersion required | none | Preserved input original | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| stage | enum required | none | Replaceable processing step Allowed: classify,read,ocr,extract,validate,independent_review,reconcile. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| adapter_version | varchar(160) required | none | Reader/model pipeline identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| input_sha256 | char(64) required | none | Input bytes/parameters digest | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| attempt_number | integer required | 1 | Initial or targeted retry | count | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| parent_job_id | fk:ProcessingJob optional | NULL | Previous targeted attempt | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| state | enum required | queued | Recoverable stage status Allowed: queued,running,succeeded,failed,blocked,cancelled. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| lease_until | instant optional | NULL | Worker recovery deadline | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| lease_token | uuid optional | NULL | Stale-worker fencing identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| result_blob_id | fk:OriginalFile optional | NULL | Preserved processing result file pending the later processing-artifact review | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| issues | json:ProcessingIssuesV1 required | empty array | Omissions/errors and targeted retry requirements | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |
| error_code | varchar(100) optional | NULL | Explicit technical failure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03"] |

Constraints: unique(document_id,stage,input_sha256,attempt_number); initial plus2 targeted retries; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; result_blob_id is an operational result file and can never establish contractual source truth

Indexes: state,lease_until; document_id,stage

## ReviewRecord

Independent review and its bounded approval scope.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| artifact_id | fk:Artifact required | none | Exact reviewed immutable target | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewer_account_id | fk:Account optional | NULL | Human reviewer if applicable | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewer_identity | varchar(160) required | none | Independent human/agent/version role | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| scope | text required | none | What was and was not checked | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| outcome | enum required | none | Review disposition Allowed: approved,rejected,changes_requested,incomplete. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| findings | json:ReviewFindingsV1 required | none | Material findings and resolution evidence | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |
| reviewed_at | instant required | none | Review time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-03", "OPS-04", "OPS-06"] |

Constraints: review does not imply design/cutover authorization; immutable; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes

Indexes: artifact_id,reviewed_at DESC

## ConsentRecord

Specific customer authorization and revocation history.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| person_id | fk:Person optional | NULL | Person whose data/action consent concerns | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "CUS-01"] |
| purpose | enum required | none | Consent scope Allowed: medical_share,abha_creation,optional_processing,representation. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| recipient | varchar(250) optional | NULL | Specific authorized recipient | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| instance_key | uuid required | none | Single consent transaction identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| status | enum required | requested | Consent state Allowed: requested,granted,revoked,expired. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| source_message_id | fk:Message optional | NULL | Exact customer authorization | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| source_span_id | fk:EvidenceSpan optional | NULL | Documented authority/consent | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| valid_until | instant optional | NULL | Explicit expiry | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |
| revoked_at | instant optional | NULL | Withdrawal event | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "CUS-01"] |

Constraints: granted requires explicit provenance; instance_key unique within owner; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; person_id IS NULL OR owner_id IS NOT NULL; source_message_id IS NULL OR owner_id IS NOT NULL

Indexes: owner_id,purpose,status

## DeletionRequest

Durable erasure workflow and approved scope.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| scope | json:DeletionScopeV1 required | none | Account/conversation/person/artifact deletion targets | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| requested_at | instant required | none | Request receipt | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| state | enum required | pending | Erasure progress Allowed: pending,blocked_by_hold,running,completed,failed. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| completed_at | instant optional | NULL | Verified erasure completion | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| verification | json:DeletionVerificationV1 required | none | Store-level erasure evidence without medical values | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| error_code | varchar(100) optional | NULL | Explicit erasure failure | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |

Constraints: completed requires verification of all scope targets; account record anonymized/purged after final receipt policy; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes

Indexes: owner_id,state

## RetentionHold

Explicit approved exception to deletion; no invented retention period.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| deletion_request_id | fk:DeletionRequest required | none | Affected deletion | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| scope | json:DeletionScopeV1 required | none | Precisely retained subset | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| basis | text required | none | Verified legal/contractual basis | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| approved_by_id | fk:Account optional | NULL only after authorized actor erasure | Authorized human decision | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| expires_at | instant required | none | Bounded hold expiry/review date | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |
| released_at | instant optional | NULL | Hold release | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01"] |

Constraints: hold cannot retain unrelated targets; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; deletion_request_id IS NULL OR owner_id IS NOT NULL

Indexes: deletion_request_id; expires_at

## AuditEvent

Minimal authorization and lifecycle audit without copied medical values.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| actor_id | fk:Account optional | NULL | Authenticated actor if retained | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| operation | varchar(100) required | none | Authorized action category | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| object_kind | varchar(100) required | none | Target resource type | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| object_id | uuid optional | NULL | Target identity if retention allows | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| occurred_at | instant required | now | Audit event time | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| outcome | enum required | none | Action result Allowed: allowed,denied,succeeded,failed. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |
| metadata | json:AuditMetadataV1 required | empty object | Safe request/revision/error metadata | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-02", "OPS-06"] |

Constraints: no personal content in metadata; append-only with explicit retention purge; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes

Indexes: owner_id,occurred_at; operation,occurred_at

## LegacyMapping

Lossless migration identity and unresolved semantic translations.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 for new records; preserve original UUID during migration | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this row was first recorded | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| owner_id | fk:Account optional | none | Account whose authorization governs this row | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| source_table | varchar(150) required | none | Pilot model/table | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| source_key | varchar(250) required | none | Original PK/compound identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| source_sha256 | char(64) required | none | Canonical preserved record fingerprint | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| target_kind | varchar(150) optional | NULL | Approved replacement target | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| target_id | json:TargetKeyV1 optional | NULL | Replacement identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| status | enum required | preserved_unmapped | Translation safety Allowed: preserved_unmapped,mapped,quarantined,erased. | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| reason | text required | none | Mapping evidence or unsafe limitation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| migration_run_key | varchar(160) required | none | Rehearsal/cutover manifest identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-06"] |
| archive_blob_id | fk:OriginalFile required | none | Preserved exact legacy source-record payload | None | No authentic private value inspected; see synthetic worked examples. | ["OPS-06"] |

Constraints: unique(migration_run_key,source_table,source_key); unmapped source payload kept in private immutable archive; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; archive_blob_id retains the exact legacy payload with matching owner;an archive is not contractual source evidence;erased source payload cannot reimport

Indexes: migration_run_key,status; target_kind,target_id

## AuthGroup

Existing Django privilege group identity.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| name | varchar(150) required | none | Permission group name | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: name unique

Indexes: name unique

## AuthPermission

Django model permission identity preserved semantically.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| codename | varchar(100) required | none | Permission operation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| name | varchar(255) required | none | Human-readable permission label | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| content_type_id | fk:ContentType required | none | Native Permission content-type relationship | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "OPS-06"] |

Constraints: unique(content_type_id,codename);native AutoField primary key

Indexes: content_type_id,codename

## AccountGroup

Explicit account group membership.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | bigint required | preserve native primary key; framework sequence for new rows | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| user_id | fk:Account required | none | Native user_id through-table FK, logically the account owner | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| group_id | fk:AuthGroup required | none | Granted privilege group | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(user_id,group_id)

Indexes: user_id,group_id

## AccountPermission

Explicit account permission grant.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | bigint required | preserve native primary key; framework sequence for new rows | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| user_id | fk:Account required | none | Native user_id through-table FK, logically the account owner | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01"] |
| permission_id | fk:AuthPermission required | none | Granted model permission | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(user_id,permission_id)

Indexes: user_id,permission_id

## GroupPermission

Permission granted to a group.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | integer required | preserve native primary key; framework sequence for new rows | Stable row identity | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| group_id | fk:AuthGroup required | none | Privilege group | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| permission_id | fk:AuthPermission required | none | Granted operation | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: unique(group_id,permission_id)

Indexes: group_id,permission_id

## AuthSession

Existing signed Django session retained with compatible settings.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| session_key | varchar(40) required | none | Django session primary lookup key | None | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |
| session_data | text required | none | Django signed session payload | None | Intentionally no real customer/authentication values inspected or included. | ["OPS-01", "OPS-06"] |
| expire_date | instant required | none | Session expiry | instant | No authentic field value established in reviewed evidence; synthetic examples only in worked-examples.md. | ["OPS-01", "OPS-06"] |

Constraints: session_key primary key; native signed Django semantics; authenticated session resolves account before private data retrieval

Indexes: session_key unique; expire_date

## ContentType

Native Django model content-type identity.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | integer required | native sequence | Native AutoField primary key | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| app_label | varchar(100) required | none | Application label | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| model | varchar(100) required | none | Model name | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |

Constraints: primary key(id);unique(app_label,model)

Indexes: app_label,model

## AdminLogEntry

Preserved Django administration audit, with privacy review of free text.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | integer required | native sequence | Native LogEntry AutoField PK | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| action_time | instant required | none | Native action timestamp | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| user_id | fk:Account required | none | Acting administrator | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| content_type_id | fk:ContentType optional | NULL | Native acted-on model | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| object_id | text optional | NULL | Native target string key | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| object_repr | varchar(200) required | empty string | Native target display text | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| action_flag | smallint required | none | Native add/change/delete flag | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-06"] |
| change_message | text required | empty string | Native admin change detail | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |

Constraints: native Django semantics;privileged access;explicit erasure mapping

Indexes: action_time;user_id

## ContentCopy

Inventory of where a private assertion payload was copied or transformed.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs | Stable row identity | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "DEC-01"] |
| created_at | instant required | now | Row recording time | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01", "DEC-01"] |
| owner_id | fk:Account required | none | Account authorization boundary | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| source_artifact_id | fk:Artifact required | none | Original private assertion/content lineage | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| destination_artifact_id | fk:Artifact required | none | Stored derived artifact containing the content | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| storage_kind | enum required | none | Physical copy class Allowed: postgres,original_storage,search_index,cache,queue,model_response,export,backup. | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| locator | varchar(500) required | none | Opaque store/location or JSON-path identity | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| state | enum required | present | Copy erasure state Allowed: present,redacted,erased,held. | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| generation | bigint required | 0 | Erasure/rebuild fencing generation | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |

Constraints: unique(source_artifact_id,destination_artifact_id,storage_kind,locator);material copy must register before publication/dispatch; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes

Indexes: source_artifact_id,state;destination_artifact_id

## ExpenseAllocation

Original-backed allocation of an expense across package/time/scope boundaries.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs | Stable row identity | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02", "CAL-03"] |
| created_at | instant required | now | Row recording time | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02", "CAL-03"] |
| owner_id | fk:Account required | none | Account authorization boundary | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OPS-01"] |
| expense_id | fk:ExpenseLine required | none | Original bill line | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| package_parent_id | fk:ExpenseLine optional | NULL | Containing package line if present | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| kind | enum required | none | Reason for allocation Allowed: included_in_package,separate_payable,excluded_component,time_split,scope_split. | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| amount | json:QuantityV1 required | none | Allocated money or unresolved amount | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-01"] |
| service_extent | json:TemporalExtentV1 required | none | Portion service time | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| boundary_fact_id | fk:CustomerFact optional | NULL | Customer fact supporting the allocation boundary when customer-supplied | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| effects | json:AllocationEffectsV1 required | none | Billing/admissibility/cap accounting membership | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| source_span_id | fk:EvidenceSpan optional | NULL | Original allocation authority | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |
| status | enum required | none | Allocation certainty Allowed: stipulated,verified,unresolved. | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["CAL-02"] |

Constraints: no package cycles;sum of nonoverlapping finite allocations <= original amount; a portion may have multiple accounting roles but is counted once per role/pool;unknown residual is not zero; unique(id,owner_id);owner_id immutable;deferred relationship checks also run on target updates/deletes; expense_id IS NULL OR owner_id IS NOT NULL; package_parent_id IS NULL OR owner_id IS NOT NULL; boundary_fact_id IS NULL OR owner_id IS NOT NULL

Indexes: expense_id;package_parent_id

## Clinician

Original-backed clinician identity scoped independently of facility names.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4; preserve existing IDs | Stable row identity | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| created_at | instant required | now | Row recording time | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| name | varchar(250) required | none | Printed practitioner name | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| registration_identifiers | json:IdentifiersV1 required | empty array | Medical registry identifiers and provenance | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |
| speciality | varchar(200) optional | NULL | Reported specialty | None | Synthetic design fixture only; authentic personal value unavailable/uninspected. | ["OBS-02"] |

Constraints: no name-only automatic merge

Indexes: name

## ClaimEvent

A claim-process event, or mandatory hospitalization notice before any claim exists, with exact actor, recipient and evidence time.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CUS-02", "CAL-02", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this record was first stored | instant | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs every private value | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim optional | NULL | Exact claim involved; absent only for a pre-claim hospitalization notice | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| episode_id | fk:TreatmentEpisode required | none | Treatment episode that the communication or payment concerns | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision required | none | Personal contract revision to which this event was addressed | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| event_key | uuid required | none | Stable identity of one real-world event across corrections | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 | Append-only revision number for that event | count | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| kind | enum required | none | Actual procedural event; events do not imply contractual admissibility Allowed: hospitalization_notice,claim_submitted,claim_received,document_requested,document_received,documentation_complete,documentation_incomplete,decision_issued,payment_made,payment_received,claim_due_confirmed,communication_received. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| occurred_at | json:TemporalExtentV1 required | none | Actual event time, date or explicitly uncertain interval | temporal extent | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| sender | json:ClaimPartyV1 required | none | Party sending or performing the event | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| recipient | json:ClaimPartyV1 required | none | Party receiving the communication or payment | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| certainty | enum required | reported | Evidence status of this event revision Allowed: reported,verified,disputed,retracted. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_span_id | fk:EvidenceSpan optional | NULL | Exact event evidence, distinct from the rule describing a deadline | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_message_id | fk:Message optional | NULL | Customer report or correction of this event | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| related_event_id | fk:ClaimEvent optional | NULL | Specific request, dispatch or other event connected to this one | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| documentation | json:ClaimDocumentationV1 optional | NULL | Explicit completeness assessment and exact requirement/receipt revisions | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimEvent optional | NULL | Previous version corrected by this event record | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |

Constraints: unique(owner_id,event_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; At least one source_span_id or source_message_id is required; claim_id required except hospitalization_notice; pre-claim notices bind episode and contract without manufacturing a submitted Claim; All cross-record claim/episode/contract identity checks use deferred constraint triggers and target key-share locks; documentation_complete requires documentation.status complete; documentation_incomplete requires incomplete or disputed; other event kinds cannot carry a completeness conclusion; Verified documentation completeness requires the exact active necessary requirements, matched receipts, original/accepted exception rules and recipient authority; ambiguity remains disputed; it is not inferred from number of uploaded files; Corrections invalidate dependent calculations/decisions; related pre-claim notice can later be linked by a new claim-bound communication without rewriting the historical notice; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules

Indexes: claim_id,kind,created_at; episode_id,customer_policy_revision_id,kind; owner_id,event_key,revision

## ClaimDocumentRequirement

An immutable claim-specific version of a required or disputed document and the authority for its necessity or accepted form.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "INS-04", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this record was first stored | instant | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs every private value | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none | Claim whose documentary condition is assessed | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| requirement_key | varchar(160) required | none | Stable identity of one document requirement within the claim | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 | Requirement revision number | count | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| document_kind | varchar(160) required | none | Registered required evidence category | None | {'value': 'original bills', 'authentic': True, 'source': '../registers/independent-original-inventory-star-ssf-r6.json', 'locator': 'V.17 original claim-document requirement'} | ["INS-09"] |
| necessity | enum required | unknown | Adjudicated necessity; requests alone do not establish every item is contractually necessary Allowed: required,conditional,not_required,disputed,unknown. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| condition | json:PredicateV1 optional | NULL | Exact conditions under which the requirement applies | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| accepted_form | enum required | unspecified | Required or accepted documentary form and certification scope Allowed: original,certified_copy,ordinary_copy,electronic,unspecified. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| request_event_id | fk:ClaimEvent optional | NULL | Specific insurer or TPA request event, if any | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| policy_rule_id | fk:PolicyRule optional | NULL | Applicable original-backed document requirement or exception | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| authority_span_id | fk:EvidenceSpan optional | NULL | Exact clause, certification requirement or accepted written exception | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| reason | text required | none | Why this requirement is necessary, conditional or disputed | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimDocumentRequirement optional | NULL | Prior requirement version | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| certainty | enum required | reported | Evidence strength of the assessed necessity and accepted form Allowed: reported,verified,disputed. | None | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(claim_id,requirement_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; At least one request_event_id, rule_id or authority_span_id is required; conditional necessity requires condition; other necessity states cannot imply unconditional document completeness; Every revision is immutable; changing necessity/form does not erase a past request or receipt; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Verified necessity/form requires applicable original or accepted exception authority, not merely the existence of a document request. Reported or disputed necessity blocks verified completeness until resolved

Indexes: claim_id,necessity; claim_id,requirement_key,revision

## ClaimDocumentReceipt

A specific delivery of a document to a named claim-processing recipient; repeats and corrected receipt times remain distinct.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "INS-04", "CUS-02"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this record was first stored | instant | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs every private value | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none | Claim receiving this document | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| receipt_event_id | fk:ClaimEvent required | none | Exact receipt event and recipient | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| requirement_id | fk:ClaimDocumentRequirement optional | NULL | Exact requirement version this delivery may satisfy | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| document_id | fk:DocumentVersion optional | NULL | Exact delivered original bytes if acquired | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| description | text required | none | Reported document identity when bytes or filename alone are insufficient | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| delivered_form | enum required | unknown | Actual delivered form; compared with accepted form Allowed: original,certified_copy,ordinary_copy,electronic,unknown. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| assessment | enum required | unassessed | Whether this delivery satisfies the named requirement Allowed: matched,insufficient,disputed,unassessed. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| assessment_span_id | fk:EvidenceSpan optional | NULL | Proof of certification, acceptance or deficiency | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| supersedes_id | fk:ClaimDocumentReceipt optional | NULL | Prior classification or identity correction of the same delivery | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 | Version of this logical delivery or payment assertion | count | No authentic private/database value established; proposal representation only. | ["INS-09"] |
| receipt_key | uuid required | none | Stable identity of one delivered item across classification or timing corrections | None | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(owner_id,receipt_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; Matched assessment requires a named applicable requirement and evidence of correct form/content; a reported delivery with no actual content remains unassessed unless authenticated acceptance explicitly establishes sufficiency; Receipt time lives only on its referenced immutable ClaimEvent revision; retransmission is a distinct event, not an overwrite; No completion or last-necessary-document date is inferred until exact requirement and receipt revisions are assessed together; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Supersession keeps owner/claim/receipt_key and receipt event logical lineage; changing classification creates a new version even when document_id and requirement_id remain unchanged; Multiple unclassified documents in one batch may have distinct receipt_keys even when document_id and requirement_id are both NULL

Indexes: claim_id,requirement_id; receipt_event_id; document_id

## ClaimPayment

An evidenced claim disbursement or reversal, retaining actual payment timing and separate indemnity, interest and other components.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09", "CAL-01", "CAL-03", "DEC-01"] |
| created_at | timestamptz required | transaction timestamp at insertion | When this record was first stored | instant | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-06"] |
| owner_id | fk:Account required | none | Account whose authorization governs every private value | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["OPS-01"] |
| claim_id | fk:Claim required | none | Claim whose liability this payment addresses | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payment_key | varchar(200) required | none | Stable owner-scoped identity for this payment transaction | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payment_event_id | fk:ClaimEvent required | none | Evidenced payment execution or receipt event | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| kind | enum required | disbursement | Payment or explicitly evidenced reversal Allowed: disbursement,reversal. | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| payee | json:ClaimPartyV1 required | none | Actual recipient, distinct from proposer/insured by default | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| total | json:QuantityV1 required | none | Total transferred amount | money | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| indemnity | json:QuantityV1 required | none | Principal claim-payment component | money | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| interest | json:QuantityV1 required | none | Separate interest component | money | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| other | json:QuantityV1 required | none | Other separately classified payment component | money | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| transaction_reference | text optional | NULL | Original transaction reference if available | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| source_span_id | fk:EvidenceSpan required | none | Actual payment amount/component evidence | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| reverses_id | fk:ClaimPayment optional | NULL | Original payment transaction partially or fully reversed | None | No authentic customer/event/database value established; this proposal does not invent an issued customer record. | ["INS-09"] |
| revision | integer required | 1 | Version of this logical delivery or payment assertion | count | No authentic private/database value established; proposal representation only. | ["INS-09"] |
| supersedes_id | fk:ClaimPayment optional | NULL | Corrected assertion about the same actual payment, distinct from a physical reversal | None | No authentic private/database value established; proposal representation only. | ["INS-09"] |

Constraints: unique(owner_id,payment_key,revision); unique(supersedes_id) WHERE supersedes_id IS NOT NULL; Known components must sum exactly to total; partial unknown components remain unknown rather than balancing inventions; kind reversal iff reverses_id is present; source payment and accumulated reversals are locked before validation; Each partial payment has distinct event, recipient and transaction identity; current claim status is not payment evidence; Indemnity alone can feed UsageEntry cover-payment postings; interest/other are not insured-sum consumption or threshold accumulation; unique(id,owner_id); owner immutable; all private FKs enforce matching owner and immutable target identity; Append-only revisions except authorized erasure; copied payloads and dependent decisions follow existing ContentCopy/DeletionRequest rules; Correcting a recorded amount/time/payee appends a same-key version and invalidates dependent ledger/decision inputs; it does not invent a bank reversal. kind reversal represents a separate evidenced financial transaction; Select one current version per payment_key for current accounting; historical reports retain exact prior versions. Revalidation/reposting uses bookkeeping reversal entries under the same logical-payment lock, preventing old and corrected versions being counted twice; Every ClaimPayment insertion, correction or authorized erasure locks the exact Claim parent FOR UPDATE before reading or changing its payment set. Use READ COMMITTED with a fresh validation statement after acquiring the lock; validate current logical versions and net reversal balances together. A corrected original below established reversals cannot publish as consistent accounting until the discrepancy is explicitly resolved. Historical versions remain intact.

Indexes: claim_id,payment_event_id; reverses_id; owner_id,payment_key

## TermsComponent

An original-backed component slot in a specific public combi edition; component legal identity and benefits remain separate.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp | Assertion insertion time, separate from contractual effective time | instant | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| wrapper_terms_id | fk:PolicyVersion required | none | Exact public combi edition defining this component slot | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| slot_code | varchar(80) required | none | Stable slot within this wrapper edition | None | health or life; design-assigned codes for original COMBI13-A, not insurer-issued codes | ["INS-10"] |
| component_product_id | fk:Product required | none | Separately issued component product and issuer | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| component_terms_id | fk:PolicyVersion optional | NULL | Independently established component edition, if available | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| asserted_component_uin | varchar(100) optional | NULL | Identifier explicitly asserted by the wrapper source | None | Health Premier ZUKHLIP25054V052425; Kotak Term Plan107N005V06, source26c72de9… COMBI13-A | ["INS-10"] |
| role | enum required | unresolved | Component role; does not expand the selected medical-insurer roster Allowed: medical,life,other,unresolved. | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_kind | enum required | unresolved | Whether this wrapper requires or permits the component Allowed: required,optional,conditional,unresolved. | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_policy_rule_id | fk:PolicyRule optional | NULL | Connected selection condition for conditional membership | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan required | none | Original supporting wrapper/component association | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| status | enum required | unresolved | Association review state; reviewed identity does not mean complete component terms Allowed: unresolved,reviewed,conflict. | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| supersedes_id | fk:TermsComponent optional | NULL | Prior association from an earlier wrapper edition | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(wrapper_terms_id,slot_code); component_terms_id, when present, belongs to component_product_id; asserted UIN disagreement sets conflict and blocks affected publication; conditional membership requires a public same-wrapper selection rule; All source spans and linked rules are public; do not manufacture a separately issued component wording from a wrapper title; Published component edges are immutable; changing an edge creates a new wrapper terms edition and invalidates dependent artifacts; No composition cycle, including cycles through resolved component terms; closure is checked before publication

Indexes: wrapper_terms_id,slot_code; component_product_id,component_terms_id; supersedes_id

## ContractBundle

Stable owned identity for a package of component policies, without inventing a third policy contract or sole issuer.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp | Assertion insertion time, separate from contractual effective time | instant | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none | Owner governing all private bundle records | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| label | varchar(250) required | none | Owner-facing package label | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| external_reference | varchar(200) optional | NULL | Issuer package reference if actually supplied | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| current_revision_id | fk:ContractBundleRevision optional | NULL | Current accepted bundle interpretation | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(id,owner_id); immutable owner; Current revision pointer targets a revision of this same bundle and owner; updates are fenced by expected revision; No global unique external reference; private erasure includes revisions, membership, subject facts, artifacts and all copies; current_revision_id can target only a sealed revision with matching owner and bundle_id; head CAS checks expected prior revision.

Indexes: owner_id,created_at; owner_id,current_revision_id

## ContractBundleRevision

Immutable owner-scoped interpretation of a package version, component membership and status, retained when customer facts or sources change.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp | Assertion insertion time, separate from contractual effective time | instant | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none | Owner governing all private bundle records | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| bundle_id | fk:ContractBundle required | none | Stable package being interpreted | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| revision | bigint required | none | Monotonic bundle revision | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| wrapper_configuration_id | fk:ProductVariant optional | NULL | Selected public wrapper version/options if resolved | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| previous_id | fk:ContractBundleRevision optional | NULL | Previous immutable interpretation | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| membership_state | enum required | unresolved | Whether actual component membership is known; stipulated is research-only Allowed: unresolved,partial,stipulated,verified. | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| status | enum required | unresolved | Package status assertion; never inferred from explanation of a cancellation consequence Allowed: proposed,in_force,expired,cancelled,separated,unresolved. | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan optional | NULL | Issued package evidence, when supplied | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| sealed_at | timestamptz optional | NULL | End of the short atomic revision construction transaction | instant | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| membership_sha256 | char(64) optional | NULL | Digest of canonical exact wrapper configuration and complete ordered member records | None | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |
| seal_format_version | smallint required | 1 | Version of canonical package-member serialization | None | Synthetic proposal metadata only; no actual customer event or issued acceptance inspected. | ["INS-10", "INS-08", "OPS-02"] |

Constraints: unique(id,owner_id); owner immutable; unique(bundle_id,revision); Verified membership requires wrapper configuration, private issued evidence and exactly one resolved member disposition for every required/selected applicable slot; conditional/unknown selection blocks closure; Stipulated membership is allowed only in explicit research fixtures and never production verified acceptance; A verified cancelled status requires insurer-event evidence; a request, rule consequence or model response alone is insufficient; Sealing members and moving bundle current_revision pointer occur atomically in one short transaction; old turns cannot advance the pointer; Previous and current revision ownership and bundle lineage checked by deferred constraint triggers under key-share and bundle row locks; CHECK((sealed_at IS NULL)=(membership_sha256 IS NULL)); seal_format_version=1. Deferred commit trigger rejects any persisted unsealed revision, including a revision not yet referenced by the bundle head.; A parent-row-locking trigger guards every member INSERT/UPDATE/DELETE. It rejects mutation of sealed membership, including late insertion, and prevents races with sealing. Authorized erasure uses its separately privileged audited path.; Only the unsealed-to-sealed transition is allowed during construction. After sealing all revision fields are immutable; unsealing is prohibited. Current head can target only a sealed same-bundle revision.; At seal time, validate component/issuer/owner/edition closure and hash exact member data; unresolved or partial interpretation may be sealed with explicit missing members but cannot become verified by sealing.

Indexes: bundle_id,revision DESC; owner_id,status; wrapper_configuration_id

## ContractBundleMember

Maps one public package slot to one actual same-owner policy revision, preserving component-specific insured membership and explicit missing or unselected slots.

| Field | Type / required | Default | Purpose | Units | Example | Basis |
|---|---|---|---|---|---|---|
| id | uuid required | uuid4 | Stable immutable row identity | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| created_at | timestamptz required | transaction timestamp | Assertion insertion time, separate from contractual effective time | instant | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["OPS-06"] |
| owner_id | fk:Account required | none | Owner governing all private bundle records | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| bundle_revision_id | fk:ContractBundleRevision required | none | Exact immutable package interpretation | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| terms_component_id | fk:TermsComponent required | none | Public component slot, including separate issuer identity | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| customer_policy_revision_id | fk:CustomerPolicyRevision optional | NULL | Actual owned issued component policy revision, if established | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| selection_status | enum required | unresolved | Membership disposition; missing is explicit, not fabricated cover Allowed: unresolved,required_missing,selected_unverified,selected_stipulated,selected_verified,not_selected. | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_span_id | fk:EvidenceSpan optional | NULL | Issued evidence for the component membership | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |
| source_fact_id | fk:CustomerFact optional | NULL | Attributed customer assertion when documentary proof is absent | None | No authentic private/database identity inspected. See the explicitly synthetic additional-r13-combi-01 fixture. | ["INS-10"] |

Constraints: unique(id,owner_id); owner immutable; unique(bundle_revision_id,terms_component_id); All member TermsComponent.wrapper_terms_id match bundle wrapper configuration terms; selected_verified requires customer_policy_revision_id and private membership evidence; selected_stipulated requires explicit research fixture; required_missing/not_selected require customer_policy_revision_id NULL; A required component cannot be not_selected; conditional disposition requires its resolved selection rule; All private links enforce composite owner FK and deferred lineage checks on both source and target changes; Members are immutable after revision sealing; changes create a new bundle revision. PolicyMember records, not package identity, determine who is insured on each component; Default reject two selected slots in one bundle revision whose CustomerPolicyRevision.customer_policy_id is the same underlying CustomerPolicy, even if their revision IDs differ. Deferred check joins underlying CustomerPolicy IDs under parent and contract key-share locks. Any exception requires an explicit reviewed same-wrapper rule with exact slot pair; no implicit exception from matching dates or names.

Indexes: bundle_revision_id,selection_status; customer_policy_revision_id; terms_component_id

