import base64
import logging
import os
import re
import time

import qbittorrentapi

from .config_data import env_keys, config

logger = logging.getLogger(__name__)


class GetInfoFromMagnet(Exception):
    """Исключение при получении данных о торренте по магнет ссылке"""
    pass


QBITTORRENT_HOST = config.addr
QBITTORRENT_PORT = config.port
QBITTORRENT_USERNAME = env_keys.QB_USER
QBITTORRENT_PASSWORD = env_keys.QB_PASSWORD

# Клиент не подключается к qBittorrent при создании, только при первом запросе
client = qbittorrentapi.Client(
    host=QBITTORRENT_HOST,
    port=QBITTORRENT_PORT,
    username=QBITTORRENT_USERNAME,
    password=QBITTORRENT_PASSWORD,
)

METADATA_MAX_RETRIES = 30  # ждем до 60 секунд (30 * 2)
METADATA_RETRY_DELAY = 2


def get_info_hash(magnet_link: str) -> str:
    """Получить info hash из магнет ссылки в hex формате (нижний регистр).
    Поддерживаются hex (40 символов) и base32 (32 символа) варианты."""
    match = re.search(r'btih:([a-zA-Z0-9]+)', magnet_link or '')
    if not match:
        raise GetInfoFromMagnet("Не удалось найти хэш магнет ссылки")
    raw_hash = match.group(1)

    if len(raw_hash) == 40 and re.fullmatch(r'[a-fA-F0-9]{40}', raw_hash):
        return raw_hash.lower()
    if len(raw_hash) == 32:
        try:
            return base64.b32decode(raw_hash.upper()).hex()
        except ValueError as e:
            raise GetInfoFromMagnet("Некорректный base32 хэш в магнет ссылке") from e
    raise GetInfoFromMagnet("Некорректный хэш в магнет ссылке")


def add_torrent_from_magnet(magnet, rename=None, path=None, tags_add=None):
    if tags_add is None:
        tags_add = []
    try:
        result = client.torrents_add(urls=magnet, rename=rename, save_path=path, tags=tags_add)
    except qbittorrentapi.exceptions.APIError as e:
        logger.exception("Ошибка API при добавлении торрента")
        return f"Ошибка API при добавлении торрента: {e}"
    except Exception as e:
        logger.exception("Ошибка при добавлении торрента")
        return f"Ошибка при добавлении торрента: {e}"

    # qBittorrent возвращает "Fails.", если торрент не добавлен (например, уже есть в клиенте)
    if isinstance(result, str) and result.strip().lower().startswith('fail'):
        return "qBittorrent не добавил торрент (возможно, он уже есть в клиенте)."

    return "Торрент добавлен!"


def _wait_files(info_hash):
    """Ждем, пока qBittorrent получит метаданные и список файлов"""
    for _ in range(METADATA_MAX_RETRIES):
        files = client.torrents_files(info_hash)
        if files:
            return files
        time.sleep(METADATA_RETRY_DELAY)
    raise GetInfoFromMagnet("Не удалось получить информацию о файлах")


def get_info_from_magnet_by_qb(magnet_link):
    info_hash = get_info_hash(magnet_link)

    # Если торрент уже есть в клиенте, используем его и ни в коем случае не удаляем
    already_exists = bool(client.torrents_info(torrent_hashes=info_hash))
    added_by_us = False

    try:
        if not already_exists:
            client.torrents_add(urls=magnet_link)
            added_by_us = True

        files = _wait_files(info_hash)

        # Общая информация о торренте (имя, сиды, пиры)
        main_info_list = client.torrents_info(torrent_hashes=info_hash)
        if not main_info_list:
            raise GetInfoFromMagnet("Не удалось получить информацию о торренте")
        main_info = main_info_list[0]

        # Список трекеров (announce)
        trackers = client.torrents_trackers(info_hash)
        announce_list = [t['url'] for t in trackers if t['url'].startswith('http')]

        # Список файлов с нужной структурой
        files_list = [{
            "name": os.path.basename(f['name']),  # только имя файла
            "path": f['name'],                    # полный путь внутри торрента
            "size": f['size'],                    # размер в байтах
        } for f in files]

        return {
            "data": {
                "announce": announce_list,
                "files": files_list,
                "infoHash": info_hash,
                "magnetURI": magnet_link,
                "name": main_info.get('name'),
                "peers": main_info.get('num_incomplete', 0),
                "seeds": main_info.get('num_seeds', 0),
            }
        }

    finally:
        # Удаляем только тот торрент, который сами добавили для получения метаданных
        if added_by_us:
            try:
                client.torrents_delete(delete_files=True, torrent_hashes=info_hash)
            except Exception:
                logger.exception("Не удалось удалить временный торрент %s", info_hash)
