# Generated by Django 5.0.4 on 2024-05-11 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_alter_user_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='Lock',
            field=models.BooleanField(default=False),
        ),
    ]
