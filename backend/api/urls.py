from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import (
    TagViewSet, IngredientViewSet, RecipeViewSet, CustomUserVIewSet
)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')
router.register('users', CustomUserVIewSet, basename='user')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
