# Generated by Django 5.0.4 on 2024-05-20 20:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_alter_repost_id_writer'),
    ]

    operations = [
        migrations.CreateModel(
            name='Check',
            fields=[
                ('Id_check', models.AutoField(primary_key=True, serialize=False)),
                ('Result', models.TextField()),
                ('DateCheck', models.DateTimeField(auto_now=True)),
                ('Id_assign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.assign')),
            ],
        ),
    ]
