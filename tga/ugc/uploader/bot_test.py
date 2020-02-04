from telethon import TelegramClient, connection, utils, types
# from FastTelethon import upload_file

from timeit import default_timer as timer
import time
from datetime import timedelta
import random
import logging
logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO)

api_id = 1002231
api_hash = '3869b51b1cbef59a5d5f480272c2c0d3'
bot_token = '1003358896:AAHDZ6qhg6120Z7d2wQ6Qu_Ka6aZ1rDe8yg'

MTPProxy = [('russia-dd.proxy.digitalresistance.dog', 443,
             'ddd41d8cd98f00b204e9800998ecf8427e'),
            ('0x03.tmp.telegramproxy.org', 443,
             'ddec0de00000000000000000000badcafe')][1]

me = '@vostenzuk'
session = 'bot_session'

MTPConnection = connection.tcpmtproxy.ConnectionTcpMTProxyRandomizedIntermediate

last_current, last_time = 0, time.time()


def progress_callback(current, total):
    global last_current, last_time
    now = time.time()
    last_current = current
    percent = int((current / total) * 100)
    print('\r{} %   '.format(percent), end='')
    if percent == 100:
        speed = round(((current - 0) / (now - last_time)) / 1000)
        print(speed, 'KB/s   ', end='')


async def uploader(client, chat_id, file):
    start_time = time.time()
    input_media_file = await upload_file(client,
                                         open(file, 'rb'),
                                         progress_callback=progress_callback)
    print('elapsed time',
          time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
    input_media_thumb = await client.upload_file(file.split('.')[0] + '.jpg')

    attributes, mime_type = utils.get_attributes(file)

    attributes[1].supports_streaming = True
    media = types.InputMediaUploadedDocument(file=input_media_file,
                                             mime_type=mime_type,
                                             attributes=attributes,
                                             thumb=input_media_thumb)

    send_file = await client.send_file(chat_id,
                                       file,
                                       thumb='tmp.jpg',
                                       supports_streaming=True,
                                       progress_callback=progress_callback)
    print(send_file.media.document)
    print(utils.pack_bot_file_id(send_file.media.document))


client = TelegramClient(
    'upload',
    api_id,
    api_hash,
    proxy=MTPProxy,
    connection=MTPConnection,
)


def main():
    with client:
        start_time = time.time()
        client.loop.run_until_complete(
            uploader(client, '@postoronniy_bot', 'tmp.mp4'))
        print('elapsed time',
              time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))


main()
