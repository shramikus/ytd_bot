# Generated by Django 2.2.10 on 2020-02-21 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ugc', '0006_auto_20200221_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='playlist_name',
            field=models.CharField(default='Плейлист <built-in function id>', max_length=255, verbose_name='Название'),
        ),
    ]