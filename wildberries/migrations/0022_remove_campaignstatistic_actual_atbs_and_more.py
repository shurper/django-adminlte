# Generated by Django 4.2.9 on 2024-07-17 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildberries', '0021_campaignstatistic_actual_atbs_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaignstatistic',
            name='actual_atbs',
        ),
        migrations.RemoveField(
            model_name='campaignstatistic',
            name='actual_orders',
        ),
        migrations.AddField(
            model_name='productstatistic',
            name='actual_atbs',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='productstatistic',
            name='actual_orders',
            field=models.IntegerField(default=0),
        ),
    ]