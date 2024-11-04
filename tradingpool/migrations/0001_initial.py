# Generated by Django 4.2.9 on 2024-11-03 18:18

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrderBook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exchange', models.CharField(max_length=255)),
                ('start', models.BigIntegerField()),
                ('end', models.BigIntegerField()),
                ('bid', models.JSONField()),
                ('ask', models.JSONField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
