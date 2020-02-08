import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
import tqdm


from django.conf import settings
from telethon.sync import TelegramClient, utils
# from tornado.platform.asyncio import AnyThreadEventLoopPolicy

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tga.tga.settings")

# asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO)

last_current = 0


def get_ids_by_link(link):
    command = ['youtube-dl', '--get-id', '--skip-download', link]

    edit = lambda x: x.strip().decode("utf-8")

    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout = list(map(edit, p.stdout.readlines())) if p.stdout else ''
    stderr = p.stderr.read().decode("utf-8") if p.stderr else ''

    if stderr:
        return stderr
    return stdout


def progress_callback(current, total):
    # if last_current == 0:
    #     last_time = time.time()
    # last_current += 1
    now = time.time()
    percent = int((current / total) * 100)
    print(f'\r{percent}%  ', end='')
    if percent == 100:
        pass
        # speed = round(((current - 0) / (now - last_time)) / 1000)
        # delta_time = now - last_time
        # print(speed, 'KB/s |', round(delta_time), 'с', end='\n')


def progress_tqdm(callback, current, total):
    callback.update()


class YtVideo:
    def __init__(self, yt_id):
        self.url = f'https://www.youtube.com/watch?v={yt_id}'
        self.yt_id = yt_id
        self.uploader = None
        self.upload_date = None
        self.title = None
        self.tags = []
        self.categories = []
        self.duration = None
        self.view_count = None
        self.like_count = None
        self.average_rating = None
        self.tg_id = ''
        self.update_metadata()

    # def __new__(cls, *args, **kwargs):

    def download_video(self):
        if not os.path.exists(settings.DOWNLOAD_PATH):
            os.mkdir(settings.DOWNLOAD_PATH)
            logging.info(f'{settings.DOWNLOAD_PATH} created')
        if os.path.exists(
                f'{settings.DOWNLOAD_PATH}/{self.yt_id}/{self.yt_id}.mp4'):
            return
        command = [
            'youtube-dl', '--quiet', '--write-thumbnail', '--write-info-json',
            '-f', 'mp4', '-o',
            f'{settings.DOWNLOAD_PATH}/%(id)s/%(id)s.%(ext)s', self.url
        ]

        stderr = subprocess.check_output(command, stderr=subprocess.STDOUT)
        logging.warning(f'{stderr=}')

    def update_metadata(self):
        YtVideo.download_video(self)

        with open(
                f'{settings.DOWNLOAD_PATH}/{self.yt_id}/{self.yt_id}.info.json'
        ) as file:
            j_data = json.loads(file.read())
            self.uploader = j_data['uploader']
            self.upload_date = j_data['upload_date']
            self.title = j_data['fulltitle']
            self.tags = j_data['tags']
            self.categories = j_data['categories']
            self.duration = j_data['duration']
            self.view_count = j_data['view_count']
            self.like_count = j_data['like_count']
            self.average_rating = j_data['average_rating']

    def send_video(self):
        # YtVideo.update_metadata(self)
        caption = '**' + self.title + '**' + '\n' + \
                  f'Автор: [{self.uploader}]({self.url})'
        file = f'{settings.DOWNLOAD_PATH}/{self.yt_id}/{self.yt_id}.mp4'
        with TelegramClient(
                f'upload',
                settings.UPLOADER.API_ID,
                settings.UPLOADER.API_HASH,
        ) as client:
            t = tqdm.tqdm(total=100)
            file = client.send_file(
                settings.TMP_CHAT,
                file,
                thumb=f'{settings.DOWNLOAD_PATH}/{self.yt_id}/{self.yt_id}.jpg',
                caption=caption,
                supports_streaming=True,
                progress_callback=lambda x, y: progress_tqdm(t, x, y))

            self.tg_id = utils.pack_bot_file_id(file.media.document)
            logging.info(f'tg_id={self.tg_id}')

            shutil.rmtree(f'{settings.DOWNLOAD_PATH}/{self.yt_id}',
                          ignore_errors=True)
