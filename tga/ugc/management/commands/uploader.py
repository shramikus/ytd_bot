import asyncio
import logging
from datetime import datetime
import time

# from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from ugc.models import Message, Video, Playlist
from ugc import utils


logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.WARNING
)


def get_videos():
    videos = Video.objects.filter(tg_id__isnull=True)
    for v in videos:
        video = utils.YoutubeVideo(v.yt_id)
        asyncio.run(video.send_video())
        logging.info("Видео загружено %s", v.yt_id)

        v.title = video.title
        v.uploader = video.uploader
        v.upload_date = timezone.get_current_timezone().localize(
            datetime.strptime(video.upload_date, "%Y%m%d")
        )
        v.view_count = video.view_count
        v.tg_id = video.tg_id
        v.rating = video.average_rating
        v.tags = video.tags
        v.categories = video.categories
        v.likes = video.like_count

        v.save()


class Command(BaseCommand):
    help = "Выгрузка видео"

    def handle(self, *args, **options):

        while True:
            get_videos()
            time.sleep(60)
