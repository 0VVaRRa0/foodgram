import csv
from io import StringIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from hashids import Hashids


def generate_short_link(obj_id):
    """Генерация короткой ссылки."""

    hashids = Hashids(min_length=settings.SHORT_LINK_MIN_LENGTH)
    return hashids.encode(obj_id)


def generate_shopping_cart_file(recipes_ingredients):
    """Генерация файла списка покупок."""

    ingredient_dict = {}
    for recipe_ingredient in recipes_ingredients:
        ingredient_name = recipe_ingredient.ingredient.name
        amount = recipe_ingredient.amount
        measurement_unit = recipe_ingredient.ingredient.measurement_unit
        if ingredient_name in ingredient_dict:
            ingredient_dict[ingredient_name]['amount'] += amount
        else:
            ingredient_dict[ingredient_name] = {
                'ingredient': ingredient_name,
                'amount': amount,
                'measurement_unit': measurement_unit
            }
    ingredients = list(ingredient_dict.values())

    output = StringIO()
    writer = csv.writer(output, delimiter=',')
    writer.writerow(['Ингредиент', 'Количество', 'Ед. измерения'])
    for ingredient in ingredients:
        writer.writerow([
            ingredient['ingredient'],
            ingredient['amount'],
            ingredient['measurement_unit']
        ])
    output.seek(0)
    return output.getvalue()


def avatar_upload_path(instance, filename):
    """Генерация названия файла аватара пользователей."""

    file_extension = Path(filename).suffix
    new_filename = f'{instance.username}_avatar_{uuid4().hex}{file_extension}'
    return str(Path('avatars') / new_filename)
