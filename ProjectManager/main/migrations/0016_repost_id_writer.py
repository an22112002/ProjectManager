# Generated by Django 5.0.4 on 2024-05-20 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_alter_user_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='repost',
            name='Id_writer',
            field=models.IntegerField(default=1),
        ),
    ]
