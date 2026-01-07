import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser if none exists and CREATE_SUPERUSER is enabled."

    def handle(self, *args, **options):
        if os.environ.get("CREATE_SUPERUSER") != "1":
            self.stdout.write("CREATE_SUPERUSER is not set to '1', skipping.")
            return

        user_model = get_user_model()
        if user_model.objects.filter(is_superuser=True).exists():
            self.stdout.write("Superuser already exists, skipping.")
            return

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        missing_vars = [
            name
            for name, value in {
                "DJANGO_SUPERUSER_USERNAME": username,
                "DJANGO_SUPERUSER_EMAIL": email,
                "DJANGO_SUPERUSER_PASSWORD": password,
            }.items()
            if not value
        ]
        if missing_vars:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing_vars)
            )

        user_model.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write("✅ Superuser created.")
