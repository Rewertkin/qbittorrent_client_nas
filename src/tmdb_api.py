'''Модуль для работы с TMDB API'''
import logging
import requests
from .config_data import env_keys
from .message_tools import Message_data, has_cyrillic, normalize_title

logger = logging.getLogger(__name__)

TMDB_API = 'Bearer ' + str(env_keys.TMDB_API)


class TmdbNotFound(Exception):
    """Фильм или сериал не найден в TMDB"""
    pass


def search_query_order(message_data: Message_data):
    """Порядок названий для поиска: сначала альтернативное (обычно английское),
    потом остальные латинские, потом русские. Без повторов."""
    ordered = [message_data.alternative_title]
    ordered += [t for t in message_data.titles if not has_cyrillic(t)]
    ordered += [t for t in message_data.titles if has_cyrillic(t)]
    ordered.append(message_data.title)
    result = []
    for t in ordered:
        if t and t not in result:
            result.append(t)
    return result


def search_movies_tmdb(message_data: Message_data, title: str):
    '''Получить данные через API TMDB по одному названию'''
    if message_data.year is None or not title:
        raise TmdbNotFound("В сообщении нет названия или года")

    if message_data.season is None:
        url = "https://api.themoviedb.org/3/search/movie"
    else:
        # если заполнен сезон, значит ищем сериал
        url = "https://api.themoviedb.org/3/search/tv"
    # year у сериалов ищет и по датам выхода эпизодов, что подходит для 2+ сезонов
    # language=ru-RU: поле title/name приходит на русском, original_title - на языке оригинала,
    # так русские названия из сообщения можно сравнить и с зарубежными, и с русскими фильмами
    params = {"query": title, "year": message_data.year, "language": "ru-RU"}

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


def pick_tmdb_id(results, message_data: Message_data):
    """Выбрать id из результатов поиска: единственный результат
    или единственное совпадение по любому из названий из сообщения"""
    if len(results) == 1:
        return results[0]['id']

    # у фильмов поля title/original_title, у сериалов name/original_name
    if message_data.season is None:
        keys = ('title', 'original_title')
    else:
        keys = ('name', 'original_name')

    titles = {normalize_title(t) for t in message_data.titles + [message_data.alternative_title] if t}
    for key in keys:
        matched = [r for r in results if normalize_title(r.get(key)) in titles]
        if len(matched) == 1:
            return matched[0]['id']
    return 0


def get_id_tmdb(message_data: Message_data):
    '''Получить id tmdb, перебирая все названия из сообщения'''
    for title in search_query_order(message_data):
        try:
            results = search_movies_tmdb(message_data, title)
        except TmdbNotFound as e:
            logger.info(str(e))
            continue
        except requests.exceptions.RequestException:
            logger.exception("Ошибка запроса к TMDB")
            return 0

        id_tmdb = pick_tmdb_id(results, message_data)
        if id_tmdb:
            return id_tmdb

    return 0
