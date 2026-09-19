"""Permit only an explicitly labelled three-product development demo release."""

from django.db import migrations

FORWARD_SQL = """
CREATE OR REPLACE FUNCTION adviser_v2_assert_release_publication()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE product_count integer;
DECLARE required_product_count integer;
DECLARE invalid_count integer;
DECLARE missing_link_count integer;
BEGIN
    IF NEW.state <> 'published' OR OLD.state = 'published' THEN
        RETURN NEW;
    END IF;
    IF NEW.release_label = 'development_alpha_3_product' THEN
        IF NEW.readiness->>'demo_subset' IS DISTINCT FROM 'true'
           OR NEW.readiness->>'catalogue_product_count' IS DISTINCT FROM '5'
           OR NEW.readiness->>'comparison_product_count' IS DISTINCT FROM '3' THEN
            RAISE EXCEPTION 'Three-product demo release metadata is invalid';
        END IF;
        required_product_count := 3;
    ELSE
        required_product_count := 5;
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
    IF product_count <> required_product_count OR invalid_count > 0 THEN
        RAISE EXCEPTION 'Publication product count or verified-rule state is invalid';
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
"""


REVERSE_SQL = """
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
"""


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0010_knowledge_release_alpha_metadata")]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
