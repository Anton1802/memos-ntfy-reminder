from __future__ import annotations

import logging
import time

from app.config import WORKER_INTERVAL
from app.memos.client import archive_memo, get_memo, add_comment
from app.notifier.ntfy import send_reminder
from app.store import db, repo

from zoneinfo import ZoneInfo
from app.config import TZ
from datetime import datetime

_LOCAL_TZ = ZoneInfo(TZ)


log = logging.getLogger(__name__)

OVERDUE_THRESHOLD_SECONDS = 60


def _format_message(text: str, due_at: int, now_ts: int) -> str:
    if now_ts - due_at > OVERDUE_THRESHOLD_SECONDS:
        return f"{text} (опоздало)"
    return text


def run_once(conn, now_ts: int | None = None) -> int:
    """Один проход: забрал due, проверил живость заметки, отправил."""
    now_ts = int(time.time()) if now_ts is None else now_ts
    rows = repo.fetch_due(conn, now_ts=now_ts)

    sent = 0
    for row in rows:
        status, memo = get_memo(row["memo_id"])

        if status == "not_found":
            log.info("worker: memo %s deleted, cancel id=%s", row["memo_id"], row["id"])
            repo.mark_cancelled(conn, row["id"], when=now_ts)
            continue

        if status == "ok" and memo is not None and memo.state != "NORMAL":
            log.info(
                "worker: memo %s archived, cancel id=%s", row["memo_id"], row["id"]
            )
            repo.mark_cancelled(conn, row["id"], when=now_ts)
            continue

        if status == "error":
            log.warning("worker: memos unavailable, sending anyway id=%s", row["id"])

        msg = _format_message(row["text"], row["due_at"], now_ts)
        if send_reminder(msg):
            repo.mark_sent(conn, row["id"], when=now_ts)
            if status == "ok":
                if not archive_memo(row["memo_id"]):
                    log.warning(
                        "worker: sent but archive failed memo=%s", row["memo_id"]
                    )
                now_local = datetime.fromtimestamp(now_ts, tz=_LOCAL_TZ)
                add_comment(
                    row["memo_id"],
                    f"✅ [memos-ntfy-reminder] Отправлено в {now_local:%H:%M}",
                )
            sent += 1
            log.info("worker: sent reminder id=%s", row["id"])
        else:
            repo.mark_error(conn, row["id"], when=now_ts)
            # attempts после mark_error
            attempts = row["attempts"] + 1
            add_comment(
                row["memo_id"],
                f"⚠️ [memos-ntfy-reminder] Ошибка отправки (попытка {attempts})",
            )
            log.warning(
                "worker: failed reminder id=%s attempts=%s", row["id"], attempts
            )

    return sent


def run_loop(db_path, stop_event) -> None:
    conn = db.connect(db_path)
    log.info("worker started, interval=%ss", WORKER_INTERVAL)
    try:
        while not stop_event.is_set():
            try:
                n = run_once(conn)
                if n:
                    log.info("worker: sent %d", n)
            except Exception:
                log.exception("worker: run_once failed")
            stop_event.wait(WORKER_INTERVAL)
    finally:
        conn.close()
        log.info("worker stopped")
