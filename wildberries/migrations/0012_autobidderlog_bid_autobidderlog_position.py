# Generated by Django 4.2.9 on 2024-07-01 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildberries', '0011_autobiddersettings_destination'),
    ]

    operations = [
        migrations.AddField(
            model_name='autobidderlog',
            name='bid',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='autobidderlog',
            name='position',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
