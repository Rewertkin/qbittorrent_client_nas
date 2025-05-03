from dataclasses import dataclass
from typing import Optional
import re

@dataclass(frozen=True)
class Message_data:
    """класс для работы данными из сообщения"""
    magnet: Optional[str] = None
    title: Optional[str] = None
    alternative_title: Optional[str] = None
    year: Optional[int] = None
    season: Optional[str] = None

    @classmethod
    def prepare_message_data(cls, message_text):
        """ получение данных из сообщения"""
        # найдем магнет ссылку
        magnet_start = message_text.find('magnet')
        if magnet_start != -1:
            magnet_end_newline = message_text.find('\n', magnet_start)
            if magnet_end_newline == -1:
                magnet_finish = len(message_text)
            else:
                magnet_finish = magnet_end_newline
            cls.magnet = message_text[magnet_start:magnet_finish].strip()

        # найдем строку с названием фильма/торрента:
        first_line_end = message_text.find(":\n")
        if first_line_end == -1:
            return cls

        title_start = first_line_end + 2
        title_finish_newline = message_text.find("\n", title_start)
        if title_finish_newline == -1:
            if magnet_start != -1:
                title_finish = magnet_start
            else:
                title_finish = len(message_text)
        else:
            title_finish = title_finish_newline

        title_string = message_text[title_start:title_finish].strip()

        # --- Парсинг строки заголовка ---

        # Сначала пытаемся найти основной формат: Название / Альт.Название ... [Год,...]
        match_full = re.search(r"^(.*?)\s*/\s*([^/([]+)\s*.*?\[(\d{4})[-,]", title_string)

        if match_full:
            cls.title = match_full.group(1).strip()
            cls.alternative_title = match_full.group(2).strip()
            cls.year = match_full.group(3)
        else:
            # Если не нашли полный формат, ищем упрощенный: Название ... [Год,...]
            match_simple = re.search(r"^(.*?)\s*\[(\d{4})[-,]", title_string)
            if match_simple:
                raw_title = match_simple.group(1).strip()
                # Убираем возможное имя режиссера в скобках в конце названия
                # (скобка должна быть последним элементом перед пробелом и [Год...])
                cls.title = re.sub(r"\s+\([^)]*\)\s*$", "", raw_title).strip()
                # alternative_title остается None
                cls.year = match_simple.group(2)
            else:
                # Если и это не сработало, берем всю строку как название
                cls.title = title_string

        # --- Поиск информации о сезоне ПОСЛЕ основного парсинга ---
        # Ищем в оригинальной строке заголовка (title_string), так как там может быть больше информации
        if cls.year:
            # Искать сезон имеет смысл только если нашли год (т.е. парсинг был успешным)
            season_match_sXX = re.search(r'\bS(\d+)\b', title_string, re.IGNORECASE)
            if season_match_sXX:
                cls.season = season_match_sXX.group(1) # Забираем только номер

            # Вариант 2: Ищем "Сезон(ы)/Season(s)" и захватываем ТОЛЬКО цифры/диапазоны/перечисления после
            elif not cls.season: # Искать только если еще не нашли
                # Ищем "Сезон/Season", двоеточие (?), пробелы, а затем группу цифр/запятых/дефисов/пробелов
                season_match_word = re.search(
                    r'(?:Сезон(?:ы)?|Season(?:s)?)\s*[:]?\s*([\d,\s-]+(?:\s*-\s*\d+)?)\b',
                    title_string,
                    re.IGNORECASE
                )
                if season_match_word:
                    # Очищаем результат от лишних пробелов и знаков препинания по краям
                    season_info = season_match_word.group(1).strip().rstrip(',.-')
                    cls.season = season_info

            # Вариант 3: Ищем числа/диапазоны, за которыми идет слово "сезон(а/ы)"
            elif not cls.season: # Искать только если еще не нашли
                season_match_num_season = re.search(
                    r'\b([\d,\s-]+(?:\s*-\s*\d+)?)\s+(?:сезон|сезона|сезоны)\b',
                    title_string,
                    re.IGNORECASE
                )
                if season_match_num_season:
                    season_info = season_match_num_season.group(1).strip().rstrip(',.-')
                    cls.season = season_info

        # Если title все еще содержит информацию о сезоне после альтернативного названия,
        # попробуем ее убрать (но это может быть рискованно и убрать нужное)
        # Пример: "Клан Сопрано / The Sopranos / Полные сезоны: ..." -> "Клан Сопрано / The Sopranos"
        # Делаем это только если есть alternative_title
        # if message_data['alternative_title'] and message_data['title']:
        #     # Ищем "/ " после alternative_title в исходной строке title_string
        #     alt_title_end_index = title_string.find(message_data['alternative_title']) + len(message_data['alternative_title'])
        #     # Если после альт. названия есть " / ", обрезаем title до этого момента
        #     # Эта логика сложная и может не всегда работать, пока оставим title как есть после первой регулярки.

        return cls