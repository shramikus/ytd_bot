# Generated by Django 2.2.7 on 2020-02-01 18:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ugc', '0004_video'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='created_at',
        ),
    ]
