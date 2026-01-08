from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("memes", "0002_memelike_and_like_count"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="memelike",
            name="unique_meme_like_per_visitor",
        ),
        migrations.RenameField(
            model_name="memelike",
            old_name="visitor_id",
            new_name="anon_id",
        ),
        migrations.RemoveField(
            model_name="memelike",
            name="ip_hash",
        ),
        migrations.RemoveField(
            model_name="memelike",
            name="ua_hash",
        ),
        migrations.AddConstraint(
            model_name="memelike",
            constraint=models.UniqueConstraint(
                fields=("meme", "anon_id"), name="unique_meme_like_per_anon"
            ),
        ),
    ]
