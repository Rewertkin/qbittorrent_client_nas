"""бот для добавления на скачивание на основе переданного сообщения"""
import requests
import logging
import telebot
from . import kinopoisk_api as kp
from . import tmdb_api as tmdb
from . import qbittorrent_client as qb
from .message_tools import Message_data
from .metadata_tools import Metadata, get_name_torrent
from .config_data import env_keys, config
from .config_logger import setup_logging


setup_logging()
logger = logging.getLogger(__name__)

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

    logger.info(f'Данные из объекта message_data: \
                title: {message_data.title}, \
                alternative_title: {message_data.alternative_title}, \
                year: {message_data.year}, \
                season {message_data.season}')

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
    
    logger.info(f'Данные из объекта metadata: \
                name: {metadata.name}, \
                inDir: {metadata.inDir}, \
                isMovies: {metadata.isMovies}, \
                files {metadata.files}')

    try:
        bot.reply_to(message, "Подготавливаем torrent к скачиванию...")
    except telebot.apihelper.ApiTelegramException as e:
        bot.reply_to(message, f"Ошибка при отправке сообщения: {e}")
    
    id_film = 0
    if metadata.isMovies:
        if config.search_database == 'kp':
            id_film = kp.get_id_kinopoisk(message_data)
        elif config.search_database == 'tmdb':
            id_film = tmdb.get_id_tmdb(message_data)
    
    id_suffix = None

    if id_film > 0 and config.search_database == 'kp':
        id_suffix = 'kp' + str(id_film)
    elif id_film > 0 and config.search_database == 'tmdb':
        id_suffix = f'[tmdbid-{id_film}]'

    #подготавливаем путь для скачивания
    tags_add = []
    title_folder = ''
    if not metadata.inDir:
    #если нет папки 1 уровня в торренте, формируем ее название
        title_folder = get_name_torrent(message_data, metadata, id_suffix)
    else:
    #если папка есть, нам надо будет ее переимновать на пост обработке
    #для этого добавим тег, которым пометит скачанную папку скрипт
        if id_suffix is not None:
            tags_add = [id_suffix]

    #определеяем в какую папку скачиваем
    if id_suffix is not None:
        if message_data.season:
            path_download = config.serials_path
        else:
            path_download = config.movies_path
    else:
        path_download = config.default_path

    if title_folder is not None:
        path_download = path_download + '/' + title_folder

    #добавляем наименование для торрента в клиенте
    name_torrent = get_name_torrent(message_data, metadata, id_suffix)

    #добавляем задачу на скачку
    try:
        result_string = qb.add_torrent_from_magnet(message_data.magnet, rename=name_torrent, path=path_download, tags_add = tags_add)
        bot.reply_to(message, result_string + f" Папка: {path_download}")
    except:
        bot.reply_to(message, "Не удалось добавить торрент!")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
