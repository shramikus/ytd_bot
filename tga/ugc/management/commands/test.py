from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from ugc.models import Message
from ugc.models import Profile
from ugc.models import Video


def get_messages():
    messages = [mess.text for mess in Message.objects.all()]
    print(messages)


@receiver(post_save, sender=Message)
def add_score(**kwargs):
    messages = [mess.text for mess in Message.objects.all()]
    print(messages)


class Command(BaseCommand):
    help = 'video finder'

    def handle(self, *args, **options):
        add_score()
