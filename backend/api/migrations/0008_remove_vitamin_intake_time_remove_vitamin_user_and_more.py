# Generated by Django 5.2.1 on 2025-06-25 11:51

import django.db.models.deletion
import multiselectfield.db.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_vitamin_photo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vitamin',
            name='intake_time',
        ),
        migrations.RemoveField(
            model_name='vitamin',
            name='user',
        ),
        migrations.CreateModel(
            name='UserVitamin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intake_time', multiselectfield.db.fields.MultiSelectField(choices=[('morning', 'Утро'), ('afternoon', 'День'), ('evening', 'Вечер'), ('workout', 'Перед тренировкой')], max_length=33, verbose_name='Время приёма')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
                ('vitamin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.vitamin', verbose_name='Витамин')),
            ],
            options={
                'verbose_name': 'Витамин пользователя',
                'verbose_name_plural': 'Витамины пользователя',
                'unique_together': {('user', 'vitamin')},
            },
        ),
    ]
