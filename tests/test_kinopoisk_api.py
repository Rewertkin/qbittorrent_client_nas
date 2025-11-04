import pytest
from src.kinopoisk_api import get_id_kinopoisk

def test_get_id_kinopoisk_movie_batman(message_movie_batman):
    test_kp_id = 47237 
    assert get_id_kinopoisk(message_movie_batman) == test_kp_id

def test_get_id_kinopoisk_serials_gto(message_serials_gto):
    test_kp_id = 408596
    assert get_id_kinopoisk(message_serials_gto) == test_kp_id
