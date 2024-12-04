from djaa_list_filter.admin import AjaxAutocompleteListFilterModelAdmin
from django.contrib import admin
from django.db.models import Count

from .models import Ingredient, Recipe, Tag, ShoppingCart, Favorite


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


class BaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user', 'recipe')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseAdmin):
    pass


@admin.register(Favorite)
class FavoriteAdmin(BaseAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(AjaxAutocompleteListFilterModelAdmin):
    list_display = ('name', 'author')
    search_fields = ('name',)
    autocomplete_list_filter = ('tags', 'author')
    readonly_fields = ('favorites_count',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(favorites_count=Count('favorites'))
        return queryset.select_related(
            'author'
        ).prefetch_related('tags', 'ingredients')

    def favorites_count(self, obj):
        return obj.favorites_count
    favorites_count.admin_order_field = 'favorites_count'
    favorites_count.short_description = 'Добавлений в избранное'
