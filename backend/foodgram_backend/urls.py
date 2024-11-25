from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cookbook.views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    ShortLinkRedirectView
)
from users.views import AvatarUpdate, CustomUserVIewSet

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)
router.register('users', CustomUserVIewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('s/<str:short_link>/', ShortLinkRedirectView.as_view()),
    path('api/users/me/avatar/', AvatarUpdate.as_view()),
    path('api/auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
