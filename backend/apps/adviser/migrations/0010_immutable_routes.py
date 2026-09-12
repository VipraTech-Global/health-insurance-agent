from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("adviser", "0009_turn_route_turnattempt_route_and_more")]
    operations = [
        migrations.RunSQL(
            sql="""
        CREATE FUNCTION adviser_immutable_route() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF (to_jsonb(NEW) - 'qualification_state') IS DISTINCT FROM (to_jsonb(OLD) - 'qualification_state') THEN
            RAISE EXCEPTION 'Route configurations are immutable';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER immutable_route BEFORE UPDATE ON adviser_routeconfiguration
          FOR EACH ROW EXECUTE FUNCTION adviser_immutable_route();
        CREATE FUNCTION adviser_immutable_qualification() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'Route qualifications are immutable'; END $$;
        CREATE TRIGGER immutable_qualification BEFORE UPDATE ON adviser_routequalification
          FOR EACH ROW EXECUTE FUNCTION adviser_immutable_qualification();
        """,
            reverse_sql="""
        DROP TRIGGER immutable_route ON adviser_routeconfiguration;
        DROP FUNCTION adviser_immutable_route();
        DROP TRIGGER immutable_qualification ON adviser_routequalification;
        DROP FUNCTION adviser_immutable_qualification();
        """,
        )
    ]
