# Generated by Django 4.2.9 on 2024-07-03 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildberries', '0013_positiontrackingtask_destination'),
    ]

    operations = [
        migrations.AddField(
            model_name='autobidderlog',
            name='destination',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='autobidderlog',
            name='keyword',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='autobidderlog',
            name='product_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
