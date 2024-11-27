from hashids import Hashids
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND
)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .constants import SHORT_LINK_MIN_LENGTH
from .filters import RecipeFilter, IngredientFilter
from .models import Tag, Ingredient, Recipe, ShortLink, ShoppingCart, Favorite
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    GetRecipesSerializer,
    RecipeSerializer,
    ShortLinkSerializer,
    ShortRecipeInfoSerializer
)
from .utils import generate_short_link, generate_shopping_cart_file
from foodgram_backend.paginators import CustomPagination


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
            raise AuthenticationFailed()
        return serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed("User is not authenticated.")
        recipe_instance = serializer.instance
        if recipe_instance.author != self.request.user:
            raise PermissionDenied()
        super().perform_update(serializer)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk):
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(
            recipe_id=recipe.id,
            defaults={'short_link': generate_short_link(recipe.id)}
        )
        serializer = ShortLinkSerializer(short_link)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            cart, _ = ShoppingCart.objects.get_or_create(user=user)
            if cart.recipe.filter(id=recipe.id).exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            cart.recipe.add(recipe)
            serializer = ShortRecipeInfoSerializer(
                recipe, context={'request': request})
            return Response(serializer.data)

        elif request.method == 'DELETE':
            cart = get_object_or_404(ShoppingCart, user=user)
            if not cart.recipe.filter(id=recipe.id).exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            cart.recipe.remove(recipe)
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        cart, _ = ShoppingCart.objects.prefetch_related(
            'recipe__recipeingredient_set__ingredient'
        ).get_or_create(user=user)
        ingredients = cart.recipe.values(
            'recipeingredient__ingredient__name',
            'recipeingredient__ingredient__measurement_unit'
        ).annotate(total_amount=Sum('recipeingredient__amount'))
        csv_file = generate_shopping_cart_file(ingredients)
        response = HttpResponse(csv_file, content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.csv"')
        return response

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(status=HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeInfoSerializer(recipe)
            return Response(serializer.data)

        if request.method == 'DELETE':
            favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            favorite.delete()
            return Response(status=HTTP_204_NO_CONTENT)


class ShortLinkRedirectView(View):
    def get(self, request, short_link):
        hashids = Hashids(min_length=SHORT_LINK_MIN_LENGTH)
        try:
            recipe_id = hashids.decode(short_link)[0]
        except IndexError:
            return Response(status=HTTP_404_NOT_FOUND)
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return redirect('recipe-detail', pk=recipe.id)
