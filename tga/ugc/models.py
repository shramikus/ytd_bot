from django.db import models
from django.utils.html import format_html


class AppConfig(models.Model):
    session_name = models.CharField(
        max_length=255, default=None, null=True, blank=False
    )

    api_id = models.CharField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text="getting from https://my.telegram.org/auth",
    )

    api_hash = models.CharField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text="getting from https://my.telegram.org/auth",
    )

    is_active = models.BooleanField(
        default=False,
        null=True,
        blank=False,
        help_text="non active config is not working",
    )

    is_bot = models.BooleanField(
        default=True,
        null=True,
        blank=False,
        help_text="select if you want to use bot account for this config",
    )

    bot_token = models.CharField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text="required if you use bot account."
        "use @botfather for create a bot or get token for available bot.",
    )

    client_phone = models.CharField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text="Телефон аккаунта, с которого загружаются видео для авторизации."
    )
    client_code = models.CharField(
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text="Код авторизации."
    )
    posting_channel = models.CharField(
        max_length=255,
        default="-1001317892207",
        null=True,
        blank=True,
        help_text="channel where the recordings will be published",
    )

    temp_chat = models.CharField(
        max_length=255,
        default="@postoronniy_bot",
        null=True,
        blank=True,
        help_text="chat where the records will be stored",
    )

    auth_users = models.CharField(
        max_length=255,
        default="261336294 448374494",
        null=True,
        blank=True,
        help_text="authenticated users for bot using",
    )

    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Бот"
        verbose_name_plural = "Боты"

    def __str__(self):
        return f"ID:{self.id}, Is active:{self.is_active}, Is bot:{self.is_bot}"


class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name="Внешний ID пользователя", unique=True
    )
    name = models.TextField(verbose_name="Имя пользователя")

    def __str__(self):
        return f"#{self.external_id} {self.name}"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


class Message(models.Model):
    profile = models.ForeignKey(
        to="ugc.Profile", verbose_name="Профиль", on_delete=models.PROTECT
    )
    text = models.TextField(verbose_name="Текст")
    message_type = models.CharField(
        verbose_name="Тип", max_length=255, blank=True, null=True
    )
    status = models.BooleanField(verbose_name="Проверено", blank=True, null=True)
    created_at = models.DateTimeField(verbose_name="Время получения", auto_now_add=True)

    def __str__(self):
        return f"Сообщение {self.pk} от {self.profile}"

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"


class Video(models.Model):
    playlist = models.ForeignKey(
        to="ugc.Playlist",
        verbose_name="Плейлист",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    yt_id = models.CharField(verbose_name="Id видео", max_length=255, unique=True)
    title = models.TextField(verbose_name="Название видео", blank=True, null=True)
    uploader = models.CharField(
        verbose_name="Канал отправителя", max_length=255, blank=True, null=True
    )
    upload_date = models.DateField(
        verbose_name="Дата публикации", blank=True, null=True
    )
    view_count = models.PositiveIntegerField(
        verbose_name="Просмотров", blank=True, null=True
    )
    rating = models.FloatField(verbose_name="Рейтинг", blank=True, null=True)
    tg_id = models.CharField(
        verbose_name="Id в телеграме", max_length=255, blank=True, null=True
    )
    status = models.PositiveIntegerField(
        verbose_name="Статус", default=0, blank=True, null=True
    )
    tags = models.TextField(verbose_name="Теги", default="", blank=True, null=True)
    categories = models.TextField(
        verbose_name="Категории", default="", blank=True, null=True
    )
    likes = models.PositiveIntegerField(
        verbose_name="Лайки", default=0, blank=True, null=True
    )
    hot = models.BooleanField(verbose_name="Новинка", default=False, null=True)

    def show_url(self):
        return format_html(
            '<a href="https://www.youtube.com/watch?v={}">{}</a>'.format(
                self.yt_id, self.yt_id
            )
        )

    show_url.allow_tags = True

    def __str__(self):
        return f"{self.yt_id}"

    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видео"


class Playlist(models.Model):
    playlist_name = models.CharField(
        verbose_name="Название", max_length=255, blank=True, null=True
    )
    playlist_url = models.URLField(verbose_name="Ссылка на плейлист")
    update_time = models.DateTimeField(
        verbose_name="Последняя проверка", blank=True, null=True
    )
    active = models.BooleanField(verbose_name="Активный", default=False, null=True)

    class Meta:
        verbose_name = "Плейлист"
        verbose_name_plural = "Плейлисты"

    def __str__(self):
        if self.playlist_name:
            return f"{self.playlist_name}"
        return f"{self.playlist_url}"


class Schedule(models.Model):
    POST_TYPES = [("msg", "message"), ("vid", "video"), ("im", "image")]

    post_type = models.CharField(
        verbose_name="Тип публикации",
        max_length=255,
        blank=True,
        null=True,
        choices=POST_TYPES,
        help_text="Пока что работает только video. Казать только поле данные"
    )
    data = models.TextField(
        verbose_name="Данные",
        blank=True,
        null=True,
        help_text="Video: youtube id или несколько (через пробел) видео из нашей базы. "
        "Message: оставить пустым. "
        "Image: ссылка или несколько на изображение",
    )
    message = models.TextField(
        verbose_name="Текст описания",
        blank=True,
        null=True,
        help_text="Сообщение в markdown формате. https://core.telegram.org/bots/api#markdown-style",
    )
    post_time = models.DateTimeField(
        verbose_name="Время Публикации", blank=True, null=True
    )
    active = models.BooleanField(verbose_name="Активный", default=False, null=True)

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписания"

    def __str__(self):
        return f"{self.post_type}:{self.data}:{self:post_time}"
