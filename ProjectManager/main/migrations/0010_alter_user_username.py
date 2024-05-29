# Generated by Django 5.0.4 on 2024-05-11 06:13

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_group_maxnumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='Username',
            field=models.TextField(unique=True, validators=[django.core.validators.MinLengthValidator(8)]),
        ),
    ]