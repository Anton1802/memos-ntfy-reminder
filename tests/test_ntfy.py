from __future__ import annotations

from unittest.mock import patch

import requests

from app.notifier import ntfy


def _resp(status: int, text: str = "") -> requests.Response:
    r = requests.Response()
    r.status_code = status
    r._content = text.encode()
    return r


@patch("app.notifier.ntfy.requests.post")
def test_send_success(mock_post):
    mock_post.return_value = _resp(200)
    assert ntfy.send_reminder("привет") is True
    mock_post.assert_called_once()
    kwargs = mock_post.call_args.kwargs
    assert kwargs["json"]["message"] == "привет"
    assert kwargs["json"]["topic"]  # topic задан


@patch("app.notifier.ntfy.requests.post")
def test_send_http_error(mock_post):
    mock_post.return_value = _resp(500, "boom")
    assert ntfy.send_reminder("привет") is False


@patch("app.notifier.ntfy.requests.post")
def test_send_network_error(mock_post):
    mock_post.side_effect = requests.ConnectionError("no route")
    assert ntfy.send_reminder("привет") is False


def test_send_empty_text():
    assert ntfy.send_reminder("") is False
    assert ntfy.send_reminder("   ") is False
