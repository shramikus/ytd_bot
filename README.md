## Описание

Простой телеграм-бот, который записывает все сообщения в БД. Скачивает видео с youtube, выкладывает его в телеграм, записывает информацию о видео в базу.

На основе telethon и Django.

Смотреть видео: [video](https://youtu.be/s9RHzPLtYWk)

## Настройка

Установить зависимости:

    pip install -r requirements.txt

Запуск админки:

    workon td
    cd /Users/vladimir/Developer/td/tga
    python manage.py runserver
    
    
Запуск бота:

    workon td
    cd /Users/vladimir/Developer/td/tga
    python manage.py bot
