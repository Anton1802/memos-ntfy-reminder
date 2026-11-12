import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone

from app.config import LOCAL_TIMEZONE, config
from app.enums import Emoji
from app.memos.client import add_comment, list_memos
from app.parsing.clean import clean_reminder_text
from app.parsing.time_parser import parse_due
from app.store import database, repository
from app.triggers.matcher import is_reminder

log = logging.getLogger(__name__)


def run_once(conn: sqlite3.Connection, now_ts: int | None = None) -> int:
    now_ts = int(time.time()) if now_ts is None else now_ts
    now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc)

    first_run = repository.is_first_run(conn)
    cutoff = now_ts - config.FIRST_RUN_LOOKBACK if first_run else None

    added = 0
    for memo in list_memos():
        if memo.state != "NORMAL" or repository.is_processed(conn, memo.id):
            continue

        if cutoff is not None and int(memo.create_time.timestamp()) < cutoff or not is_reminder(memo):
            repository.mark_processed(conn, memo.id, when=now_ts)
            continue

        due = parse_due(memo.content, now_dt)
        if due is None:
            due = now_dt + timedelta(minutes=config.TRIGGER_DEFAULT_MINUTES)

        text = clean_reminder_text(memo.content)
        if not text:
            repository.mark_processed(conn, memo.id, when=now_ts)
            continue

        ok = repository.add_reminder(conn, memo_id=memo.id, text=text, due_at=int(due.timestamp()), created_at=now_ts)
        if ok:
            added += 1
            due_local = due.astimezone(LOCAL_TIMEZONE)
            add_comment(memo.id, f"{Emoji.PROCESSED} Взято в работу. Отправлю {due_local:%d.%m.%Y %H:%M}")
            log.info("poller: added reminder memo=%s due=%s", memo.id, due.isoformat())

        repository.mark_processed(conn, memo.id, when=now_ts)

    return added


def run_loop(db_path: str, stop_event: threading.Event) -> None:
    conn = database.connect(db_path)
    log.info("Poller started, interval=%ss", config.POLL_INTERVAL)

    try:
        while not stop_event.is_set():
            try:
                added = run_once(conn)
                log.info("poller: added %d reminder(s)", added)
            except Exception:
                log.exception("poller: run_once failed")
            stop_event.wait(config.POLL_INTERVAL)
    finally:
        conn.close()
        log.info("poller stopped")
