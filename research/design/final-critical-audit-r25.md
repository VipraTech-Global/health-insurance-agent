# Final critical audit of the complete database proposal

Revision: `discussion-r25-final-review`  
Result: passed for presentation; explicit human approval of the complete design is pending.

## Changes made

The audit removed two optional/out-of-scope models (`AIPreference`, `PolicyEvent`), one duplicate relationship (`Message.turn_id`), narrowed advice/upload types, corrected the starting-versus-final profile lifecycle and hardened private-payload commitments. At that audit boundary the application had **62 custom models, 587 fields and 167 typed foreign keys**. The approved 2026-09-22 route-pinning amendment adds `TurnRouteBinding` and `Turn.route_commitment`, bringing the current design to **63 models, 601 fields and 170 typed foreign keys** without changing the audit's scope conclusions.

No customer claim, treatment bill, insurer receipt, payment ledger, cancellation workflow, refund workflow, legal-hold subsystem, live legacy-mapping table or custom reimplementation of Django auth/session tables remains.

## Model-by-model verdict

| Model | Verdict | Reason |
|---|---|---|
| `Account` | Keep | Logical authentication principal implemented by the retained accounts.User(AbstractUser) model.. |
| `Person` | Keep | A minimal owner-scoped human label; medical, role and identity assertions live in sourced fact records.. |
| `PersonRelationship` | Keep | Directional relationship between two owner-scoped people, separate from proposed or issued policy membership.. |
| `Conversation` | Keep | Persistent conversation and its current accepted state.. |
| `Message` | Keep | Immutable submitted or published conversational content.. |
| `ConversationMessageChunk` | Keep | Replaceable private lexical/semantic index for an exact section of one immutable conversation message.. |
| `CustomerStatement` | Keep | A meaningful source span inside one customer message, retained so unusual or unresolved information cannot be silently dropped.. |
| `CustomerProfileRevision` | Keep | Small immutable checkpoint created only when customer facts or requirements change.. |
| `CustomerFact` | Keep | One validated version of a customer fact; active historical state is reconstructed by logical key and profile revision.. |
| `CustomerRequirement` | Keep | One atomic mandatory, preferred or informational condition used to filter, rank or explain policy configurations.. |
| `AdviceRequest` | Keep | One customer advice goal spanning any number of clarification messages; execution attempts later pin exact profile revisions.. |
| `Insurer` | Keep | One insurer in the approved research roster and the issuer identity used by products and official documents.. |
| `DiscoveryRun` | Keep | One autonomous Codex session tasked with discovering public documents for one insurer.. |
| `SourceURL` | Keep | One unique public web address discovered by Codex, independent of how often or where it was observed.. |
| `SourceObservation` | Keep | One retained occasion on which a Codex discovery run encountered a source URL.. |
| `SourceCapture` | Keep | One attempt by a Codex discovery run to preserve the content currently returned by a source URL.. |
| `OriginalFile` | Keep | Content-addressed exact bytes preserved from a public source or private customer upload.. |
| `CustomerUploadedDocument` | Keep | One private document supplied by a customer, separate from its content-addressed bytes.. |
| `DocumentSeries` | Keep | Stable identity of one continuing publication across editions, such as a product policy wording.. |
| `DocumentVersion` | Keep | One identified edition within a DocumentSeries, with evidence-backed dates and explicit supersession.. |
| `DocumentPage` | Keep | One physical PDF page and its explicit review state, including pages on which extraction failed.. |
| `EvidenceSpan` | Keep | One exact passage, table cell, footnote or region from either a public capture or private customer upload.. |
| `Product` | Keep | Stable insurer product family, independent of policy editions, named variants and optional additions.. |
| `PolicyVersion` | Keep | One complete legal terms package for a Product, assembled from every applicable governing document.. |
| `PolicyVersionDocument` | Keep | Membership, role, conditional applicability and proven precedence of one DocumentVersion in a PolicyVersion.. |
| `ProductVariant` | Keep | One insurer-defined base variant and its allowed sums insured, deductibles, room categories and family choices.. |
| `ProductOption` | Keep | One optional or mandatory add-on, rider or election available with a ProductVariant.. |
| `CustomerPolicy` | Keep | Stable identity of one insurer-issued customer policy or customer-specific offer.. |
| `CustomerPolicyRevision` | Keep | One exact set of insurer-issued customer selections applying during a defined interval.. |
| `PolicyMember` | Keep | One person actually covered under one customer policy revision.. |
| `CustomerPolicyOption` | Keep | One customer-specific selected, declined or unresolved ProductOption decision.. |
| `CustomerPolicyFact` | Keep | One document-backed structured fact about a particular customer's issued policy revision.. |
| `PolicyRule` | Keep | One immutable, reviewed condition, benefit, restriction or calculation instruction from a public policy version.. |
| `PolicyRuleEvidence` | Keep | One exact public source passage supporting, defining, restricting or contradicting a policy rule.. |
| `PolicyRuleLink` | Keep | A reviewed connection requiring two policy rules to be interpreted together.. |
| `PolicyRuleTableCell` | Keep | One original-backed result selected by the complete axes declared in a policy rule body.. |
| `ProviderLocation` | Keep | One exact public hospital or healthcare-facility branch identity used for network matching.. |
| `ProviderNetworkSnapshot` | Keep | One dated, scoped insurer network source or directory query, including a zero-result or failed check.. |
| `ProviderNetworkEntry` | Keep | One exact facility branch status printed in one immutable provider-network snapshot.. |
| `Quote` | Keep | One immutable, evidence-backed personal insurer quote for an exact customer profile and product selection.. |
| `KnowledgeRelease` | Keep | Immutable set of reviewed policy rules that the buying adviser may use together.. |
| `KnowledgeReleaseRule` | Keep | Includes one exact reviewed policy rule in one knowledge release.. |
| `KnowledgeChannel` | Keep | Selects the current published knowledge release for one application environment.. |
| `PolicySearchChunk` | Keep | Replaceable public search index text for one exact section of a policy document.. |
| `Recommendation` | Keep | One saved buying/comparison result for an exact customer profile and published policy-knowledge release.. |
| `PolicyCandidateAssessment` | Keep | One exact public policy configuration evaluated for the customer, including exclusions and uncertain candidates.. |
| `PolicyRequirementMatch` | Keep | How one policy candidate performs against one exact customer requirement.. |
| `InformationNeed` | Keep | One missing customer fact, requirement or document confirmation that should be asked before stronger advice.. |
| `RecommendationStatement` | Keep | One independently checkable customer-facing statement in a buying recommendation.. |
| `RecommendationCitation` | Keep | Exact original policy passage supporting, restricting or conflicting with one recommendation statement.. |
| `Calculation` | Keep | One immutable deterministic calculation with exact inputs, operation order, assumptions and result.. |
| `Turn` | Keep | One durable, idempotent and cancellable customer-message processing request.. |
| `TurnEvent` | Keep | One immutable ordered UI event that reconnecting clients can replay without repeating inference.. |
| `Outbox` | Keep | Reliable typed dispatch record committed with the work that Celery or publication must deliver.. |
| `ModelRoute` | Keep | One exact secret-free CLIProxyAPI/Codex route configuration.. |
| `ModelQualification` | Keep | One completed test of an exact route against one application schema and capability set.. |
| `ModelAttempt` | Keep | One actual CLIProxyAPI/Codex call with explicit identity, timing, usage and failure.. |
| `ProcessingJob` | Keep | One resumable public-policy or private-upload classification, reading, extraction, validation or independent-review task.. |
| `ConsentRecord` | Keep | One customer grant for CoverGuide to process account, health or uploaded-document data for buying advice, with optional later revocation.. |
| `DeletionRequest` | Keep | One durable customer request to erase an account, conversation, upload or selected disclosure and its derived private copies.. |
| `AuditEvent` | Keep | Minimal append-only record of sensitive-data access, publication, deletion and administration without copied customer medical text.. |
| `PolicyPackageComponent` | Keep | One original-backed component slot in a public packaged policy, used to compare which separately issued product supplies medical or supplementary cover.. |

## Separate benchmark verdict

The prior 36-model quality-store proposal was reduced to 24. It keeps exact immutable case/oracle versions, exposure blocking, insurer rule denominators, freeze membership, three attempts per case, independent scoring, critical blockers and external gates. It removes local user/role duplication, generic artifact ownership, redundant case/version and assessment wrappers, per-attempt events, adjudication wrappers and mutable safe-export rows.

## Structural verification limits

The verifier confirms field uniqueness, foreign-key closure, JSON-contract reachability, 400 safe case mappings, field traceability, absence of removed models/fields and the fixed acceptance denominators. It does not prove original-source completeness, case-answer correctness, independent isolation, knowledge coverage, adviser accuracy, runtime permissions, performance or migration success. Those remain implementation/evidence work after complete-design approval.
