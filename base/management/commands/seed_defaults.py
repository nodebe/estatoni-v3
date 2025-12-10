import os
from django.core.management import call_command
from django.core.management.base import BaseCommand

current_dir = os.path.abspath(os.path.dirname(__name__))


class Command(BaseCommand):

    def handle(self, *args, **options):

        for command in ["create_default_permissions", "create_default_roles", "create_superadmin --first_admin=True",
                        "seed_cities --country Nigeria"]:
            call_command(command)
