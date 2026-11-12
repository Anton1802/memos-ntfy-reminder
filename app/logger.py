import logging


def setup_logging(level: str | None = "INFO") -> None:
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s")
