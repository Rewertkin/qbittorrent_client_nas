'''Модуль для работы с Кинопоиск API'''
import requests
from config_data import env_keys
from message_tools import Message_data


def search_movies_kinopoisk(message_data: Message_data):
    '''Получить данные через API кинопоиска'''
    if message_data.year is None or message_data.title is None:
        return 0

    KINOPOISK_API= env_keys.KINOPOISK_API
    name = message_data.title

    url = f"https://api.kinopoisk.dev/v1.4/movie/search?page=1&limit=10&query={name}"

    headers = {"accept": "application/json",
            "X-API-KEY": KINOPOISK_API }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    if response.json()['total'] == 0: #если ничего не найдено, вызываем ошибку
        raise Exception

    return response.json()['docs']


def get_id_kinopoisk(message_data: Message_data):
    '''Получить id кинопоиска'''
    #определяем, является ли фильм сериалом
    is_series = False 
    if message_data.season is not None:
        is_series = True

    try:
        data_kinopoisk = search_movies_kinopoisk(message_data)
    except:
        return 0

    #уменьшим шорт лист по маркеру года и маркеру многосерийности
    data_film = [docs for docs in data_kinopoisk if docs['year'] == int(message_data.year)
                 and docs['isSeries'] == is_series]

    if len(data_film) == 1:
        return data_film[0]['id']

    #попробуем найти фильм по альтернативному названию
    data_film_alternative = [docs for docs in data_film if docs['alternativeName'] == message_data.alternative_title]

    if len(data_film_alternative) == 1:
        return data_film_alternative[0]['id']

    #если дошли до сюда, попробуем жадно по локализованному названию найти
    data_film_localname = [docs for docs in data_film if docs['name'] == message_data.title]

    if len(data_film_localname) == 1:
        return data_film_localname[0]['id']
    
    return 0