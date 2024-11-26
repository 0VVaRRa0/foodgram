# from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as BaseUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import SerializerMethodField

from .models import CustomUser, Subscription
# from cookbook.serializers import ShortRecipeInfoSerializer


class UserSerializer(BaseUserSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        follower = self.context['request'].user
        following = CustomUser.objects.get(id=obj.id)
        if Subscription.objects.filter(
            follower=follower, following=following
        ).exists():
            return True
        return False


class ExtendedUserSerializer(UserSerializer):
    # recipes = ShortRecipeInfoSerializer(many=True, read_only=True)
    # recipes_count = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields

    # def get_recipes_count(self, obj):
    #     user = get_object_or_404(CustomUser, id=obj.id)
    #     return user.recipes.count()
