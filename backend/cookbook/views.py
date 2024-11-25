# from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, SAFE_METHODS
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet


from .models import Tag, Ingredient, Recipe
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    GetRecipesSerializer,
    RecipeSerializer
)


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
        # elif self.action == 'get_short_link':
        #     return ...
        return RecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    # @action(detail=True, methods=['get'], url_path='get-link')
    # def get_short_link(self, request, pk=None):
    #     pass
