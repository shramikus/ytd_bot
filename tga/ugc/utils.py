import json
import logging
import os
import shutil
import subprocess

import time
from django.conf import settings
from telethon import TelegramClient, utils

from ugc.models import AppConfig, Video

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)


def markdown_link(youtube_id):
    link = f"https://www.youtube.com/watch?v={youtube_id}"
    return f"[{link}]({link})"


def parse_message(message):
    if message.startswith("/video"):
        message = message[len("/video") + 1 :]
        return "video", message

    if message.startswith("/playlist"):
        message = message[len("/playlist") + 1 :]
        return "playlist", message

    if message.startswith("/schedule"):
        message = message[len("/schedule") + 1 :]
        return "schedule", message

    return "message", message


def existed_videos(youtube_ids):
    if isinstance(youtube_ids, str):
        return youtube_ids
    dowloaded_videos = list(Video.objects.values_list("yt_id", flat=True))
    new_youtube_ids = [yt_id for yt_id in youtube_ids if yt_id not in dowloaded_videos]
    if not new_youtube_ids:
        return "Нет новых видео"

    return new_youtube_ids


def format_date(date):
    return date.strftime("%Y%m%d")


def get_ids_by_link(link, num=None, date_after=None):
    if date_after is None and num is None:
        num = 3

    if num:
        command = [
            "youtube-dl",
            "--get-id",
            "--skip-download",
            "--playlist-end",
            str(num),
            link,
        ]
    elif date_after:
        command = [
            "youtube-dl",
            "--get-id",
            "--skip-download",
            "--dateafter",
            format_date(date_after),
            link,
        ]

    edit = lambda x: x.strip().decode("utf-8")

    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = list(map(edit, p.stdout.readlines())) if p.stdout else ""
    stderr = p.stderr.read()
    try:
        encoded_stderr = stderr.decode("utf-8") if stderr else ""
    except UnicodeDecodeError:
        encoded_stderr = str(stderr if stderr else "")
    if encoded_stderr:
        return encoded_stderr
    print(stdout)
    return stdout


def get_bot_config(is_bot=False):
    if is_bot:
        configs = AppConfig.objects.filter(is_bot=True, is_active=True)
        config = configs[0]
        config.bot_token = str(config.bot_token)
        config.posting_channel = int(config.posting_channel)
        config.auth_users = list(map(int, config.auth_users.split()))
    else:
        configs = AppConfig.objects.filter(is_bot=False, is_active=True)
        config = configs[0]
        config.session_name = str(config.session_name)
        config.api_id = int(config.api_id)
        config.api_hash = str(config.api_hash)
        config.temp_chat = str(config.temp_chat)

    logging.info("selected config %s", config)
    return config


def progress_callback(current, total):
    percent = int((current / total) * 100)
    print(f"\r{percent}%  ", end="")
    if percent == 100:
        print()


class YoutubeVideo:
    def __init__(self, video_id):
        self.video_id = video_id
        self.uploader = ""
        self.upload_date = ""
        self.title = ""
        self.tags = []
        self.categories = []
        self.duration = 0
        self.view_count = 0
        self.like_count = 0
        self.average_rating = 0.0
        self.tg_id = ""
        self.update_metadata()

    def make_url(self):
        url = f"https://www.youtube.com/watch?v={self.video_id}"
        return url

    def get_full_path(self, extension=None):
        if extension:
            video_path = os.path.join(
                settings.DOWNLOAD_PATH, self.video_id, f"{self.video_id}.{extension}"
            )
        else:
            video_path = os.path.join(settings.DOWNLOAD_PATH, self.video_id)
        return video_path

    def download_video(self):
        if not os.path.exists(settings.DOWNLOAD_PATH):
            os.mkdir(settings.DOWNLOAD_PATH)
            logging.info("%s created", settings.DOWNLOAD_PATH)

        if os.path.exists(self.get_full_path("mp4")):
            logging.warning("file already downloaded %s", self.get_full_path("mp4"))
            return None

        command = [
            "youtube-dl",
            "--quiet",
            "--write-thumbnail",
            "--write-info-json",
            "-f",
            "mp4",
            "-o",
            f"{settings.DOWNLOAD_PATH}/%(id)s/%(id)s.%(ext)s",
            self.make_url(),
        ]

        stderr = subprocess.check_output(command, stderr=subprocess.STDOUT)
        if stderr:
            logging.warning("stderr: %s", stderr)

    def update_metadata(self):

        self.download_video()

        with open(self.get_full_path("info.json"), "r") as file:
            j_data = json.loads(file.read())

            self.uploader = j_data["uploader"]
            self.upload_date = j_data["upload_date"]
            self.title = j_data["fulltitle"]
            self.tags = j_data["tags"]
            self.categories = j_data["categories"]
            self.duration = j_data["duration"]
            self.view_count = j_data["view_count"]
            self.like_count = j_data["like_count"]
            self.average_rating = j_data["average_rating"]

    async def session_login(self, client, config):
        if not await client.is_user_authorized():
            logging.info("Требуется авторизация номера %s", config.client_phone)
            await client.send_code_request(config.client_phone)
            while not config.client_code:
                time.sleep(30)
                config = get_bot_config()
            await client.sign_in(config.client_phone, config.client_code)

    async def send_video(self):
        config = get_bot_config()

        client = TelegramClient(config.session_name, config.api_id, config.api_hash,)
        await client.connect()
        await self.session_login(client, config)

        async with client:
            file = await client.send_file(
                config.temp_chat,
                self.get_full_path("mp4"),
                thumb=self.get_full_path("jpg"),
                supports_streaming=True,
                # progress_callback=progress_callback,
            )

            self.tg_id = utils.pack_bot_file_id(file.media.document)
            logging.info("tg_id: %s", self.tg_id)

            shutil.rmtree(self.get_full_path(), ignore_errors=True)
