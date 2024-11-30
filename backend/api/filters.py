from django_filters import rest_framework as filters

from cookbook.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр по полям рецептов"""
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.CharFilter(
        field_name='tags__slug', method='filter_tags', lookup_expr='in')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset.exclude(favorite__user=self.request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset
        if value:
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset.exclude(shoppingcart__user=self.request.user)

    def filter_tags(self, queryset, name, value):
        tag_list = self.request.query_params.getlist('tags')
        if tag_list:
            return queryset.filter(tags__slug__in=tag_list).distinct()
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр по полям ингредиентов"""
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
