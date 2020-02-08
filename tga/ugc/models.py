from django.db import models
from django.utils.html import format_html


class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name="Внешний ID пользователя", unique=True)
    name = models.TextField(verbose_name="Имя пользователя")

    def __str__(self):
        return f"#{self.external_id} {self.name}"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


class Message(models.Model):
    profile = models.ForeignKey(to="ugc.Profile",
                                verbose_name="Профиль",
                                on_delete=models.PROTECT)
    text = models.TextField(verbose_name="Текст")
    created_at = models.DateTimeField(verbose_name="Время получения",
                                      auto_now_add=True)

    def __str__(self):
        return f"Сообщение {self.pk} от {self.profile}"

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"


class Video(models.Model):
    yt_id = models.TextField(verbose_name="Id видео", primary_key=True)
    yt_url = models.URLField(verbose_name="Ссылка на видео")
    # created_at = models.DateTimeField(
    #     verbose_name='Время получения',
    #     auto_now_add=True)
    title = models.TextField(verbose_name="Название видео")
    uploader = models.TextField(verbose_name="Канал отправителя")
    upload_date = models.DateField(verbose_name="Дата публикации")
    view_count = models.PositiveIntegerField(verbose_name="Просмотров")
    rating = models.FloatField(verbose_name="Рейтинг")
    tg_id = models.TextField(verbose_name="Id в телеграме")

    def show_url(self):
        return format_html('<a href="{}">{}</a>'.format(
            self.yt_url, self.yt_url))

    show_url.allow_tags = True

    def __str__(self):
        return f"{self.yt_id}"

    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео"