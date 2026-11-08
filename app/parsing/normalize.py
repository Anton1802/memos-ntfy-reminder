from __future__ import annotations

from app.config import config


def normalize(text: str) -> str:
    return text.casefold().replace("ё", "е")


def normalize_index_safe(text: str) -> str:
    return text.replace("ё", "е").replace("Ё", "Е").lower()


def normalized_phrases(phrases: list[str] | tuple[str, ...] | None = None) -> tuple[str, ...]:
    source = config.TRIGGER_PHRASES if phrases is None else phrases
    return tuple(normalize(p) for p in source if p and p.strip())
