# Generated by Django 2.2.10 on 2020-02-21 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ugc', '0010_auto_20200221_2340'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='active',
            field=models.FloatField(default=False, verbose_name='Активный'),
        ),
    ]
