import logging

import requests

from app.config import config

log = logging.getLogger(__name__)

NTFY_PRIORITY = 4
NTFY_TAGS = ["bell"]


def send_reminder(text: str, title: str = "Напоминание") -> bool:
    if not text or not text.strip():
        log.warning("Skip empty text")
        return False

    payload = {
        "topic": config.NTFY_TOPIC,
        "title": title,
        "message": text,
        "priority": NTFY_PRIORITY,
        "tags": NTFY_TAGS,
    }

    headers = {}
    if config.NTFY_TOKEN:
        headers["Authorization"] = f"Bearer {config.NTFY_TOKEN}"

    try:
        response = requests.post(config.NTFY_URL, json=payload, headers=headers, timeout=config.NTFY_TIMEOUT)
    except requests.RequestException as e:
        log.error("Request failed: %s", e)
        return False

    if not response.ok:
        log.error("Returned %s: %s", response.status_code, response.text[:200])
        return False

    return True
