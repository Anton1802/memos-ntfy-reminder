from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS processed (
    memo_id TEXT PRIMARY KEY,
    processed_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memo_id TEXT NOT NULL UNIQUE,
    text TEXT NOT NULL,
    due_at INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','sent','error')),
    created_at INTEGER NOT NULL,
    sent_at INTEGER,
    attempts INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_reminders_due
    ON reminders(status, due_at);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Открывает соединение. Каждый поток должен звать это сам — sqlite не шарится."""
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
