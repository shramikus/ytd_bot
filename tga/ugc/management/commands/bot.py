import asyncio
import logging
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F

from telegram import Bot, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, \
    MessageHandler, Updater
from telegram.utils.request import Request

from ugc.models import Message, Profile, Video
from ugc.uploader import utils

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f"Произошла ошибка: {e}"
            print(error_message)
            raise e

    return inner


# @log_errors
def do_echo(update: Update, context: CallbackContext):
    if update.effective_chat.type == 'private':
        chat_id = update.effective_chat.id
        text = update.message.text
        username = update.message.from_user.username

        p, _ = Profile.objects.get_or_create(external_id=chat_id,
                                             defaults={"name": username})
        m = Message(profile=p, text=text)
        m.save()

        reply_text = f"Принято\n" \
                     f"chat_id: {chat_id}\n" \
                     f"username: {username}"
        update.message.reply_text(text=reply_text)


@log_errors
def send_video(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text.split()[-1]
    username = update.message.from_user.username

    p, _ = Profile.objects.get_or_create(external_id=chat_id,
                                         defaults={"name": username})
    yt_ids = utils.get_ids_by_link(text)
    logging.info(yt_ids)

    if isinstance(yt_ids, list):
        for yt_id in yt_ids:
            video = utils.YtVideo(yt_id)
            asyncio.run(video.send_video())
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
        update.message.reply_text(text=f'{yt_ids}\n Успешно')
    elif isinstance(yt_ids, str):
        update.message.reply_text(text=yt_ids)


@log_errors
def send_post(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    v = Video.objects.order_by('status', '-view_count')[0]
    print(v.tg_id, v.status)
    caption = '*' + v.title + '*' + '\n' + \
              f'Автор: [{v.uploader}]({v.yt_url})'
    v.status += 1
    v.save()

    context.bot.send_video(chat_id,
                           v.tg_id,
                           caption=caption,
                           parse_mode='Markdown')


def send_post_context(context: CallbackContext):
    chat_id = settings.CHANNEL
    v = Video.objects.order_by('status', '-view_count')[0]
    print(v.tg_id, v.status)
    caption = '*' + v.title + '*' + '\n' + \
              f'Автор: [{v.uploader}]({v.yt_url})'
    v.status += 1
    v.save()

    context.bot.send_video(chat_id,
                           v.tg_id,
                           caption=caption,
                           parse_mode='Markdown')


# @log_errors
def job_maker(update: Update, context: CallbackContext):
    assert update.effective_chat.id in settings.AUTH_USERS
    chat_id = update.message.chat_id
    text = update.message.text.split()[1:]
    try:
        interval = int(text[0])
        first = context.args[1]
        if first == 'now':
            first = None
        else:
            h = int(first.split(':')[0])
            m = int(first.split(':')[1])
            first = datetime.now().replace(hour=h, minute=m)

        # Add job to queue and stop current one if there is a timer already
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_repeating(send_post_context,
                                                  interval,
                                                  first,
                                                  context=chat_id)
        context.chat_data['job'] = new_job

        update.message.reply_text('Успешно!')

    except (IndexError, ValueError):
        update.message.reply_text('Используй: /job <интервал> <начало>')


def unset(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Timer successfully unset!')


class Command(BaseCommand):
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        request = Request(connect_timeout=5, read_timeout=5, con_pool_size=8)
        bot = Bot(
            request=request,
            token=settings.BOT_TOKEN,
            # base_url=getattr(settings, "PROXY_URL", None)
        )
        print(bot.get_me())

        updater = Updater(bot=bot, use_context=True)
        message_handler = MessageHandler(Filters.text, do_echo)
        updater.dispatcher.add_handler(CommandHandler("video", send_video))
        updater.dispatcher.add_handler(CommandHandler("send", send_post))
        updater.dispatcher.add_handler(CommandHandler("set", job_maker))
        updater.dispatcher.add_handler(CommandHandler("unset", unset))
        updater.dispatcher.add_handler(message_handler)
        updater.start_polling()
        updater.idle()
