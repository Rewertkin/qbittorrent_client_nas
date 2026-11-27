import json
import logging
import os
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Класс для работы с конфигурацией"""
    def __init__(self, data: dict):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, Config(value))
            else:
                setattr(self, key, value)

    def __getattr__(self, name: str):
        raise AttributeError(f"'{type(self).__name__}' объект не имеет атрибут '{name}'")


def load_config() -> Config:
    """Считываем данные конфига"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    return Config(config_data)


class Env_keys:
    """Класс для работы с API ключами"""
    def __init__(self, KINOPOISK_API, TG_BOT_TOKEN, QB_USER, QB_PASSWORD, TMDB_API):
        self.KINOPOISK_API = KINOPOISK_API
        self.TG_BOT_TOKEN = TG_BOT_TOKEN
        self.QB_USER = QB_USER
        self.QB_PASSWORD = QB_PASSWORD
        self.TMDB_API = TMDB_API


def load_env() -> Env_keys:
    load_dotenv(find_dotenv())
    # Раньше использовались USER/PASSWORD, но USER - системная переменная
    # (имя пользователя ОС), она перекрывала значение из .env. Поэтому QB_USER/QB_PASSWORD.
    qb_user = os.getenv('QB_USER')
    qb_password = os.getenv('QB_PASSWORD')
    if qb_user is None or qb_password is None:
        logger.warning("Не заданы QB_USER/QB_PASSWORD в .env - подключение к qBittorrent может не работать")
    return Env_keys(os.getenv('KINOPOISK_API'),
                    os.getenv('TG_BOT_TOKEN'),
                    qb_user,
                    qb_password,
                    os.getenv('TMDB_API'))


config = load_config()
env_keys = load_env()
