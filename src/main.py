"""бот для добавления на скачивание на основе переданного сообщения"""
import re
import requests
import telebot
from . import kinopoisk_api as kp
from . import qbittorrent_client as qb
from .message_tools import Message_data
from .metadata_tools import Metadata, get_name_torrent
from .config_data import env_keys, config



TG_BOT_TOKEN = env_keys.TG_BOT_TOKEN
bot = telebot.TeleBot(TG_BOT_TOKEN)

WHITELIST = config.allowed_users

@bot.message_handler(func=lambda message: True)  # Обрабатывает все текстовые сообщения

def echo_all(message):

    user_id = message.from_user.id
    if user_id not in WHITELIST:
        bot.reply_to(message, "❌ Извините, у вас нет доступа к этому боту.")
        print(f"Доступ запрещен для {user_id}")
        return

    try:
        bot.reply_to(message, "Анализируем сообщение...")
    except telebot.apihelper.ApiTelegramException as e:
        bot.reply_to(message, f"Ошибка при отправке сообщения: {e}")

    message_data = Message_data.prepare_message_data(message.text) #получаем данные из сообщения

    if not message_data.magnet:
        bot.reply_to(message, "Магнет ссылка не найдена!")
        return
    try:
        metadata = Metadata.prepare_from_magnet(message_data.magnet)#получаем метаданные торрента
    except requests.exceptions.HTTPError:
        bot.reply_to(message, "Торрент не найден!")
        return
    except requests.exceptions.ReadTimeout:
        bot.reply_to(message, "Торрент не найден!")
        return

    try:
        bot.reply_to(message, "Подготавливаем torrent к скачиванию...")
    except telebot.apihelper.ApiTelegramException as e:
        bot.reply_to(message, f"Ошибка при отправке сообщения: {e}")
    
    kp_id = 0
    if metadata.isMovies:
        kp_id = kp.get_id_kinopoisk(message_data)

    #подготавливаем путь для скачивания
    tags_add = []
    title_folder = ''
    if not metadata.inDir:
    #если нет папки 1 уровня в торренте, формируем ее название
        title_folder = get_name_torrent(message_data, metadata, kp_id)
    else:
    #если папка есть, нам надо будет ее переимновать на пост обработке
    #для этого добавим тег, которым пометит скачанную папку скрипт
        if kp_id > 0:
            tags_add = ['kp' + str(kp_id)]

    #определеяем в какую папку скачиваем
    if kp_id > 0:
        if message_data.season:
            path_download = config.serials_path
        else:
            path_download = config.movies_path
    else:
        path_download = config.default_path

    if title_folder is not None:
        path_download = path_download + '/' + title_folder

    #добавляем наименование для торрента в клиенте
    name_torrent = get_name_torrent(message_data, metadata, kp_id)

    #добавляем задачу на скачку
    try:
        result_string = qb.add_torrent_from_magnet(message_data.magnet, rename=name_torrent, path=path_download, tags_add = tags_add)
        bot.reply_to(message, result_string + f" Папка: {path_download}")
    except:
        bot.reply_to(message, "Не удалось добавить торрент!")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
