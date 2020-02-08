from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from telethon.sync import TelegramClient, events

from ugc.models import Message, Profile, Video
from ugc.uploader import utils


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f"Произошла ошибка: {e}"
            print(error_message)
            raise e

    return inner


@log_errors
async def echo(event):
    p, _ = Profile.objects.get_or_create(
        external_id=event.chat_id, defaults={"name": event.chat.username})
    m = Message(profile=p, text=event.text)
    m.save()

    reply_text = f"Принято\n" \
                 f"chat_id: {event.chat_id}\n" \
                 f"username: {event.chat.username}"
    await event.respond(reply_text)


@log_errors
async def send_video(event):
    chat_id = event.chat_id
    text = event.text

    p, _ = Profile.objects.get_or_create(
        external_id=chat_id, defaults={"name": event.chat.username})
    yt_ids = utils.get_ids_by_link(text)

    if isinstance(yt_ids, list):
        for yt_id in yt_ids:
            video = utils.YtVideo(yt_id)
            await video.send_video()
            v = Video(yt_id=video.yt_id,
                      title=video.title,
                      uploader=video.uploader,
                      upload_date=timezone.get_current_timezone().localize(
                          datetime.strptime(video.upload_date, "%Y%m%d")),
                      view_count=video.view_count,
                      tg_id=video.tg_id,
                      rating=video.average_rating,
                      yt_url=video.url)
            v.save()
        await event.respond(f'{yt_ids}\n Успешно')
    elif isinstance(yt_ids, str):
        await event.respond(yt_ids)


class Command(BaseCommand):
    help = "Telethon-bot"

    def handle(self, *args, **options):
        bot = TelegramClient(
            'bot', settings.API_ID,
            settings.API_HASH).start(bot_token=settings.BOT_TOKEN)

        bot.add_event_handler(echo, events.NewMessage)
        bot.add_event_handler(send_video,
                              events.NewMessage(pattern=r'http[s]?://'))
        bot.run_until_disconnected()
