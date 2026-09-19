from __future__ import annotations

import logging

import requests

from app.config import NTFY_URL, NTFY_TOPIC, NTFY_TOKEN

log = logging.getLogger(__name__)

_TIMEOUT = 10


def send_reminder(text: str, title: str = "Напоминание") -> bool:
    """Отправляет пуш в ntfy. True при 2xx, False при любой ошибке.

    Топик уходит в JSON (NTFY_URL — только база без пути).
    """
    if not text or not text.strip():
        log.warning("send_reminder: пустой текст, пропускаем")
        return False

    if not NTFY_TOPIC:
        log.error("send_reminder: NTFY_TOPIC не задан")
        return False

    payload = {
        "topic": NTFY_TOPIC,
        "title": title,
        "message": text,
        "priority": 4,
        "tags": ["bell"],
    }
    headers = {}
    if NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {NTFY_TOKEN}"

    try:
        r = requests.post(NTFY_URL, json=payload, headers=headers, timeout=_TIMEOUT)
    except requests.RequestException as e:
        log.error("ntfy request failed: %s", e)
        return False

    if not r.ok:
        log.error("ntfy returned %s: %s", r.status_code, r.text[:200])
        return False

    return True
