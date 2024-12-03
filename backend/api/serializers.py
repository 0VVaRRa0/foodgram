from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as BaseUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from cookbook.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscription


User = get_user_model()


class UserSerializer(BaseUserSerializer):
    """Сериализатор модели пользователей."""

    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        follower = self.context['request'].user
        if not follower.is_authenticated:
            return False
        following = get_object_or_404(User, id=obj.id)
        return Subscription.objects.filter(
            follower=follower, following=following
        ).exists()


class ExtendedUserSerializer(UserSerializer):
    """Расширенный сериализатор модели пользователей."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'recipes_limit', settings.DEFAULT_RECIPES_LIMIT)
        if str(recipes_limit).isdigit():
            recipes_limit = int(recipes_limit)
        else:
            recipes_limit = settings.DEFAULT_RECIPES_LIMIT
        recipes = obj.recipes.all()[:recipes_limit]
        return ShortRecipeInfoSerializer(recipes, many=True).data


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('follower', 'following')


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор поля 'avatar' пользователей."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        avatar = data.get('avatar')
        if not avatar:
            raise serializers.ValidationError(
                {'avatar': 'Поле "avatar" не может быть пустым.'})
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Tag"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ingredient"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class GetRecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор безопасных запросов модели RecipeIngredient."""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class GetRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор безопасных запросов рецептов."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredients = instance.recipeingredient.all()
        representation['ingredients'] = GetRecipeIngredientsSerializer(
            ingredients, many=True).data
        return representation


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели RecipeIngredient."""

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели рецептов"""

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
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return GetRecipesSerializer(instance, context=context).data

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Добавьте хотя бы один ингредиент'})
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Добавьте хотя бы один тег'})
        if len(data['tags']) > len(set(data['tags'])):
            raise serializers.ValidationError(
                {'tags': 'Теги не могут повторяться'})
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = Ingredient.objects.filter(
                id=ingredient_item['id']).first()
            # XXX: делаем фильтрацию вручную,
            # чтобы при ошибке вернуть 400, а не 404
            if ingredient is None:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиента с таким id не существует'}
                )
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты должны быть уникальными'})
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) < 1:
                raise serializers.ValidationError(
                    {
                        'ingredients':
                        'Убедитесь, что количество ингредиента больше 0'
                    }
                )
        if not data['image'] or data['image'] is None:
            raise serializers.ValidationError({'image': 'Обязательное поле'})
        data['ingredients'] = ingredients
        return data


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор коротких ссылок рецептов."""

    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, obj):
        return f'{settings.SITE_URL}/s/{obj.short_link}/'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('short_link')
        return representation


class ShortRecipeInfoSerializer(serializers.ModelSerializer):
    """Укороченный сериализатор рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
