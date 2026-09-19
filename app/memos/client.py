from __future__ import annotations

import logging

import requests

from app.config import MEMOS_TOKEN, MEMOS_URL
from app.memos.models import Memo

log = logging.getLogger(__name__)

_TIMEOUT = 10


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if MEMOS_TOKEN:
        h["Authorization"] = f"Bearer {MEMOS_TOKEN}"
    return h


def list_memos(limit: int = 200) -> list[Memo]:
    """Возвращает список заметок. Пустой список при ошибке."""
    try:
        r = requests.get(
            f"{MEMOS_URL}/api/v1/memos",
            headers=_headers(),
            params={"pageSize": limit},
            timeout=_TIMEOUT,
        )
    except requests.RequestException as e:
        log.error("memos list failed: %s", e)
        return []

    if not r.ok:
        log.error("memos list returned %s: %s", r.status_code, r.text[:200])
        return []

    out: list[Memo] = []
    for item in r.json().get("memos", []):
        try:
            out.append(Memo.from_payload(item))
        except (KeyError, ValueError, TypeError) as e:
            log.warning("skip malformed memo: %s", e)
    return out


def archive_memo(memo_id: str) -> bool:
    """Архивирует заметку. True при 2xx."""
    try:
        r = requests.patch(
            f"{MEMOS_URL}/api/v1/{memo_id}",
            params={"updateMask": "state"},
            json={"state": "ARCHIVED"},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
    except requests.RequestException as e:
        log.error("memos archive failed: %s", e)
        return False

    if not r.ok:
        log.error("memos archive returned %s: %s", r.status_code, r.text[:200])
        return False

    return True


def get_memo(memo_id: str) -> tuple[str, Memo | None]:
    """Возвращает ('ok', memo) | ('not_found', None) | ('error', None).

    - 'ok'        — заметка есть, memo заполнен
    - 'not_found' — 404, заметки нет (удалили)
    - 'error'     — сеть/5xx/битый ответ
    """
    try:
        r = requests.get(
            f"{MEMOS_URL}/api/v1/{memo_id}",
            headers=_headers(),
            timeout=_TIMEOUT,
        )
    except requests.RequestException as e:
        log.error("memos get failed: %s", e)
        return ("error", None)

    if r.status_code == 404:
        return ("not_found", None)

    if not r.ok:
        log.error("memos get returned %s: %s", r.status_code, r.text[:200])
        return ("error", None)

    try:
        return ("ok", Memo.from_payload(r.json()))
    except (KeyError, ValueError, TypeError) as e:
        log.warning("malformed memo %s: %s", memo_id, e)
        return ("error", None)
