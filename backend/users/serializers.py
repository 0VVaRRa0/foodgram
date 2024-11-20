from djoser.serializers import UserSerializer as BaseUserSerializer
# from drf_extra_fields.fields import Base64ImageField

from .models import CustomUser


class UserSerializer(BaseUserSerializer):
    # avatar = Base64ImageField(required=False, blank=True, null=True)

    class Meta(BaseUserSerializer.Meta):
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            # 'avatar'
        )
