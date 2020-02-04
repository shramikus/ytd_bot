from django.db.models.signals import post_save
from django.db.models import F
from django.dispatch import receiver
from django.conf import settings
from .models import Video, Message


def message_saved_handler(sender, instance, created, **kwargs):
    if created and instance.external_id in settings.AUTH_USERS:
        pass
