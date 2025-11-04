from typing import Optional
import re

def correct_forbidden_characters(folder_name):
    """проверяем и убираем в наименование запрещенные символы"""
    forbidden_characters_regex = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized_name = re.sub(forbidden_characters_regex, '_', folder_name)
    sanitized_name = sanitized_name.lstrip(".").rstrip(".")
    return sanitized_name

class Message_data:
    """класс для работы данными из сообщения"""
    magnet: Optional[str] = None
    title: Optional[str] = None
    alternative_title: Optional[str] = None
    year: Optional[int] = None
    season: Optional[str] = None

    def __init__(self, magnet: Optional[str] = None, title: Optional[str] = None,
                 alternative_title: Optional[str] = None, year: Optional[int] = None,
                 season: Optional[str] = None):
        self.magnet = magnet
        self.title = title
        self.alternative_title = alternative_title
        self.year = year
        self.season = season

    def __repr__(self): # Для удобного вывода объекта
        return (f"Message_data(title='{self.title}', alt_title='{self.alternative_title}', "
                f"year={self.year}, season='{self.season}', magnet_present={bool(self.magnet)})")


    @classmethod
    def prepare_message_data(cls, message_text: str) -> 'Message_data': # Явно указываем тип возврата
        """ получение данных из сообщения и создание нового экземпляра Message_data"""
        # Инициализируем переменные для хранения найденных значений
        parsed_magnet: Optional[str] = None
        parsed_title: Optional[str] = None
        parsed_alternative_title: Optional[str] = None
        parsed_year: Optional[int] = None
        parsed_season: Optional[str] = None

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
            if parsed_magnet and magnet_start != -1 and title_start < magnet_start : # Убедимся, что magnet_start после title_start
                title_finish = magnet_start
            else:
                title_finish = len(message_text)
        else:
            title_finish = title_finish_newline

        title_string = message_text[title_start:title_finish].strip()

        # --- Поиск года ---
        year_match = re.search(r'\[(\d{4})', title_string)
        if year_match:
            try:
                parsed_year = int(year_match.group(1))
            except ValueError:
                parsed_year = None

        # --- Поиск информации о сезоне ---
        if title_string: # Искать сезон имеет смысл только если есть строка заголовка
            season_match_sXX = re.search(r'\bS(\d+)\b', title_string, re.IGNORECASE)
            if season_match_sXX:
                parsed_season = season_match_sXX.group(1)
            elif not parsed_season:
                season_match_word = re.search(
                    r'(?:Сезон(?:ы)?|Season(?:s)?)\s*[:]?\s*([\d,\s-]+(?:\s*-\s*\d+)?)\b',
                    title_string,
                    re.IGNORECASE
                )
                if season_match_word:
                    season_info = season_match_word.group(1).strip().rstrip(',.-')
                    parsed_season = season_info.split(',')[0].strip()
            elif not parsed_season:
                season_match_num_season = re.search(
                    r'\b([\d,\s-]+(?:\s*-\s*\d+)?)\s+(?:сезон|сезона|сезоны)\b',
                    title_string,
                    re.IGNORECASE
                )
                if season_match_num_season:
                    season_info = season_match_num_season.group(1).strip().rstrip(',.-')
                    parsed_season = season_info.split(',')[0].strip()
            if not parsed_season:
                # Ищем паттерн [XX из XX] или [XX из XX, ...]
                episodes_match = re.search(r"\[\s*(\d+)\s+из\s+\1\s*(?:\]|,|$)", title_string, re.IGNORECASE)
                if episodes_match:
                    # Если такой паттерн найден и сезон до сих пор не определен,
                    # считаем, что это первый сезон.
                    parsed_season = "1"

        # --- Извлечение основного и альтернативного названий ---
        # Определяем сегмент, который содержит только название и альтернативное название,
        # исключая последующие блоки метаданных (страна, год, жанр, качество и т.д.).
        # Ищем первый открывающийся квадратную скобку, который не является [X из X] (т.к. его обрабатывает сезон).
        # Если такого нет, берем всю строку.
        match_end_of_title_segment = re.search(r'\[(?!\s*\d+\s+из\s+\d+\s*\])', title_string)

        title_and_episode_segment = ""
        if match_end_of_title_segment:
            title_and_episode_segment = title_string[:match_end_of_title_segment.start()].strip()
        else:
            title_and_episode_segment = title_string.strip()

        # Удаляем информацию о количестве эпизодов, если она осталась в скобках [X из X].
        cleaned_title_for_name_only = re.sub(r'\s*\[\d+\s+из\s+\d+\]', '', title_and_episode_segment).strip()

        # Пытаемся извлечь русское и альтернативное название, используя разделитель '/'
        # Теперь '([^/(]+)' не будет захватывать квадратные скобки, т.к. мы их уже убрали.
        title_alt_match = re.match(r"^(.*?)\s*/\s*([^/(]+)", cleaned_title_for_name_only)

        if title_alt_match:
            parsed_title = title_alt_match.group(1).strip()
            # Убираем возможное (Режиссер) из альтернативного названия
            parsed_alternative_title = re.sub(r"\s+\([^)]+\)\s*$", "", title_alt_match.group(2).strip()).strip()
        else:
            # Если нет '/', то вся очищенная строка - это основное название
            # Убираем (Режиссер) из основного названия, если он там есть в конце
            parsed_title = re.sub(r"\s+\([^)]+\)\s*$", "", cleaned_title_for_name_only).strip()

        # Возвращаем новый экземпляр класса с извлеченными данными
        return cls(
            magnet=parsed_magnet,
            title=parsed_title,
            alternative_title=parsed_alternative_title,
            year=parsed_year,
            season=parsed_season
        )