from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import re

_RE_REL = re.compile(
    r"через\s+(\d+)\s*"
    r"(минут\w*|мин|м|час\w*|ч|день|дня|дней|дн|д|недел\w*|нед|месяц\w*|мес)\b"
)
_RE_TOMORROW = re.compile(r"(завтра|послезавтра)\s+в\s+(\d{1,2})(?::(\d{2}))?")
_RE_TODAY = re.compile(r"\bв\s+(\d{1,2})(?::(\d{2}))?\b")

_UNIT_SECONDS = {
    "м": 60,
    "мин": 60,
    "минута": 60,
    "минуту": 60,
    "минуты": 60,
    "минут": 60,
    "ч": 3600,
    "час": 3600,
    "часа": 3600,
    "часов": 3600,
    "д": 86400,
    "дн": 86400,
    "день": 86400,
    "дня": 86400,
    "дней": 86400,
    "нед": 604800,
    "неделя": 604800,
    "неделю": 604800,
    "недели": 604800,
    "недель": 604800,
    "мес": 2592000,
    "месяц": 2592000,
    "месяца": 2592000,
    "месяцев": 2592000,
}

_RE_REL_WORD = re.compile(r"через\s+(полчаса|час|неделю|месяц|год|день)\b")

_WORD_SECONDS = {
    "полчаса": 1800,
    "час": 3600,
    "день": 86400,
    "неделю": 604800,
    "месяц": 2592000,
    "год": 31536000,
}


def parse_due(text: str, now: datetime) -> datetime | None:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not text or not text.strip():
        return None

    normalized = re.sub(r"\s+", " ", text.casefold().replace("ё", "е")).strip()

    # --- A: "через 15 минут", "через 2 недели" ---
    m = _RE_REL.search(normalized)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        secs = _UNIT_SECONDS.get(unit)
        # n > 0: "через 0 минут" бессмысленно
        if n > 0 and secs:
            return (now + timedelta(seconds=n * secs)).astimezone(timezone.utc)

    # --- A2: "через неделю", "через месяц" (слово без цифры) ---
    m = _RE_REL_WORD.search(normalized)
    if m:
        secs = _WORD_SECONDS.get(m.group(1))
        if secs:
            return (now + timedelta(seconds=secs)).astimezone(timezone.utc)

    # Локальное "сейчас" нужно, чтобы "завтра" и "в 9" считались от местной даты,
    # а не от UTC-даты. now может прийти в UTC — приводим к его же зоне.
    tz = now.tzinfo
    local_now = now.astimezone(tz)

    # --- B: "завтра в 9", "послезавтра в 9:30" ---
    m = _RE_TOMORROW.search(normalized)
    if m:
        day_word = m.group(1)
        hh = int(m.group(2))
        mm = int(m.group(3) or 0)  # минут нет → 0
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            days = 1 if day_word == "завтра" else 2
            base = local_now + timedelta(days=days)
            # Обнуляем секунды/микросекунды — иначе унаследуются от local_now
            due_local = base.replace(hour=hh, minute=mm, second=0, microsecond=0)
            return due_local.astimezone(timezone.utc)

    # --- C: "в 18:00", "в 9", "в 9:30" ---
    m = _RE_TODAY.search(normalized)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2) or 0)
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            due_local = local_now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            # Время уже прошло (или ровно сейчас) → переносим на завтра.
            # "<=", а не "<": иначе "в 18:00" при now=18:00 сработает мгновенно.
            if due_local <= local_now:
                due_local += timedelta(days=1)
            return due_local.astimezone(timezone.utc)

    return None
