import logging
import time
import re
import requests
from datetime import datetime, timezone
from xml.etree import ElementTree

# from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from ugc.models import Message, Video, Playlist
from ugc import utils


logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


def get_id(url):
    channel_id = re.findall(r"channel\/([\w\d\-\_]+)", url)[0]
    return channel_id


def get_videos_json(playlist_id):
    api_key = "AIzaSyDdO6QM7ytguBUstgv3BWh0Q37dT5T3N6w"
    request_url = "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={}&maxResults=5&order=date&type=video&key={}"

    playlist_info = requests.get(request_url.format(playlist_id, api_key)).json()[
        "items"
    ]
    return playlist_info


def get_videos_xml(playlist_id):
    request_url = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
    playlist_info = requests.get(request_url.format(playlist_id)).content
    return ElementTree.fromstring(playlist_info)


def get_video_data_json(video):
    video_id = video["id"]["videoId"]
    video_publication_date_string = video["snippet"]["publishedAt"].replace(
        "Z", "+00:00"
    )
    video_publication_date = datetime.fromisoformat(video_publication_date_string)
    return (video_id, video_publication_date)


def get_video_data_xml(video):
    video_id = video.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
    video_publication_date_string = video.find(
        "{http://www.w3.org/2005/Atom}published"
    ).text
    video_publication_date = datetime.fromisoformat(video_publication_date_string)
    return (video_id, video_publication_date)


def get_videos_data(url, num=3, parser="xml"):
    playlist_id = get_id(url)
    videos_data = []

    if parser == "xml":
        videos = get_videos_xml(playlist_id)
        for video in videos.findall("{http://www.w3.org/2005/Atom}entry")[:num]:
            videos_data.append(get_video_data_xml(video))

    elif parser == "json":
        videos = get_videos_json(playlist_id)

        for video in videos[:num]:
            videos_data.append(get_video_data_json(video))

    elif parser == "yotube-dl":
        videos = utils.get_ids_by_link(url, num=num)
        videos_data = [[video, None] for video in videos]

    return videos_data


def create_playlist(message):
    playlist = Playlist(playlist_url=message.text)
    playlist.save()
    logging.info("Плейлист добавлен: %s", message.text)
    return playlist


def add_video_to_base(video_data, playlist=None):
    """
    Add a single video to playlist with hot status from playlist status.
    """
    video_id = video_data[0]
    video_date = video_data[1]
    video = Video(
        yt_id=video_id, upload_date=video_date, playlist=playlist, hot=playlist.active
    )
    video.save()
    return video


def get_new_videos(url, parser='xml'):
    """
    Get new videos from playlist.
    """
    # dateafter = playlist.update_time

    existed_videos = Video.objects.values_list("yt_id", flat=True)

    received_videos = get_videos_data(url, num=3, parser=parser)

    if isinstance(received_videos, str):
        logging.info("%s", received_videos)
        return []

    new_videos = [video for video in received_videos if video[0] not in existed_videos]
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
        logging.info(
            "    New videos: %s from %s",
            new_videos,
            playlist.playlist_name,
        )

        for video in new_videos:
            add_video_to_base(video, playlist)
        return True
    return False


def playlists_update_checker():
    """
    Get a list of playlists and channels and check them for new videos.
    """
    # playlists = Playlist.objects.filter(active=True)
    playlists = Playlist.objects.all()
    logging.info("Обработка плейлистов %s", playlists)

    for playlist in playlists:

        playlist = Playlist.objects.get(id=playlist.id)

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
            new_videos = get_new_videos(url, parser='yotube-dl')

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
