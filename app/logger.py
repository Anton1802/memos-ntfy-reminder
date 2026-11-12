import logging


class ColoredFormatter(logging.Formatter):
    # Цвета
    BLUE = "\033[36m"
    WHITE = "\033[37m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    GRAY = "\033[90m"
    GREEN = "\033[32m"

    # Специальные
    BOLD = "\033[31m"
    RESET = "\033[0m"

    # Цвета под уровни
    LEVEL_COLORS = {
        "DEBUG": BLUE,
        "INFO": WHITE,
        "WARNING": YELLOW,
        "ERROR": RED,
        "CRITICAL": RED + BOLD,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Это пизда что я придумал нахуй
        # Добавляем к уровню пробелы чтобы выровнять красиво вывод
        maxsize_levelname = len("CRITICAL")
        current_levelname_size = len(record.levelname)
        add_spaces = maxsize_levelname - current_levelname_size
        spaces = " " * add_spaces

        # Задаём цвет разным частям лога в зависимости от их уровня
        level_color = self.LEVEL_COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{level_color}{record.levelname}{spaces}{self.RESET}"
        record.name = f"{self.GRAY}{record.name}{self.RESET}"
        record.funcName = f"{self.GRAY}{record.funcName}{self.RESET}"
        record.msg = f"{level_color}{record.msg}{self.RESET}"

        return super().format(record)


def get_logger(name: str, level: str = "DEBUG") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    format = "%(asctime)s | %(levelname)s | %(name)s.%(funcName)s | %(message)s"
    date_format = "%y-%m-%d %H:%M:%S"
    formatter = ColoredFormatter(fmt=format, datefmt=date_format)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
