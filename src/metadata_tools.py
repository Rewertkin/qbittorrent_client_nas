from dataclasses import dataclass
import os
import requests
from typing import Optional

def get_metadata_api(magnet = None):
    """получить метаданные по магнет ссылке"""
    if magnet is None:
        return
    url = 'https://torrentmeta.fly.dev/'
    data_url = {
    'query' : magnet
    }
    response = requests.post(url, data=data_url, timeout=10)
    response.raise_for_status()
    return response.json()

def is_file_in_directory(data):
    """Проверяет, указана ли папка на верхнем уровне в торренте"""
    #если торрент сразу грузится в папку, то не создаем папку для него
    #если хоть один файл кладется вне папки, то считаем, что он грузится без папки
    for file in data['data']['files']:
        if '/' not in file['path']:
            return False
    return True

def is_movies_files(torrent_data):
    """
    Проверяет, содержит ли торрент медиафайлы (видео/аудио) 
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
        print("Предупреждение: Некорректная структура данных торрента.")
        return False

    return False

@dataclass(frozen=True)
class Metadata:
    name: Optional[str] = None
    inDir: Optional[bool] = None
    isMedia: Optional[bool] = False
    files: Optional[list] = None

    @classmethod
    def prepare_from_magnet(cls, magnet):
        data = get_metadata_api(magnet)
        cls.name = data["data"]['name']
        cls.inDir = is_file_in_directory(data)
        cls.isMovies = is_movies_files(data)
        cls.files = data['data']['files']
        
        return cls
