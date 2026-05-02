from django.core.management.base import BaseCommand

from stagedoor.models import AuthToken


class Command(BaseCommand):
    help = "Clean up stale authentication tokens"

    def handle(self, *args, **options):
        deleted_count = AuthToken.delete_stale()
        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {deleted_count} stale tokens")
        )