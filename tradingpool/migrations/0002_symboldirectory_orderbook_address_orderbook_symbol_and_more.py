# Generated by Django 4.2.9 on 2024-11-04 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tradingpool', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SymbolDirectory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=512, unique=True)),
                ('symbol', models.CharField(max_length=32)),
                ('symbol_type', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='orderbook',
            name='address',
            field=models.CharField(max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='orderbook',
            name='symbol',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='orderbook',
            name='symbol_type',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='orderbook',
            name='exchange',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
