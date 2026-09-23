"""Replace ranked recommendation storage with neutral policy comparisons."""

from __future__ import annotations

from django.db import migrations, models

FORWARD_SQL = r"""
UPDATE adviser_v2_advice_request
   SET request_type = 'product_comparison'
 WHERE request_type = 'purchase_recommendation';

ALTER TABLE adviser_v2_turn_route_binding
  DROP CONSTRAINT IF EXISTS v2_turn_route_binding_role_ck;
UPDATE adviser_v2_turn_route_binding
   SET role = 'comparison_answer'
 WHERE role = 'recommendation_answer';

UPDATE adviser_v2_turn_event
   SET event_type = 'comparison',
       payload = (payload - 'decision_id' - 'kind')
                 || jsonb_build_object(
                      'kind', 'comparison',
                      'comparison_id', payload->'decision_id'
                    )
 WHERE event_type = 'recommendation';

ALTER TABLE adviser_v2_product
  RENAME COLUMN recommendation_role TO comparison_role;
ALTER TABLE adviser_v2_recommendation
  RENAME TO adviser_v2_comparison;
ALTER TABLE adviser_v2_message
  RENAME COLUMN recommendation_id TO comparison_id;
ALTER TABLE adviser_v2_policy_candidate_assessment
  RENAME TO adviser_v2_policy_comparison_assessment;
ALTER TABLE adviser_v2_policy_comparison_assessment
  RENAME COLUMN recommendation_id TO comparison_id;
ALTER TABLE adviser_v2_policy_requirement_match
  RENAME COLUMN candidate_assessment_id TO comparison_assessment_id;
ALTER TABLE adviser_v2_information_need
  RENAME COLUMN recommendation_id TO comparison_id;
ALTER TABLE adviser_v2_recommendation_statement
  RENAME TO adviser_v2_comparison_statement;
ALTER TABLE adviser_v2_comparison_statement
  RENAME COLUMN recommendation_id TO comparison_id;
ALTER TABLE adviser_v2_comparison_statement
  RENAME COLUMN candidate_assessment_id TO comparison_assessment_id;
ALTER TABLE adviser_v2_recommendation_citation
  RENAME TO adviser_v2_comparison_citation;
ALTER TABLE adviser_v2_comparison_citation
  RENAME COLUMN recommendation_statement_id TO comparison_statement_id;

ALTER TABLE adviser_v2_policy_comparison_assessment
  DROP CONSTRAINT IF EXISTS v2_policy_candidate_assessment_uq_2;
ALTER TABLE adviser_v2_policy_comparison_assessment
  DROP CONSTRAINT IF EXISTS v2_policy_candidate_assessment_ck_1;
ALTER TABLE adviser_v2_policy_comparison_assessment DROP COLUMN disposition;
ALTER TABLE adviser_v2_policy_comparison_assessment DROP COLUMN rank;

DO $$
DECLARE
    item record;
    proposed text;
BEGIN
    FOR item IN
        SELECT c.oid, c.conname, relation.relname
          FROM pg_constraint c
          JOIN pg_class relation ON relation.oid = c.conrelid
         WHERE relation.relname LIKE 'adviser_v2_%'
           AND (c.conname LIKE '%recommendation%' OR c.conname LIKE '%candidate_assessment%')
    LOOP
        proposed := replace(
            replace(
                replace(item.conname, 'policy_candidate_assessment', 'policy_comparison_assessment'),
                'candidate_assessment', 'comparison_assessment'
            ),
            'recommendation', 'comparison'
        );
        IF length(proposed) > 63 THEN
            proposed := left(proposed, 54) || '_' || left(md5(proposed), 8);
        END IF;
        EXECUTE format('ALTER TABLE %I RENAME CONSTRAINT %I TO %I', item.relname, item.conname, proposed);
    END LOOP;

    FOR item IN
        SELECT indexname
          FROM pg_indexes
         WHERE schemaname = current_schema()
           AND tablename LIKE 'adviser_v2_%'
           AND (indexname LIKE '%recommendation%' OR indexname LIKE '%candidate_assessment%')
    LOOP
        proposed := replace(
            replace(
                replace(item.indexname, 'policy_candidate_assessment', 'policy_comparison_assessment'),
                'candidate_assessment', 'comparison_assessment'
            ),
            'recommendation', 'comparison'
        );
        IF length(proposed) > 63 THEN
            proposed := left(proposed, 54) || '_' || left(md5(proposed), 8);
        END IF;
        EXECUTE format('ALTER INDEX %I RENAME TO %I', item.indexname, proposed);
    END LOOP;
END;
$$;

DO $$
DECLARE
    item record;
BEGIN
    FOR item IN
        SELECT relation.relname, trigger.tgname
          FROM pg_trigger trigger
          JOIN pg_class relation ON relation.oid = trigger.tgrelid
         WHERE NOT trigger.tgisinternal
           AND relation.relname IN (
               'adviser_v2_message',
               'adviser_v2_comparison',
               'adviser_v2_policy_comparison_assessment',
               'adviser_v2_policy_requirement_match',
               'adviser_v2_information_need',
               'adviser_v2_comparison_statement',
               'adviser_v2_comparison_citation'
           )
    LOOP
        EXECUTE format('DROP TRIGGER %I ON %I', item.tgname, item.relname);
    END LOOP;
END;
$$;

CREATE TRIGGER adviser_v2_message_identity_immut
BEFORE UPDATE ON adviser_v2_message FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_identity_immutable('owner_id');
CREATE CONSTRAINT TRIGGER adviser_v2_message_conversation_owner
AFTER INSERT OR UPDATE OF conversation_id, owner_id ON adviser_v2_message
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('conversation_id', 'adviser_v2_conversation');
CREATE CONSTRAINT TRIGGER adviser_v2_message_comparison_owner
AFTER INSERT OR UPDATE OF comparison_id, owner_id ON adviser_v2_message
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('comparison_id', 'adviser_v2_comparison');
CREATE TRIGGER adviser_v2_message_sequence_next
BEFORE INSERT ON adviser_v2_message FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_next_sequence('conversation_id', 'sequence');

CREATE TRIGGER adviser_v2_comparison_identity_immut
BEFORE UPDATE ON adviser_v2_comparison FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_identity_immutable('owner_id');
CREATE CONSTRAINT TRIGGER adviser_v2_comparison_turn_owner
AFTER INSERT OR UPDATE OF turn_id, owner_id ON adviser_v2_comparison
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('turn_id', 'adviser_v2_turn');
CREATE CONSTRAINT TRIGGER adviser_v2_comparison_request_owner
AFTER INSERT OR UPDATE OF advice_request_id, owner_id ON adviser_v2_comparison
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('advice_request_id', 'adviser_v2_advice_request');
CREATE CONSTRAINT TRIGGER adviser_v2_comparison_profile_owner
AFTER INSERT OR UPDATE OF profile_revision_id, owner_id ON adviser_v2_comparison
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('profile_revision_id', 'adviser_v2_customer_profile_revision');
CREATE CONSTRAINT TRIGGER adviser_v2_comparison_supersedes_owner
AFTER INSERT OR UPDATE OF supersedes_id, owner_id ON adviser_v2_comparison
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('supersedes_id', 'adviser_v2_comparison');
CREATE CONSTRAINT TRIGGER adviser_v2_comparison_supersedes_lineage
AFTER INSERT OR UPDATE OF supersedes_id, owner_id, advice_request_id ON adviser_v2_comparison
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_lineage('supersedes_id', 'owner_id', 'advice_request_id');

CREATE TRIGGER adviser_v2_policy_comparison_assessment_identity_immut
BEFORE UPDATE ON adviser_v2_policy_comparison_assessment FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_identity_immutable('owner_id');
CREATE CONSTRAINT TRIGGER adviser_v2_policy_comparison_parent_owner
AFTER INSERT OR UPDATE OF comparison_id, owner_id ON adviser_v2_policy_comparison_assessment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('comparison_id', 'adviser_v2_comparison');
CREATE CONSTRAINT TRIGGER adviser_v2_policy_comparison_quote_owner
AFTER INSERT OR UPDATE OF quote_id, owner_id ON adviser_v2_policy_comparison_assessment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('quote_id', 'adviser_v2_quote');

CREATE TRIGGER adviser_v2_policy_requirement_match_identity_immut
BEFORE UPDATE ON adviser_v2_policy_requirement_match FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_identity_immutable('owner_id');
CREATE CONSTRAINT TRIGGER adviser_v2_requirement_comparison_owner
AFTER INSERT OR UPDATE OF comparison_assessment_id, owner_id ON adviser_v2_policy_requirement_match
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('comparison_assessment_id', 'adviser_v2_policy_comparison_assessment');
CREATE CONSTRAINT TRIGGER adviser_v2_requirement_customer_owner
AFTER INSERT OR UPDATE OF customer_requirement_id, owner_id ON adviser_v2_policy_requirement_match
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('customer_requirement_id', 'adviser_v2_customer_requirement');

CREATE TRIGGER adviser_v2_information_need_identity_immut
BEFORE UPDATE ON adviser_v2_information_need FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_identity_immutable('owner_id');
CREATE CONSTRAINT TRIGGER adviser_v2_information_comparison_owner
AFTER INSERT OR UPDATE OF comparison_id, owner_id ON adviser_v2_information_need
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('comparison_id', 'adviser_v2_comparison');
CREATE CONSTRAINT TRIGGER adviser_v2_information_person_owner
AFTER INSERT OR UPDATE OF subject_person_id, owner_id ON adviser_v2_information_need
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('subject_person_id', 'adviser_v2_person');
CREATE CONSTRAINT TRIGGER adviser_v2_information_message_owner
AFTER INSERT OR UPDATE OF asked_in_message_id, owner_id ON adviser_v2_information_need
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('asked_in_message_id', 'adviser_v2_message');
CREATE CONSTRAINT TRIGGER adviser_v2_information_profile_owner
AFTER INSERT OR UPDATE OF resolved_in_profile_revision_id, owner_id ON adviser_v2_information_need
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('resolved_in_profile_revision_id', 'adviser_v2_customer_profile_revision');

CREATE TRIGGER adviser_v2_comparison_statement_identity_immut
BEFORE UPDATE ON adviser_v2_comparison_statement FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_identity_immutable('owner_id');
CREATE CONSTRAINT TRIGGER adviser_v2_statement_comparison_owner
AFTER INSERT OR UPDATE OF comparison_id, owner_id ON adviser_v2_comparison_statement
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('comparison_id', 'adviser_v2_comparison');
CREATE CONSTRAINT TRIGGER adviser_v2_statement_assessment_owner
AFTER INSERT OR UPDATE OF comparison_assessment_id, owner_id ON adviser_v2_comparison_statement
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('comparison_assessment_id', 'adviser_v2_policy_comparison_assessment');
CREATE CONSTRAINT TRIGGER adviser_v2_statement_match_owner
AFTER INSERT OR UPDATE OF requirement_match_id, owner_id ON adviser_v2_comparison_statement
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('requirement_match_id', 'adviser_v2_policy_requirement_match');
CREATE CONSTRAINT TRIGGER adviser_v2_statement_need_owner
AFTER INSERT OR UPDATE OF information_need_id, owner_id ON adviser_v2_comparison_statement
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('information_need_id', 'adviser_v2_information_need');
CREATE CONSTRAINT TRIGGER adviser_v2_statement_calculation_owner
AFTER INSERT OR UPDATE OF calculation_id, owner_id ON adviser_v2_comparison_statement
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('calculation_id', 'adviser_v2_calculation');

CREATE TRIGGER adviser_v2_comparison_citation_identity_immut
BEFORE UPDATE ON adviser_v2_comparison_citation FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_identity_immutable('owner_id');
CREATE CONSTRAINT TRIGGER adviser_v2_citation_statement_owner
AFTER INSERT OR UPDATE OF comparison_statement_id, owner_id ON adviser_v2_comparison_citation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION adviser_v2_assert_owner_fk('comparison_statement_id', 'adviser_v2_comparison_statement');

ALTER TABLE adviser_v2_turn_route_binding
  ADD CONSTRAINT v2_turn_route_binding_role_ck
  CHECK (role IN ('fact_interpretation', 'comparison_answer'));
"""


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0012_turn_route_bindings")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL)],
            state_operations=[
                migrations.RenameField("product", "recommendation_role", "comparison_role"),
                migrations.AlterField(
                    model_name="advicerequest",
                    name="request_type",
                    field=models.CharField(
                        choices=[
                            ("product_comparison", "product_comparison"),
                            ("coverage_question", "coverage_question"),
                            ("renewal_review", "renewal_review"),
                            ("portability_review", "portability_review"),
                        ],
                        max_length=18,
                    ),
                ),
                migrations.RenameModel("Recommendation", "Comparison"),
                migrations.AlterModelTable("comparison", "adviser_v2_comparison"),
                migrations.RemoveConstraint("comparison", "v2_recommendation_id_owner_uq"),
                migrations.RemoveConstraint("comparison", "v2_recommendation_uq_1"),
                migrations.AddConstraint(
                    "comparison",
                    models.UniqueConstraint(
                        fields=("id", "owner"), name="v2_comparison_id_owner_uq"
                    ),
                ),
                migrations.AddConstraint(
                    "comparison",
                    models.UniqueConstraint(fields=("turn",), name="v2_comparison_uq_1"),
                ),
                migrations.RenameField("message", "recommendation", "comparison"),
                migrations.RemoveConstraint("message", "v2_message_uq_3"),
                migrations.AddConstraint(
                    "message",
                    models.UniqueConstraint(
                        fields=("comparison",),
                        condition=models.Q(comparison__isnull=False),
                        name="v2_message_uq_3",
                    ),
                ),
                migrations.RenameModel("PolicyCandidateAssessment", "PolicyComparisonAssessment"),
                migrations.AlterModelTable(
                    "policycomparisonassessment",
                    "adviser_v2_policy_comparison_assessment",
                ),
                migrations.RenameField(
                    "policycomparisonassessment", "recommendation", "comparison"
                ),
                migrations.RemoveConstraint(
                    "policycomparisonassessment",
                    "v2_policy_candidate_assessment_id_owner_uq",
                ),
                migrations.RemoveConstraint(
                    "policycomparisonassessment", "v2_policy_candidate_assessment_uq_1"
                ),
                migrations.RemoveConstraint(
                    "policycomparisonassessment", "v2_policy_candidate_assessment_uq_2"
                ),
                migrations.RemoveConstraint(
                    "policycomparisonassessment", "v2_policy_candidate_assessment_ck_1"
                ),
                migrations.RemoveField("policycomparisonassessment", "disposition"),
                migrations.RemoveField("policycomparisonassessment", "rank"),
                migrations.AddConstraint(
                    "policycomparisonassessment",
                    models.UniqueConstraint(
                        fields=("id", "owner"),
                        name="v2_policy_comparison_assessment_id_owner_uq",
                    ),
                ),
                migrations.AddConstraint(
                    "policycomparisonassessment",
                    models.UniqueConstraint(
                        fields=("comparison", "product_variant", "selection_commitment"),
                        name="v2_policy_comparison_assessment_uq_1",
                    ),
                ),
                migrations.RenameField(
                    "policyrequirementmatch",
                    "candidate_assessment",
                    "comparison_assessment",
                ),
                migrations.RemoveConstraint(
                    "policyrequirementmatch", "v2_policy_requirement_match_uq_1"
                ),
                migrations.AddConstraint(
                    "policyrequirementmatch",
                    models.UniqueConstraint(
                        fields=("comparison_assessment", "customer_requirement"),
                        name="v2_policy_requirement_match_uq_1",
                    ),
                ),
                migrations.RenameField("informationneed", "recommendation", "comparison"),
                migrations.RemoveConstraint("informationneed", "v2_information_need_uq_1"),
                migrations.AddConstraint(
                    "informationneed",
                    models.UniqueConstraint(
                        fields=(
                            "comparison",
                            "subject_person",
                            "need_kind",
                            "information_key",
                        ),
                        name="v2_information_need_uq_1",
                        nulls_distinct=False,
                    ),
                ),
                migrations.RenameModel("RecommendationStatement", "ComparisonStatement"),
                migrations.AlterModelTable(
                    "comparisonstatement", "adviser_v2_comparison_statement"
                ),
                migrations.RenameField("comparisonstatement", "recommendation", "comparison"),
                migrations.RenameField(
                    "comparisonstatement",
                    "candidate_assessment",
                    "comparison_assessment",
                ),
                migrations.RemoveConstraint(
                    "comparisonstatement", "v2_recommendation_statement_id_owner_uq"
                ),
                migrations.RemoveConstraint(
                    "comparisonstatement", "v2_recommendation_statement_uq_1"
                ),
                migrations.RemoveConstraint(
                    "comparisonstatement", "v2_recommendation_statement_ck_1"
                ),
                migrations.AddConstraint(
                    "comparisonstatement",
                    models.UniqueConstraint(
                        fields=("id", "owner"), name="v2_comparison_statement_id_owner_uq"
                    ),
                ),
                migrations.AddConstraint(
                    "comparisonstatement",
                    models.UniqueConstraint(
                        fields=("comparison", "ordinal"),
                        name="v2_comparison_statement_uq_1",
                    ),
                ),
                migrations.AddConstraint(
                    "comparisonstatement",
                    models.CheckConstraint(
                        condition=(
                            (
                                models.Q(comparison_assessment__isnull=True)
                                & models.Q(requirement_match__isnull=True)
                                & models.Q(information_need__isnull=True)
                            )
                            | (
                                models.Q(comparison_assessment__isnull=False)
                                & models.Q(requirement_match__isnull=True)
                                & models.Q(information_need__isnull=True)
                            )
                            | (
                                models.Q(comparison_assessment__isnull=True)
                                & models.Q(requirement_match__isnull=False)
                                & models.Q(information_need__isnull=True)
                            )
                            | (
                                models.Q(comparison_assessment__isnull=True)
                                & models.Q(requirement_match__isnull=True)
                                & models.Q(information_need__isnull=False)
                            )
                        ),
                        name="v2_comparison_statement_ck_1",
                    ),
                ),
                migrations.RenameModel("RecommendationCitation", "ComparisonCitation"),
                migrations.AlterModelTable("comparisoncitation", "adviser_v2_comparison_citation"),
                migrations.RenameField(
                    "comparisoncitation", "recommendation_statement", "comparison_statement"
                ),
                migrations.RemoveConstraint(
                    "comparisoncitation", "v2_recommendation_citation_id_owner_uq"
                ),
                migrations.RemoveConstraint(
                    "comparisoncitation", "v2_recommendation_citation_uq_1"
                ),
                migrations.AddConstraint(
                    "comparisoncitation",
                    models.UniqueConstraint(
                        fields=("id", "owner"), name="v2_comparison_citation_id_owner_uq"
                    ),
                ),
                migrations.AddConstraint(
                    "comparisoncitation",
                    models.UniqueConstraint(
                        fields=("comparison_statement", "evidence_span", "role"),
                        name="v2_comparison_citation_uq_1",
                    ),
                ),
                migrations.AlterField(
                    model_name="turnevent",
                    name="event_type",
                    field=models.CharField(
                        choices=[
                            ("queued", "queued"),
                            ("started", "started"),
                            ("clarification", "clarification"),
                            ("progress", "progress"),
                            ("comparison", "comparison"),
                            ("cancelled", "cancelled"),
                            ("failed", "failed"),
                            ("stale", "stale"),
                        ],
                        max_length=16,
                    ),
                ),
                migrations.AlterField(
                    model_name="modelqualification",
                    name="schema_name",
                    field=models.CharField(
                        choices=[
                            ("fact_interpretation", "fact_interpretation"),
                            ("policy_extraction", "policy_extraction"),
                            ("policy_review", "policy_review"),
                            ("comparison_answer", "comparison_answer"),
                        ],
                        max_length=19,
                    ),
                ),
                migrations.AlterField(
                    model_name="turnroutebinding",
                    name="role",
                    field=models.CharField(
                        choices=[
                            ("fact_interpretation", "fact_interpretation"),
                            ("comparison_answer", "comparison_answer"),
                        ],
                        max_length=19,
                    ),
                ),
                migrations.RemoveConstraint("turnroutebinding", "v2_turn_route_binding_role_ck"),
                migrations.AddConstraint(
                    "turnroutebinding",
                    models.CheckConstraint(
                        condition=models.Q(role__in=["fact_interpretation", "comparison_answer"]),
                        name="v2_turn_route_binding_role_ck",
                    ),
                ),
            ],
        ),
        migrations.RunPython(migrations.RunPython.noop),
    ]
