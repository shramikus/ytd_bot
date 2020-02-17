import asyncio
import logging
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from telegram import Bot, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)
from telegram.utils.request import Request

from ugc.models import Message, Profile, Video
from ugc.uploader import utils


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING
)


def log_errors(function):
    def inner(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception:
            error_message = f"Произошла ошибка: {Exception}"
            print(error_message)
            raise Exception

    return inner


@log_errors
def do_echo(update: Update):
    if update.effective_chat.type == "private":
        message_chat_id = update.effective_chat.id
        message_text = update.message.text
        message_username = update.message.from_user.username

        profile, _ = Profile.objects.get_or_create(
            external_id=message_chat_id, defaults={"name": message_username}
        )
        message = Message(profile=profile, text=message_text)
        message.save()

        reply_text = (
            f"Принято\n" f"chat_id: {message_chat_id}\n" f"username: {message_username}"
        )
        update.message.reply_text(text=reply_text)


@log_errors
def send_video(update: Update, context: CallbackContext):
    assert update.effective_chat.id in settings.AUTH_USERS
    text = update.message.text.split()

    message = update.message.reply_text(text="Получаю информацию о списке видео")

    if len(text) == 3:
        num_videos = int(text[-1])
        yt_ids = utils.get_ids_by_link(text[1], num=num_videos)
    else:
        yt_ids = utils.get_ids_by_link(text[1])

    if isinstance(yt_ids, list):
        logging.info(yt_ids)

        for i, yt_id in enumerate(yt_ids):
            context.bot.edit_message_text(
                chat_id=message.chat_id,
                message_id=message.message_id,
                text=f"Загружаю видео {i+1} из {len(yt_ids)}\n"
                f"[https://www.youtube.com/watch?v={yt_id}]"
                f"(https://www.youtube.com/watch?v={yt_id})",
                parse_mode="Markdown",
            )

            video = utils.YtVideo(yt_id)
            asyncio.run(video.send_video())
            v = Video(
                yt_id=video.yt_id,
                title=video.title,
                uploader=video.uploader,
                upload_date=timezone.get_current_timezone().localize(
                    datetime.strptime(video.upload_date, "%Y%m%d")
                ),
                view_count=video.view_count,
                tg_id=video.tg_id,
                rating=video.average_rating,
                yt_url=video.url,
                tags=video.tags,
                categories=video.categories,
                likes=video.like_count,
            )
            v.save()

        success_text = f"{len(yt_ids)} видео успешно загружены\n" + "\n".join(
            [
                f"[https://www.youtube.com/watch?v={yt_id}]"
                f"(https://www.youtube.com/watch?v={yt_id})"
                for yt_id in yt_ids
            ]
        )
        context.bot.edit_message_text(
            chat_id=message.chat_id,
            message_id=message.message_id,
            text=success_text,
            parse_mode="Markdown",
        )

    elif isinstance(yt_ids, str):
        logging.error(yt_ids)
        context.bot.edit_message_text(
            chat_id=message.chat_id, message_id=message.message_id, text=yt_ids
        )


@log_errors
def send_post_context(context: CallbackContext, video_id=None):
    chat_id = settings.CHANNEL
    if video_id:
        v = Video.objects.get(yt_id=video_id)
    else:
        v = Video.objects.order_by("status", "-upload_date")[0]
    print(v.tg_id, v.status)
    caption = "*" + v.title + "*" + "\n" + f"Автор: [{v.uploader}]({v.yt_url})"
    v.status += 1
    v.save()

    context.bot.send_video(chat_id, v.tg_id, caption=caption, parse_mode="Markdown")


@log_errors
def send_post(update: Update, context: CallbackContext):
    assert update.effective_chat.id in settings.AUTH_USERS
    text = update.message.text.split()[1:]
    if len(text) == 2:
        h = int(text[1].split(":")[0])
        m = int(text[1].split(":")[1])
        push_time = (
            datetime.now().replace(hour=h, minute=m, second=1) - datetime.now()
        ).seconds

        context.job_queue.run_once(
            lambda x: send_post_context(x, text[0]), push_time,
        )
    elif len(text) == 0:
        context.job_queue.run_once(
            send_post_context, 1,
        )
    elif len(text) == 1:
        context.job_queue.run_once(
            lambda x: send_post_context(x, text[0]), 1,
        )


@log_errors
def job_maker(update: Update, context: CallbackContext):
    assert update.effective_chat.id in settings.AUTH_USERS
    text = update.message.text.split()[1:]
    try:
        interval = int(text[0])
        first = context.args[1]
        if first == "now":
            first = None
            dt = datetime.now().hour, datetime.now().minute
        else:
            h = int(first.split(":")[0])
            m = int(first.split(":")[1])
            first = datetime.now().replace(hour=h, minute=m, second=1)
            dt = first.hour, first.minute

        if "job" in context.chat_data:
            old_job = context.chat_data["job"]
            old_job.schedule_removal()
        new_job = context.job_queue.run_repeating(send_post_context, interval, first)

        context.chat_data["job"] = new_job
        update.message.reply_text(
            "Расписание настроено"
            f"Интервал: {interval/60} мин"
            f"Начало: {dt[0]}:{dt[1]}"
        )

    except (IndexError, ValueError):
        update.message.reply_text("Используй: /set <интервал> <начало>")


@log_errors
def unset(update: Update, context: CallbackContext):
    if "job" not in context.chat_data:
        update.message.reply_text("Автопубликации не настроены")
        return

    job = context.chat_data["job"]
    job.schedule_removal()
    del context.chat_data["job"]

    update.message.reply_text("Автопубликация выключена")


@log_errors
def help_command(update: Update):

    text = (
        "Список комманд:\n"
        "/video <ссылка на видео/канал/плейлист> "
        "<опционально, колличество видео для загрузки>\n"
        "/send <id видео> <время отправки>\n"
        "/set <интервал> <начало>\n"
        "/unset - убрать расписание"
    )

    update.message.reply_text(text=text)


class Command(BaseCommand):
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        request = Request(connect_timeout=5, read_timeout=5, con_pool_size=8)
        bot = Bot(request=request, token=settings.BOT_TOKEN,)
        print(bot.get_me())

        updater = Updater(bot=bot, use_context=True)
        message_handler = MessageHandler(Filters.text, do_echo)
        updater.dispatcher.add_handler(CommandHandler("help", help_command))
        updater.dispatcher.add_handler(CommandHandler("video", send_video))
        updater.dispatcher.add_handler(CommandHandler("send", send_post))
        updater.dispatcher.add_handler(CommandHandler("set", job_maker))
        updater.dispatcher.add_handler(CommandHandler("unset", unset))
        updater.dispatcher.add_handler(message_handler)
        updater.start_polling()
        updater.idle()
