from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """Кастомный класс резрешений"""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if type(obj) is type(user) and obj == user:
            return True
        return request.method in SAFE_METHODS or user.is_staff
