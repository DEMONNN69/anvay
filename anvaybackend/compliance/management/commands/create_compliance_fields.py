from django.core.management.base import BaseCommand
from compliance.models import ComplianceField


class Command(BaseCommand):
    help = 'Create initial compliance fields'

    def handle(self, *args, **options):
        fields_data = [
            {'name': 'MRP', 'icon': 'rupee'},
            {'name': 'Net Quantity', 'icon': 'package'},
            {'name': 'Manufacturer', 'icon': 'building'},
            {'name': 'Country of Origin', 'icon': 'globe'},
            {'name': 'Manufacturing Date', 'icon': 'calendar'},
        ]
        
        for field_data in fields_data:
            field, created = ComplianceField.objects.get_or_create(
                name=field_data['name'],
                defaults={'icon': field_data['icon']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created compliance field: {field.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Compliance field already exists: {field.name}')
                )