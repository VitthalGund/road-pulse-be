# Generated by Django 4.2.7 on 2025-06-12 12:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Carrier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('main_office_address', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_number', models.CharField(max_length=50, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('carrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drivers', to='core.carrier')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle_number', models.CharField(max_length=50, unique=True)),
                ('license_plate', models.CharField(max_length=20)),
                ('state', models.CharField(max_length=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('carrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vehicles', to='core.carrier')),
            ],
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_longitude', models.FloatField()),
                ('current_latitude', models.FloatField()),
                ('pickup_longitude', models.FloatField()),
                ('pickup_latitude', models.FloatField()),
                ('dropoff_longitude', models.FloatField()),
                ('dropoff_latitude', models.FloatField()),
                ('current_cycle_hours', models.FloatField(default=0.0)),
                ('start_time', models.DateTimeField()),
                ('status', models.CharField(choices=[('PLANNED', 'Planned'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed')], default='PLANNED', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trips', to='core.driver')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trips', to='core.vehicle')),
            ],
        ),
        migrations.CreateModel(
            name='ELDLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_miles', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eld_logs', to='core.trip')),
            ],
            options={
                'db_table': 'eld_logs',
            },
        ),
        migrations.CreateModel(
            name='DutyStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('OFF_DUTY', 'Off Duty'), ('SLEEPER_BERTH', 'Sleeper Berth'), ('DRIVING', 'Driving'), ('ON_DUTY_NOT_DRIVING', 'On Duty Not Driving')], max_length=20)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('longitude', models.FloatField()),
                ('latitude', models.FloatField()),
                ('location_description', models.CharField(max_length=255)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='duty_statuses', to='core.trip')),
            ],
        ),
        migrations.AddIndex(
            model_name='carrier',
            index=models.Index(fields=['name'], name='core_carrie_name_074a51_idx'),
        ),
        migrations.AddIndex(
            model_name='vehicle',
            index=models.Index(fields=['vehicle_number'], name='core_vehicl_vehicle_ed41fa_idx'),
        ),
        migrations.AddIndex(
            model_name='trip',
            index=models.Index(fields=['driver', 'start_time'], name='core_trip_driver__41aceb_idx'),
        ),
        migrations.AddIndex(
            model_name='trip',
            index=models.Index(fields=['status'], name='core_trip_status_41c948_idx'),
        ),
        migrations.AddIndex(
            model_name='eldlog',
            index=models.Index(fields=['trip', 'date'], name='eld_logs_trip_id_53704e_idx'),
        ),
        migrations.AddIndex(
            model_name='dutystatus',
            index=models.Index(fields=['trip', 'start_time'], name='core_dutyst_trip_id_0d1113_idx'),
        ),
        migrations.AddIndex(
            model_name='driver',
            index=models.Index(fields=['license_number'], name='core_driver_license_5ffe57_idx'),
        ),
    ]
