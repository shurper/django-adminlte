# Generated by Django 4.2.9 on 2024-07-01 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildberries', '0010_autobiddersettings_is_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='autobiddersettings',
            name='destination',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
