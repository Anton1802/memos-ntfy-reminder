from __future__ import annotations

from app.config import TRIGGER_PHRASES

from app.parsing.normalize import normalize, normalized_phrases

_NORMALIZED_PHRASES = normalized_phrases()


def is_reminder(memo, phrases=None) -> bool:
    if memo is None:
        return False

    content = getattr(memo, "content", memo)
    if not isinstance(content, str) or not content.strip():
        return False

    normalized = normalize(content)
    if phrases is None:
        return any(phrase in normalized for phrase in _NORMALIZED_PHRASES)
    return any(normalize(p) in normalized for p in phrases if p.strip())
