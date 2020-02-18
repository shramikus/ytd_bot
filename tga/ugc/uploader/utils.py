import json
import logging
import os
import shutil
import subprocess

# import time

from django.conf import settings
from telethon import TelegramClient, utils

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.WARNING
)


def get_ids_by_link(link, num=None):
    if num:
        command = [
            "youtube-dl",
            "--get-id",
            "--skip-download",
            "--playlist-end",
            str(num),
            link,
        ]
    else:
        command = [
            "youtube-dl",
            "--get-id",
            "--skip-download",
            link,
        ]
    edit = lambda x: x.strip().decode("utf-8")

    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = list(map(edit, p.stdout.readlines())) if p.stdout else ""
    stderr = p.stderr.read().decode("utf-8") if p.stderr else ""

    if stderr:
        return stderr
    return stdout


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

    async def send_video(self):

        # YoutubeVideo.update_metadata(self)
        caption = f"**{self.title}**\n" + f"Автор: [{self.uploader}]({self.make_url()})"

        async with TelegramClient(
                "upload", settings.API_ID, settings.API_HASH,
        ) as client:
            file = await client.send_file(
                settings.TMP_CHAT,
                self.get_full_path("mp4"),
                thumb=self.get_full_path("jpg"),
                caption=caption,
                supports_streaming=True,
                # progress_callback=progress_callback,
            )

            self.tg_id = utils.pack_bot_file_id(file.media.document)
            logging.info("tg_id: %s", self.tg_id)

            shutil.rmtree(self.get_full_path(), ignore_errors=True)
