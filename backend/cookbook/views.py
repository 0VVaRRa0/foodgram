from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet


from .models import Tag, Ingredient
from .serializers import TagSerializer, IngredienSerializer


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredienSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
