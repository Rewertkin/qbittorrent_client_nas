import pytest

from src.config_data import Config, Env_keys, parse_allowed_users, get_allowed_users


@pytest.mark.parametrize("value, expected", [
    ("111,222", [111, 222]),
    ("111, 222", [111, 222]),
    ("111 222", [111, 222]),
    ("[111, 222]", [111, 222]),
    ("111", [111]),
    ("", []),
    (None, None),
])
def test_parse_allowed_users(value, expected):
    assert parse_allowed_users(value) == expected


def test_parse_allowed_users_invalid():
    with pytest.raises(ValueError):
        parse_allowed_users("111,abc")


def env(allowed):
    return Env_keys(None, None, None, None, None, allowed)


def test_allowed_users_from_env_has_priority():
    assert get_allowed_users(env([1, 2]), Config({"allowed_users": [3]})) == [1, 2]


def test_allowed_users_fallback_to_config():
    assert get_allowed_users(env(None), Config({"allowed_users": [3]})) == [3]


def test_allowed_users_not_set_anywhere():
    assert get_allowed_users(env(None), Config({})) == []
