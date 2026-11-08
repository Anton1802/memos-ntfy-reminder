import logging
import sqlite3
import threading
import time
from datetime import datetime

from app.config import LOCAL_TIMEZONE, config
from app.enums import Emoji
from app.memos.client import add_comment, archive_memo, get_memo
from app.notifier.ntfy import send_reminder
from app.store import database, repository

log = logging.getLogger(__name__)


def _format_message(text: str, due_at: int, now_ts: int) -> str:
    return f"{text} (опоздало)" if now_ts - due_at > config.OVERDUE_THRESHOLD_SECONDS else text


def run_once(conn: sqlite3.Connection, now_ts: int | None = None) -> int:
    now_ts = int(time.time()) if now_ts is None else now_ts
    rows = repository.fetch_due(conn, now_ts=now_ts)

    sent = 0
    for row in rows:
        status, memo = get_memo(row["memo_id"])

        if status == "not_found":
            log.info("worker: memo %s deleted, cancel id=%s", row["memo_id"], row["id"])
            repository.mark_cancelled(conn, row["id"], when=now_ts)
            continue

        if status == "ok" and memo is not None and memo.state != "NORMAL":
            log.info("worker: memo %s archived, cancel id=%s", row["memo_id"], row["id"])
            repository.mark_cancelled(conn, row["id"], when=now_ts)
            continue

        if status == "error":
            log.warning("worker: memos unavailable, sending anyway id=%s", row["id"])

        msg = _format_message(row["text"], row["due_at"], now_ts)
        if send_reminder(msg):
            repository.mark_sent(conn, row["id"], when=now_ts)
            if status == "ok":
                if not archive_memo(row["memo_id"]):
                    log.warning("worker: sent but archive failed memo=%s", row["memo_id"])

                now_local = datetime.fromtimestamp(now_ts, tz=LOCAL_TIMEZONE)
                add_comment(row["memo_id"], f"{Emoji.OK} Отправлено {now_local:%d.%m.%Y %H:%M}")

            sent += 1
            log.info("worker: sent reminder id=%s", row["id"])
        else:
            repository.mark_error(conn, row["id"], when=now_ts)
            attempts = row["attempts"] + 1
            add_comment(row["memo_id"], f"{Emoji.WARNING} Ошибка отправки (попытка {attempts})")
            log.warning("worker: failed reminder id=%s attempts=%s", row["id"], attempts)

    return sent


def run_loop(db_path: str, stop_event: threading.Event) -> None:
    conn = database.connect(db_path)
    log.info("worker started, interval=%ss", config.WORKER_INTERVAL)

    try:
        while not stop_event.is_set():
            try:
                sent = run_once(conn)
                if sent:
                    log.info("worker: sent %d", sent)
            except Exception:
                log.exception("worker: run_once failed")
            stop_event.wait(config.WORKER_INTERVAL)
    finally:
        conn.close()
        log.info("worker stopped")
