# Generated by Django 4.2.9 on 2024-12-20 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('nickname', models.CharField(max_length=255, unique=True)),
                ('phone', models.CharField(max_length=15, unique=True)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('messenger', models.CharField(choices=[('whatsapp', 'WhatsApp'), ('telegram', 'Telegram')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='OTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flutterapp.user')),
            ],
        ),
    ]
