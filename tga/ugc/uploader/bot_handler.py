#!/usr/bin/env python3
# A simple script to print all updates received.
# Import modules to access environment, sleep, write to stderr
import os
import sys
import time

# Import the client
from telethon import TelegramClient, events, utils

import logging
logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO)

# Define some variables so the code reads easier
api_id = 1002231
api_hash = '3869b51b1cbef59a5d5f480272c2c0d3'
bot_token = '1003358896:AAHDZ6qhg6120Z7d2wQ6Qu_Ka6aZ1rDe8yg'
proxy = None  # https://github.com/Anorov/PySocks

client = TelegramClient('wait_messages', api_id,
                        api_hash).start(bot_token=bot_token)


@client.on(events.NewMessage)
async def my_event_handler(event):
    print(event)
    print(event.media.document)
    file_id = utils.pack_bot_file_id(event.media.document)
    print(file_id)
    await client.send_file(
        '@vostenzuk',
        file_id,
        # thumb='tmp.jpg',
        # supports_streaming=True
    )


client.start()
client.run_until_disconnected()
