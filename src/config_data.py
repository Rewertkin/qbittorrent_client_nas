import json
import logging
import os
import re
from typing import List, Optional
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


def parse_allowed_users(value: Optional[str]) -> Optional[List[int]]:
    """Разобрать ALLOWED_USERS из .env в список id.
    Допустимые форматы: "111,222", "111 222", "[111, 222]".
    None, если переменная не задана."""
    if value is None:
        return None
    parts = [p for p in re.split(r'[\s,;\[\]]+', value) if p]
    try:
        return [int(p) for p in parts]
    except ValueError as e:
        raise ValueError(f"ALLOWED_USERS должен содержать только числовые id через запятую, получено: {value!r}") from e


class Env_keys:
    """Класс для работы с API ключами"""
    def __init__(self, KINOPOISK_API, TG_BOT_TOKEN, QB_USER, QB_PASSWORD, TMDB_API, ALLOWED_USERS=None):
        self.KINOPOISK_API = KINOPOISK_API
        self.TG_BOT_TOKEN = TG_BOT_TOKEN
        self.QB_USER = QB_USER
        self.QB_PASSWORD = QB_PASSWORD
        self.TMDB_API = TMDB_API
        self.ALLOWED_USERS = ALLOWED_USERS


def load_env() -> Env_keys:
    load_dotenv(find_dotenv())
    # Раньше использовались USER/PASSWORD, но USER - системная переменная
    # (имя пользователя ОС), она перекрывала значение из .env. Поэтому QB_USER/QB_PASSWORD.
    qb_user = os.getenv('QB_USER')
    qb_password = os.getenv('QB_PASSWORD')
    return Env_keys(os.getenv('KINOPOISK_API'),
                    os.getenv('TG_BOT_TOKEN'),
                    qb_user,
                    qb_password,
                    os.getenv('TMDB_API'),
                    parse_allowed_users(os.getenv('ALLOWED_USERS')))


def get_allowed_users(env: Env_keys, cfg: Config) -> List[int]:
    """Список пользователей с доступом: из ALLOWED_USERS в .env,
    для совместимости - из allowed_users в config.json"""
    if env.ALLOWED_USERS is not None:
        return env.ALLOWED_USERS
    try:
        users = list(cfg.allowed_users)
    except AttributeError:
        logger.warning("Не задан ALLOWED_USERS в .env - доступ к боту запрещен всем")
        return []
    logger.warning("allowed_users берется из config.json - перенесите его в ALLOWED_USERS в .env")
    return users


config = load_config()
env_keys = load_env()
