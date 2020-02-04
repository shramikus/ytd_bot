from django.contrib import admin

from .forms import ProfileForm
from .models import Message
from .models import Profile
from .models import Video


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name')
    form = ProfileForm


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'text', 'created_at')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('yt_id', 'show_url', 'title', 'uploader', 'view_count',
                    'rating')
