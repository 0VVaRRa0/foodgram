import csv
import os

import pandas as pd
from dotenv import load_dotenv
from hashids import Hashids

from .models import Ingredient


load_dotenv()
SHORT_LINK_MIN_LENGTH = os.getenv('SHORT_LINK_MIN_LENGTH', 3)


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


def load_ingredients():
    with open('data/ingredients.csv', mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            name, measurement_unit = row[0], row[1]
            Ingredient.objects.create(
                name=name, measurement_unit=measurement_unit)
