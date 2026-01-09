from django.db import migrations, models
import django.db.models.deletion
def seed_meta_options(apps, schema_editor):
    MetaCategory = apps.get_model("exams", "MetaCategory")
    MetaOption = apps.get_model("exams", "MetaOption")
    categories = [("type", "Typ"), ("year", "Jahr"), ("subject", "Fach"), ("program", "Programm")]
    options = {
        "type": [("EXAM", "Prüfung"), ("MATERIAL", "Lernstoff")],
        "year": [(str(year), str(year)) for year in range(2022, 2027)],
        "subject": [("Mathe", "Mathe"), ("Deutsch", "Deutsch"), ("Englisch", "Englisch"), ("Französisch", "Französisch"), ("Geschichte", "Geschichte"), ("Finanzwesen", "Finanzwesen"), ("Wirtschaft", "Wirtschaft"), ("Recht", "Recht"), ("Rechnungswesen", "Rechnungswesen"), ("ABU", "ABU")],
        "program": [("BM1", "BM1"), ("BM2", "BM2"), ("KV EFZ", "KV EFZ")],
    }
    for order, (key, label) in enumerate(categories, start=1):
        category, _ = MetaCategory.objects.get_or_create(key=key, defaults={"label": label, "sort_order": order})
        for opt_order, (value_key, opt_label) in enumerate(options.get(key, []), start=1):
            MetaOption.objects.get_or_create(
                category=category,
                value_key=value_key,
                defaults={"label": opt_label, "sort_order": opt_order},
            )
class Migration(migrations.Migration):

    dependencies = [
        ("ranking", "0001_initial"),
        ("exams", "0002_uploadbatch_uploadfile"),
    ]

    operations = [
        migrations.CreateModel(
            name="MetaCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=40, unique=True)),
                ("label", models.CharField(max_length=120)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ("sort_order", "label")},
        ),
        migrations.CreateModel(
            name="MetaOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value_key", models.CharField(max_length=120)),
                ("label", models.CharField(max_length=120)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="exams.metacategory")),
            ],
            options={"ordering": ("sort_order", "label"), "unique_together": {("category", "value_key")}},
        ),
        migrations.AddField(
            model_name="uploadbatch",
            name="program_option",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="upload_batches_program", to="exams.metaoption"),
        ),
        migrations.AddField(
            model_name="uploadbatch",
            name="subject_option",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="upload_batches_subject", to="exams.metaoption"),
        ),
        migrations.AddField(
            model_name="uploadbatch",
            name="teacher",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="upload_batches", to="ranking.teacher"),
        ),
        migrations.AddField(
            model_name="uploadbatch",
            name="type_option",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="upload_batches_type", to="exams.metaoption"),
        ),
        migrations.AddField(
            model_name="uploadbatch",
            name="year_option",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="upload_batches_year", to="exams.metaoption"),
        ),
        migrations.RunPython(seed_meta_options, migrations.RunPython.noop),
    ]
