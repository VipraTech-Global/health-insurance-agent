# CoverGuide database design in simple language

Revision: `discussion-r25-final-review`

This guide explains the complete application proposal in small review sections. It contains 62 custom application models. Django's standard group, permission, session, content-type and admin-log tables are documented separately. The independent evaluation database has 24 models and is explained in `benchmark-storage-proposal.md`.

The application is a buying and comparison adviser. It stores what the customer said, the exact original policy evidence, structured rules, dated quotes/network observations and the recommendation it produced. It does not administer claims, treatment bills, insurer receipts, premium payments, cancellations or refunds.

## End-to-end example

Asha asks for insurance for her father Ravi and initially says, ambiguously, ‘I have diabetes.’ CoverGuide keeps the message, extracts separate statements, asks who has diabetes, records the correction against the correct person, and creates a new profile revision. It filters exact product variants by entry age and other mandatory rules, retrieves diabetes waiting-period and underwriting clauses with connected exceptions, compares any dated quotes, asks for missing facts, calculates only supported examples, and saves each recommendation statement with an exact citation.

If Asha corrects Ravi's age, the old profile and recommendation remain historical. A new turn starts from the last accepted profile, applies the new message, and publishes a recommendation against the resulting profile only if concurrent corrections did not make it stale.

## 1. Account, people and conversation

| Model | What it stores |
|---|---|
| `Account` | Logical authentication principal implemented by the retained accounts.User(AbstractUser) model.. |
| `Person` | A minimal owner-scoped human label; medical, role and identity assertions live in sourced fact records.. |
| `PersonRelationship` | Directional relationship between two owner-scoped people, separate from proposed or issued policy membership.. |
| `Conversation` | Persistent conversation and its current accepted state.. |
| `Message` | Immutable submitted or published conversational content.. |
| `ConversationMessageChunk` | Replaceable private lexical/semantic index for an exact section of one immutable conversation message.. |

## 2. Customer meaning and profile

| Model | What it stores |
|---|---|
| `CustomerStatement` | A meaningful source span inside one customer message, retained so unusual or unresolved information cannot be silently dropped.. |
| `CustomerProfileRevision` | Small immutable checkpoint created only when customer facts or requirements change.. |
| `CustomerFact` | One validated version of a customer fact; active historical state is reconstructed by logical key and profile revision.. |
| `CustomerRequirement` | One atomic mandatory, preferred or informational condition used to filter, rank or explain policy configurations.. |
| `AdviceRequest` | One customer advice goal spanning any number of clarification messages; execution attempts later pin exact profile revisions.. |

## 3. Autonomous source discovery and exact evidence

| Model | What it stores |
|---|---|
| `Insurer` | One insurer in the approved research roster and the issuer identity used by products and official documents.. |
| `DiscoveryRun` | One autonomous Codex session tasked with discovering public documents for one insurer.. |
| `SourceURL` | One unique public web address discovered by Codex, independent of how often or where it was observed.. |
| `SourceObservation` | One retained occasion on which a Codex discovery run encountered a source URL.. |
| `SourceCapture` | One attempt by a Codex discovery run to preserve the content currently returned by a source URL.. |
| `OriginalFile` | Content-addressed exact bytes preserved from a public source or private customer upload.. |
| `CustomerUploadedDocument` | One private document supplied by a customer, separate from its content-addressed bytes.. |
| `DocumentSeries` | Stable identity of one continuing publication across editions, such as a product policy wording.. |
| `DocumentVersion` | One identified edition within a DocumentSeries, with evidence-backed dates and explicit supersession.. |
| `DocumentPage` | One physical PDF page and its explicit review state, including pages on which extraction failed.. |
| `EvidenceSpan` | One exact passage, table cell, footnote or region from either a public capture or private customer upload.. |

## 4. Public products and exact legal versions

| Model | What it stores |
|---|---|
| `Product` | Stable insurer product family, independent of policy editions, named variants and optional additions.. |
| `PolicyVersion` | One complete legal terms package for a Product, assembled from every applicable governing document.. |
| `PolicyVersionDocument` | Membership, role, conditional applicability and proven precedence of one DocumentVersion in a PolicyVersion.. |
| `ProductVariant` | One insurer-defined base variant and its allowed sums insured, deductibles, room categories and family choices.. |
| `ProductOption` | One optional or mandatory add-on, rider or election available with a ProductVariant.. |
| `PolicyPackageComponent` | One original-backed component slot in a public packaged policy, used to compare which separately issued product supplies medical or supplementary cover.. |

## 5. Existing cover and customer-specific offers

| Model | What it stores |
|---|---|
| `CustomerPolicy` | Stable identity of one insurer-issued customer policy or customer-specific offer.. |
| `CustomerPolicyRevision` | One exact set of insurer-issued customer selections applying during a defined interval.. |
| `PolicyMember` | One person actually covered under one customer policy revision.. |
| `CustomerPolicyOption` | One customer-specific selected, declined or unresolved ProductOption decision.. |
| `CustomerPolicyFact` | One document-backed structured fact about a particular customer's issued policy revision.. |

## 6. Structured policy knowledge

| Model | What it stores |
|---|---|
| `PolicyRule` | One immutable, reviewed condition, benefit, restriction or calculation instruction from a public policy version.. |
| `PolicyRuleEvidence` | One exact public source passage supporting, defining, restricting or contradicting a policy rule.. |
| `PolicyRuleLink` | A reviewed connection requiring two policy rules to be interpreted together.. |
| `PolicyRuleTableCell` | One original-backed result selected by the complete axes declared in a policy rule body.. |

## 7. Dated quotes and hospital observations

| Model | What it stores |
|---|---|
| `ProviderLocation` | One exact public hospital or healthcare-facility branch identity used for network matching.. |
| `ProviderNetworkSnapshot` | One dated, scoped insurer network source or directory query, including a zero-result or failed check.. |
| `ProviderNetworkEntry` | One exact facility branch status printed in one immutable provider-network snapshot.. |
| `Quote` | One immutable, evidence-backed personal insurer quote for an exact customer profile and product selection.. |

## 8. Safe knowledge publication and search

| Model | What it stores |
|---|---|
| `KnowledgeRelease` | Immutable set of reviewed policy rules that the buying adviser may use together.. |
| `KnowledgeReleaseRule` | Includes one exact reviewed policy rule in one knowledge release.. |
| `KnowledgeChannel` | Selects the current published knowledge release for one application environment.. |
| `PolicySearchChunk` | Replaceable public search index text for one exact section of a policy document.. |

## 9. Saved buying/comparison decisions

| Model | What it stores |
|---|---|
| `Recommendation` | One saved buying/comparison result for an exact customer profile and published policy-knowledge release.. |
| `PolicyCandidateAssessment` | One exact public policy configuration evaluated for the customer, including exclusions and uncertain candidates.. |
| `PolicyRequirementMatch` | How one policy candidate performs against one exact customer requirement.. |
| `InformationNeed` | One missing customer fact, requirement or document confirmation that should be asked before stronger advice.. |
| `RecommendationStatement` | One independently checkable customer-facing statement in a buying recommendation.. |
| `RecommendationCitation` | Exact original policy passage supporting, restricting or conflicting with one recommendation statement.. |
| `Calculation` | One immutable deterministic calculation with exact inputs, operation order, assumptions and result.. |

## 10. Durable processing and model evidence

| Model | What it stores |
|---|---|
| `Turn` | One durable, idempotent and cancellable customer-message processing request.. |
| `TurnEvent` | One immutable ordered UI event that reconnecting clients can replay without repeating inference.. |
| `Outbox` | Reliable typed dispatch record committed with the work that Celery or publication must deliver.. |
| `ModelRoute` | One exact secret-free CLIProxyAPI/Codex route configuration.. |
| `ModelQualification` | One completed test of an exact route against one application schema and capability set.. |
| `ModelAttempt` | One actual CLIProxyAPI/Codex call with explicit identity, timing, usage and failure.. |
| `ProcessingJob` | One resumable public-policy or private-upload classification, reading, extraction, validation or independent-review task.. |

## 11. Minimum privacy operations

| Model | What it stores |
|---|---|
| `ConsentRecord` | One customer grant for CoverGuide to process account, health or uploaded-document data for buying advice, with optional later revocation.. |
| `DeletionRequest` | One durable customer request to erase an account, conversation, upload or selected disclosure and its derived private copies.. |
| `AuditEvent` | Minimal append-only record of sensitive-data access, publication, deletion and administration without copied customer medical text.. |

## Important boundaries to review

- `PersonRelationship` says how two people are related. `PolicyMember` separately proves who an insurer actually covered.
- `CustomerFact` and `CustomerRequirement` accept code-controlled types plus versioned closed values, so new customer information can be added without creating a database column for every possible sentence.
- `SourceURL` is a discovered address; `SourceCapture` is one attempt; `OriginalFile` is exact bytes; `DocumentVersion` is the identified publication; `EvidenceSpan` is the exact supporting passage.
- `Product`, `PolicyVersion`, `ProductVariant` and `ProductOption` are separate because a product family, legal edition, base configuration and optional add-on change independently.
- `CustomerPolicy` models existing cover or a customer-specific offer only so it can be compared with a proposed purchase. There is no servicing workflow.
- `PolicyRule` is mandatory structured knowledge. `PolicySearchChunk` helps find supporting text quickly but cannot override mandatory-rule selection.
- `Recommendation` pins the final customer profile and knowledge release. `Turn` pins the starting profile before interpreting the new message.
- Evaluation questions and answers live only in the separate benchmark service and cannot enter application retrieval or tuning data.

For every field, default, validation rule, unit, constraint and index, use [field-dictionary.md](field-dictionary.md). For relationships, use [complete-entity-relationships.mmd](complete-entity-relationships.mmd).
