# Generated by Django 4.2.9 on 2024-06-23 12:13

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('wildberries', '0006_autocampaignkeywordstatistic'),
    ]

    operations = [
        migrations.CreateModel(
            name='PositionTrackingTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.IntegerField()),
                ('keyword', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('request', 'Request'), ('in_progress', 'In Progress'), ('done', 'Done')], max_length=50)),
                ('actual_position', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wildberries.campaign')),
            ],
        ),
        migrations.CreateModel(
            name='AutoBidderSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.IntegerField()),
                ('keyword', models.CharField(max_length=255)),
                ('max_bid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('position_ranges', models.JSONField()),
                ('intra_day_schedule', models.JSONField()),
                ('weekly_schedule', models.JSONField()),
                ('campaign', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='wildberries.campaign')),
            ],
        ),
        migrations.CreateModel(
            name='AutoBidderLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('message', models.TextField()),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wildberries.campaign')),
            ],
        ),
    ]