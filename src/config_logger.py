"""Настраивает базовое логирование для всего приложения."""
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO, # Уровень логирования по умолчанию
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        # Можно добавить обработчики для записи в файл, если потребуется:
        handlers=[
             logging.FileHandler("app.log"),
             logging.StreamHandler()
             ]
    )
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('qbittorrentapi').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
