from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("memes", "0003_anon_like_cookie"),
    ]

    operations = [
        migrations.AlterField(
            model_name="meme",
            name="title",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
