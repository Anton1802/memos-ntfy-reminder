import logging


class ColoredFormatter(logging.Formatter):
    # Цвета
    BLUE = "\033[36m"
    WHITE = "\033[37m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    GRAY = "\033[90m"

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
        level_color = self.LEVEL_COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        record.name = f"{self.GRAY}{record.name}{self.RESET}"
        record.funcName = f"{self.GRAY}{record.funcName}{self.RESET}"
        record.msg = f"{level_color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logging(level: str | None = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s | %(name)s.%(funcName)s | %(message)s",
        datefmt="%y-%m-%d %H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()

    formatter = ColoredFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


setup_logging("DEBUG")

logger = get_logger(__name__)
logger.info("Hello!")
logger.debug("Hello!")
logger.warning("Hello!")
logger.error("Hello!")
logger.critical("Hello!")
