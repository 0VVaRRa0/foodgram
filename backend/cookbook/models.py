from django.core.validators import MinValueValidator
from django.db import models


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
    cooking_time = models.IntegerField(
        'Время приготовления в минутах', validators=[MinValueValidator(1)])
    author = models.ForeignKey(
        'users.CustomUser',
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', verbose_name='Ингредиент')

    class Meta:
        ordering = ('id', 'name')
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField(
        'Количество', validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ('recipe', 'ingredient')


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
