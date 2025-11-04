# tests/test_message_tools.py
import pytest
from src.message_tools import correct_forbidden_characters, Message_data

# 1. Тесты для correct_forbidden_characters
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "input_name, expected_name",
    [
        ("Valid Name 123", "Valid Name 123"),
        ("Name with <forbidden>", "Name with _forbidden_"),
        ("Path/to/file", "Path_to_file"),
        ("Stars*and*question?", "Stars_and_question_"),
        ("Control\x00char", "Control_char"),
        ("Test./Name", "Test._Name"),
        ("Test.\\Name", "Test._Name"),
    ]
)
def test_correct_forbidden_characters(input_name, expected_name):
    assert correct_forbidden_characters(input_name) == expected_name

# 2. Тесты для Message_data.prepare_message_data
# -----------------------------------------------------------------------------

def assert_message_data_equals(result_data: Message_data, expected_data: dict):
    assert isinstance(result_data, Message_data)
    assert result_data.magnet == expected_data.get("magnet")
    assert result_data.title == expected_data.get("title")
    assert result_data.alternative_title == expected_data.get("alternative_title")
    assert result_data.year == expected_data.get("year")
    assert result_data.season == expected_data.get("season")

MESSAGE_TEXT_BATMAN = """[2] #4627564 [rutracker], 2023-11-10 (https://hashurl.ru/...):
Бэтмен: Начало / Batman Begins (Кристофер Нолан / Christopher Nolan) [2005, боевик, триллер, драма, криминал, BDRip 720p] Dub + MVO (Киномания) + DVO (Tycoon) + 2x AVO (Гаврилов, Королев) + Original Eng + Sub (Rus, Eng)

✅ (проверено) | 8.4 GB
...
magnet:?xt=urn:btih:MMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
...
"""
EXPECTED_DATA_BATMAN = {
    "magnet": "magnet:?xt=urn:btih:MMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",
    "title": "Бэтмен: Начало", "alternative_title": "Batman Begins", "year": 2005, "season": None
}

MESSAGE_TAKING_CHANCE = """[3] #1856381 [rutracker], 2016-12-08 (...):
Добровольцы (Забирая Чэнса) / Taking Chance (Росс Кац \\ Ross Katz) [2009, США, Военная драма, DVD5 (сжатый)]

✅ (проверено) | 4.35 GB
...
magnet:?xt=urn:btih:LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL
...
"""
EXPECTED_TAKING_CHANCE = {
    "magnet": "magnet:?xt=urn:btih:LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL",
    "title": "Добровольцы (Забирая Чэнса)", "alternative_title": "Taking Chance", "year": 2009, "season": None
}

MESSAGE_DUDE_IN_ME = """[1] #5901712 [rutracker], 2024-02-26 (...):
Тот, кто сидит внутри / Мужик внутри меня / Nae aneui geunom / The Dude In Me (Кан Хё-джин / Hyo-jin Kang) [2019, Южная Корея, Комедия, фэнтези, мелодрама, WEB-DL 1080p] DVO (GREEN TEA) + Sub Rus, Eng, Kor + Original Kor
...
magnet:?xt=urn:btih:CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
...
"""
EXPECTED_DUDE_IN_ME = {
    "magnet": "magnet:?xt=urn:btih:CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
    "title": "Тот, кто сидит внутри", "alternative_title": "Мужик внутри меня", "year": 2019, "season": None
}

MESSAGE_GTO = """[4] #5257365 [rutracker], 2025-03-29 (...):
Крутой учитель Онизука / GTO: Great Teacher Onizuka (Абэ Нориюки) [TV] [43 из 43] [RUS(ext), UKR, JAP+Sub] [1999, школа, драма, комедия, DVDRip]
...
magnet:?xt=urn:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
...
"""
EXPECTED_GTO = {
    "magnet": "magnet:?xt=urn:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "title": "Крутой учитель Онизука", "alternative_title": "GTO: Great Teacher Onizuka", "year": 1999, "season": "1"
}

MESSAGE_GENERATION_KILL = """[2] #4981151 [rutracker], 2025-03-05 (...):
Поколение убийц / Generation Kill / Сезон: 1 / Серии: 1-7 из 7 (Сузанна Уайт, Саймон Селлан Джоунс / Susanna White, Simon Cellan Jones) [2008, США, Великобритания, драма, военный, BDRip-AVC] 2x MVO + VO + Original (Eng) + Sub (Rus, Eng)
...
magnet:?xt=urn:AAAAAAAAAAAAAAAAAAAAAAAAAAAA
...
"""
EXPECTED_GENERATION_KILL = {
    "magnet": "magnet:?xt=urn:AAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "title": "Поколение убийц", "alternative_title": "Generation Kill", "year": 2008, "season": "1"
}


@pytest.mark.parametrize(
    "message_text, expected_data",
    [
        (MESSAGE_TEXT_BATMAN, EXPECTED_DATA_BATMAN),
        (MESSAGE_TAKING_CHANCE, EXPECTED_TAKING_CHANCE),
        (MESSAGE_DUDE_IN_ME, EXPECTED_DUDE_IN_ME),
        (MESSAGE_GTO, EXPECTED_GTO),
        (MESSAGE_GENERATION_KILL, EXPECTED_GENERATION_KILL)   
    ]
)
def test_prepare_message_data(message_text, expected_data):
    # Для отладки можно временно раскомментировать, чтобы видеть, какой текст сейчас тестируется
    # if "Добровольцы" in message_text:
    #     print(f"\nTesting with: Добровольцы")
    # elif "Тот, кто сидит внутри" in message_text:
    #     print(f"\nTesting with: Тот, кто сидит внутри")
    # elif "Онизука" in message_text:
    #     print(f"\nTesting with: Онизука")
    # elif "Поколение убийц" in message_text:
    #     print(f"\nTesting with: Поколение убийц")

    result = Message_data.prepare_message_data(message_text)
    assert_message_data_equals(result, expected_data)