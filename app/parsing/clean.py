from __future__ import annotations

import re

from app.config import TRIGGER_PHRASES

_TAG_RE = re.compile(r"#\S+")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_len_preserving(text: str) -> str:
    """lower + ё→е. Длина строки сохраняется — можно резать оригинал по индексам."""
    return text.replace("ё", "е").replace("Ё", "Е").lower()


def _find_spans(text: str, phrases: tuple[str, ...]) -> list[tuple[int, int]]:
    """Возвращает непересекающиеся спаны всех вхождений фраз в text (по нормализованной копии)."""
    norm = _normalize_len_preserving(text)
    spans: list[tuple[int, int]] = []
    for phrase in phrases:
        p = _normalize_len_preserving(phrase).strip()
        if not p:
            continue
        start = 0
        while True:
            idx = norm.find(p, start)
            if idx == -1:
                break
            spans.append((idx, idx + len(p)))
            start = idx + len(p)

    if not spans:
        return []

    # Сортируем и сливаем пересечения/соседние
    spans.sort()
    merged: list[tuple[int, int]] = [spans[0]]
    for s, e in spans[1:]:
        ls, le = merged[-1]
        if s <= le:
            merged[-1] = (ls, max(le, e))
        else:
            merged.append((s, e))
    return merged


def _cut_spans(text: str, spans: list[tuple[int, int]]) -> str:
    """Вырезает спаны, идя с конца, чтобы не сбить индексы."""
    for s, e in reversed(spans):
        text = text[:s] + " " + text[e:]
    return text


def clean_reminder_text(
    content: str, phrases: list[str] | tuple[str, ...] | None = None
) -> str:
    """Чистит текст заметки для пуша: убирает теги и триггер-фразы, схлопывает пробелы.

    Время намеренно НЕ вырезается — оно полезно в тексте пуша.
    Регистр и буква «ё» в остатке сохраняются.
    """
    if not content or not content.strip():
        return ""

    # 1. Теги — до триггеров, иначе #напомни съестся как фраза и останется висячий #
    text = _TAG_RE.sub(" ", content)

    # 2. Триггер-фразы
    if phrases is None:
        phrases = TRIGGER_PHRASES
    spans = _find_spans(text, tuple(phrases))
    if spans:
        text = _cut_spans(text, spans)

    # 3. Переносы строк → пробел, схлопнуть множественные пробелы
    text = _WHITESPACE_RE.sub(" ", text)

    return text.strip()
