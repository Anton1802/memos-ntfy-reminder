from __future__ import annotations

from app.config import TRIGGER_PHRASES

_NORMALIZED_PHRASES: tuple[str, ...] = tuple(
    p.casefold().replace("ё", "е") for p in TRIGGER_PHRASES if p.strip()
)


def _normalize(text: str) -> str:
    """Приводит к единому виду: casefold + ё→е (люди пишут ё непоследовательно)."""
    return text.casefold().replace("ё", "е")


def is_reminder(memo, phrases=None) -> bool:
    """True, если заметка похожа на запрос напоминания.

    Принимает объект заметки с атрибутом ``content`` или обычную строку.
    """
    if memo is None:
        return False

    content = getattr(memo, "content", memo)
    if not isinstance(content, str) or not content.strip():
        return False

    normalized = _normalize(content)
    if phrases is None:
        return any(phrase in normalized for phrase in _NORMALIZED_PHRASES)
    return any(_normalize(p) in normalized for p in phrases if p.strip())
