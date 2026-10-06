from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0022_immutable_fact_cards")]
    operations = [
        migrations.RunSQL(
            """CREATE FUNCTION prevent_demo_fact_card_update() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'Fact cards are immutable; create a new version'; END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER demo_fact_card_no_update BEFORE UPDATE ON adviser_v2_demofactcard
        FOR EACH ROW EXECUTE FUNCTION prevent_demo_fact_card_update();""",
            "DROP TRIGGER demo_fact_card_no_update ON adviser_v2_demofactcard; DROP FUNCTION prevent_demo_fact_card_update();",
        )
    ]
