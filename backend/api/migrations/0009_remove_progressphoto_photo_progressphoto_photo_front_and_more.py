# Generated by Django 5.2.1 on 2025-06-25 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_remove_vitamin_intake_time_remove_vitamin_user_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='progressphoto',
            name='photo',
        ),
        migrations.AddField(
            model_name='progressphoto',
            name='photo_front',
            field=models.ImageField(default=1, upload_to='progrss_photos/', verbose_name='Фотография спереди'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='progressphoto',
            name='photo_side',
            field=models.ImageField(default=1, upload_to='progrss_photos/', verbose_name='Фотография сбоку'),
            preserve_default=False,
        ),
    ]
