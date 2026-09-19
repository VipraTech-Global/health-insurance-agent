"""Fail expired turn leases closed while retaining safe processing-job recovery."""

from __future__ import annotations

from django.db import migrations

FORWARD_SQL = r"""
CREATE OR REPLACE FUNCTION adviser_v2_assert_lease_fence()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    supplied text;
    recovery_requested text;
BEGIN
    IF OLD.state = 'running' AND NEW.state <> OLD.state
       AND NEW.state NOT IN ('cancel_requested') THEN
        recovery_requested := current_setting(
            'coverguide.recover_expired_lease', true
        );
        IF TG_TABLE_NAME = 'adviser_v2_processing_job'
           AND OLD.lease_until <= statement_timestamp()
           AND NEW.state = 'queued'
           AND NEW.lease_token IS NULL
           AND NEW.lease_until IS NULL
           AND recovery_requested = 'true'
           AND (
               to_jsonb(NEW) - 'state' - 'lease_token' - 'lease_until' - 'updated_at'
           ) IS NOT DISTINCT FROM (
               to_jsonb(OLD) - 'state' - 'lease_token' - 'lease_until' - 'updated_at'
           ) THEN
            RETURN NEW;
        END IF;
        IF TG_TABLE_NAME = 'adviser_v2_turn'
           AND OLD.lease_until <= statement_timestamp()
           AND NEW.state = 'failed'
           AND NEW.error_code = 'worker_lease_expired'
           AND NEW.lease_token IS NULL
           AND NEW.lease_until IS NULL
           AND recovery_requested = 'true'
           AND (
               to_jsonb(NEW) - 'state' - 'error_code' - 'lease_token' - 'lease_until' - 'updated_at'
           ) IS NOT DISTINCT FROM (
               to_jsonb(OLD) - 'state' - 'error_code' - 'lease_token' - 'lease_until' - 'updated_at'
           ) THEN
            RETURN NEW;
        END IF;
        supplied := current_setting('coverguide.lease_token', true);
        IF supplied IS NULL OR supplied = '' OR supplied::uuid IS DISTINCT FROM OLD.lease_token
           OR OLD.lease_until <= statement_timestamp() THEN
            RAISE EXCEPTION 'Stale or unfenced CoverGuide worker cannot publish';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
"""


REVERSE_SQL = r"""
CREATE OR REPLACE FUNCTION adviser_v2_assert_lease_fence()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    supplied text;
    recovery_requested text;
BEGIN
    IF OLD.state = 'running' AND NEW.state <> OLD.state
       AND NEW.state NOT IN ('cancel_requested') THEN
        recovery_requested := current_setting(
            'coverguide.recover_expired_lease', true
        );
        IF TG_TABLE_NAME = 'adviser_v2_processing_job'
           AND OLD.lease_until <= statement_timestamp()
           AND NEW.state = 'queued'
           AND NEW.lease_token IS NULL
           AND NEW.lease_until IS NULL
           AND recovery_requested = 'true'
           AND (
               to_jsonb(NEW) - 'state' - 'lease_token' - 'lease_until' - 'updated_at'
           ) IS NOT DISTINCT FROM (
               to_jsonb(OLD) - 'state' - 'lease_token' - 'lease_until' - 'updated_at'
           ) THEN
            RETURN NEW;
        END IF;
        supplied := current_setting('coverguide.lease_token', true);
        IF supplied IS NULL OR supplied = '' OR supplied::uuid IS DISTINCT FROM OLD.lease_token
           OR OLD.lease_until <= statement_timestamp() THEN
            RAISE EXCEPTION 'Stale or unfenced CoverGuide worker cannot publish';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
"""


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0008_processing_job_index_stage")]

    operations = [migrations.RunSQL(FORWARD_SQL, reverse_sql=REVERSE_SQL)]
