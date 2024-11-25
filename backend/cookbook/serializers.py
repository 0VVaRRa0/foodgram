from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .constants import SITE_URL
from .models import (
    Ingredient,
    Tag,
    Recipe,
    RecipeIngredient,
    ShortLink,
    ShoppingCart
)
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    '''Сериализатор для модели Tag'''

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    '''Сериализатор для модели Ingredient'''

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class GetRecipeIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class GetRecipesSerializer(serializers.ModelSerializer):
    '''Сериализатор для безопасных запросов рецептов'''

    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredients = instance.recipeingredient_set.all()
        representation['ingredients'] = GetRecipeIngredientsSerializer(
            ingredients, many=True).data
        return representation


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def create_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),)
            for ingredient in ingredients
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe=recipe, ingredients=ingredients)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return GetRecipesSerializer(instance, context=context).data


class ShortLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = ShortLink
        fields = ['short_link']

    def get_short_link(self, obj):
        return f'{SITE_URL}/s/{obj.short_link}'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('short_link')
        return representation


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.first.id', read_only=True)
    name = serializers.CharField(source='recipe.first.name', read_only=True)
    image = serializers.ImageField(source='recipe.first.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.first.cooking_time', read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')
