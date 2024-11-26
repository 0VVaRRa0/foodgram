from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer, ExtendedUserSerializer
from .models import Subscription


User = get_user_model()


class AvatarUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = UserSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request.user.avatar = None
        request.user.save()
        return Response(status=HTTP_204_NO_CONTENT)


class CustomUserVIewSet(UserViewSet):

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
