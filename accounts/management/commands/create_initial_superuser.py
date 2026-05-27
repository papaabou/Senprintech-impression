import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the initial production superuser when none exists."

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Superuser already exists. Skipping initial admin creation.")
            return

        username = os.environ.get("ADMIN_USERNAME", "admin").strip()
        email = os.environ.get("ADMIN_EMAIL", "admin@senprintech.com").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")

        if not password:
            self.stdout.write("ADMIN_PASSWORD is not set. Skipping initial admin creation.")
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"Created initial superuser: {user.username}"))
