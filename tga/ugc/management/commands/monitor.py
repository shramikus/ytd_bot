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


def add_video_to_base(video_id, playlist=None):
    """
    Add a single video to playlist with hot status from playlist status.
    """
    video = Video(yt_id=video_id, playlist=playlist, hot=playlist.active)
    video.save()
    return video


def get_new_videos(url):
    """
    Get new videos from playlist.
    """
    # dateafter = playlist.update_time

    existed_videos = Video.objects.values_list("yt_id", flat=True)
    received_videos = utils.get_ids_by_link(url, num=2)

    if isinstance(received_videos, str):
        logging.info("%s", received_videos)
        return []

    new_videos = [video for video in received_videos if video not in existed_videos]
    return new_videos


def get_playlist_videos(playlist):
    url = playlist.playlist_url

    return get_new_videos(url)


def playlist_check(playlist):
    """
    Check playlist for new videos and add them to database if not existed.
    """
    url = playlist.playlist_url
    new_videos = get_new_videos(url)
    if new_videos:
        logging.info("    %s. New videos: %s from %s", playlist.id, new_videos, playlist.playlist_name)

        for video in new_videos:
            add_video_to_base(video, playlist)
        return True
    return False


def playlists_update_checker():
    """
    Get a list of playlists and channels and check them for new videos.
    """
    playlists = Playlist.objects.values_list("id", flat=True)
    logging.info("Обработка плейлистов %s", playlists)

    for playlist_id in playlists:

        playlist = Playlist.objects.get(id=playlist_id)

        if playlist_check(playlist):
            playlist.last_video_date = datetime.now(tz=timezone.utc)

        playlist.update_time = datetime.now(tz=timezone.utc)
        playlist.save()


def messages_check():
    try:
        messages = Message.objects.filter(Q(status=False) & ~Q(message_type="message"))
    except:
        messages = []
    logging.info("Обработка сообщений %s", list(messages))

    for message in messages:
        logging.info("\t%s", message)
        if message.message_type == "playlist":
            create_playlist(message)

        elif message.message_type == "video":
            url = message.text
            new_videos = get_new_videos(url)

        logging.info("\tNew videos: %s", new_videos)

        for video in new_videos:
            add_video_to_base(video)

        message.status = True
        message.save()


class Command(BaseCommand):
    help = "Мониторинг сообщений"

    def handle(self, *args, **options):

        while True:
            messages_check()
            playlists_update_checker()

            time.sleep(30)
