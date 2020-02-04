from django.core.management.base import BaseCommand
from django.conf import settings

from telegram import Bot
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.utils.request import Request
from datetime import datetime
from django.utils import timezone

from ugc.models import Message
from ugc.models import Profile
from ugc.models import Video

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
def do_echo(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    p, _ = Profile.objects.get_or_create(external_id=chat_id,
                                         defaults={
                                             "name":
                                             update.message.from_user.username,
                                         })
    m = Message(
        profile=p,
        text=text
    )
    m.save()

    reply_text = f"Ваш ID = {chat_id}\n{text}"
    update.message.reply_text(text=reply_text)


@log_errors
def do_count(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    p, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={"name": update.message.from_user.username})
    # count = Message.objects.filter(profile=p).count()
    count = 0
    update.message.reply_text(text=f"У вас {count} сообщений")


@log_errors
def send_video(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text.split()[-1]

    p, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={"name": update.message.from_user.username})
    yt_ids = utils.get_ids_by_link(text)

    if isinstance(yt_ids, list):
        for yt_id in yt_ids:
            video = utils.YtVideo(yt_id)
            video.send_video()
            v = Video(
                yt_id=video.yt_id,
                title=video.title,
                uploader=video.uploader,
                upload_date=timezone.get_current_timezone().localize(
                    datetime.strptime(video.upload_date, "%Y%m%d")),
                view_count=video.view_count,
                tg_id=video.tg_id,
                rating=video.average_rating,
                yt_url=video.url,
            )
            v.save()
        update.message.reply_text(text="Успешно")
    elif isinstance(yt_ids, str):
        update.message.reply_text(text=yt_ids)


class Command(BaseCommand):
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        request = Request(connect_timeout=5, read_timeout=5, con_pool_size=8)
        bot = Bot(request=request,
                  token=settings.TOKEN,
                  base_url=getattr(settings, "PROXY_URL", None))
        print(bot.get_me())

        # 2 -- обработчики
        updater = Updater(bot=bot, use_context=True)
        message_handler = MessageHandler(Filters.text, do_echo)
        updater.dispatcher.add_handler(message_handler)
        updater.dispatcher.add_handler(CommandHandler("count", do_count))
        updater.dispatcher.add_handler(CommandHandler("video", send_video))
        updater.start_polling()
        updater.idle()
