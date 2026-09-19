"""Repair dynamic trigger existence checks on already-migrated databases."""

from django.db import migrations

FORWARD_SQL = r"""
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
        RAISE EXCEPTION 'Referenced CoverGuide row does not exist (% on %.%)',
            reference_id, TG_TABLE_NAME, TG_ARGV[0];
    END IF;
    IF source_owner IS DISTINCT FROM target_owner THEN
        RAISE EXCEPTION 'Cross-owner CoverGuide relationship rejected';
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
"""


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0003_integrity_triggers")]

    operations = [migrations.RunSQL(FORWARD_SQL, reverse_sql=migrations.RunSQL.noop)]
