# Generated by Django 2.2.10 on 2020-02-21 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ugc', '0004_auto_20200221_1438'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='yt_url',
        ),
        migrations.AlterField(
            model_name='video',
            name='title',
            field=models.TextField(blank=True, null=True, verbose_name='Название видео'),
        ),
        migrations.AlterField(
            model_name='video',
            name='uploader',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Канал отправителя'),
        ),
    ]
