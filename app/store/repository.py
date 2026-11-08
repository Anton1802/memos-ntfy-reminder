import sqlite3
import time


def add_reminder(conn: sqlite3.Connection, memo_id: str, text: str, due_at: int, created_at: int | None = None) -> bool:
    ts = int(time.time()) if created_at is None else created_at
    query = "INSERT OR IGNORE INTO reminders (memo_id, text, due_at, status, created_at, attempts) VALUES (?, ?, ?, 'pending', ?, 0)"
    cur = conn.execute(query, (memo_id, text, due_at, ts))
    return cur.rowcount > 0


def is_processed(conn: sqlite3.Connection, memo_id: str) -> bool:
    query = "SELECT 1 FROM processed WHERE memo_id = ?"
    row = conn.execute(query, (memo_id,)).fetchone()
    return row is not None


def mark_sent(conn: sqlite3.Connection, reminder_id: int, when: int | None = None) -> None:
    ts = int(time.time()) if when is None else when
    query = "UPDATE reminders SET status='sent', sent_at=? WHERE id=?"
    conn.execute(query, (ts, reminder_id))


def mark_processed(conn: sqlite3.Connection, memo_id: str, when: int | None = None) -> None:
    ts = int(time.time()) if when is None else when
    query = "INSERT OR IGNORE INTO processed (memo_id, processed_at) VALUES (?, ?)"
    conn.execute(query, (memo_id, ts))


def mark_cancelled(conn: sqlite3.Connection, reminder_id: int, when: int | None = None) -> None:
    ts = int(time.time()) if when is None else when
    query = "UPDATE reminders SET status='cancelled', sent_at=? WHERE id=?"
    conn.execute(query, (ts, reminder_id))


def mark_error(conn: sqlite3.Connection, reminder_id: int, when: int | None = None) -> None:
    ts = int(time.time()) if when is None else when
    query = "UPDATE reminders SET status='error', attempts = attempts + 1, sent_at=? WHERE id=?"
    conn.execute(query, (ts, reminder_id))


def fetch_due(conn: sqlite3.Connection, now_ts: int, limit: int = 50) -> list[sqlite3.Row]:
    query = """
        SELECT id, memo_id, text, due_at, attempts
        FROM reminders
        WHERE status IN ('pending', 'error')
        AND due_at <= ?
        ORDER BY due_at ASC
        LIMIT ?
    """
    return conn.execute(query, (now_ts, limit)).fetchall()
