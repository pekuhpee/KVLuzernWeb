from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exams", "0004_merge_0003_category_0003_meta_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="uploadbatch",
            name="download_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
