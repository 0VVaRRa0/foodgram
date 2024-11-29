# Generated by Django 3.2.3 on 2024-11-26 21:08

from django.db import migrations, models
import users.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_subscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[users.validators.validate_username]),
        ),
    ]