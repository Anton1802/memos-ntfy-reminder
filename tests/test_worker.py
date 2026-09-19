from __future__ import annotations

from unittest.mock import patch

import pytest

from app.memos.models import Memo
from app.store import db, repo
from app.worker import run_once


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    db.init_schema(c)
    yield c
    c.close()


@pytest.fixture(autouse=True)
def mock_add_comment():
    """Глушим add_comment во всех тестах — иначе он стучится в реальный Memos."""
    with patch("app.worker.add_comment", return_value=True) as m:
        yield m


def _add(conn, memo_id="memos/1", text="x", due_at=100):
    repo.add_reminder(conn, memo_id=memo_id, text=text, due_at=due_at, created_at=0)
    return conn.execute("SELECT id, memo_id FROM reminders").fetchone()


def _memo(state="NORMAL"):
    from datetime import datetime, timezone

    return Memo(
        id="memos/1",
        content="напомни x",
        create_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state=state,
    )


@patch("app.worker.send_reminder", return_value=True)
@patch("app.worker.archive_memo", return_value=True)
@patch("app.worker.get_memo")
def test_send_and_archive(mock_get, mock_arch, mock_send, conn):
    row = _add(conn)
    mock_get.return_value = ("ok", _memo("NORMAL"))

    assert run_once(conn, now_ts=200) == 1
    mock_send.assert_called_once()
    mock_arch.assert_called_once_with(row["memo_id"])
    assert conn.execute("SELECT status FROM reminders").fetchone()["status"] == "sent"


@patch("app.worker.send_reminder")
@patch("app.worker.get_memo")
def test_cancel_on_404(mock_get, mock_send, conn):
    _add(conn)
    mock_get.return_value = ("not_found", None)

    assert run_once(conn, now_ts=200) == 0
    mock_send.assert_not_called()
    assert (
        conn.execute("SELECT status FROM reminders").fetchone()["status"] == "cancelled"
    )


@patch("app.worker.send_reminder")
@patch("app.worker.get_memo")
def test_cancel_on_archived(mock_get, mock_send, conn):
    _add(conn)
    mock_get.return_value = ("ok", _memo("ARCHIVED"))

    assert run_once(conn, now_ts=200) == 0
    mock_send.assert_not_called()
    assert (
        conn.execute("SELECT status FROM reminders").fetchone()["status"] == "cancelled"
    )


@patch("app.worker.archive_memo")
@patch("app.worker.send_reminder", return_value=True)
@patch("app.worker.get_memo")
def test_send_when_memos_down(mock_get, mock_send, mock_arch, conn):
    _add(conn)
    mock_get.return_value = ("error", None)

    assert run_once(conn, now_ts=200) == 1
    mock_send.assert_called_once()
    mock_arch.assert_not_called()  # не архивируем, если Memos лежал
    assert conn.execute("SELECT status FROM reminders").fetchone()["status"] == "sent"


@patch("app.worker.add_comment", return_value=True)
@patch("app.worker.archive_memo", return_value=True)
@patch("app.worker.send_reminder", return_value=True)
@patch("app.worker.get_memo")
def test_comment_on_send(mock_get, mock_send, mock_arch, mock_comment, conn):
    _add(conn)
    mock_get.return_value = ("ok", _memo("NORMAL"))
    run_once(conn, now_ts=200)
    mock_comment.assert_called_once()
    text = mock_comment.call_args[0][1]
    assert "Отправлено" in text


@patch("app.worker.add_comment", return_value=True)
@patch("app.worker.send_reminder", return_value=False)
@patch("app.worker.get_memo")
def test_comment_on_error(mock_get, mock_send, mock_comment, conn):
    _add(conn)
    mock_get.return_value = ("ok", _memo("NORMAL"))
    run_once(conn, now_ts=200)
    mock_comment.assert_called_once()
    text = mock_comment.call_args[0][1]
    assert "Ошибка" in text
    assert "попытка 1" in text
