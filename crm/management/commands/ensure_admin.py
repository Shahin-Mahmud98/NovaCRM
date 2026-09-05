"""
Creates (or updates the password of) a superuser from environment
variables. Safe to run on every deploy — this is how you get your first
admin login on hosts like Render's free tier, which doesn't offer shell
access to run `createsuperuser` interactively.

Set these as environment variables (e.g. in the Render dashboard, or your
local .env for testing):
  DJANGO_SUPERUSER_USERNAME
  DJANGO_SUPERUSER_PASSWORD
  DJANGO_SUPERUSER_EMAIL   (optional)

If DJANGO_SUPERUSER_USERNAME isn't set, this command does nothing and
exits quietly — so it's safe to always include in build.sh.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update a superuser from DJANGO_SUPERUSER_* environment variables."

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write("DJANGO_SUPERUSER_USERNAME/PASSWORD not set — skipping admin creation.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True},
        )
        user.email = email or user.email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} superuser '{username}'."))
