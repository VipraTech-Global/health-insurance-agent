"""Distinguish a global owner-less target from a missing target row."""

from django.db import migrations

FORWARD_SQL = r"""
CREATE OR REPLACE FUNCTION adviser_v2_assert_owner_fk()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    source_owner text;
    reference_id uuid;
    target_row jsonb;
    target_owner text;
BEGIN
    source_owner := to_jsonb(NEW)->>'owner_id';
    reference_id := NULLIF(to_jsonb(NEW)->>TG_ARGV[0], '')::uuid;
    IF reference_id IS NULL THEN
        RETURN NEW;
    END IF;
    EXECUTE format(
        'SELECT jsonb_build_object(''owner_id'', owner_id::text) '
        'FROM %I WHERE id = $1 FOR KEY SHARE',
        TG_ARGV[1]
    ) INTO target_row USING reference_id;
    IF target_row IS NULL THEN
        RAISE EXCEPTION 'Referenced CoverGuide row does not exist (% on %.%)',
            reference_id, TG_TABLE_NAME, TG_ARGV[0];
    END IF;
    target_owner := target_row->>'owner_id';
    IF source_owner IS DISTINCT FROM target_owner THEN
        RAISE EXCEPTION 'Cross-owner CoverGuide relationship rejected';
    END IF;
    RETURN NEW;
END;
$$;
"""


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0005_allow_prepublication_release_states")]

    operations = [migrations.RunSQL(FORWARD_SQL, reverse_sql=migrations.RunSQL.noop)]
