# Generated by Django 4.2.9 on 2024-06-27 18:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildberries', '0008_alter_autobiddersettings_intra_day_schedule_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='autobiddersettings',
            name='intra_day_schedule',
        ),
        migrations.RemoveField(
            model_name='autobiddersettings',
            name='position_ranges',
        ),
        migrations.RemoveField(
            model_name='autobiddersettings',
            name='weekly_schedule',
        ),
        migrations.CreateModel(
            name='WeeklySchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.CharField(max_length=20)),
                ('autobidder_settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weekly_schedules', to='wildberries.autobiddersettings')),
            ],
        ),
        migrations.CreateModel(
            name='PositionRange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_position', models.IntegerField()),
                ('end_position', models.IntegerField()),
                ('bid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('autobidder_settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='position_ranges', to='wildberries.autobiddersettings')),
            ],
        ),
        migrations.CreateModel(
            name='IntraDaySchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('autobidder_settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='intra_day_schedules', to='wildberries.autobiddersettings')),
            ],
        ),
    ]
