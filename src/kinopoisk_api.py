'''Модуль для работы с Кинопоиск API'''
import logging
import requests
from .config_data import env_keys
from .message_tools import Message_data

logger = logging.getLogger(__name__)


def search_movies_kinopoisk(message_data: Message_data):
    '''Получить данные через API кинопоиска. Возвращает список найденных фильмов (может быть пустым).'''
    if message_data.year is None or message_data.title is None:
        return []

    url = "https://api.kinopoisk.dev/v1.4/movie/search"
    params = {"page": 1, "limit": 10, "query": message_data.title}
    headers = {"accept": "application/json",
               "X-API-KEY": env_keys.KINOPOISK_API}

    logger.info("Кинопоиск запрос: %s %s", url, params)

    # requests сам экранирует параметры (символы &, #, ? в названии)
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get('total', 0) == 0:
        return []

    return data.get('docs', [])


def get_id_kinopoisk(message_data: Message_data):
    '''Получить id кинопоиска'''
    # определяем, является ли фильм сериалом
    is_series = message_data.season is not None

    try:
        data_kinopoisk = search_movies_kinopoisk(message_data)
    except requests.exceptions.RequestException:
        logger.exception("Ошибка запроса к Кинопоиску")
        return 0

    if not data_kinopoisk:
        return 0

    # уменьшим шорт лист по маркеру года и маркеру многосерийности
    data_film = [docs for docs in data_kinopoisk
                 if docs.get('year') == int(message_data.year)
                 and docs.get('isSeries') == is_series]

    if len(data_film) == 1:
        return data_film[0]['id']

    # попробуем найти фильм по альтернативному названию
    data_film_alternative = [docs for docs in data_film
                             if docs.get('alternativeName') == message_data.alternative_title]
    if len(data_film_alternative) == 1:
        return data_film_alternative[0]['id']

    # если дошли до сюда, попробуем жадно по локализованному названию найти
    data_film_localname = [docs for docs in data_film if docs.get('name') == message_data.title]
    if len(data_film_localname) == 1:
        return data_film_localname[0]['id']

    return 0
