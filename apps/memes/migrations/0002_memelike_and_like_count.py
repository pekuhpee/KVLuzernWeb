from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("memes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="meme",
            name="title",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="meme",
            name="like_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name="MemeLike",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visitor_id", models.UUIDField()),
                ("ip_hash", models.CharField(blank=True, max_length=64)),
                ("ua_hash", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("meme", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="likes", to="memes.meme")),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name="memelike",
            constraint=models.UniqueConstraint(fields=("meme", "visitor_id"), name="unique_meme_like_per_visitor"),
        ),
    ]
