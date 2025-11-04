import sys
import os
import pytest
from unittest.mock import MagicMock
from src.message_tools import Message_data

#для чтения из папки /src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# 1. Фикстуры Message_data
# -----------------------------------------------------------------------------
@pytest.fixture
def message_movie_batman():
    """Фикстура для MessageData с заполненными всеми основными полями."""
    return Message_data(
        magnet="magnet:?xt=urn:btih:MMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
        title="Бэтмен: Начало",
        alternative_title="Batman Begins",
        year=2005,
        season=None
    )

@pytest.fixture
def message_serials_gto():
    """Фикстура для MessageData, представляющая фильм без информации о сезоне."""
    return Message_data(
        magnet="magnet:?xt=urn:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        title="Крутой учитель Онизука",
        alternative_title="GTO: Great Teacher Onizuka",
        year=1999,
        season="1"
    )
