import csv
import os
from io import StringIO
from pathlib import Path
from uuid import uuid4

from hashids import Hashids


SHORT_LINK_MIN_LENGTH = os.getenv('SHORT_LINK_MIN_LENGTH', 3)


def generate_short_link(obj_id):
    hashids = Hashids(min_length=SHORT_LINK_MIN_LENGTH)
    return hashids.encode(obj_id)


def generate_shopping_cart_file(ingredients):
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
    file_extension = Path(filename).suffix
    new_filename = f'{instance.username}_avatar_{uuid4().hex}{file_extension}'
    return str(Path('avatars') / new_filename)