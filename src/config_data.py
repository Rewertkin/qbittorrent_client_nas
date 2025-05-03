import json
import os
from dotenv import load_dotenv, find_dotenv

class Config:
    """Класс для работы с конфигурацией"""
    def __init__(self, data: dict):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, Config(value))
            else:
                setattr(self,key, value)
    def __getattr__(self, name: str):
        raise AttributeError(f"'{type(self).__name__}' объект не имеет атрибут '{name}'")

def load_config() -> Config:
    """Считываем данные конфига"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    return Config(config_data)

class Env_keys:
    """класс для работы с апи ключами"""
    def __init__(self, KINOPOISK_API, TG_BOT_TOKEN, USER, PASSWORD):
        # Считываем данные токенов
        self.KINOPOISK_API = KINOPOISK_API
        self.TG_BOT_TOKEN = TG_BOT_TOKEN
        self.USER = USER
        self.PASSWORD = PASSWORD

def load_env() -> Env_keys:
    load_dotenv(find_dotenv())
    return Env_keys(os.getenv('KINOPOISK_API'),
                    os.getenv('TG_BOT_TOKEN'),
                    os.getenv('USER'),
                    os.getenv('PASSWORD')
                    )

config = load_config()
env_keys = load_env()
