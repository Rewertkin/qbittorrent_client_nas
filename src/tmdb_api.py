'''Модуль для работы с TMDB API'''
import logging
import requests
from .config_data import env_keys
from .message_tools import Message_data

logger = logging.getLogger(__name__)

TMDB_API = 'Bearer ' + str(env_keys.TMDB_API)


class TmdbNotFound(Exception):
    """Фильм или сериал не найден в TMDB"""
    pass


def search_movies_tmdb(message_data: Message_data):
    '''Получить данные через API TMDB'''
    if message_data.year is None or message_data.title is None:
        raise TmdbNotFound("В сообщении нет названия или года")

    if message_data.alternative_title is not None:
        title = message_data.alternative_title
    else:
        title = message_data.title

    if message_data.season is None:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"query": title, "year": message_data.year}
    else:
        # если заполнен сезон, значит ищем сериал
        url = "https://api.themoviedb.org/3/search/tv"
        # year у сериалов ищет и по датам выхода эпизодов, что подходит для 2+ сезонов
        params = {"query": title, "year": message_data.year}

    headers = {
        "accept": "application/json",
        "Authorization": TMDB_API,
    }

    logger.info("TMDB запрос: %s %s", url, params)

    # requests сам экранирует параметры (символы &, #, ? в названии)
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get('total_results', 0) == 0:
        raise TmdbNotFound(f"Ничего не найдено: {title} ({message_data.year})")

    return data['results']


def get_id_tmdb(message_data: Message_data):
    '''Получить id tmdb'''
    try:
        data_tmdb = search_movies_tmdb(message_data)
    except TmdbNotFound as e:
        logger.info(str(e))
        return 0
    except requests.exceptions.RequestException:
        logger.exception("Ошибка запроса к TMDB")
        return 0

    if len(data_tmdb) == 1:
        return data_tmdb[0]['id']

    # у фильмов поля title/original_title, у сериалов name/original_name
    if message_data.season is None:
        title_key, original_key = 'title', 'original_title'
    else:
        title_key, original_key = 'name', 'original_name'

    # попробуем найти по локализованному названию
    data_tmdb_title = [r for r in data_tmdb if r.get(title_key) == message_data.alternative_title]
    if len(data_tmdb_title) == 1:
        return data_tmdb_title[0]['id']

    # попробуем найти по оригинальному названию
    data_tmdb_original_title = [r for r in data_tmdb if r.get(original_key) == message_data.alternative_title]
    if len(data_tmdb_original_title) == 1:
        return data_tmdb_original_title[0]['id']

    return 0
