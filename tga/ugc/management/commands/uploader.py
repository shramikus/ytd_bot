import asyncio
import logging
from datetime import datetime
import time

# from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from ugc.models import Video
from ugc import utils


logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


def get_videos():
    videos = Video.objects.filter(Q(tg_id__isnull=True) | Q(tg_id=""))
    print(videos)
    for v in videos:
        try:
            v = Video.objects.get(yt_id=v.yt_id)
            video = utils.YoutubeVideo(v.yt_id)

            loop = asyncio.get_event_loop()
            loop.run_until_complete(video.send_video())

            logging.info("Видео загружено %s", v.yt_id)

            v.title = video.title
            v.uploader = video.uploader
            v.view_count = video.view_count
            v.tg_id = video.tg_id
            v.rating = video.average_rating
            v.tags = video.tags
            v.categories = video.categories
            v.likes = video.like_count

            if not v.upload_date:
                v.upload_date = timezone.get_current_timezone().localize(
                    datetime.strptime(video.upload_date, "%Y%m%d")
                )

            v.save()
        except Exception as e:

            logging.warning(e)



class Command(BaseCommand):
    help = "Выгрузка видео"

    def handle(self, *args, **options):

        while True:
            try:
                get_videos()
            except Exception as e:
                logging.warning(e)
            time.sleep(30)
