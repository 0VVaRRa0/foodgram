import os

from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Exists, OuterRef, Value, Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import (NotAuthenticated, PermissionDenied,
                                       ValidationError)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from cookbook.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                             ShoppingCart, Tag)
from users.models import Subscription

from .filters import IngredientFilter, RecipeFilter
from .paginators import CustomPagination
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (AvatarSerializer, ExtendedUserSerializer,
                          GetRecipesSerializer, IngredientSerializer,
                          RecipeSerializer, ShortLinkSerializer,
                          ShortRecipeInfoSerializer, TagSerializer)
from .utils import generate_shopping_cart_file, generate_short_link


User = get_user_model()
SHORT_LINK_MIN_LENGTH = os.getenv('SHORT_LINK_MIN_LENGTH', 3)


class CustomUserVIewSet(UserViewSet):
    """Модифицированный ViewSet пользователей"""
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        return super().me(request, *args, **kwargs)

    @action(
        detail=False, methods=['put', 'delete'],
        url_path='me/avatar', permission_classes=[IsAuthenticated]
    )
    def create_destroy_avatar(self, request):
        user = get_object_or_404(User, id=request.user.id)

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                instance=request.user, partial=True,
                data=request.data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=HTTP_200_OK)
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribtions(self, request, id):
        follower = request.user
        if not follower.is_authenticated:
            raise NotAuthenticated()
        following = get_object_or_404(User, id=id)

        if follower == following:
            return Response(status=HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                follower=follower, following=following)
            if not created:
                return Response(status=HTTP_400_BAD_REQUEST)
            recipes_limit = request.query_params.get('recipes_limit')
            following = User.objects.annotate(
                recipes_count=Count('recipes')).get(id=id)
            serializer = ExtendedUserSerializer(
                following,
                context={'request': request, 'recipes_limit': recipes_limit}
            )
            return Response(serializer.data, status=HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                subscription = get_object_or_404(
                    Subscription, follower=follower, following=following)
            except Http404:
                raise ValidationError('Вы не подписаны на пользователя')
            subscription.delete()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def get_subscriptions(self, request):
        subscriptions = request.user.followers.all()
        followings = [subscription.following for subscription in subscriptions]
        followings_queryset = User.objects.filter(
            id__in=[following.id for following in followings]).annotate(
                recipes_count=Count('recipes'))
        paginator = PageNumberPagination()
        paginator.page_size_query_param = 'limit'
        paginator.page_query_param = 'page'
        paginated_followings = paginator.paginate_queryset(
            followings_queryset, request, view=self)
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = ExtendedUserSerializer(
            paginated_followings,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit},
        )
        return paginator.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet ингредиентов"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """ViewSet рецептов"""
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'recipeingredient__ingredient')
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    user=user, recipe=OuterRef('pk'))),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    user=user, recipe=OuterRef('pk'))))
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField())
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return GetRecipesSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise NotAuthenticated()
        recipe = serializer.save(author=user)
        recipe.is_favorited = Favorite.objects.filter(
            user=user, recipe=recipe).exists()
        recipe.is_in_shopping_cart = ShoppingCart.objects.filter(
            user=user, recipe=recipe).exists()
        return recipe

    def perform_update(self, serializer):
        if not self.request.user.is_authenticated:
            raise NotAuthenticated()
        recipe_instance = serializer.instance
        if recipe_instance.author != self.request.user:
            raise PermissionDenied()
        super().perform_update(serializer)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if not self.request.user.is_authenticated:
            raise NotAuthenticated()
        if self.request.user != recipe.author:
            raise PermissionDenied()
        recipe.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk):
        recipe = self.get_object()
        if not recipe.short_link:
            recipe.short_link = generate_short_link(recipe.id)
            recipe.save()
        serializer = ShortLinkSerializer(recipe)
        return Response(serializer.data, HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk):
        return self.shopping_cart_and_favorite(request, pk, ShoppingCart)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk):
        return self.shopping_cart_and_favorite(request, pk, Favorite)

    def shopping_cart_and_favorite(self, request, pk, model):
        user = request.user
        if not user.is_authenticated:
            raise NotAuthenticated()
        recipe = get_object_or_404(Recipe, id=pk)
        # По спецификации же нужно возвращать 404 для несуществующего рецепта
        # и при POST, и при DELETE запросе

        if request.method == 'POST':
            _, created = model.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response(status=HTTP_400_BAD_REQUEST)
            serializer = ShortRecipeInfoSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted, _ = model.objects.filter(
                user=user, recipe=recipe).delete()
            if not deleted:
                return Response(status=HTTP_400_BAD_REQUEST)
            # А в случае неуспешного удаления нужно возвращать 400
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        recipes_ingredients = RecipeIngredient.objects.filter(
            recipe__in=shopping_cart.values('recipe')
        ).select_related('ingredient', 'recipe')
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
        csv_file = generate_shopping_cart_file(ingredients)
        response = HttpResponse(csv_file, content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"')
        return response


class ShortLinkRedirectView(View):
    """Представление обработки коротких ссылок рецептов"""
    def get(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect('recipe-detail', pk=recipe.id)
