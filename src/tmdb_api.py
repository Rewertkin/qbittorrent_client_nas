'''Модуль для работы с TMDB API'''
import requests
from .config_data import env_keys
from .message_tools import Message_data


TMDB_API = 'Bearer ' + str(env_keys.TMDB_API)

def search_movies_tmdb(message_data: Message_data):
    '''Получить данные через API TMDB'''
    if message_data.year is None or message_data.title is None:
        return 0
    if message_data.alternative_title is None:
        title = message_data.alternative_title
    else:
        title = message_data.title
  
    year = message_data.year

    if message_data.season is None:
        url = f"https://api.themoviedb.org/3/search/movie?query={title}&year={year}"
    else:
        #если заполнено, значит ищем сериал
        url = f"https://api.themoviedb.org/3/search/tv?query={title}&year={year}"

    headers = {
        "accept": "application/json",
        "Authorization": f"{TMDB_API}"
        }
 
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    if response.json()['total_results'] == 0: #если ничего не найдено, вызываем ошибку
        raise Exception

    return response.json()['results']

def get_id_tmdb(message_data: Message_data):
    '''Получить id tmdb'''
    data_tmdb = search_movies_tmdb(message_data)

    if len(data_tmdb) == 1:
        return data_tmdb[0]['id']
    
    #попробуем жадно найти по названию
    data_tmdb_title = [result for result in data_tmdb if result['title'] == message_data.alternative_title]

    if len(data_tmdb_title) == 1:
        return data_tmdb_title[0]['id']

    #попробуем жадно найти по оригинальному названию
    data_tmdb_original_title = [result for result in data_tmdb if result['original_title'] == message_data.alternative_title]

    if len(data_tmdb_original_title) == 1:
        return data_tmdb_original_title[0]['id']
    
    return 0