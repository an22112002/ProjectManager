# Generated by Django 5.0.4 on 2024-04-18 19:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_alter_project_budget'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='Avatar',
            field=models.ImageField(null=True, upload_to='avatars/'),
        ),
    ]
