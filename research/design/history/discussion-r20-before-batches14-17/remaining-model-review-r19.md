# Critical review of all remaining application models

Status: Batch 13 is now approved. Batch 14 onward remains a review proposal until discussed with the user.

Governing product scope: CoverGuide collects customer facts and requirements, finds applicable health-insurance products, compares their rules and current observations, asks focused clarification questions, and produces evidence-backed buying recommendations. It does not administer claims, treatment expenses, policy servicing or legal-hold operations.

## Review result

| Current model | Recommendation | Reason |
|---|---|---|
| `Turn` | Keep and simplify | Required for one durable, cancellable, idempotent customer request. Remove duplicated request payload hash and numeric expected revision; the immutable input message and pinned profile revision already provide them. |
| `TurnEvent` | Keep and simplify | Required for reconnectable streaming without repeating inference. Remove duplicate `recorded_at`; inherited `created_at` is the commit time. Rename the `decision` event kind to `recommendation`. |
| `Outbox` | Keep but replace generic target/payload | Required to avoid losing work between a committed database transaction and Celery/Redis dispatch. Replace `aggregate_id` and copied payload with explicit nullable FKs to `Turn`, `ProcessingJob` or `KnowledgeRelease`, with exactly one target. |
| `ModelRoute` | Keep and simplify | Required because the application uses a strict CLIProxyAPI/Codex adapter and must not silently change model identity. Replace derived qualified/unqualified status with optional `disabled_at`; qualifications live in `ModelQualification`. |
| `ModelQualification` | Keep and simplify | A route can pass one schema and fail another, so this cannot be folded into `ModelRoute`. Remove duplicate qualification time and unresolvable artifact hash. |
| `ModelAttempt` | Keep with a small correction | Required to expose the actual model, attempt, latency, usage and explicit failures. Rename the response locator and add its digest when a structured response is retained. Exactly one of turn or processing job is the parent. |
| `ProcessingJob` | Keep and correct input/output typing | Required for resumable reading, OCR, extraction, validation and independent review. Accept exactly one public `SourceCapture` or private `CustomerUploadedDocument`. Store optional result location and digest instead of pretending an operational result is an `OriginalFile` contractual source. A separate generic review model is unnecessary because review is a processing stage with retained issues. |
| `ConsentRecord` | Keep and simplify | Basic privacy/health-data authorization is relevant. Remove ABHA, external medical sharing, recipient, instance key, evidence-span and guessed expiry machinery because those capabilities are outside the buying adviser. |
| `DeletionRequest` | Keep and simplify | Customers need account, conversation, document and selected-disclosure erasure. Remove duplicate `requested_at`; inherited `created_at` is the request time. Keep closed scope and store-level completion evidence. |
| `RetentionHold` | Remove/defer | A legal-hold subsystem is not needed for the buying adviser and cannot be designed without an established legal/operational requirement. Add it later only if that requirement becomes real. |
| `AuditEvent` | Keep and simplify | Needed for sensitive-data access, publication, deletion and administration. Remove duplicate `occurred_at`; use inherited `created_at`. Keep metadata closed and free of medical text. |
| `LegacyMapping` | Remove from live application schema | Migration needs a signed/reviewed migration manifest and archives, not a permanent generic model in the buyer application. Directly map safe account/message records and preserve unsafe rows in the migration evidence package. |
| `AuthGroup` | Framework-managed, not a custom proposal model | Supplied by Django auth. Document its preservation and permissions; do not implement it manually. |
| `AuthPermission` | Framework-managed, not a custom proposal model | Supplied by Django auth/contenttypes. |
| `AccountGroup` | Framework-managed, not a custom proposal model | Django creates the user-group through table. |
| `AccountPermission` | Framework-managed, not a custom proposal model | Django creates the user-permission through table. |
| `GroupPermission` | Framework-managed, not a custom proposal model | Django creates the group-permission through table. |
| `AuthSession` | Framework-managed, not a custom proposal model | Supplied by Django sessions. |
| `ContentType` | Framework-managed, not a custom proposal model | Supplied by Django contenttypes. |
| `AdminLogEntry` | Framework-managed, not a custom proposal model | Supplied by Django admin. Its free-text privacy behavior still needs configuration and tests. |
| `TermsComponent` | Keep one simplified public model and rename to `PolicyPackageComponent` | Some public health products are wrappers around separately issued components. The adviser must know which component provides medical cover and which extra component is required or optional. Remove its redundant self-supersession field; wrapper `PolicyVersion` history already provides versioning. |
| `ContractBundle` | Remove | Models an owned package as a separately managed object. `CustomerPolicy`, customer facts and public package rules are enough for buying/comparison. |
| `ContractBundleRevision` | Remove | Sealing and revising actual package membership is policy-administration behavior outside scope. |
| `ContractBundleMember` | Remove | Actual component servicing is outside scope. A customer's existing component policies remain separate `CustomerPolicy` records and relevant package membership can be a sourced `CustomerFact`. |

## Proposed remaining review batches

1. **Batch 14 — minimum privacy operations:** simplified `ConsentRecord`, `DeletionRequest` and `AuditEvent`; remove `RetentionHold`.
2. **Batch 15 — framework and migration boundary:** remove `LegacyMapping` from the live schema and move the eight Django-managed tables into a framework appendix.
3. **Batch 16 — public packaged products:** keep simplified `PolicyPackageComponent`; remove `ContractBundle`, `ContractBundleRevision` and `ContractBundleMember`.
4. **Batch 17 — independent quality and evaluation stores:** review these separately from the runtime application. Their protected questions/oracles and independent rule inventory must never enter implementation retrieval or tuning data.
5. **Final audit:** reassess every approved model and field against the governing product scope, trace all live fields, remove remaining duplication, verify all foreign keys/JSON contracts/case mappings, and present every material observation for final human review.

## Expected direction if these recommendations are approved

The current application catalogue has 77 entries. Removing one legal-hold model, one live migration model, eight framework-managed entries and three private package-administration models removes 13 entries. Renaming/simplifying `TermsComponent` preserves one public packaged-product entity. The seven runtime and three privacy models remain. Before any further additions, the custom application proposal would therefore move toward approximately 64 entities, with Django's native tables documented separately rather than counted as custom CoverGuide models.

The exact final count can change slightly as fields are simplified in Batches 13–16. Counts are a review aid, not a quality target.
