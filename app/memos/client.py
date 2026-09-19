from app.config import MEMOS_TOKEN, MEMOS_URL
import requests
import logging

_TIMEOUT = 5

log = logging.getLogger(__name__)


def archive_memo(memo_id: str) -> bool:
    """Архивирует заметку. True при 2xx.

    memo_id — полное имя ресурса, например 'memos/YWZw...'.
    """
    headers = {"Content-Type": "application/json"}
    if MEMOS_TOKEN:
        headers["Authorization"] = f"Bearer {MEMOS_TOKEN}"

    url = f"{MEMOS_URL}/api/v1/{memo_id}"
    try:
        r = requests.patch(
            url,
            params={"updateMask": "state"},
            json={"state": "ARCHIVED"},
            headers=headers,
            timeout=_TIMEOUT,
        )
    except requests.RequestException as e:
        log.error("memos archive failed: %s", e)
        return False

    if not r.ok:
        log.error("memos archive returned %s: %s", r.status_code, r.text[:200])
        return False

    return True
