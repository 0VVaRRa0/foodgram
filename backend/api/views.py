from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework.decorators import action
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
from .permissions import IsAuthenticatedAuthor
from .serializers import (AvatarSerializer, ExtendedUserSerializer,
                          GetRecipesSerializer, IngredientSerializer,
                          RecipeSerializer, ShortLinkSerializer,
                          ShortRecipeInfoSerializer, SubscriptionSerializer,
                          TagSerializer)
from .utils import generate_shopping_cart_file, generate_short_link


User = get_user_model()


class CustomUserVIewSet(UserViewSet):
    """Модифицированный ViewSet пользователей."""

    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        if self.action == 'list':
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['put', 'delete'],
            url_path='me/avatar')
    def create_destroy_avatar(self, request):
        user = request.user

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
            if user.avatar:
                user.avatar.delete()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscriptions(self, request, id):
        follower = request.user
        following = get_object_or_404(
            User.objects.annotate(recipes_count=Count('recipes')), id=id)
        # По спецификации же нужно возвращать 404 для несуществующего рецепта
        # и при POST, и при DELETE запросе

        if follower == following:
            return Response(status=HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            data = {'follower': request.user.id, 'following': id}
            serializer = SubscriptionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                recipes_limit = request.query_params.get('recipes_limit')
                user_serializer = ExtendedUserSerializer(
                    following,
                    context={
                        'request': request, 'recipes_limit': recipes_limit
                    }
                )
                return Response(user_serializer.data, status=HTTP_201_CREATED)
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                follower=follower, following=following).delete()
            if not deleted:
                return Response(status=HTTP_400_BAD_REQUEST)
                # А в случае неуспешного удаления нужно возвращать 400
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def get_subscriptions(self, request):
        subscriptions = request.user.followers.values_list(
            'following_id', flat=True)
        followings_queryset = User.objects.filter(
            id__in=subscriptions
        ).annotate(recipes_count=Count('recipes'))
        paginated_followings = self.paginate_queryset(
            followings_queryset)
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = ExtendedUserSerializer(
            paginated_followings,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit},
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """ViewSet рецептов."""

    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'get_short_link':
            return [AllowAny()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticatedAuthor()]
        if self.action == 'destroy':
            return [IsAuthenticatedAuthor()]
        return super().get_permissions()

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
        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return GetRecipesSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        user = self.request.user
        recipe = serializer.save(author=user)
        return recipe

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
        csv_file = generate_shopping_cart_file(recipes_ingredients)
        response = HttpResponse(csv_file, content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"')
        return response


class ShortLinkRedirectView(View):
    """Представление обработки коротких ссылок рецептов."""

    def get(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect('recipe-detail', pk=recipe.id)
