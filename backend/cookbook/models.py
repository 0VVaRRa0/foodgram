from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название', max_length=32)
    slug = models.SlugField('Слаг', max_length=32)

    class Meta:
        ordering = ('id', 'name')
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField('Единицы измерения', max_length=64)

    class Meta:
        ordering = ('id', 'name')
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField('Название рецепта', max_length=256)
    image = models.ImageField('Изображение', upload_to='recipe_images/')
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=[MinValueValidator(1), MaxValueValidator(10080)]
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        verbose_name='Ингредиент', related_name='recipes'
    )
    short_link = models.CharField(
        'Короткая ссылка', max_length=6, null=True, default=None)

    class Meta:
        ordering = ('id', 'name')
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient, verbose_name='Игредиент', on_delete=models.CASCADE)
    amount = models.IntegerField(
        'Количество', validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return (
            f'{self.amount} {self.ingredient.measurement_unit} '
            f'{self.ingredient.name} в рецепте {self.recipe.name}'
        )


class BaseUserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        ordering = ('id',)

    def __str__(self):
        return f'{self._meta.verbose_name} пользователя {self.user.username}'


class ShoppingCart(BaseUserRecipeRelation):
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Favorite(BaseUserRecipeRelation):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
