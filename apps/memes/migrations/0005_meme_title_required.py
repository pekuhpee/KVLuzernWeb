from django.db import migrations, models
from django.db.models import Q


def populate_meme_titles(apps, schema_editor):
    Meme = apps.get_model("memes", "Meme")
    for meme in Meme.objects.filter(Q(title="") | Q(title__isnull=True)).only("id"):
        meme.title = f"Meme #{meme.id}"
        meme.save(update_fields=["title"])


class Migration(migrations.Migration):
    dependencies = [
        ("memes", "0004_meme_title_default"),
    ]

    operations = [
        migrations.RunPython(populate_meme_titles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="meme",
            name="title",
            field=models.CharField(max_length=200),
        ),
    ]
