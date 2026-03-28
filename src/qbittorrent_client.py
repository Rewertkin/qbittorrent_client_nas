import qbittorrentapi
import time
import re
import os
from .config_data import env_keys, config

class GetInfoFromMagnet(Exception):
    """искллючение для получения данных"""
    pass

QBITTORRENT_HOST = config.addr
QBITTORRENT_PORT = config.port
QBITTORRENT_USERNAME = env_keys.USER
QBITTORRENT_PASSWORD = env_keys.PASSWORD


client = qbittorrentapi.Client(
    host=QBITTORRENT_HOST,
    port=QBITTORRENT_PORT,
    username=QBITTORRENT_USERNAME,
    password=QBITTORRENT_PASSWORD,
)

def add_torrent_from_magnet(magnet, rename = None, path = None, tags_add = None):
    if tags_add is None:
        tags_add = []
    try:
        client.torrents_add(urls=magnet, rename = rename, save_path = path, tags = tags_add)
    except qbittorrentapi.exceptions.APIError as e:
        return "Ошибка API при добавлении торрента"
    except Exception as e:
       return f"Ошибка при добавлении торрента: {e}"
    
    return "Торрент добавлен!"

def get_info_from_magnet_by_qb(magnet_link):
    match = re.search(r'btih:([a-fA-F0-9]+)', magnet_link)
    if not match:
        raise GetInfoFromMagnet("Не удалось найти хэш магнет ссылки")
    info_hash = match.group(1).lower()

    client.torrents_add(magnet_link)

    max_retries = 30 # Ждем до 60 секунд (30 * 2) 
    files_info = []

    try:
        for _ in range(max_retries):
            files = client.torrents_files(info_hash) #получаем файлы
            if files:
                metadata_received = True
                break
            time.sleep(2)
        
        if not metadata_received:
            raise GetInfoFromMagnet("Не удалось получить информацию о файлах")
        
        main_info_list = client.torrents_info(torrent_hashes=info_hash) # Общая информация о торренте (имя, сиды, пиры)
        
        if not main_info_list:
            raise GetInfoFromMagnet("Не удалось получить информацию о торренте")
        
        main_info = main_info_list[0]

        # Список трекеров (announce)
        trackers = client.torrents_trackers(info_hash)
        announce_list = [t['url'] for t in trackers if t['url'].startswith('http')]

        # Список файлов с нужной структурой
        files_list = []
        for f in files:
            files_list.append({
                "name": os.path.basename(f['name']), # Только имя файла
                "path": f['name'],                  # Полный путь внутри торрента
                "size": f['size']                   # Размер в байтах
            })

        # Итоговый результат
        result = {
            "data": {
                "announce": announce_list,
                "files": files_list,
                "infoHash": info_hash,
                "magnetURI": magnet_link,
                "name": main_info.get('name'),
                "peers": main_info.get('num_incomplete', 0),
                "seeds": main_info.get('num_seeds', 0)
            }
        }

        return result

    finally:
        # Очистка: удаляем торрент в любом случае (даже если упали по ошибке),
        client.torrents_delete(delete_files=True, torrent_hashes=info_hash)

