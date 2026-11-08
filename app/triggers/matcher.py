from __future__ import annotations

from app.memos.models import Memo
from app.parsing.normalize import normalize, normalized_phrases

_NORMALIZED_PHRASES = normalized_phrases()


def is_reminder(memo: Memo | None, phrases: list[str] | None = None) -> bool:
    if memo is None:
        return False

    if not isinstance(memo.content, str) or not memo.content.strip():
        return False

    normalized = normalize(memo.content)
    if phrases is None:
        return any(phrase in normalized for phrase in _NORMALIZED_PHRASES)
    return any(normalize(p) in normalized for p in phrases if p.strip())
