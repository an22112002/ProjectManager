# Generated by Django 5.0.4 on 2024-05-15 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_remove_videoconnect_answer_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='Join',
            field=models.BooleanField(default=True),
        ),
    ]