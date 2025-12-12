from django.core.management.base import BaseCommand
import json
import os
from django.conf import settings
from tqdm import tqdm
from payment.models import Bank  # Replace 'banks' with your actual app name


class Command(BaseCommand):
    help = 'Upload banks data from JSON file to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to the JSON file containing bank data',
            default=os.path.join(settings.BASE_DIR, 'payment/data', 'banks.json')
        )

    def handle(self, *args, **options):
        file_path = options['file']

        self.stdout.write(self.style.SUCCESS(f"Reading bank data from: {file_path}"))

        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Read and decode JSON data
        try:
            with open(file_path, 'r') as file:
                banks = json.load(file)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON file: {str(e)}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(banks)} banks in the file"))

        success = 0
        skipped = 0

        # Process each bank with a progress bar
        for bank_data in tqdm(banks, desc="Uploading banks"):
            # Check if bank already exists
            exists = Bank.objects.filter(code=bank_data['code']).exists()

            if exists:
                skipped += 1
                continue

            # Create new bank
            bank = Bank(
                name=bank_data['name'],
                code=bank_data['code'],
                country='NG'
            )

            # Save the bank
            bank.save()
            success += 1

        self.stdout.write(self.style.SUCCESS("Bank upload completed!"))
        self.stdout.write(self.style.SUCCESS(f"Uploaded: {success} banks"))
        self.stdout.write(self.style.SUCCESS(f"Skipped: {skipped} banks (already existed)"))