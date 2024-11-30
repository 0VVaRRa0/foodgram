import os

from django.contrib.auth import get_user_model
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from dotenv import load_dotenv
from rest_framework.decorators import action
from rest_framework.exceptions import (
    NotAuthenticated, PermissionDenied, ValidationError)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import RecipeFilter, IngredientFilter
from .paginators import CustomPagination
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (
    AvatarSerializer,
    ExtendedUserSerializer,
    TagSerializer,
    IngredientSerializer,
    GetRecipesSerializer,
    RecipeSerializer,
    ShortLinkSerializer,
    ShortRecipeInfoSerializer
)
from .utils import generate_short_link, generate_shopping_cart_file
from cookbook.models import (
    Tag, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Favorite
)
from users.models import Subscription


User = get_user_model()
load_dotenv()
SHORT_LINK_MIN_LENGTH = os.getenv('SHORT_LINK_MIN_LENGTH', 3)


class CustomUserVIewSet(UserViewSet):
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
        paginator = PageNumberPagination()
        paginator.page_size_query_param = 'limit'
        paginator.page_query_param = 'page'
        paginated_followings = paginator.paginate_queryset(
            followings, request, view=self)
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = ExtendedUserSerializer(
            paginated_followings,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit},
        )
        return paginator.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return GetRecipesSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise NotAuthenticated()
        return serializer.save(author=self.request.user)

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
        user = request.user
        if not user.is_authenticated:
            raise NotAuthenticated()
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            cart, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response(status=HTTP_400_BAD_REQUEST)
            serializer = ShortRecipeInfoSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
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

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            raise NotAuthenticated()
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeInfoSerializer(recipe)
            return Response(serializer.data, status=HTTP_201_CREATED)

        if request.method == 'DELETE':
            try:
                favorite = get_object_or_404(
                    Favorite, user=user, recipe=recipe)
            except Http404:
                raise ValidationError('Рецепт ещё не добавлен в избранное')
            favorite.delete()
            return Response(status=HTTP_204_NO_CONTENT)


class ShortLinkRedirectView(View):
    def get(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect('recipe-detail', pk=recipe.id)
