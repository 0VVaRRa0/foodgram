# Generated by Django 3.2.3 on 2024-11-27 00:10

from django.db import migrations, models
import users.utils


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_customuser_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='avatar',
            field=models.ImageField(blank=True, default=None, null=True, upload_to=users.utils.avatar_upload_path),
        ),
    ]
