from django.contrib import admin

from .forms import ProfileForm
from .models import Message
from .models import Profile
from .models import Video
from .models import AppConfig
from .models import Playlist
from .models import Schedule


@admin.register(AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    # list_display = ('session_name', 'api_id', 'api_hash', 'is_active', 'is_bot',
    #                 'bot_token', 'posting_channel', 'temp_chat', 'timestamp')
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "external_id", "name")
    form = ProfileForm


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "message_type", "text", "status", "created_at")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "yt_id",
        "show_url",
        "title",
        "uploader",
        "view_count",
        "rating",
        "status",
    )


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "playlist_name",
        "playlist_url",
        "active",
        "last_video_date",
        "update_time",
    )


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "post_type", "data", "active", "post_time")
