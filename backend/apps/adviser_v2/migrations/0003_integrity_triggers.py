"""Deferred cross-row invariants from the approved r25 design."""

from __future__ import annotations

import hashlib

from django.db import migrations


def _trigger_name(table: str, field: str, suffix: str) -> str:
    raw = f"{table}_{field}_{suffix}"
    if len(raw) <= 60:
        return raw
    return f"{raw[:51]}_{hashlib.sha1(raw.encode()).hexdigest()[:8]}"


OWNER_TABLES = [
    "person",
    "person_relationship",
    "conversation",
    "message",
    "conversation_message_chunk",
    "customer_statement",
    "customer_profile_revision",
    "customer_fact",
    "customer_requirement",
    "advice_request",
    "original_file",
    "customer_uploaded_document",
    "customer_policy",
    "customer_policy_revision",
    "policy_member",
    "customer_policy_option",
    "customer_policy_fact",
    "quote",
    "recommendation",
    "policy_candidate_assessment",
    "policy_requirement_match",
    "information_need",
    "recommendation_statement",
    "recommendation_citation",
    "calculation",
    "turn",
    "turn_event",
    "outbox",
    "model_attempt",
    "processing_job",
    "consent_record",
    "deletion_request",
    "audit_event",
]

ALL_TABLES = [
    "person",
    "person_relationship",
    "conversation",
    "message",
    "conversation_message_chunk",
    "customer_statement",
    "customer_profile_revision",
    "customer_fact",
    "customer_requirement",
    "advice_request",
    "insurer",
    "discovery_run",
    "source_url",
    "source_observation",
    "source_capture",
    "original_file",
    "customer_uploaded_document",
    "document_series",
    "document_version",
    "document_page",
    "evidence_span",
    "product",
    "policy_version",
    "policy_version_document",
    "product_variant",
    "product_option",
    "customer_policy",
    "customer_policy_revision",
    "policy_member",
    "customer_policy_option",
    "customer_policy_fact",
    "policy_rule",
    "policy_rule_evidence",
    "policy_rule_link",
    "policy_rule_table_cell",
    "provider_location",
    "provider_network_snapshot",
    "provider_network_entry",
    "quote",
    "knowledge_release",
    "knowledge_release_rule",
    "knowledge_channel",
    "policy_search_chunk",
    "recommendation",
    "policy_candidate_assessment",
    "policy_requirement_match",
    "information_need",
    "recommendation_statement",
    "recommendation_citation",
    "calculation",
    "turn",
    "turn_event",
    "outbox",
    "model_route",
    "model_qualification",
    "model_attempt",
    "processing_job",
    "consent_record",
    "deletion_request",
    "audit_event",
    "policy_package_component",
]

# source table, FK column, owner-bearing target table
OWNER_LINKS = [
    ("person_relationship", "from_person_id", "person"),
    ("person_relationship", "to_person_id", "person"),
    ("person_relationship", "source_statement_id", "customer_statement"),
    ("conversation", "current_profile_revision_id", "customer_profile_revision"),
    ("message", "conversation_id", "conversation"),
    ("message", "recommendation_id", "recommendation"),
    ("conversation_message_chunk", "conversation_id", "conversation"),
    ("conversation_message_chunk", "message_id", "message"),
    ("customer_statement", "source_message_id", "message"),
    ("customer_statement", "subject_person_id", "person"),
    ("customer_profile_revision", "conversation_id", "conversation"),
    ("customer_fact", "introduced_in_revision_id", "customer_profile_revision"),
    ("customer_fact", "source_statement_id", "customer_statement"),
    ("customer_requirement", "introduced_in_revision_id", "customer_profile_revision"),
    ("customer_requirement", "source_statement_id", "customer_statement"),
    ("customer_requirement", "subject_person_id", "person"),
    ("advice_request", "conversation_id", "conversation"),
    ("advice_request", "source_statement_id", "customer_statement"),
    ("customer_uploaded_document", "original_file_id", "original_file"),
    ("customer_uploaded_document", "source_message_id", "message"),
    ("customer_policy", "proposer_id", "person"),
    ("customer_policy", "payer_id", "person"),
    ("customer_policy_revision", "customer_policy_id", "customer_policy"),
    ("policy_member", "customer_policy_revision_id", "customer_policy_revision"),
    ("policy_member", "person_id", "person"),
    ("customer_policy_option", "customer_policy_revision_id", "customer_policy_revision"),
    ("customer_policy_fact", "customer_policy_revision_id", "customer_policy_revision"),
    ("customer_policy_fact", "person_id", "person"),
    ("customer_policy_fact", "related_customer_policy_id", "customer_policy"),
    ("customer_policy_fact", "supersedes_id", "customer_policy_fact"),
    ("quote", "profile_revision_id", "customer_profile_revision"),
    ("recommendation", "turn_id", "turn"),
    ("recommendation", "advice_request_id", "advice_request"),
    ("recommendation", "profile_revision_id", "customer_profile_revision"),
    ("recommendation", "supersedes_id", "recommendation"),
    ("policy_candidate_assessment", "recommendation_id", "recommendation"),
    ("policy_candidate_assessment", "quote_id", "quote"),
    ("policy_requirement_match", "candidate_assessment_id", "policy_candidate_assessment"),
    ("policy_requirement_match", "customer_requirement_id", "customer_requirement"),
    ("information_need", "recommendation_id", "recommendation"),
    ("information_need", "subject_person_id", "person"),
    ("information_need", "asked_in_message_id", "message"),
    ("information_need", "resolved_in_profile_revision_id", "customer_profile_revision"),
    ("recommendation_statement", "recommendation_id", "recommendation"),
    ("recommendation_statement", "candidate_assessment_id", "policy_candidate_assessment"),
    ("recommendation_statement", "requirement_match_id", "policy_requirement_match"),
    ("recommendation_statement", "information_need_id", "information_need"),
    ("recommendation_statement", "calculation_id", "calculation"),
    ("recommendation_citation", "recommendation_statement_id", "recommendation_statement"),
    ("calculation", "advice_request_id", "advice_request"),
    ("turn", "conversation_id", "conversation"),
    ("turn", "input_message_id", "message"),
    ("turn", "starting_profile_revision_id", "customer_profile_revision"),
    ("turn_event", "turn_id", "turn"),
    ("outbox", "turn_id", "turn"),
    ("outbox", "processing_job_id", "processing_job"),
    ("model_attempt", "turn_id", "turn"),
    ("model_attempt", "processing_job_id", "processing_job"),
    ("processing_job", "customer_uploaded_document_id", "customer_uploaded_document"),
    ("consent_record", "person_id", "person"),
    ("consent_record", "source_message_id", "message"),
]

LINEAGES = [
    ("document_version", "supersedes_id", ["document_series_id"]),
    ("policy_version", "supersedes_id", ["product_id"]),
    ("policy_rule", "supersedes_id", ["policy_version_id", "rule_key"]),
    (
        "customer_policy_fact",
        "supersedes_id",
        ["owner_id", "customer_policy_revision_id", "fact_type"],
    ),
    ("recommendation", "supersedes_id", ["owner_id", "advice_request_id"]),
    ("provider_location", "supersedes_id", []),
]


FUNCTIONS_SQL = r"""
CREATE OR REPLACE FUNCTION adviser_v2_assert_identity_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.id IS DISTINCT FROM OLD.id THEN
        RAISE EXCEPTION 'CoverGuide stable row IDs are immutable';
    END IF;
    IF TG_NARGS > 0 AND (to_jsonb(NEW)->>TG_ARGV[0]) IS DISTINCT FROM
       (to_jsonb(OLD)->>TG_ARGV[0]) THEN
        RAISE EXCEPTION 'CoverGuide row ownership is immutable';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_owner_fk()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    source_owner text;
    reference_id uuid;
    target_owner text;
BEGIN
    source_owner := to_jsonb(NEW)->>'owner_id';
    reference_id := NULLIF(to_jsonb(NEW)->>TG_ARGV[0], '')::uuid;
    IF reference_id IS NULL THEN
        RETURN NEW;
    END IF;
    EXECUTE format('SELECT owner_id::text FROM %I WHERE id = $1 FOR KEY SHARE', TG_ARGV[1])
        INTO target_owner USING reference_id;
    IF target_owner IS NULL THEN
        RAISE EXCEPTION 'Referenced CoverGuide row does not exist';
    END IF;
    IF source_owner IS DISTINCT FROM target_owner THEN
        RAISE EXCEPTION 'Cross-owner CoverGuide relationship rejected';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_next_sequence()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    group_value text;
    expected bigint;
    supplied bigint;
BEGIN
    group_value := to_jsonb(NEW)->>TG_ARGV[0];
    supplied := (to_jsonb(NEW)->>TG_ARGV[1])::bigint;
    PERFORM pg_advisory_xact_lock(hashtextextended(TG_TABLE_NAME || ':' || group_value, 9125));
    EXECUTE format(
        'SELECT COALESCE(MAX(%I), 0) + 1 FROM %I WHERE %I::text = $1',
        TG_ARGV[1], TG_TABLE_NAME, TG_ARGV[0]
    ) INTO expected USING group_value;
    IF supplied <> expected THEN
        RAISE EXCEPTION 'CoverGuide sequence must be the next value (expected %, got %)',
            expected, supplied;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_next_release()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected bigint;
BEGIN
    PERFORM pg_advisory_xact_lock(284651982);
    SELECT COALESCE(MAX(release_number), 0) + 1 INTO expected
      FROM adviser_v2_knowledge_release;
    IF NEW.release_number <> expected THEN
        RAISE EXCEPTION 'Knowledge release number must be the next value (expected %, got %)',
            expected, NEW.release_number;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_lineage()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    parent_id uuid;
    parent_row jsonb;
    has_cycle boolean;
    index integer;
BEGIN
    parent_id := NULLIF(to_jsonb(NEW)->>TG_ARGV[0], '')::uuid;
    IF parent_id IS NULL THEN
        RETURN NEW;
    END IF;
    IF parent_id = NEW.id THEN
        RAISE EXCEPTION 'CoverGuide lineage cannot self-reference';
    END IF;
    EXECUTE format('SELECT to_jsonb(t) FROM %I t WHERE id = $1 FOR KEY SHARE', TG_TABLE_NAME)
        INTO parent_row USING parent_id;
    IF parent_row IS NULL THEN
        RAISE EXCEPTION 'CoverGuide lineage parent does not exist';
    END IF;
    IF TG_NARGS > 1 THEN
        FOR index IN 1..TG_NARGS - 1 LOOP
            IF (to_jsonb(NEW)->>TG_ARGV[index]) IS DISTINCT FROM
               (parent_row->>TG_ARGV[index]) THEN
                RAISE EXCEPTION 'CoverGuide lineage crosses an immutable partition';
            END IF;
        END LOOP;
    END IF;
    EXECUTE format(
        'WITH RECURSIVE chain(id, parent_id) AS ('
        ' SELECT id, %1$I FROM %2$I WHERE id = $1'
        ' UNION SELECT row.id, row.%1$I FROM %2$I row JOIN chain ON row.id = chain.parent_id'
        ') SELECT EXISTS (SELECT 1 FROM chain WHERE id = $2)',
        TG_ARGV[0], TG_TABLE_NAME
    ) INTO has_cycle USING parent_id, NEW.id;
    IF has_cycle THEN
        RAISE EXCEPTION 'CoverGuide lineage cycle rejected';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_contractual_authority()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE authority_value text;
BEGIN
    SELECT series.authority INTO authority_value
      FROM adviser_v2_document_version version
      JOIN adviser_v2_document_series series ON series.id = version.document_series_id
     WHERE version.id = NEW.document_version_id
     FOR KEY SHARE OF version, series;
    IF authority_value NOT IN ('insurer_issued', 'regulator_issued') THEN
        RAISE EXCEPTION 'Contractual policy documents require insurer or regulator authority';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_rule_evidence_authority()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE evidence_is_valid boolean;
BEGIN
    SELECT EXISTS (
        SELECT 1
          FROM adviser_v2_policy_rule rule
          JOIN adviser_v2_evidence_span span ON span.id = NEW.evidence_span_id
          JOIN adviser_v2_source_capture capture ON capture.id = span.source_capture_id
          JOIN adviser_v2_policy_version_document membership
            ON membership.policy_version_id = rule.policy_version_id
           AND membership.document_version_id = capture.document_version_id
         WHERE rule.id = NEW.policy_rule_id
           AND span.customer_uploaded_document_id IS NULL
           AND capture.status = 'captured'
    ) INTO evidence_is_valid;
    IF NOT evidence_is_valid THEN
        RAISE EXCEPTION 'Policy rule evidence must be public, captured and in the exact policy bundle';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_verified_rule()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE evidence_count integer;
DECLARE bad_evidence_count integer;
BEGIN
    IF NEW.review_status <> 'verified' THEN
        RETURN NEW;
    END IF;
    SELECT COUNT(*), COUNT(*) FILTER (
        WHERE span.verification NOT IN ('text_verified', 'visually_verified', 'reviewed')
    ) INTO evidence_count, bad_evidence_count
      FROM adviser_v2_policy_rule_evidence link
      JOIN adviser_v2_evidence_span span ON span.id = link.evidence_span_id
     WHERE link.policy_rule_id = NEW.id AND link.is_required;
    IF evidence_count = 0 OR bad_evidence_count > 0 THEN
        RAISE EXCEPTION 'A verified policy rule requires verified, exact required evidence';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_release_rule()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE valid_rule boolean;
DECLARE release_state text;
BEGIN
    SELECT state INTO release_state FROM adviser_v2_knowledge_release
     WHERE id = NEW.knowledge_release_id FOR KEY SHARE;
    IF release_state IN ('published', 'retired') THEN
        RAISE EXCEPTION 'Published knowledge-release membership is immutable';
    END IF;
    SELECT EXISTS (
        SELECT 1 FROM adviser_v2_policy_rule rule
         WHERE rule.id = NEW.policy_rule_id
           AND rule.review_status = 'verified'
           AND NOT EXISTS (
               SELECT 1 FROM adviser_v2_policy_rule successor
                WHERE successor.supersedes_id = rule.id
           )
    ) INTO valid_rule;
    IF NOT valid_rule THEN
        RAISE EXCEPTION 'Only a verified unsuperseded rule may enter a knowledge release';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_release_rule_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE release_id uuid;
DECLARE release_state text;
BEGIN
    release_id := COALESCE(NEW.knowledge_release_id, OLD.knowledge_release_id);
    SELECT state INTO release_state FROM adviser_v2_knowledge_release
     WHERE id = release_id FOR KEY SHARE;
    IF release_state IN ('published', 'retired') THEN
        RAISE EXCEPTION 'Published knowledge-release membership is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_release_publication()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE product_count integer;
DECLARE invalid_count integer;
DECLARE missing_link_count integer;
BEGIN
    IF NEW.state <> 'published' OR OLD.state = 'published' THEN
        RETURN NEW;
    END IF;
    SELECT COUNT(DISTINCT version.product_id),
           COUNT(*) FILTER (
               WHERE rule.review_status <> 'verified'
                  OR version.publication_status <> 'published'
                  OR EXISTS (
                      SELECT 1 FROM adviser_v2_policy_rule successor
                       WHERE successor.supersedes_id = rule.id
                  )
           )
      INTO product_count, invalid_count
      FROM adviser_v2_knowledge_release_rule member
      JOIN adviser_v2_policy_rule rule ON rule.id = member.policy_rule_id
      JOIN adviser_v2_policy_version version ON version.id = rule.policy_version_id
     WHERE member.knowledge_release_id = NEW.id;
    IF product_count <> 5 OR invalid_count > 0 THEN
        RAISE EXCEPTION 'Publication requires exactly five products and only published verified rules';
    END IF;
    SELECT COUNT(*) INTO missing_link_count
      FROM adviser_v2_knowledge_release_rule member
      JOIN adviser_v2_policy_rule_link link ON link.from_policy_rule_id = member.policy_rule_id
      LEFT JOIN adviser_v2_knowledge_release_rule linked
        ON linked.knowledge_release_id = member.knowledge_release_id
       AND linked.policy_rule_id = link.to_policy_rule_id
     WHERE member.knowledge_release_id = NEW.id
       AND linked.id IS NULL;
    IF missing_link_count > 0 THEN
        RAISE EXCEPTION 'Knowledge release is missing mandatory linked-rule closure';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_current_release()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE selected_state text;
BEGIN
    IF NEW.current_release_id IS NOT NULL THEN
        SELECT state INTO selected_state FROM adviser_v2_knowledge_release
         WHERE id = NEW.current_release_id FOR KEY SHARE;
        IF selected_state <> 'published' THEN
            RAISE EXCEPTION 'Knowledge channels may select only a published release';
        END IF;
    END IF;
    IF TG_OP = 'UPDATE' AND NEW.current_release_id IS DISTINCT FROM OLD.current_release_id
       AND NEW.generation <> OLD.generation + 1 THEN
        RAISE EXCEPTION 'Knowledge channel generation must advance exactly once with release selection';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_lease_fence()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE supplied text;
BEGIN
    IF OLD.state = 'running' AND NEW.state <> OLD.state
       AND NEW.state NOT IN ('cancel_requested') THEN
        supplied := current_setting('coverguide.lease_token', true);
        IF supplied IS NULL OR supplied = '' OR supplied::uuid IS DISTINCT FROM OLD.lease_token
           OR OLD.lease_until <= statement_timestamp() THEN
            RAISE EXCEPTION 'Stale or unfenced CoverGuide worker cannot publish';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION adviser_v2_assert_model_route_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (to_jsonb(NEW) - 'disabled_at') IS DISTINCT FROM (to_jsonb(OLD) - 'disabled_at') THEN
        RAISE EXCEPTION 'Model route revisions are immutable';
    END IF;
    IF OLD.disabled_at IS NOT NULL AND NEW.disabled_at IS DISTINCT FROM OLD.disabled_at THEN
        RAISE EXCEPTION 'A disabled model route cannot be re-enabled or rewritten';
    END IF;
    RETURN NEW;
END;
$$;
"""


def _identity_trigger_sql() -> str:
    owner_tables = set(OWNER_TABLES)
    statements = []
    for short_table in ALL_TABLES:
        table = f"adviser_v2_{short_table}"
        arguments = "('owner_id')" if short_table in owner_tables else "()"
        statements.append(
            f"CREATE TRIGGER {_trigger_name(table, 'identity', 'immut')} "
            f"BEFORE UPDATE ON {table} FOR EACH ROW "
            f"EXECUTE FUNCTION adviser_v2_assert_identity_immutable{arguments};"
        )
    return "\n".join(statements)


def _owner_trigger_sql() -> str:
    statements = []
    for short_table, field, target in OWNER_LINKS:
        table = f"adviser_v2_{short_table}"
        target_table = f"adviser_v2_{target}"
        statements.append(
            f"CREATE CONSTRAINT TRIGGER {_trigger_name(table, field, 'owner')} "
            f"AFTER INSERT OR UPDATE OF {field}, owner_id ON {table} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            f"EXECUTE FUNCTION adviser_v2_assert_owner_fk('{field}', '{target_table}');"
        )
    return "\n".join(statements)


def _lineage_trigger_sql() -> str:
    statements = []
    for short_table, field, partitions in LINEAGES:
        table = f"adviser_v2_{short_table}"
        arguments = ", ".join(repr(item) for item in [field, *partitions])
        watched = ", ".join([field, *partitions])
        statements.append(
            f"CREATE CONSTRAINT TRIGGER {_trigger_name(table, field, 'lineage')} "
            f"AFTER INSERT OR UPDATE OF {watched} ON {table} "
            "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
            f"EXECUTE FUNCTION adviser_v2_assert_lineage({arguments});"
        )
    return "\n".join(statements)


TRIGGERS_SQL = "\n".join(
    [
        _identity_trigger_sql(),
        _owner_trigger_sql(),
        _lineage_trigger_sql(),
        """
CREATE TRIGGER adviser_v2_profile_revision_next
BEFORE INSERT ON adviser_v2_customer_profile_revision FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_next_sequence('conversation_id', 'revision');
CREATE TRIGGER adviser_v2_policy_revision_next
BEFORE INSERT ON adviser_v2_customer_policy_revision FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_next_sequence('customer_policy_id', 'revision_number');
CREATE TRIGGER adviser_v2_message_sequence_next
BEFORE INSERT ON adviser_v2_message FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_next_sequence('conversation_id', 'sequence');
CREATE TRIGGER adviser_v2_release_number_next
BEFORE INSERT ON adviser_v2_knowledge_release FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_next_release();

CREATE CONSTRAINT TRIGGER adviser_v2_document_authority
AFTER INSERT OR UPDATE OF document_version_id, role ON adviser_v2_policy_version_document
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_contractual_authority();
CREATE CONSTRAINT TRIGGER adviser_v2_rule_evidence_authority
AFTER INSERT OR UPDATE OF policy_rule_id, evidence_span_id ON adviser_v2_policy_rule_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_rule_evidence_authority();
CREATE CONSTRAINT TRIGGER adviser_v2_verified_rule_evidence
AFTER INSERT OR UPDATE OF review_status ON adviser_v2_policy_rule
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_verified_rule();
CREATE TRIGGER adviser_v2_release_rule_valid
BEFORE INSERT OR UPDATE ON adviser_v2_knowledge_release_rule FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_release_rule();
CREATE TRIGGER adviser_v2_release_rule_mutable
BEFORE UPDATE OR DELETE ON adviser_v2_knowledge_release_rule FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_release_rule_mutation();
CREATE CONSTRAINT TRIGGER adviser_v2_release_publishable
AFTER UPDATE OF state ON adviser_v2_knowledge_release
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_release_publication();
CREATE CONSTRAINT TRIGGER adviser_v2_channel_current_release
AFTER INSERT OR UPDATE OF current_release_id, generation ON adviser_v2_knowledge_channel
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_current_release();

CREATE TRIGGER adviser_v2_turn_lease_fence
BEFORE UPDATE OF state ON adviser_v2_turn FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_lease_fence();
CREATE TRIGGER adviser_v2_processing_lease_fence
BEFORE UPDATE OF state ON adviser_v2_processing_job FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_lease_fence();
CREATE TRIGGER adviser_v2_model_route_immutable
BEFORE UPDATE ON adviser_v2_model_route FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_model_route_immutable();

ALTER TABLE adviser_v2_message
  ADD CONSTRAINT adviser_v2_message_commitment_hex
  CHECK (payload_commitment ~ '^[0-9a-f]{64}$');
ALTER TABLE adviser_v2_conversation_message_chunk
  ADD CONSTRAINT adviser_v2_chunk_commitment_hex
  CHECK (content_commitment ~ '^[0-9a-f]{64}$');
ALTER TABLE adviser_v2_policy_candidate_assessment
  ADD CONSTRAINT adviser_v2_selection_commitment_hex
  CHECK (selection_commitment ~ '^[0-9a-f]{64}$');
ALTER TABLE adviser_v2_model_attempt
  ADD CONSTRAINT adviser_v2_request_commitment_hex
  CHECK (request_commitment ~ '^[0-9a-f]{64}$');
ALTER TABLE adviser_v2_processing_job
  ADD CONSTRAINT adviser_v2_input_commitment_hex
  CHECK (input_commitment ~ '^[0-9a-f]{64}$');
CREATE UNIQUE INDEX adviser_v2_model_attempt_turn_number
  ON adviser_v2_model_attempt(turn_id, attempt_number) WHERE turn_id IS NOT NULL;
CREATE UNIQUE INDEX adviser_v2_model_attempt_job_number
  ON adviser_v2_model_attempt(processing_job_id, attempt_number)
  WHERE processing_job_id IS NOT NULL;
""",
    ]
)


def _reverse_sql() -> str:
    statements = []
    for short_table in ALL_TABLES:
        table = f"adviser_v2_{short_table}"
        statements.append(
            f"DROP TRIGGER IF EXISTS {_trigger_name(table, 'identity', 'immut')} ON {table};"
        )
    for short_table, field, _ in OWNER_LINKS:
        table = f"adviser_v2_{short_table}"
        statements.append(
            f"DROP TRIGGER IF EXISTS {_trigger_name(table, field, 'owner')} ON {table};"
        )
    for short_table, field, _ in LINEAGES:
        table = f"adviser_v2_{short_table}"
        statements.append(
            f"DROP TRIGGER IF EXISTS {_trigger_name(table, field, 'lineage')} ON {table};"
        )
    statements.append(
        r"""
DROP TRIGGER IF EXISTS adviser_v2_profile_revision_next ON adviser_v2_customer_profile_revision;
DROP TRIGGER IF EXISTS adviser_v2_policy_revision_next ON adviser_v2_customer_policy_revision;
DROP TRIGGER IF EXISTS adviser_v2_message_sequence_next ON adviser_v2_message;
DROP TRIGGER IF EXISTS adviser_v2_release_number_next ON adviser_v2_knowledge_release;
DROP TRIGGER IF EXISTS adviser_v2_document_authority ON adviser_v2_policy_version_document;
DROP TRIGGER IF EXISTS adviser_v2_rule_evidence_authority ON adviser_v2_policy_rule_evidence;
DROP TRIGGER IF EXISTS adviser_v2_verified_rule_evidence ON adviser_v2_policy_rule;
DROP TRIGGER IF EXISTS adviser_v2_release_rule_valid ON adviser_v2_knowledge_release_rule;
DROP TRIGGER IF EXISTS adviser_v2_release_rule_mutable ON adviser_v2_knowledge_release_rule;
DROP TRIGGER IF EXISTS adviser_v2_release_publishable ON adviser_v2_knowledge_release;
DROP TRIGGER IF EXISTS adviser_v2_channel_current_release ON adviser_v2_knowledge_channel;
DROP TRIGGER IF EXISTS adviser_v2_turn_lease_fence ON adviser_v2_turn;
DROP TRIGGER IF EXISTS adviser_v2_processing_lease_fence ON adviser_v2_processing_job;
DROP TRIGGER IF EXISTS adviser_v2_model_route_immutable ON adviser_v2_model_route;
DROP INDEX IF EXISTS adviser_v2_model_attempt_turn_number;
DROP INDEX IF EXISTS adviser_v2_model_attempt_job_number;
ALTER TABLE adviser_v2_message DROP CONSTRAINT IF EXISTS adviser_v2_message_commitment_hex;
ALTER TABLE adviser_v2_conversation_message_chunk DROP CONSTRAINT IF EXISTS adviser_v2_chunk_commitment_hex;
ALTER TABLE adviser_v2_policy_candidate_assessment DROP CONSTRAINT IF EXISTS adviser_v2_selection_commitment_hex;
ALTER TABLE adviser_v2_model_attempt DROP CONSTRAINT IF EXISTS adviser_v2_request_commitment_hex;
ALTER TABLE adviser_v2_processing_job DROP CONSTRAINT IF EXISTS adviser_v2_input_commitment_hex;
DROP FUNCTION IF EXISTS adviser_v2_assert_model_route_immutable();
DROP FUNCTION IF EXISTS adviser_v2_assert_lease_fence();
DROP FUNCTION IF EXISTS adviser_v2_assert_current_release();
DROP FUNCTION IF EXISTS adviser_v2_assert_release_publication();
DROP FUNCTION IF EXISTS adviser_v2_assert_release_rule_mutation();
DROP FUNCTION IF EXISTS adviser_v2_assert_release_rule();
DROP FUNCTION IF EXISTS adviser_v2_assert_verified_rule();
DROP FUNCTION IF EXISTS adviser_v2_assert_rule_evidence_authority();
DROP FUNCTION IF EXISTS adviser_v2_assert_contractual_authority();
DROP FUNCTION IF EXISTS adviser_v2_assert_lineage();
DROP FUNCTION IF EXISTS adviser_v2_assert_next_release();
DROP FUNCTION IF EXISTS adviser_v2_assert_next_sequence();
DROP FUNCTION IF EXISTS adviser_v2_assert_owner_fk();
DROP FUNCTION IF EXISTS adviser_v2_assert_identity_immutable();
"""
    )
    return "\n".join(statements)


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0002_initial")]

    operations = [
        migrations.RunSQL(FUNCTIONS_SQL + "\n" + TRIGGERS_SQL, reverse_sql=_reverse_sql()),
    ]
