from rest_framework.permissions import IsAuthenticated


class IsAuthenticatedAuthor(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.author
