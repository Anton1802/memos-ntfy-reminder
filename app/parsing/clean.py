import re

from app.config import config

_TAG_RE = re.compile(r"#\S+")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_len_preserving(text: str) -> str:
    return text.replace("ё", "е").replace("Ё", "Е").lower()


def _find_spans(text: str, phrases: tuple[str, ...]) -> list[tuple[int, int]]:
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
    for s, e in reversed(spans):
        text = text[:s] + " " + text[e:]
    return text


def clean_reminder_text(content: str, phrases: list[str] | tuple[str, ...] | None = None) -> str:
    if not content or not content.strip():
        return ""

    text = _TAG_RE.sub(" ", content)
    phrases = phrases or config.TRIGGER_PHRASES

    spans = _find_spans(text, tuple(phrases))
    if spans:
        text = _cut_spans(text, spans)

    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()
