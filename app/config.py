import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    MEMOS_URL: str
    MEMOS_TOKEN: str
    MEMOS_TIMEOUT: int

    NTFY_URL: str
    NTFY_TOKEN: str | None
    NTFY_TOPIC: str
    NTFY_TIMEOUT: int

    TRIGGER_PHRASES: list[str]
    TRIGGER_DEFAULT_MINUTES: int

    POLL_INTERVAL: int
    WORKER_INTERVAL: int
    FIRST_RUN_LOOKBACK: int
    OVERDUE_THRESHOLD_SECONDS: int

    LOGGING_LEVEL: str
    TIMEZONE: str
    DATABASE_PATH: str


def load_config_from_dotenv() -> Config:
    load_dotenv()

    trigger_phrases = [
        phrase.strip().lower() for phrase in os.getenv("TRIGGER_PHRASES", "").split(",") if phrase.strip()
    ]

    return Config(
        MEMOS_URL=os.environ["MEMOS_URL"],
        MEMOS_TOKEN=os.environ["MEMOS_TOKEN"],
        MEMOS_TIMEOUT=int(os.getenv("MEMOS_TIMEOUT", 10)),
        NTFY_URL=os.environ["NTFY_URL"],
        NTFY_TOKEN=os.getenv("NTFY_TOKEN"),
        NTFY_TOPIC=os.environ["NTFY_TOPIC"],
        NTFY_TIMEOUT=int(os.getenv("NTFY_TIMEOUT", 10)),
        TRIGGER_PHRASES=trigger_phrases,
        TRIGGER_DEFAULT_MINUTES=int(os.getenv("TRIGGER_DEFAULT_MINUTES", 60)),
        POLL_INTERVAL=int(os.getenv("POLL_INTERVAL", 30)),
        WORKER_INTERVAL=int(os.getenv("WORKER_INTERVAL", 30)),
        FIRST_RUN_LOOKBACK=int(os.getenv("FIRST_RUN_LOOKBACK", 3600)),
        OVERDUE_THRESHOLD_SECONDS=int(os.getenv("OVERDUE_THRESHOLD_SECONDS", 60)),
        LOGGING_LEVEL=os.getenv("LOGGING_LEVEL", "INFO"),
        TIMEZONE=os.getenv("TIMEZONE", "Europe/Moscow"),
        DATABASE_PATH=os.getenv("DATABASE_PATH", "data/reminders.db"),
    )


config = load_config_from_dotenv()

LOCAL_TIMEZONE = ZoneInfo(config.TIMEZONE)
