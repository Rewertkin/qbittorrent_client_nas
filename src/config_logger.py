import logging

def setup_logging():
    """
    Настраивает базовое логирование для всего приложения.
    Вызывать эту функцию нужно один раз в точке входа приложения (например, в main.py).
    """
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
