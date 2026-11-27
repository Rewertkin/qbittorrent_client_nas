from typing import List, Optional
import re

def correct_forbidden_characters(folder_name):
    """проверяем и убираем в наименование запрещенные символы"""
    forbidden_characters_regex = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized_name = re.sub(forbidden_characters_regex, '_', folder_name)
    sanitized_name = sanitized_name.lstrip(".").rstrip(".")
    return sanitized_name

# Сегменты вида "Сезон: 1", "Серии: 1-7 из 7" - это не названия
NOT_TITLE_SEGMENT_REGEX = re.compile(r'^(?:сезон|сезоны|серии|серия|season|seasons|episodes?)\b', re.IGNORECASE)


def has_cyrillic(text: str) -> bool:
    return bool(re.search(r'[а-яА-ЯёЁ]', text))


def has_latin(text: str) -> bool:
    return bool(re.search(r'[a-zA-Z]', text))


def split_titles(text_before_year: str) -> List[str]:
    """Разбить строку до года на список названий.
    Пример: 'Дорога, дорога домой / На заднем сиденье / The Way Way Back (Нат Факсон / Nat Faxon)'
    -> ['Дорога, дорога домой', 'На заднем сиденье', 'The Way Way Back']"""
    # всё после первой '[' - это уже теги раздачи ([TV], [43 из 43] и т.п.)
    text = text_before_year.split('[', 1)[0].strip()
    # последняя группа в скобках - режиссеры, в ней тоже бывает '/', поэтому убираем до разбиения
    text = re.sub(r'\s*\([^()]*\)\s*$', '', text).strip()

    titles = []
    for segment in text.split('/'):
        segment = segment.strip()
        if not segment or NOT_TITLE_SEGMENT_REGEX.match(segment):
            continue
        titles.append(segment)
    return titles


def choose_alternative_title(titles: List[str]) -> Optional[str]:
    """Альтернативное название: последнее латинское (обычно английское/оригинальное),
    если латинских нет - второе по счету."""
    if len(titles) < 2:
        return None
    latin_titles = [t for t in titles[1:] if has_latin(t) and not has_cyrillic(t)]
    if latin_titles:
        return latin_titles[-1]
    return titles[1]


class Message_data:
    """класс для работы данными из сообщения"""
    magnet: Optional[str] = None
    title: Optional[str] = None
    alternative_title: Optional[str] = None
    year: Optional[int] = None
    season: Optional[str] = None

    def __init__(self, magnet: Optional[str] = None, title: Optional[str] = None,
                 alternative_title: Optional[str] = None, year: Optional[int] = None,
                 season: Optional[str] = None, titles: Optional[List[str]] = None):
        self.magnet = magnet
        self.title = title
        self.alternative_title = alternative_title
        self.year = year
        self.season = season
        # все найденные названия в порядке из сообщения (русские, английские, оригинальные)
        self.titles = list(titles) if titles else [t for t in (title, alternative_title) if t]

    def __repr__(self): # Для удобного вывода объекта
        return (f"Message_data(title='{self.title}', alt_title='{self.alternative_title}', "
                f"year={self.year}, season='{self.season}', titles={self.titles}, magnet_present={bool(self.magnet)})")


    @classmethod
    def prepare_message_data(cls, message_text: str) -> 'Message_data': # Явно указываем тип возврата
        """ получение данных из сообщения и создание нового экземпляра Message_data"""
        # Инициализируем переменные для хранения найденных значений
        parsed_magnet: Optional[str] = None
        parsed_title: Optional[str] = None
        parsed_alternative_title: Optional[str] = None
        parsed_year: Optional[int] = None
        parsed_season: Optional[str] = None
        parsed_titles: List[str] = []
        title_string: Optional[str] = None # Инициализируем title_string

        # найдем магнет ссылку
        magnet_start = message_text.find('magnet')
        if magnet_start != -1:
            magnet_end_newline = message_text.find('\n', magnet_start)
            if magnet_end_newline == -1:
                magnet_finish = len(message_text)
            else:
                magnet_finish = magnet_end_newline
            parsed_magnet = message_text[magnet_start:magnet_finish].strip()

        # найдем строку с названием фильма/торрента:
        first_line_end = message_text.find(":\n")
        if first_line_end == -1:
            # Если нет заголовка, возвращаем экземпляр с теми данными, что уже могли найти (например, magnet)
            return cls(
                magnet=parsed_magnet,
                title=parsed_title,
                alternative_title=parsed_alternative_title,
                year=parsed_year,
                season=parsed_season
            )

        title_start = first_line_end + 2
        title_finish_newline = message_text.find("\n", title_start)
        if title_finish_newline == -1:
            if magnet_start != -1 and title_start < magnet_start : # Убедимся, что magnet_start после title_start
                title_finish = magnet_start
            else:
                title_finish = len(message_text)
        else:
            title_finish = title_finish_newline

        title_string = message_text[title_start:title_finish].strip()

        # Попробуем сначала найти год, так как он обычно является хорошим якорем
        year_match = re.search(r'\[(\d{4})', title_string)
        if year_match:
            try:
                parsed_year = int(year_match.group(1))
            except ValueError:
                parsed_year = None

            parsed_titles = split_titles(title_string[:year_match.start()])
            if parsed_titles:
                parsed_title = parsed_titles[0]
                parsed_alternative_title = choose_alternative_title(parsed_titles)
        else:
            # Если год не найден стандартным способом, просто берем всю строку как название
            parsed_title = title_string


        # --- Поиск информации о сезоне ПОСЛЕ основного парсинга ---
        if parsed_year and title_string: # Искать сезон имеет смысл только если нашли год и есть строка заголовка
            season_match_sXX = re.search(r'\bS(\d+)\b', title_string, re.IGNORECASE)
            if season_match_sXX:
                parsed_season = season_match_sXX.group(1)
            # Добавим elif, чтобы не перезаписывать уже найденный сезон
            elif not parsed_season:
                season_match_word = re.search(
                    r'(?:Сезон(?:ы)?|Season(?:s)?)\s*[:]?\s*([\d,\s-]+(?:\s*-\s*\d+)?)\b',
                    title_string,
                    re.IGNORECASE
                )
                if season_match_word:
                    season_info = season_match_word.group(1).strip().rstrip(',.-')
                    # Возьмем только первую цифру/диапазон, если их несколько через запятую
                    parsed_season = season_info.split(',')[0].strip()


            # Добавим elif
            elif not parsed_season:
                season_match_num_season = re.search(
                    r'\b([\d,\s-]+(?:\s*-\s*\d+)?)\s+(?:сезон|сезона|сезоны)\b',
                    title_string,
                    re.IGNORECASE
                )
                if season_match_num_season:
                    season_info = season_match_num_season.group(1).strip().rstrip(',.-')
                    # Возьмем только первую цифру/диапазон
                    parsed_season = season_info.split(',')[0].strip()

            if not parsed_season:
                # Ищем паттерн [XX из XX] или [XX из XX, ...]
                # \s*(\d+)\s* - захватываем первое число (серии), разрешая пробелы вокруг
                # \s+из\s+ - " из " с пробелами
                # \1 - обратная ссылка на первое захваченное число (должно быть то же самое)
                # \s*(?:\]|,|$) - после второго числа может быть пробел и закрывающая скобка,
                #                  или запятая (если дальше идет еще что-то в этих скобках),
                #                  или конец строки (менее вероятно, но для полноты)
                # Мы используем re.IGNORECASE на всякий случай, хотя "из" обычно в нижнем регистре
                episodes_match = re.search(r"\[\s*(\d+)\s+из\s+\1\s*(?:\]|,|$)", title_string, re.IGNORECASE)
                if episodes_match:
                    # Если такой паттерн найден и сезон до сих пор не определен,
                    # считаем, что это первый сезон.
                    parsed_season = "1"

        # Возвращаем новый экземпляр класса с извлеченными данными
        return cls(
            magnet=parsed_magnet,
            title=parsed_title,
            alternative_title=parsed_alternative_title,
            year=parsed_year,
            season=parsed_season,
            titles=parsed_titles
        )