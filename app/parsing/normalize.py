from __future__ import annotations

from app.config import TRIGGER_PHRASES


def normalize(text: str) -> str:
    """casefold + ё→е. Для сравнений (может менять длину в редких юникод-кейсах)."""
    return text.casefold().replace("ё", "е")


def normalize_index_safe(text: str) -> str:
    """lower + ё→е. Гарантирует len(результат) == len(вход) — для поиска по индексам."""
    return text.replace("ё", "е").replace("Ё", "Е").lower()


def normalized_phrases(
    phrases: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """Нормализованные непустые триггер-фразы. По умолчанию — из конфига."""
    source = TRIGGER_PHRASES if phrases is None else phrases
    return tuple(normalize(p) for p in source if p and p.strip())
