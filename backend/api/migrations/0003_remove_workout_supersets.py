# Generated by Django 5.2.1 on 2025-06-11 04:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_supersetexercise_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workout',
            name='supersets',
        ),
    ]
