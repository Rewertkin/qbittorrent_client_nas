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

            # Текст до года (или до квадратной скобки с годом)
            text_before_year = title_string[:year_match.start()].strip()

            # Пытаемся извлечь русское и альтернативное название
            # (Русское название) / (Английское название) ...
            title_alt_match = re.match(r"^(.*?)\s*/\s*([^/([]+)", text_before_year)
            if title_alt_match:
                parsed_title = title_alt_match.group(1).strip()
                # Убираем возможное (Режиссер) из альтернативного названия
                parsed_alternative_title = re.sub(r"\s+\([^)]+\)\s*$", "", title_alt_match.group(2).strip()).strip()
            else:
                # Если нет '/', то все до года (и до режиссера в скобках, если есть) - это основное название
                # Убираем (Режиссер) из основного названия, если он там есть в конце
                parsed_title = re.sub(r"\s+\([^)]+\)\s*$", "", text_before_year).strip()
        else:
            # Если год не найден стандартным способом, просто берем всю строку как название
            # Это маловероятно для ваших примеров, но как запасной вариант
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
            season=parsed_season
        )