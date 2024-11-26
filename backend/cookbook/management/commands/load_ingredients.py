import json

from django.core.management.base import BaseCommand

from cookbook.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path', type=str, help='Path to the JSON file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )

            self.stdout.write(self.style.SUCCESS('Данные успешно загружены!'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка загрузки данных: {e}'))
