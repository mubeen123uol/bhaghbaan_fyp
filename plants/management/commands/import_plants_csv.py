import csv
from django.core.management.base import BaseCommand
from plants.models import Plant

class Command(BaseCommand):
    help = 'Bulk imports plant encyclopedia entries from a CSV file (FR-X3)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the plants CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        imported = 0
        with open(csv_file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Plant.objects.update_or_create(
                    scientific_name=row['scientific_name'],
                    defaults={
                        'name_en': row['name_en'],
                        'name_ur': row['name_ur'],
                        'name_roman': row.get('name_roman', ''),
                        'category': row.get('category', 'ORNAMENTAL'),
                        'description_en': row.get('description_en', ''),
                        'description_ur': row.get('description_ur', ''),
                        'watering_interval_days': int(row.get('watering_interval_days', 2)),
                        'fertilizer_interval_days': int(row.get('fertilizer_interval_days', 30)),
                        'pruning_season': row.get('pruning_season', ''),
                        'sunlight_requirement': row.get('sunlight_requirement', 'Full Sun'),
                        'is_indoor_suitable': row.get('is_indoor_suitable', 'False').lower() == 'true',
                        'climate_notes_pakistan': row.get('climate_notes_pakistan', ''),
                    }
                )
                imported += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported/updated {imported} plants from CSV."))
