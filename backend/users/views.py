from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST
)

from .models import Subscription
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (
    AvatarSerializer,
    ExtendedUserSerializer
)


User = get_user_model()


class CustomUserVIewSet(UserViewSet):
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    @action(
        detail=False, methods=['put', 'delete'],
        url_path='me/avatar', permission_classes=[IsAuthenticated]
    )
    def create_destroy_avatar(self, request):
        user = get_object_or_404(User, id=request.user.id)

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                instance=request.user, partial=True,
                data=request.data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=HTTP_200_OK)
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribtions(self, request, id):
        follower = request.user
        following = get_object_or_404(User, id=id)

        if follower == following:
            return Response(status=HTTP_400_BAD_REQUEST)

        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                follower=follower, following=following)
            if not created:
                return Response(status=HTTP_400_BAD_REQUEST)
            serializer = ExtendedUserSerializer(
                following, context={'request': request})
            return Response(serializer.data)

        elif request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscription, follower=follower, following=following)
            subscription.delete()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def get_subscriptions(self, request):
        subscriptions = request.user.following.all()
        followings = [subscription.following for subscription in subscriptions]
        paginator = PageNumberPagination()
        paginator.page_size_query_param = 'limit'
        paginator.page_query_param = 'page'
        paginated_followings = paginator.paginate_queryset(
            followings, request, view=self)
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = ExtendedUserSerializer(
            paginated_followings,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit},
        )
        return paginator.get_paginated_response(serializer.data)
