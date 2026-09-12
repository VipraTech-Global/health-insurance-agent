# Pilot preservation requirements — source inventory, 2026-09-10

This is a technical preservation inventory, separate from the 400-case insurance derivation. It does not propose replacement entities or authorize schema implementation, migration or cutover. Existing architecture is not a constraint on the replacement. Records that cannot be interpreted safely must remain preserved legacy history with an explicit unresolved mapping.

Evidence is source-only. No database rows, live settings, credentials, sessions, actual password hashes, customer messages or evaluation cases were inspected. Models describe intended current code, not verified deployed schema or populated records. The repository has no resolvable HEAD in this inspection; companion JSON fingerprints the inspected source files. No migration or rollback has been executed or verified.

## Preservation decisions the eventual approved migration must satisfy

| Requirement | Preservation rule | Unsafe translation or missing evidence |
|---|---|---|
| OP-P01 Accounts and authentication | Preserve UUID, email, complete encoded password value, usable/unusable state, login/join dates, deletion state and privilege flags exactly. Retain groups and explicit permissions with semantic identity. | Do not call create_user or set_password on an existing encoded password: those paths hash inputs. Do not reset passwords, fabricate identities or normalize distinct legacy emails into one account. Existing algorithm support must be checked in the replacement runtime. |
| OP-P02 Sessions | Preserve valid sessions and account bindings where compatibility permits; retain required signing/key/backend configuration through an authorized secure operational process, without copying secrets into reports. | Session data is signed and security-sensitive. Session keys, signing compatibility, cookie domain/path, expiry, auth backend and unchanged password hash all matter; copying rows alone does not prove preserved login. An incompatible session strategy requires explicit discussion. |
| OP-P03 Ownership | Preserve owner-to-conversation, owner-to-snapshot and user-to-AI-preference mappings. Revalidate indirect answer/attempt/message ownership. | A profile revision integer is unique only within its conversation. A snapshot with no linked answer has an owner and revision number but no unambiguous conversation. Never guess that association. |
| OP-P04 Conversations and facts | Preserve conversation/message UUIDs, content, roles, origins, timestamps, all profile JSON, provenance, confirmation state and revision order. | Profile data is a generic conversation-level JSON snapshot. It does not by itself establish insured-person identity, medical fact subject, DOB, units or detailed source-turn history. Preserve missing/blank/null/false distinctly. |
| OP-P05 Suggestions versus confirmations | Preserve profile_suggestion blocks as unconfirmed model proposals with their original attempt context. | Interview extraction returns candidate patches in AnswerArtifact.blocks; publish_ai_answer does not apply them as confirmed customer facts. Do not convert suggestions, quoted messages or assistant text into accepted disclosures. |
| OP-P06 Request/attempt history | Preserve request_id, payload_hash, original input, operation, expected revision, every attempt status/deadline/code, route and corpus references. Preserve idempotency. | Do not recompute payload_hash using new serialization or replay historical turns through the model. Active work needs an explicit coordinated drain/cancel/recovery boundary before cutover. |
| OP-P07 Saved advice and model audit | Preserve artifacts, blocks, claims, cited facts/bundles, recommendation snapshots/calculations, rule version, model identities, usage, timing and safe error codes. Mark legacy validation scope accurately. | Succeeded or ai_validated does not imply the new 400-case acceptance target or recommendability. JSON fact IDs and revision numbers need explicit identity mapping; historical calculations must not be silently recomputed. |
| OP-P08 Originals and source history | Preserve original bytes, SHA-256, media/size, source observations including failures, document identities/versions, roles and applicability, all extraction maps and parser manifests. | Database backups omit filesystem bytes. An observation content hash has no direct FK to a blob. A catalogue listing has no direct FK to a product version. Matching by display name or URL alone is unsafe. |
| OP-P09 Citation resolution | Keep original document/extraction/page/span/bundle identities and ordering or an explicit lossless old-to-new locator map. Verify originals and extraction hashes. | physical_index is zero-based in the pilot; serialized PDF page is physical_index + 1. Source lines start at 1 and inclusive ranges are used. Printed labels, rotations, dimensions, word IDs and region boundaries must not be conflated or regenerated silently. |
| OP-P10 Publication and qualifications | Preserve old corpus manifests/current selection and immutable route/qualification histories as historical evidence. Requalify any changed configuration before use. | Old published/reviewed flags and opaque applicability/value JSON are not independent original-rule validation. No automatic promotion into the replacement approved corpus. |
| OP-P11 Deletion and retained history | Carry forward valid deletion outcomes and authorization scope. Avoid resurrection from backup imports, profiles, messages, snapshots, search copies, model artifacts or queued work. | deleted_at exists but current delete_account hard-deletes the user and related conversation/advice data. A source-only inventory cannot reconstruct deleted rows or establish a legally approved retention policy. ReviewEvent can survive with reviewer NULL. |
| OP-P12 Rollback | Preserve an independently restorable pilot database, original storage, extraction artifacts, exact application/dependency/configuration identities and publication references. Keep the pilot available during replacement work. | Migration reversal functions are not a data-preservation rollback. Existing migration 0006 rewrites active attempt states; its reverse data function is a noop. Post-cutover writes/deletions need an agreed reconciliation strategy before rollback is considered safe. |

## Existing model and field ledger

All concrete models inheriting UUIDModel also have `id` (UUID primary key, generated default, noneditable) and `created_at` (creation timestamp). Preserve both without regeneration. Foreign keys and one-to-one fields imply stored `_id` columns. The table below lists every explicitly declared adviser model field, including relationship deletion behavior and declared constraints in field options. It is an existing-source ledger, not a replacement field proposal.

User additionally inherits the following fields, confirmed by accounts migration 0001: `password` CharField(128); `last_login` nullable DateTime; `is_superuser` Boolean default false; `first_name` and `last_name` blank CharField(150); `is_staff` Boolean default false; `is_active` Boolean default true; `date_joined` DateTime default timezone.now; `groups` and `user_permissions` many-to-many links. It deliberately has no username field. Preserve all inherited values and join records.

### User

Source: `backend/apps/accounts/models.py:23`. See inherited/implicit fields noted above and below.

| Field | Existing declaration |
|---|---|
| `id` | `models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)` |
| `email` | `models.EmailField(unique=True)` |
| `deleted_at` | `models.DateTimeField(null=True, blank=True)` |

### UUIDModel

Source: `backend/apps/adviser/models.py:12`. Abstract base; no own table.

| Field | Existing declaration |
|---|---|
| `id` | `models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)` |
| `created_at` | `models.DateTimeField(auto_now_add=True)` |

### Insurer

Source: `backend/apps/adviser/models.py:20`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `name` | `models.CharField(max_length=200, unique=True)` |
| `aliases` | `models.JSONField(default=list)` |
| `official_domains` | `models.JSONField(default=list)` |

### CatalogueListing

Source: `backend/apps/adviser/models.py:26`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `ditto_path` | `models.CharField(max_length=500, unique=True)` |
| `displayed_name` | `models.CharField(max_length=250)` |
| `insurer` | `models.ForeignKey(Insurer, null=True, on_delete=models.PROTECT)` |
| `status` | `models.CharField(max_length=30, choices=Status, default=Status.DISCOVERED)` |
| `status_reason` | `models.TextField(blank=True)` |
| `last_observed_at` | `models.DateTimeField()` |

### PlanVersion

Source: `backend/apps/adviser/models.py:44`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `insurer` | `models.ForeignKey(Insurer, on_delete=models.PROTECT)` |
| `uin` | `models.CharField(max_length=100, blank=True)` |
| `name` | `models.CharField(max_length=250)` |
| `variant` | `models.CharField(max_length=200, blank=True)` |
| `effective_from` | `models.DateField(null=True, blank=True)` |
| `effective_to` | `models.DateField(null=True, blank=True)` |
| `available_for_new_purchase` | `models.BooleanField(null=True)` |
| `review_state` | `models.CharField(max_length=30, default='pending')` |

### SourceLocator

Source: `backend/apps/adviser/models.py:64`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `url` | `models.URLField(max_length=1000)` |
| `source_organisation` | `models.CharField(max_length=250)` |
| `expected_document_type` | `models.CharField(max_length=100)` |

### SourceObservation

Source: `backend/apps/adviser/models.py:70`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `locator` | `models.ForeignKey(SourceLocator, on_delete=models.PROTECT)` |
| `fetched_at` | `models.DateTimeField()` |
| `status_code` | `models.PositiveSmallIntegerField(null=True)` |
| `final_url` | `models.URLField(max_length=1000, blank=True)` |
| `content_sha256` | `models.CharField(max_length=64, blank=True)` |
| `available` | `models.BooleanField(default=False)` |
| `error_code` | `models.CharField(max_length=100, blank=True)` |

### SourceBlob

Source: `backend/apps/adviser/models.py:80`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `sha256` | `models.CharField(max_length=64, unique=True)` |
| `stored_path` | `models.CharField(max_length=500, unique=True)` |
| `byte_size` | `models.PositiveBigIntegerField()` |
| `media_type` | `models.CharField(max_length=100)` |

### DocumentVersion

Source: `backend/apps/adviser/models.py:87`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `blob` | `models.ForeignKey(SourceBlob, on_delete=models.PROTECT)` |
| `document_type` | `models.CharField(max_length=100)` |
| `language` | `models.CharField(max_length=20, default='en')` |
| `identity` | `models.CharField(max_length=300)` |
| `effective_from` | `models.DateField(null=True, blank=True)` |

### PlanDocumentAssociation

Source: `backend/apps/adviser/models.py:95`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `plan_version` | `models.ForeignKey(PlanVersion, on_delete=models.PROTECT)` |
| `document_version` | `models.ForeignKey(DocumentVersion, on_delete=models.PROTECT)` |
| `role` | `models.CharField(max_length=100)` |
| `applicability` | `models.JSONField(default=dict)` |
| `reviewed` | `models.BooleanField(default=False)` |

### ExtractionRevision

Source: `backend/apps/adviser/models.py:111`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `document_version` | `models.ForeignKey(DocumentVersion, on_delete=models.PROTECT)` |
| `revision` | `models.PositiveIntegerField()` |
| `parser_manifest` | `models.JSONField(default=dict)` |
| `artifact_sha256` | `models.CharField(max_length=64)` |
| `source_map_path` | `models.CharField(max_length=500)` |
| `published` | `models.BooleanField(default=False)` |

### DocumentPage

Source: `backend/apps/adviser/models.py:127`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `extraction_revision` | `models.ForeignKey(ExtractionRevision, on_delete=models.PROTECT)` |
| `physical_index` | `models.PositiveIntegerField()` |
| `printed_label` | `models.CharField(max_length=30, blank=True)` |
| `width` | `models.DecimalField(max_digits=12, decimal_places=4)` |
| `height` | `models.DecimalField(max_digits=12, decimal_places=4)` |
| `rotation` | `models.SmallIntegerField(default=0)` |
| `geometry` | `models.JSONField(default=dict)` |

### EvidenceSpan

Source: `backend/apps/adviser/models.py:144`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `page` | `models.ForeignKey(DocumentPage, on_delete=models.PROTECT)` |
| `region_id` | `models.CharField(max_length=100)` |
| `start_line` | `models.PositiveIntegerField()` |
| `end_line` | `models.PositiveIntegerField()` |
| `source_word_ids` | `models.JSONField(default=list)` |
| `quote` | `models.TextField()` |
| `geometry` | `models.JSONField(default=list)` |

### EvidenceBundle

Source: `backend/apps/adviser/models.py:154`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `label` | `models.CharField(max_length=250)` |
| `review_state` | `models.CharField(max_length=30, default='pending')` |
| `spans` | `models.ManyToManyField(EvidenceSpan, through='EvidenceBundleSpan')` |

### EvidenceBundleSpan

Source: `backend/apps/adviser/models.py:162`. See inherited/implicit fields noted above and below.

| Field | Existing declaration |
|---|---|
| `bundle` | `models.ForeignKey(EvidenceBundle, on_delete=models.CASCADE)` |
| `span` | `models.ForeignKey(EvidenceSpan, on_delete=models.PROTECT)` |
| `role` | `models.CharField(max_length=30, default='primary')` |
| `order` | `models.PositiveSmallIntegerField(default=0)` |

### VerifiedFact

Source: `backend/apps/adviser/models.py:175`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `plan_version` | `models.ForeignKey(PlanVersion, on_delete=models.PROTECT)` |
| `category` | `models.CharField(max_length=100)` |
| `value_type` | `models.CharField(max_length=30)` |
| `value` | `models.JSONField()` |
| `applicability` | `models.JSONField(default=dict)` |
| `evidence_bundle` | `models.ForeignKey(EvidenceBundle, on_delete=models.PROTECT)` |
| `verification_state` | `models.CharField(max_length=30, default='pending')` |
| `conflict` | `models.BooleanField(default=False)` |

### Clause

Source: `backend/apps/adviser/models.py:186`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `document_version` | `models.ForeignKey(DocumentVersion, on_delete=models.PROTECT)` |
| `section_path` | `models.JSONField(default=list)` |
| `heading` | `models.CharField(max_length=500, blank=True)` |
| `evidence_bundles` | `models.ManyToManyField(EvidenceBundle)` |

### RatingObservation

Source: `backend/apps/adviser/models.py:193`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `plan_version` | `models.ForeignKey(PlanVersion, on_delete=models.PROTECT)` |
| `rating` | `models.DecimalField(max_digits=6, decimal_places=3)` |
| `scale` | `models.DecimalField(max_digits=6, decimal_places=3)` |
| `observed_at` | `models.DateTimeField()` |
| `evidence_bundle` | `models.ForeignKey(EvidenceBundle, on_delete=models.PROTECT)` |

### PremiumObservation

Source: `backend/apps/adviser/models.py:201`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `plan_version` | `models.ForeignKey(PlanVersion, on_delete=models.PROTECT)` |
| `amount` | `models.DecimalField(max_digits=14, decimal_places=2)` |
| `currency` | `models.CharField(max_length=3, default='INR')` |
| `assumptions` | `models.JSONField(default=dict)` |
| `tax_basis` | `models.CharField(max_length=100, blank=True)` |
| `observed_at` | `models.DateTimeField()` |
| `evidence_bundle` | `models.ForeignKey(EvidenceBundle, on_delete=models.PROTECT)` |

### ReviewEvent

Source: `backend/apps/adviser/models.py:211`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `object_type` | `models.CharField(max_length=100)` |
| `object_id` | `models.UUIDField()` |
| `expected_revision` | `models.CharField(max_length=100)` |
| `decision` | `models.CharField(max_length=30)` |
| `reason` | `models.TextField()` |
| `reviewer` | `models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)` |

### IngestionRun

Source: `backend/apps/adviser/models.py:220`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `stage` | `models.CharField(max_length=50)` |
| `state` | `models.CharField(max_length=30)` |
| `inputs` | `models.JSONField(default=dict)` |
| `outputs` | `models.JSONField(default=dict)` |
| `errors` | `models.JSONField(default=list)` |
| `retry_count` | `models.PositiveSmallIntegerField(default=0)` |
| `updated_at` | `models.DateTimeField(auto_now=True)` |

### CorpusRelease

Source: `backend/apps/adviser/models.py:230`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `name` | `models.CharField(max_length=200, unique=True)` |
| `manifest` | `models.JSONField(default=dict)` |
| `activated_at` | `models.DateTimeField(null=True, blank=True)` |
| `is_current` | `models.BooleanField(default=False)` |

### Conversation

Source: `backend/apps/adviser/models.py:246`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `owner` | `models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)` |
| `title` | `models.CharField(max_length=200, default='New conversation')` |
| `updated_at` | `models.DateTimeField(auto_now=True)` |
| `current_profile` | `models.ForeignKey('ProfileRevision', null=True, blank=True, on_delete=models.SET_NULL, related_name='current_for')` |
| `active_attempt` | `models.OneToOneField('TurnAttempt', null=True, blank=True, on_delete=models.SET_NULL, related_name='active_for_conversation')` |

### ProfileRevision

Source: `backend/apps/adviser/models.py:266`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `conversation` | `models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='profiles')` |
| `revision` | `models.PositiveIntegerField()` |
| `data` | `models.JSONField(default=dict)` |
| `field_provenance` | `models.JSONField(default=dict)` |
| `confirmed_at` | `models.DateTimeField(null=True, blank=True)` |

### Message

Source: `backend/apps/adviser/models.py:283`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `conversation` | `models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')` |
| `role` | `models.CharField(max_length=20, choices=[('user', 'User'), ('assistant', 'Assistant')])` |
| `content` | `models.TextField()` |
| `origin` | `models.CharField(max_length=30, default='text')` |
| `answer` | `models.OneToOneField('AnswerArtifact', null=True, blank=True, on_delete=models.SET_NULL, related_name='message')` |

### Turn

Source: `backend/apps/adviser/models.py:299`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `conversation` | `models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='turns')` |
| `request_id` | `models.UUIDField()` |
| `payload_hash` | `models.CharField(max_length=64)` |
| `route` | `models.ForeignKey('RouteConfiguration', null=True, on_delete=models.PROTECT)` |
| `input_text` | `models.TextField()` |
| `operation` | `models.CharField(max_length=50, default='chat')` |
| `expected_profile_revision` | `models.PositiveIntegerField(null=True)` |

### TurnAttempt

Source: `backend/apps/adviser/models.py:316`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `turn` | `models.ForeignKey(Turn, on_delete=models.CASCADE, related_name='attempts')` |
| `conversation` | `models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='attempts', editable=False)` |
| `status` | `models.CharField(max_length=30, choices=Status, default=Status.ACCEPTED)` |
| `profile_revision` | `models.PositiveIntegerField(null=True)` |
| `corpus_release` | `models.ForeignKey(CorpusRelease, null=True, on_delete=models.PROTECT)` |
| `route` | `models.ForeignKey('RouteConfiguration', null=True, on_delete=models.PROTECT)` |
| `deadline_at` | `models.DateTimeField()` |
| `terminal_code` | `models.CharField(max_length=100, blank=True)` |
| `updated_at` | `models.DateTimeField(auto_now=True)` |

### RouteConfiguration

Source: `backend/apps/adviser/models.py:358`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `relay_type` | `models.CharField(max_length=40)` |
| `base_url` | `models.URLField(max_length=1000)` |
| `configured_model` | `models.CharField(max_length=200)` |
| `api_dialect` | `models.CharField(max_length=50)` |
| `capabilities` | `models.JSONField(default=dict)` |
| `context_limit` | `models.PositiveIntegerField()` |
| `timeout_policy` | `models.JSONField(default=dict)` |
| `configuration_hash` | `models.CharField(max_length=64, unique=True)` |
| `qualification_state` | `models.CharField(max_length=30, default='unqualified')` |

### RouteQualification

Source: `backend/apps/adviser/models.py:370`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `route` | `models.ForeignKey(RouteConfiguration, on_delete=models.PROTECT)` |
| `tested_configuration_hash` | `models.CharField(max_length=64)` |
| `evaluation_results` | `models.JSONField(default=dict)` |
| `state` | `models.CharField(max_length=30)` |

### ModelCallAttempt

Source: `backend/apps/adviser/models.py:377`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `turn_attempt` | `models.ForeignKey(TurnAttempt, null=True, on_delete=models.CASCADE)` |
| `task` | `models.CharField(max_length=50)` |
| `route` | `models.ForeignKey(RouteConfiguration, on_delete=models.PROTECT)` |
| `requested_model` | `models.CharField(max_length=200)` |
| `upstream_reported_model` | `models.CharField(max_length=200, blank=True)` |
| `status` | `models.CharField(max_length=30)` |
| `duration_ms` | `models.PositiveIntegerField(null=True)` |
| `reported_usage` | `models.JSONField(default=dict)` |
| `safe_error_code` | `models.CharField(max_length=100, blank=True)` |

### AnswerArtifact

Source: `backend/apps/adviser/models.py:389`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `attempt` | `models.OneToOneField(TurnAttempt, on_delete=models.CASCADE, related_name='answer')` |
| `outcome` | `models.CharField(max_length=40)` |
| `blocks` | `models.JSONField(default=list)` |
| `verification_status` | `models.CharField(max_length=30)` |
| `profile_revision` | `models.PositiveIntegerField(null=True)` |
| `corpus_release` | `models.ForeignKey(CorpusRelease, null=True, on_delete=models.PROTECT)` |

### AnswerClaim

Source: `backend/apps/adviser/models.py:398`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `answer` | `models.ForeignKey(AnswerArtifact, on_delete=models.CASCADE, related_name='claims')` |
| `claim_type` | `models.CharField(max_length=40)` |
| `display_text` | `models.TextField()` |
| `fact_ids` | `models.JSONField(default=list)` |
| `evidence_bundles` | `models.ManyToManyField(EvidenceBundle)` |
| `verification_result` | `models.CharField(max_length=30)` |

### RecommendationSnapshot

Source: `backend/apps/adviser/models.py:407`. Includes UUIDModel fields.

| Field | Existing declaration |
|---|---|
| `answer` | `models.OneToOneField(AnswerArtifact, null=True, on_delete=models.CASCADE)` |
| `owner` | `models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)` |
| `profile_revision` | `models.PositiveIntegerField()` |
| `corpus_release` | `models.ForeignKey(CorpusRelease, on_delete=models.PROTECT)` |
| `candidate_results` | `models.JSONField(default=list)` |
| `rankings` | `models.JSONField(default=list)` |
| `calculations` | `models.JSONField(default=list)` |
| `rule_version` | `models.CharField(max_length=50)` |

### AIPreference

Source: `backend/apps/adviser/models.py:418`. See inherited/implicit fields noted above and below.

| Field | Existing declaration |
|---|---|
| `user` | `models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)` |
| `route` | `models.ForeignKey(RouteConfiguration, null=True, on_delete=models.PROTECT)` |
| `updated_at` | `models.DateTimeField(auto_now=True)` |

## Implicit framework records and joins

The source installs auth, contenttypes, sessions and admin. Their records are part of preservation even though they are not application model declarations:

| Existing record | Fields and links to preserve | Qualification |
|---|---|---|
| Session | session_key (primary key), session_data, expire_date | Preserve securely; do not decode or print customer sessions during reporting. Confirm actual configured session backend before rehearsing. |
| Group | id, name, permissions join | Preserve user-group links and effective privileges. |
| Permission | id, name, content_type_id, codename | If numeric IDs change, map by content-type app_label/model and codename. New model permissions need deliberate review, not blind privilege escalation. |
| ContentType | id, app_label, model | Required for permissions and admin historical object references. |
| LogEntry | id, action_time, user_id, content_type_id, object_id, object_repr, action_flag, change_message | Object IDs are text and can refer to renamed/replaced models; preserve old reference context. Audit text may contain private data and belongs under retention/access controls. |
| User.groups / User.user_permissions / Group.permissions joins | implicit id and both relationship keys | Preserve exact memberships and check uniqueness. |
| Clause.evidence_bundles / AnswerClaim.evidence_bundles joins | implicit id and both relationship keys | Preserve citation relationships; there is no explicit order field in these implicit joins. |
| EvidenceBundleSpan | implicit BigAutoField id plus declared bundle, span, role and order | Ordered by order then id; preserve tie ordering. |
| django_migrations | id, app, name, applied | Snapshot migration state separately for the old database. Do not import it blindly into a differently designed replacement database. |

Framework field names above were checked against installed Django source. Actual deployed framework/version, table state, extra indexes, sequences, views and extensions remain for isolated inventory/rehearsal. The pilot migration files include vector extension enablement; model code alone does not prove the current database's extension versions.

## Relationship and invariant preservation

- Root customer ownership follows User → Conversation → ProfileRevision, Message, Turn and TurnAttempt; TurnAttempt → AnswerArtifact → AnswerClaim; User → RecommendationSnapshot and AIPreference. The snapshot also optionally links to an answer. Deleting owners/conversations normally cascades through their data, while Message.answer and Conversation.current_profile/active_attempt are nullable references using SET_NULL.
- Conversation and ProfileRevision/TurnAttempt form insertion-order cycles. A future import must preserve IDs, load permissible null pointers, load referenced history, then restore validated pointers in an approved process. current_profile must belong to its conversation; active_attempt must belong to its conversation and have a valid current status. Do not use a global revision-number join.
- TurnAttempt.conversation must agree with Turn.conversation. The model save method checks this, but bulk imports bypass save. Validate it independently. The database constraint allows only one accepted/running attempt per conversation. The active pointer and status restriction require separate reconciliation.
- Unique constraints include insurer/name; catalogue ditto_path; plan insurer/uin/variant/effective_from with NULLS NOT DISTINCT; plan/document/role; document/extraction revision; extraction/page index; bundle/span; conversation/profile revision; conversation/request ID; one active attempt per conversation; one current corpus; route configuration hash; source hash/path; and declared one-to-one/primary keys. Preserve literal empty versus null identity components before any semantic normalization. This is an inventory of old constraints, not a recommendation to replicate them.
- Original evidence dependencies use PROTECT through insurer/product/document/blob/extraction/page/span and bundle references. These are shared knowledge, not account-owned customer rows. Preserve extraction artifact files alongside database references; copy byte-identical compressed maps because artifact hashes address the compressed bytes.
- ReviewEvent.object_type/object_id and expected_revision are generic strings/UUIDs with no target FK. CorpusRelease.manifest, RecommendationSnapshot JSON, AnswerClaim.fact_ids and applicability/value structures can embed identifiers outside relational constraints. Every embedded reference needs an explicit map, unresolved reporting and dependency check; a SQL FK pass alone is insufficient.
- Migration 0010 creates PostgreSQL triggers forbidding changes to route configurations except qualification_state and forbidding qualification updates. Preserve immutable historical records; do not refresh old base URLs/model names in place. Reusing a saved user route preference requires current qualification rather than merely copying a FK.

## Service behavior that affects translation

`services.owned_conversation` filters by owner; profile revision and confirmation use row locks and expected revision conflicts. `revise_profile` shallow-merges JSON and records supplied/unconfirmed per-field metadata, then supersedes active attempts. This provenance does not establish exact original turn, medical subject or evidence by itself. `confirm_profile` changes confirmation metadata on an existing revision, so a revision is not a fully immutable event log.

`accept_turn` hashes canonical request JSON, makes one user message and a persisted turn/attempt under a transaction, and reuses matching request IDs. It does not give Message a FK to Turn; exact mapping of historical user messages to turns must not be inferred from approximate timestamp or repeated content alone. Assistant messages gained a nullable answer link in migration 0007 without backfilling old links. Preserve unresolved historical messages as messages, without guessing answer ownership.

`publish_ai_answer` verifies profile revision, route, corpus and evidence before saving; interview suggestions remain answer blocks. `publish_controlled_answer` and model-assisted publication can produce legacy outcomes whose safety scope is narrower than the intended replacement. Preserve original outcome/code and validation label, while withholding new completion claims.

`streaming.py` currently yields accepted/progress/result events from the request-owned async stream and performs the model call there. No durable event model appears in the complete adviser model ledger. `tasks.py` implements abandoned-turn reconciliation and a cache health marker. Existing attempt/answer history therefore cannot be promoted into a fabricated complete event log or worker-owned execution history. Retain what exists and label missing historical events explicitly. Redis cache state and in-flight requests must be inventoried operationally before cutover; no Redis data was read here.

`source_maps.store_pdf_bytes` writes content-addressed originals beneath the configured DATA_ROOT source-blobs directory; `extract_native_document` writes compressed frozen extraction maps under extractions. `verified_source_path` and evidence loading validate file hashes. Storage roots and X-Accel private-file routing must be preserved or deliberately mapped; do not place the originals or medical artifacts in a new public web directory.

## Isolated rehearsal and reversible cutover evidence still required

1. After database-design approval, identify the exact active database, services, migration state, filesystems, framework versions, runtime key/session configuration and any extra storage. Record an authorized consistent snapshot boundary and a private manifest; do not print credentials or customer values.
2. Back up the pilot database and all original/extraction bytes consistently. Verify restore in isolated infrastructure with separate database, queue/cache namespace, storage and service ports. Prevent restored workers/crawlers/relay calls from executing merely because historical active attempts were imported.
3. Establish exact source/target identity maps and per-table/set accounting. Compare field-level values securely, including unchanged encoded password bytes, original document hashes, ordered messages, profile history, embedded citation references and unresolved mappings. Preserve all legacy records that lack a safe semantic translation; never coerce them to complete/verified facts.
4. Exercise login using controlled rehearsal accounts without rotating real passwords; check account privilege equivalence, session continuity where intended, ownership rejection, reopened history, citation downloads, deleted-record non-resurrection and request idempotency. Verify frozen extraction geometry and historical corpus/route selection. These checks have not run.
5. Rehearse rollback to the retained pilot with the matching database/files/configuration, including routing, queues and current corpus. Define what happens to new writes, password changes and deletion requests during/after cutover; restoring an older snapshot alone can lose new data or resurrect deleted data. Agree the reverse synchronization or bounded maintenance strategy before cutover.
6. Preserve the existing pilot until acceptance and rollback evidence are approved. Production cutover remains separately authorized; this document neither requests nor executes it.

The next design discussion should resolve uncertain translations and operational retention/concurrency/session choices alongside the scenario-derived requirements. No replacement schema is selected by this inventory.
