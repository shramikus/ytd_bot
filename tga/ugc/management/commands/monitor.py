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
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


def create_playlist(message):
    playlist = Playlist(playlist_url=message.text)
    playlist.save()
    logging.info("Плейлист добавлен: %s", message.text)
    return playlist


def create_video(video_id, playlist=None):
    video = Video(yt_id=video_id, playlist=playlist, hot=playlist.active)
    video.save()
    logging.info("Видео добавлено: %s", video_id)
    return video


def playlists_check():
    playlists = Playlist.objects.all()

    for playlist in playlists:

        playlist_url = playlist.playlist_url
        date_after = playlist.update_time

        playlist_videos = utils.get_ids_by_link(playlist_url, date_after=date_after)

        filtred_videos = utils.existed_videos(playlist_videos)

        if isinstance(filtred_videos, str):
            logging.warning("%s", filtred_videos)

        else:
            for video_id in filtred_videos:
                create_video(video_id, playlist=playlist)

        playlist.update_time = datetime.now(tz=timezone.utc)
        playlist.save()


def messages_check():
    try:
        messages = Message.objects.filter(Q(status=False) & ~Q(message_type="message"))
    except:
        messages = []
    logging.info("Обработка сообщений %s", list(messages))

    for message in messages:
        if message.message_type == "playlist":
            create_playlist(message)

        elif message.message_type == "video":
            video_ids = utils.get_ids_by_link(message.text)
            filtred_ids = utils.existed_videos(video_ids)

            if isinstance(filtred_ids, list):
                for video_id in filtred_ids:
                    create_video(video_id)
            elif isinstance(filtred_ids, str):
                logging.warning("%s", filtred_ids)

        message.status = True
        message.save()


class Command(BaseCommand):
    help = "Мониторинг сообщений"

    def handle(self, *args, **options):

        while True:
            messages_check()
            playlists_check()

            time.sleep(60)
