from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from .validators import validate_username
from api.utils import avatar_upload_path


class CustomUserManager(BaseUserManager):

    def create_user(
            self, username, email, first_name, last_name, password):
        if not all([username, email, first_name, last_name, password]):
            raise ValueError("All fields are required")
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
            self, username, email, first_name, last_name, password):
        user = self.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username = models.CharField(
        max_length=150, unique=True,
        validators=[validate_username],
        verbose_name='Имя пользователя'
    )
    email = models.EmailField(
        unique=True, blank=False, verbose_name='Email', max_length=254)
    first_name = models.CharField(
        max_length=150, blank=False, verbose_name='Имя')
    last_name = models.CharField(
        max_length=150, blank=False, verbose_name='Фамилия')
    avatar = models.ImageField(
        upload_to=avatar_upload_path, default=None,
        null=True, blank=True,
        verbose_name='Аватар'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    follower = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='followers'
    )
    following = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('follower', 'following')

    def __str__(self):
        return (
            f'{self.follower.username} подписан на {self.following.username}')
