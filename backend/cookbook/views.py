from hashids import Hashids
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .constants import SHORT_LINK_MIN_LENGTH
from .models import Tag, Ingredient, Recipe, ShortLink, ShoppingCart
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    GetRecipesSerializer,
    RecipeSerializer,
    ShortLinkSerializer,
    ShoppingCartSerializer
)
from .utils import generate_short_link


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


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return GetRecipesSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk):
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(
            recipe_id=recipe.id,
            defaults={'short_link': generate_short_link(recipe.id)}
        )
        serializer = ShortLinkSerializer(short_link)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='shopping_cart')
    def add_to_shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        cart, _ = ShoppingCart.objects.get_or_create(user=user)
        if cart.recipe.filter(id=recipe.id).exists():
            return Response(status=HTTP_400_BAD_REQUEST)
        cart.recipe.add(recipe)
        serializer = ShoppingCartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='shopping_cart')
    def remove_from_shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        cart = get_object_or_404(ShoppingCart, user=user)
        if not cart.recipe.filter(id=recipe.id).exists():
            return Response(status=HTTP_400_BAD_REQUEST)
        cart.recipe.remove(recipe)
        return Response(status=HTTP_204_NO_CONTENT)


class ShortLinkRedirectView(View):
    def get(self, request, short_link):
        hashids = Hashids(min_length=SHORT_LINK_MIN_LENGTH)
        try:
            recipe_id = hashids.decode(short_link)[0]
        except IndexError:
            return HttpResponseNotFound('Ссылка не найдена')
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return HttpResponseNotFound('Рецепт не найден')
        return redirect('recipe-detail', pk=recipe.id)
