import os
from uuid import uuid4

import pandas as pd
from hashids import Hashids


SHORT_LINK_MIN_LENGTH = os.getenv('SHORT_LINK_MIN_LENGTH', 3)


def generate_short_link(obj_id):
    hashids = Hashids(min_length=SHORT_LINK_MIN_LENGTH)
    return hashids.encode(obj_id)


def generate_shopping_cart_file(ingredients):
    data = [
        (ingredient['ingredient'],
         ingredient['amount'],
         ingredient['measurement_unit'])
        for ingredient in ingredients
    ]
    df = pd.DataFrame(
        data, columns=['Ингредиент', 'Количество', 'Ед. измерения'])
    return df.to_csv(index=False)


def avatar_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    new_filename = f"{instance.username}_avatar_{uuid4().hex}{ext}"
    return os.path.join('avatars/', new_filename)
