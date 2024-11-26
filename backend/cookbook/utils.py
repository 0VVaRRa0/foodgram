import pandas as pd
from hashids import Hashids

from .constants import SHORT_LINK_MIN_LENGTH


def generate_short_link(obj_id):
    hashids = Hashids(min_length=SHORT_LINK_MIN_LENGTH)
    return hashids.encode(obj_id)


def generate_shopping_cart_file(ingredients):
    data = [
        (ingredient['recipeingredient__ingredient__name'],
         ingredient['total_amount'],
         ingredient['recipeingredient__ingredient__measurement_unit'])
        for ingredient in ingredients
    ]
    df = pd.DataFrame(
        data,
        columns=['Ингредиент', 'Количество', 'Ед. измерения']
    )
    return df.to_csv(index=False)
