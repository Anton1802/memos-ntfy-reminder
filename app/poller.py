from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from app.config import (
    FIRST_RUN_LOOKBACK,
    POLL_INTERVAL,
    TRIGGER_DEFAULT_MINUTES,
)
from app.memos.client import list_memos
from app.parsing.clean import clean_reminder_text
from app.parsing.time_parser import parse_due
from app.store import repo, db
from app.triggers.matcher import is_reminder

log = logging.getLogger(__name__)


def _is_first_run(conn) -> bool:
    row = conn.execute("SELECT 1 FROM processed LIMIT 1").fetchone()
    return row is None


def run_once(conn, now_ts: int | None = None) -> int:
    """Один проход: опросил Memos, положил новые напоминания.

    Возвращает число добавленных reminders.
    """
    now_ts = int(time.time()) if now_ts is None else now_ts
    now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc)

    first_run = _is_first_run(conn)
    cutoff = now_ts - FIRST_RUN_LOOKBACK if first_run else None

    added = 0
    for memo in list_memos():
        if memo.state != "NORMAL":
            continue

        if repo.is_processed(conn, memo.id):
            continue

        # Первый запуск: старые заметки помечаем processed, но не обрабатываем
        if cutoff is not None and int(memo.create_time.timestamp()) < cutoff:
            repo.mark_processed(conn, memo.id, when=now_ts)
            continue

        if not is_reminder(memo):
            repo.mark_processed(conn, memo.id, when=now_ts)
            continue

        due = parse_due(memo.content, now_dt)
        if due is None:
            due = now_dt + timedelta(minutes=TRIGGER_DEFAULT_MINUTES)

        text = clean_reminder_text(memo.content)
        if not text:
            # после чистки пусто — нечего слать
            repo.mark_processed(conn, memo.id, when=now_ts)
            continue

        ok = repo.add_reminder(
            conn,
            memo_id=memo.id,
            text=text,
            due_at=int(due.timestamp()),
            created_at=now_ts,
        )
        if ok:
            added += 1
            log.info("poller: added reminder memo=%s due=%s", memo.id, due.isoformat())

        repo.mark_processed(conn, memo.id, when=now_ts)

    return added


def run_loop(db_path, stop_event) -> None:
    conn = db.connect(db_path)
    log.info("poller started, interval=%ss", POLL_INTERVAL)
    try:
        while not stop_event.is_set():
            try:
                added = run_once(conn)
                if added:
                    log.info("poller: added %d reminder(s)", added)
            except Exception:
                log.exception("poller: run_once failed")
            stop_event.wait(POLL_INTERVAL)
    finally:
        conn.close()
        log.info("poller stopped")
