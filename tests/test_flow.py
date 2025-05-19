from src.message_tools import Message_data
import src.kinopoisk_api as kp
from src.message_tools import Message_data
from src.metadata_tools import Metadata, get_name_torrent
from src.config_data import env_keys, config

def run(text):
    message_data = Message_data.prepare_message_data(text) #получаем данные из сообщения
    
    print("Message_data.magnet: " + message_data.magnet)
    print("Message_data.title: " + message_data.title)
    print("Message_data.alternative_title: " + message_data.alternative_title)
    print("Message_data.year: " + str(message_data.year))
    
    print("Message_data.season: ")
    print(message_data.season)

    metadata = Metadata.prepare_from_magnet(message_data.magnet)#получаем метаданные торрента

    print("metadata.name: " + metadata.name)
    print("metadata.inDir: " + str(metadata.inDir))
    print("metadata.isMovies: " + str(metadata.isMovies))
    #print("metadata.files: ")
    #print(metadata.files)

    kp_id = 0
    if metadata.isMovies:
        kp_id = kp.get_id_kinopoisk(message_data)

    print("kp_id: " + str(kp_id))
    print("metadata.isMovies: " + str(metadata.isMovies))    

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
    print("tags_add :")
    print(tags_add)
    print("title_folder: " + title_folder)

    #определеяем в какую папку скачиваем
    if kp_id > 0:
        if message_data.season:
            path_download = config.serials_path
        else:
            path_download = config.movies_path
    else:
        path_download = config.default_path
    
    print("path_download: " + path_download)

    if title_folder is not None:
        path_download = path_download + '/' + title_folder

    #добавляем наименование для торрента в клиенте
    name_torrent = get_name_torrent(message_data, metadata, kp_id)

    print("name_torrent: " + name_torrent)

