from django.db import models


class Tag(models.Model):
    name = models.CharField('Название', max_length=32)
    slug = models.SlugField('Слаг', max_length=32)

    class Meta:
        default_related_name = 'tags'
        ordering = ('id', 'name')
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField('Единицы измерения', max_length=64)

    class Meta:
        default_related_name = 'ingredients'
        ordering = ('id', 'name')
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name
