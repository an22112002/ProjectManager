# Generated by Django 5.0.4 on 2024-05-20 21:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_check_id_writer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='check',
            name='Id_writer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.member'),
        ),
    ]