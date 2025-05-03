import qbittorrentapi
from config_data import env_keys, config

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