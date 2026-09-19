from __future__ import annotations

import time

import pytest

from app.store import db, repo


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_schema(c)
    yield c
    c.close()


def test_is_processed_false_initially(conn):
    assert repo.is_processed(conn, "memos/1") is False


def test_mark_processed_idempotent(conn):
    repo.mark_processed(conn, "memos/1", when=100)
    repo.mark_processed(conn, "memos/1", when=200)
    assert repo.is_processed(conn, "memos/1") is True


def test_add_reminder_dedup(conn):
    ok1 = repo.add_reminder(conn, "memos/1", "text", due_at=1000, created_at=100)
    ok2 = repo.add_reminder(conn, "memos/1", "text", due_at=1000, created_at=100)
    assert ok1 is True
    assert ok2 is False
    count = conn.execute("SELECT COUNT(*) FROM reminders").fetchone()[0]
    assert count == 1


def test_fetch_due_only_due(conn):
    repo.add_reminder(conn, "memos/1", "past", due_at=100, created_at=0)
    repo.add_reminder(conn, "memos/2", "future", due_at=10_000, created_at=0)
    rows = repo.fetch_due(conn, now_ts=500)
    assert len(rows) == 1
    assert rows[0]["memo_id"] == "memos/1"


def test_fetch_due_ordered_by_due_at(conn):
    repo.add_reminder(conn, "memos/1", "later", due_at=300, created_at=0)
    repo.add_reminder(conn, "memos/2", "earlier", due_at=100, created_at=0)
    rows = repo.fetch_due(conn, now_ts=500)
    assert [r["memo_id"] for r in rows] == ["memos/2", "memos/1"]


def test_mark_sent_excluded_from_fetch(conn):
    repo.add_reminder(conn, "memos/1", "x", due_at=100, created_at=0)
    rid = conn.execute("SELECT id FROM reminders").fetchone()[0]
    repo.mark_sent(conn, rid, when=200)
    assert repo.fetch_due(conn, now_ts=500) == []


def test_mark_error_retries_until_max(conn):
    repo.add_reminder(conn, "memos/1", "x", due_at=100, created_at=0)
    rid = conn.execute("SELECT id FROM reminders").fetchone()[0]

    for _ in range(repo.MAX_ATTEMPTS):
        rows = repo.fetch_due(conn, now_ts=500)
        assert len(rows) == 1
        repo.mark_error(conn, rid, when=200)

    # attempts == MAX → больше не берём
    assert repo.fetch_due(conn, now_ts=500) == []


def test_check_constraint_status(conn):
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO reminders (memo_id, text, due_at, status, created_at, attempts)"
            " VALUES ('x','y',1,'bogus',0,0)"
        )
