import logging
from datetime import datetime

# from django.conf import settings
from django.core.management.base import BaseCommand

# from django.utils import timezone

from telegram import Bot, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
    JobQueue,
)
from telegram.utils.request import Request

from ugc.models import Message, Profile, Video, Schedule, Settings
from ugc import utils


config = utils.get_bot_config(is_bot=True)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def log_errors(function):
    def inner(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exception:
            error_message = f"Произошла ошибка: {exception}"
            print(error_message)
            raise exception

    return inner


def do_echo(update: Update, context: CallbackContext):
    if update.effective_chat.type == "private":
        message_chat_id = update.effective_chat.id
        message_text = update.message.text
        message_username = update.message.from_user.username

        profile, _ = Profile.objects.get_or_create(
            external_id=message_chat_id, defaults={"name": message_username}
        )

        parsed_message = utils.parse_message(message_text)
        if parsed_message[0] != "message":
            assert update.effective_chat.id in config.auth_users
            message = Message(
                profile=profile,
                text=parsed_message[1],
                message_type=parsed_message[0],
                status=False,
            )
            reply_text = f"Принято\ntype: {parsed_message[0]}"
            update.message.reply_text(text=reply_text)
        else:
            message = Message(
                profile=profile, text=parsed_message[1], message_type=parsed_message[0],
            )

        message.save()


def send_post_context(context: CallbackContext, video_id=None):

    if video_id:
        v = Video.objects.get(yt_id=video_id)
    else:
        v = Video.objects.order_by("status", "-upload_date").first()

    caption = (
        f"*{v.title}*\n"
        f"Автор: [{v.uploader}](https://www.youtube.com/watch?v={v.yt_id})"
    )
    v.status += 1
    v.save()

    try:
        job = Schedule.objects.get(data=video_id)
        job.delete()
    except:
        pass

    context.bot.send_video(
        config.posting_channel, v.tg_id, caption=caption, parse_mode="Markdown"
    )
    logging.info("Видео опубликовано %s", v.title)


def send_post(update: Update, context: CallbackContext, push_data=None):
    assert update.effective_chat.id in config.auth_users

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


def job_maker(update: Update, context: CallbackContext):
    assert update.effective_chat.id in config.auth_users
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


def unset(update: Update, context: CallbackContext):
    if "job" not in context.chat_data:
        update.message.reply_text("Автопубликации не настроены")
        return

    job = context.chat_data["job"]
    job.schedule_removal()
    del context.chat_data["job"]

    update.message.reply_text("Автопубликация выключена")


def help_command(update: Update, context: CallbackContext):
    text = (
        "Список комманд:\n"
        "/video <видео/канал/плейлист> - загрузить видео\n"
        "/playlist <канал/плейлист> - мониторинг новых видео"
        "/send <id видео> <время отправки>\n"
        "/set <интервал> <начало>\n"
        "/unset - убрать расписание"
    )

    update.message.reply_text(text=text)

def tags_intersection(true_tags, tags):
    tags = tags.lower()
    for tag in true_tags:
        tag = tag.lower()
        if tag in tags:
            return True
    return False


def upload_hot_video(context: CallbackContext):
    videos = Video.objects.filter(hot=True, tg_id__isnull=False, status=0)
    publication_tags = [tag.tags for tag in Settings.objects.all()]
    
    for v in videos:
        if tags_intersection(publication_tags, v.tags):
            caption = (
                f"*{v.title}*\n"
                f"Автор: [{v.uploader}](https://www.youtube.com/watch?v={v.yt_id})"
            )
            v.status += 1
            v.save()

            context.bot.send_video(
                config.posting_channel, v.tg_id, caption=caption, parse_mode="Markdown"
            )


def setup_schedule(context: CallbackContext):
    jobs = Schedule.objects.all()
    for job in jobs:
        existed_jobs = [j.name for j in context.job_queue.jobs()]

        job_name = f"{job.post_type}_{job.data.split()[0]}"
        if job_name not in existed_jobs:
            context.job_queue.run_once(
                lambda x: send_post_context(x, job.data), job.post_time, name=job_name
            )
            logging.info(
                "Видео %s добавлено в расписание, время публикации %s",
                job.data,
                job.post_time,
            )


class Command(BaseCommand):
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        request = Request(connect_timeout=5, read_timeout=5, con_pool_size=8)
        bot = Bot(request=request, token=config.bot_token)
        print(bot.get_me())

        job_queue = JobQueue()
        updater = Updater(bot=bot, use_context=True)

        job_queue.set_dispatcher(updater.dispatcher)
        job_queue.run_repeating(upload_hot_video, 30, name="hot")
        job_queue.run_repeating(setup_schedule, 30, name="schedule_setup")
        job_queue.start()

        message_handler = MessageHandler(Filters.text, do_echo)
        updater.dispatcher.add_handler(CommandHandler("help", help_command))
        updater.dispatcher.add_handler(CommandHandler("send", send_post))
        updater.dispatcher.add_handler(CommandHandler("set", job_maker))
        updater.dispatcher.add_handler(CommandHandler("unset", unset))
        updater.dispatcher.add_handler(message_handler)
        updater.start_polling()
        updater.idle()
