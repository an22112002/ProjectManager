# Generated by Django 5.0.4 on 2024-05-16 23:28

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_alter_user_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='Username',
            field=models.TextField(validators=[django.core.validators.MinLengthValidator(8)]),
        ),
    ]