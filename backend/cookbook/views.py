from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.views import View
from hashids import Hashids
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet


from .constants import SHORT_LINK_MIN_LENGTH
from .models import Tag, Ingredient, Recipe, ShortLink
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    GetRecipesSerializer,
    RecipeSerializer,
    ShortLinkSerializer
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
        elif self.action == 'get_short_link':
            return ShortLinkSerializer
        elif self.action == 'add_to_shopping_cart':
            pass
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

    # @action(detail=True, methods=['post'], url_path='shopping_cart')
    # def add_to_shopping_cart(self, request, pk):
    #     pass

    # @action(detail=True, methods=['delete'], url_path='shopping_cart')
    # def remove_from_shopping_cart(self, request, pk):
    #     pass


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
