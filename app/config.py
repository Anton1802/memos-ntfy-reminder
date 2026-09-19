import os
from dotenv import load_dotenv

load_dotenv()

MEMOS_URL = os.getenv("MEMOS_URL", "http://127.0.0.1:5230").rstrip("/")
MEMOS_TOKEN = os.getenv("MEMOS_TOKEN", "")
NTFY_TOKEN = os.getenv("NTFY_TOKEN") or None
NTFY_URL = os.getenv("NTFY_URL")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")
TRIGGER_PHRASES = [
    p.strip().lower() for p in os.getenv("TRIGGER_PHRASES", "").split(",") if p.strip()
]
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
FIRST_RUN_LOOKBACK = int(os.getenv("FIRST_RUN_LOOKBACK", "3600"))
WORKER_INTERVAL = int(os.getenv("WORKER_INTERVAL", "30"))
TRIGGER_DEFAULT_MINUTES = int(os.getenv("TRIGGER_DEFAULT_MINUTES", "60"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
TZ = os.getenv("TZ", "Europe/Moscow")
DB_PATH = os.getenv("DB_PATH", "data/reminders.db")
