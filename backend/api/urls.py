from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import (
    TagViewSet, IngredientViewSet, RecipeViewSet, CustomUserVIewSet
)

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)
router.register('users', CustomUserVIewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
