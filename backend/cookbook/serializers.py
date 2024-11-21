from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import Ingredient, Tag, Recipe
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredienSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags, many=True).data
        return representation
