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


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name="short_link",
        verbose_name="Рецепт"
    )
    short_link = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Короткая ссылка"
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Короткая ссылка на рецепт'
        verbose_name_plural = 'Короткие ссылки на рецепты'
        unique_together = ('recipe', 'short_link')

    def __str__(self):
        return (
            f'Короткая ссылка для рецепта {self.recipe.name}: '
            f'{self.short_link}'
        )


class ShoppingCart(models.Model):
    user = models.OneToOneField(
        User, verbose_name='Пользователь', on_delete=models.CASCADE)
    recipe = models.ManyToManyField(Recipe, verbose_name='Рецепты')

    class Meta:
        ordering = ('id',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'Список покупок пользователя {self.user.username}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'Избранное пользователя {self.user.username}'
