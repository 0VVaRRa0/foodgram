# Generated by Django 3.2.3 on 2024-12-04 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cookbook', '0009_recipe_created_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipe',
            options={'ordering': ('-created_at',), 'verbose_name': 'Рецепт', 'verbose_name_plural': 'Рецепты'},
        ),
    ]
