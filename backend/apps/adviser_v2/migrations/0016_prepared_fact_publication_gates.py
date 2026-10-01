"""A separate cited-fact proof path; every included rule keeps its existing gates."""

from importlib import import_module

from django.db import migrations

PREVIOUS = import_module('apps.adviser_v2.migrations.0014_three_product_catalogue').FORWARD_SQL
FACT_PRODUCT_CHECK = """
    IF NEW.readiness->>'fact_release_version' = 'prepared-source-facts/1' THEN
        IF NEW.release_label <> 'development_alpha_3_product' THEN
            RAISE EXCEPTION 'Prepared facts require the explicit three-product demo';
        END IF;
        IF EXISTS (
            SELECT 1 FROM adviser_v2_knowledge_release_fact f
            JOIN adviser_v2_processing_job job ON job.id = f.validation_job_id
            JOIN adviser_v2_policy_version version ON version.id = f.policy_version_id
            WHERE f.knowledge_release_id = NEW.id AND (
                job.state <> 'succeeded' OR job.stage <> 'validate'
                OR job.result_storage_sha256 IS DISTINCT FROM f.validation_sha256
                OR version.publication_status <> 'published'
                OR f.fact->>'status' IS DISTINCT FROM 'supported'
                OR f.fact->>'criterion' IS DISTINCT FROM f.criterion
                OR COALESCE(f.fact->>'value', '') = ''
                OR jsonb_typeof(f.fact->'citations') IS DISTINCT FROM 'array'
                OR jsonb_array_length(f.fact->'citations') = 0
                OR f.fact->'unknown_reasons' IS DISTINCT FROM '[]'::jsonb
                OR f.criterion NOT IN ('sum_insured','room_category','copay','deductible',
                   'ped_waiting_period','initial_specific_waiting_periods','maternity','newborn',
                   'restoration','family_floater','portability','geography','eligibility')
                OR NOT EXISTS (
                    SELECT 1 FROM adviser_v2_policy_version_document member
                    JOIN adviser_v2_source_capture capture ON capture.document_version_id = member.document_version_id
                    WHERE capture.id = job.source_capture_id AND member.policy_version_id = f.policy_version_id
                      AND member.role = 'base_wording'
                )
            )
        ) THEN
            RAISE EXCEPTION 'Prepared fact source validation or membership is invalid';
        END IF;
        IF EXISTS (
            SELECT policy_version_id FROM adviser_v2_knowledge_release_fact
            WHERE knowledge_release_id = NEW.id GROUP BY policy_version_id HAVING count(*) <> 13
        ) THEN
            RAISE EXCEPTION 'Every prepared product requires all thirteen distinct criteria';
        END IF;
        SELECT COUNT(DISTINCT version.product_id) INTO product_count
          FROM adviser_v2_knowledge_release_fact f
          JOIN adviser_v2_policy_version version ON version.id = f.policy_version_id
         WHERE f.knowledge_release_id = NEW.id;
        IF (SELECT count(*) FROM adviser_v2_knowledge_release_fact WHERE knowledge_release_id = NEW.id) <> 39
           OR EXISTS (
               SELECT 1 FROM adviser_v2_knowledge_release_rule member
               JOIN adviser_v2_policy_rule rule ON rule.id = member.policy_rule_id
               WHERE member.knowledge_release_id = NEW.id AND NOT EXISTS (
                   SELECT 1 FROM adviser_v2_knowledge_release_fact fact
                   WHERE fact.knowledge_release_id = NEW.id AND fact.policy_version_id = rule.policy_version_id
                     AND fact.fact->>'rule_status' = 'executable'
                     AND fact.fact->'rule_ids' @> jsonb_build_array(rule.id::text)
               )
           ) THEN
            RAISE EXCEPTION 'Prepared release count or executable-rule scope is invalid';
        END IF;
    END IF;
"""

FORWARD = PREVIOUS.replace(
    '    IF product_count <> required_product_count OR invalid_count > 0 THEN',
    FACT_PRODUCT_CHECK + '\n    IF product_count <> required_product_count OR invalid_count > 0 THEN',
) + """
CREATE TRIGGER adviser_v2_release_fact_mutable
BEFORE INSERT OR UPDATE OR DELETE ON adviser_v2_knowledge_release_fact
FOR EACH ROW EXECUTE FUNCTION adviser_v2_assert_release_rule_mutation();

CREATE FUNCTION adviser_v2_freeze_fact_release_metadata() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.state IN ('published','retired') AND (
        NEW.readiness IS DISTINCT FROM OLD.readiness OR NEW.manifest_sha256 IS DISTINCT FROM OLD.manifest_sha256
        OR NEW.supported_scope IS DISTINCT FROM OLD.supported_scope OR NEW.release_label IS DISTINCT FROM OLD.release_label
    ) THEN
        RAISE EXCEPTION 'Published knowledge-release proof metadata is immutable';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER adviser_v2_release_metadata_immutable
BEFORE UPDATE ON adviser_v2_knowledge_release
FOR EACH ROW EXECUTE FUNCTION adviser_v2_freeze_fact_release_metadata();
"""

REVERSE = """
DROP TRIGGER adviser_v2_release_metadata_immutable ON adviser_v2_knowledge_release;
DROP FUNCTION adviser_v2_freeze_fact_release_metadata();
DROP TRIGGER adviser_v2_release_fact_mutable ON adviser_v2_knowledge_release_fact;
""" + PREVIOUS


class Migration(migrations.Migration):
    dependencies = [('adviser_v2', '0015_prepared_fact_release')]
    operations = [migrations.RunSQL(FORWARD, REVERSE)]
