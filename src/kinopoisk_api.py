'''Модуль для работы с Кинопоиск API'''
import logging
import requests
from .config_data import env_keys
from .message_tools import Message_data, has_cyrillic, normalize_title

logger = logging.getLogger(__name__)


def search_movies_kinopoisk(message_data: Message_data, title=None):
    '''Получить данные через API кинопоиска. Возвращает список найденных фильмов (может быть пустым).'''
    title = title or message_data.title
    if message_data.year is None or not title:
        return []

    url = "https://api.kinopoisk.dev/v1.4/movie/search"
    params = {"page": 1, "limit": 10, "query": title}
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


def pick_kinopoisk_id(data_kinopoisk, message_data: Message_data):
    """Выбрать id из результатов поиска Кинопоиска"""
    is_series = message_data.season is not None

    # уменьшим шорт лист по маркеру года и маркеру многосерийности
    data_film = [docs for docs in data_kinopoisk
                 if docs.get('year') == int(message_data.year)
                 and docs.get('isSeries') == is_series]

    if len(data_film) == 1:
        return data_film[0]['id']

    titles = {normalize_title(t) for t in message_data.titles + [message_data.title, message_data.alternative_title] if t}

    # попробуем найти по альтернативному (оригинальному) названию, потом по локализованному
    for key in ('alternativeName', 'enName', 'name'):
        matched = [docs for docs in data_film if normalize_title(docs.get(key)) in titles]
        if len(matched) == 1:
            return matched[0]['id']

    return 0


def get_id_kinopoisk(message_data: Message_data):
    '''Получить id кинопоиска, перебирая названия: сначала русские, потом остальные'''
    if message_data.year is None:
        return 0

    candidates = [message_data.title] + [t for t in message_data.titles if has_cyrillic(t)] \
        + [message_data.alternative_title] + message_data.titles
    queries = []
    for t in candidates:
        if t and t not in queries:
            queries.append(t)

    for title in queries:
        try:
            data_kinopoisk = search_movies_kinopoisk(message_data, title)
        except requests.exceptions.RequestException:
            logger.exception("Ошибка запроса к Кинопоиску")
            return 0

        if not data_kinopoisk:
            continue

        id_kp = pick_kinopoisk_id(data_kinopoisk, message_data)
        if id_kp:
            return id_kp

    return 0
