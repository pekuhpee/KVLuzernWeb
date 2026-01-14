from django.db import migrations


def backfill_type_option(apps, schema_editor):
    UploadBatch = apps.get_model("exams", "UploadBatch")
    MetaCategory = apps.get_model("exams", "MetaCategory")
    MetaOption = apps.get_model("exams", "MetaOption")

    category, _ = MetaCategory.objects.get_or_create(
        key="type",
        defaults={"label": "Typ", "sort_order": 1},
    )
    options_by_value = {
        option.value_key: option
        for option in MetaOption.objects.filter(category=category)
    }
    batches = UploadBatch.objects.filter(type_option__isnull=True).exclude(content_type__isnull=True).exclude(content_type="")
    for batch in batches.iterator():
        value_key = batch.content_type
        option = options_by_value.get(value_key)
        if not option:
            option = MetaOption.objects.create(
                category=category,
                value_key=value_key,
                label=value_key,
                sort_order=0,
            )
            options_by_value[value_key] = option
        UploadBatch.objects.filter(pk=batch.pk).update(type_option=option)


class Migration(migrations.Migration):

    dependencies = [
        ("exams", "0005_uploadbatch_download_count"),
    ]

    operations = [
        migrations.RunPython(backfill_type_option, migrations.RunPython.noop),
    ]
