from dataclasses import dataclass
import logging
import os
import requests
from typing import Optional
from .message_tools import correct_forbidden_characters, Message_data
from .config_data import config
from .qbittorrent_client import get_info_from_magnet_by_qb

logger = logging.getLogger(__name__)


class MetadataError(Exception):
    """Не удалось получить метаданные торрента"""
    pass


def get_metadata_api(magnet = None):
    """получить метаданные по магнет ссылке"""
    try:
        source = config.metadata_service
    except AttributeError: #по умолчанию, если нет конфига, внешний вызываем
        source = 'external'
    
    if source == 'qb':
        return get_info_from_magnet_by_qb(magnet)
    elif source == 'external':
        if magnet is None:
            return
        url = 'https://torrentmeta.fly.dev/'
        data_url = {
        'query' : magnet
        }
        response = requests.post(url, data=data_url, timeout=10)
        response.raise_for_status()
        return response.json()
    else:
        return

def is_file_in_directory(data):
    """Проверяет, указана ли папка на верхнем уровне в торренте"""
    #если торрент сразу грузится в папку, то не создаем папку для него
    #если хоть один файл кладется вне папки, то считаем, что он грузится без папки
    files = data['data'].get('files', [])
    if not files:
        return False
    for file in files:
        if '/' not in file['path']:
            return False
    return True

def is_movies_files(torrent_data):
    """
    Проверяет, содержит ли торрент медиафайлы (видео) 
    на основе расширений файлов.
    """
    media_extensions = {
        # Видео
        ".avi", ".mkv", ".mp4", ".mov", ".wmv", ".flv", ".webm", ".mpg", ".mpeg", 
        ".ts", ".m2ts",
    }

    try:
        files = torrent_data.get("data", {}).get("files", [])
        
        if not files: # Если списка файлов нет или он пуст
            return False

        for file_info in files:
            file_name = file_info.get("name")
            if not file_name:
                continue # Пропускаем, если у файла нет имени
            
            _ , extension = os.path.splitext(file_name) 
            extension = extension.lower()

            # Проверяем, есть ли расширение в нашем списке
            if extension in media_extensions:
                return True # Нашли медиафайл, дальше можно не искать

    except (AttributeError, TypeError, KeyError):
        logger.warning("Некорректная структура данных торрента")
        return False

    return False

@dataclass(frozen=True)
class Metadata:
    name: Optional[str] = None
    inDir: Optional[bool] = None
    isMovies: Optional[bool] = False
    files: Optional[list] = None

    @classmethod
    def prepare_from_magnet(cls, magnet) -> 'Metadata':
        data = get_metadata_api(magnet)
        if not data or 'data' not in data:
            raise MetadataError("Не удалось получить метаданные торрента")
        return cls(
            name=data['data'].get('name'),
            inDir=is_file_in_directory(data),
            isMovies=is_movies_files(data),
            files=data['data'].get('files', []),
        )

def get_name_torrent(message_data: Message_data, metadata: Metadata, id_suffix = None):
    """формирование наименование торрента или папки для скачивания"""
    name_torrent = metadata.name or 'Без названия'

    if message_data.title and message_data.year:
        name_torrent = f'{message_data.title} ({message_data.year})'

    if id_suffix is not None:
        name_torrent = name_torrent + ' ' + id_suffix
    return correct_forbidden_characters(name_torrent)
