"""бот для добавления на скачивание на основе переданного сообщения"""
import logging
import telebot
from . import kinopoisk_api as kp
from . import tmdb_api as tmdb
from . import qbittorrent_client as qb
from .message_tools import Message_data
from .metadata_tools import Metadata, get_name_torrent
from .config_data import env_keys, config, get_allowed_users
from .config_logger import setup_logging


setup_logging()
logger = logging.getLogger(__name__)
logger.info("Логирование запущено")

TG_BOT_TOKEN = env_keys.TG_BOT_TOKEN
bot = telebot.TeleBot(TG_BOT_TOKEN)

WHITELIST = get_allowed_users(env_keys, config)


def safe_reply(message, text):
    """Ответить на сообщение, не роняя обработчик при ошибке Telegram API"""
    try:
        bot.reply_to(message, text)
    except telebot.apihelper.ApiTelegramException:
        logger.exception("Ошибка при отправке сообщения в Telegram")


@bot.message_handler(func=lambda message: True)  # Обрабатывает все текстовые сообщения
def echo_all(message):
    user_id = message.from_user.id
    if user_id not in WHITELIST:
        safe_reply(message, "❌ Извините, у вас нет доступа к этому боту.")
        logger.warning("Доступ запрещен для %s", user_id)
        return

    try:
        process_message(message)
    except Exception as e:
        # Любая непредвиденная ошибка: логируем и сообщаем пользователю, а не молчим
        logger.exception("Ошибка при обработке сообщения")
        safe_reply(message, f"Ошибка при обработке сообщения: {e}")


def process_message(message):
    safe_reply(message, "Анализируем сообщение...")

    message_data = Message_data.prepare_message_data(message.text)  # получаем данные из сообщения
    logger.info("Данные из сообщения: %r", message_data)

    if not message_data.magnet:
        safe_reply(message, "Магнет ссылка не найдена!")
        return

    if getattr(config, 'metadata_service', 'external') == 'qb':
        safe_reply(message, "Получаем список файлов через qBittorrent, это может занять до минуты...")

    try:
        metadata = Metadata.prepare_from_magnet(message_data.magnet)  # получаем метаданные торрента
    except Exception as e:
        # requests (external сервис), qbittorrentapi и GetInfoFromMagnet (qb), MetadataError
        logger.exception("Не удалось получить метаданные торрента")
        safe_reply(message, f"Торрент не найден! ({e})")
        return

    logger.info("Метаданные: name=%s, inDir=%s, isMovies=%s, files=%s",
                metadata.name, metadata.inDir, metadata.isMovies, metadata.files)

    safe_reply(message, "Подготавливаем torrent к скачиванию...")

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

    # подготавливаем путь для скачивания
    tags_add = []
    title_folder = ''
    if not metadata.inDir:
        # если нет папки 1 уровня в торренте, формируем ее название
        title_folder = get_name_torrent(message_data, metadata, id_suffix)
    elif id_suffix is not None:
        # если папка есть, ее надо будет переименовать на пост обработке,
        # для этого добавим тег, по которому скрипт найдет скачанную папку
        tags_add = [id_suffix]

    # определяем, в какую папку скачиваем
    if id_suffix is not None:
        path_download = config.serials_path if message_data.season else config.movies_path
    else:
        path_download = config.default_path

    if title_folder:
        path_download = path_download + '/' + title_folder

    # наименование торрента в клиенте
    name_torrent = get_name_torrent(message_data, metadata, id_suffix)

    # добавляем задачу на скачивание
    result_string = qb.add_torrent_from_magnet(message_data.magnet, rename=name_torrent,
                                               path=path_download, tags_add=tags_add)
    safe_reply(message, result_string + f" Папка: {path_download}")


if __name__ == '__main__':
    logger.info("Бот запущен...")
    bot.infinity_polling()
