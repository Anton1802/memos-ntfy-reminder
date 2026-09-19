from __future__ import annotations

import sqlite3
import time

MAX_ATTEMPTS = 3


def is_processed(conn: sqlite3.Connection, memo_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM processed WHERE memo_id = ?", (memo_id,)
    ).fetchone()
    return row is not None


def mark_processed(
    conn: sqlite3.Connection, memo_id: str, when: int | None = None
) -> None:
    ts = int(time.time()) if when is None else when
    conn.execute(
        "INSERT OR IGNORE INTO processed (memo_id, processed_at) VALUES (?, ?)",
        (memo_id, ts),
    )


def mark_cancelled(
    conn: sqlite3.Connection, reminder_id: int, when: int | None = None
) -> None:
    """Помечает reminder отменённым (заметку удалили/архивировали до отправки)."""
    ts = int(time.time()) if when is None else when
    conn.execute(
        "UPDATE reminders SET status='cancelled', sent_at=? WHERE id=?",
        (ts, reminder_id),
    )


def add_reminder(
    conn: sqlite3.Connection,
    memo_id: str,
    text: str,
    due_at: int,
    created_at: int | None = None,
) -> bool:
    """True если добавили, False если такой memo_id уже есть (дедуп)."""
    ts = int(time.time()) if created_at is None else created_at
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO reminders
            (memo_id, text, due_at, status, created_at, attempts)
        VALUES (?, ?, ?, 'pending', ?, 0)
        """,
        (memo_id, text, due_at, ts),
    )
    return cur.rowcount > 0


def fetch_due(
    conn: sqlite3.Connection, now_ts: int, limit: int = 50
) -> list[sqlite3.Row]:
    """Pending + error с исчерпанными попытками НЕ берём. Порядок — по due_at."""
    return conn.execute(
        """
        SELECT id, memo_id, text, due_at, attempts
        FROM reminders
        WHERE status IN ('pending', 'error')
          AND due_at <= ?
        ORDER BY due_at ASC
        LIMIT ?
        """,
        (now_ts, limit),
    ).fetchall()


def mark_sent(
    conn: sqlite3.Connection, reminder_id: int, when: int | None = None
) -> None:
    ts = int(time.time()) if when is None else when
    conn.execute(
        "UPDATE reminders SET status='sent', sent_at=? WHERE id=?",
        (ts, reminder_id),
    )


def mark_error(
    conn: sqlite3.Connection, reminder_id: int, when: int | None = None
) -> None:
    """attempts += 1. Статус остаётся 'error' — fetch_due подхватит, пока attempts < MAX."""
    ts = int(time.time()) if when is None else when
    conn.execute(
        "UPDATE reminders SET status='error', attempts = attempts + 1, sent_at=? WHERE id=?",
        (ts, reminder_id),
    )
