from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("adviser_v2", "0007_recover_expired_processing_leases")]

    operations = [
        migrations.AlterField(
            model_name="processingjob",
            name="stage",
            field=models.CharField(
                choices=[
                    ("classify", "classify"),
                    ("read", "read"),
                    ("ocr", "ocr"),
                    ("extract", "extract"),
                    ("validate", "validate"),
                    ("index", "index"),
                    ("independent_review", "independent_review"),
                    ("reconcile", "reconcile"),
                ],
                max_length=18,
            ),
        ),
    ]
