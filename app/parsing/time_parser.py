from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.config import TZ

_LOCAL_TZ = ZoneInfo(TZ)
_FALLBACK = object()  # сигнал: парсер матчит, но нужен fallback (stop, return None)


# --- относительное с цифрой -------------------------------------------------

_RE_REL = re.compile(
    r"через\s+(\d+(?:[.,]\d+)?)\s*"
    r"(минут\w*|мин|м|час\w*|ч|день|дня|дней|дн|д|суток|сутки|"
    r"недел\w*|нед|месяц\w*|мес|год\w*|лет|г)\b"
)

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
    "сутки": 86400,
    "суток": 86400,
    "нед": 604800,
    "неделя": 604800,
    "неделю": 604800,
    "недели": 604800,
    "недель": 604800,
    "мес": 2592000,
    "месяц": 2592000,
    "месяца": 2592000,
    "месяцев": 2592000,
    "г": 31536000,
    "год": 31536000,
    "года": 31536000,
    "лет": 31536000,
    "годов": 31536000,
}


def _match_rel_number(text: str) -> timedelta | None:
    m = _RE_REL.search(text)
    if not m:
        return None
    try:
        n = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    if n <= 0:
        return None
    secs = _UNIT_SECONDS.get(m.group(2))
    if not secs:
        return None
    return timedelta(seconds=round(n * secs))


# --- относительное словом ---------------------------------------------------

_WORD_SECONDS: dict[str, int] = {
    "полчаса": 1800,
    "пару часов": 7200,
    "пару минут": 120,
    "минуту": 60,
    "час": 3600,
    "день": 86400,
    "сутки": 86400,
    "неделю": 604800,
    "месяц": 2592000,
    "год": 31536000,
}
_WORD_KEYS_SORTED = tuple(sorted(_WORD_SECONDS.keys(), key=len, reverse=True))

_RE_REL_WORD = re.compile(
    r"через\s+(" + "|".join(re.escape(k) for k in _WORD_KEYS_SORTED) + r")\b"
)

_NUM_WORDS: dict[str, float] = {
    "одну": 1,
    "один": 1,
    "одна": 1,
    "две": 2,
    "два": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
    "десять": 10,
    "полтора": 1.5,
    "полторы": 1.5,
}

# Единицы — те же, что в _RE_REL, чтобы не дублировать смысл
_RE_REL_NUM_WORD = re.compile(
    r"через\s+(" + "|".join(_NUM_WORDS.keys()) + r")\s+"
    r"(минут\w*|мин|м|час\w*|ч|день|дня|дней|дн|д|суток|сутки|"
    r"недел\w*|нед|месяц\w*|мес|год\w*|лет|г)\b"
)


def _match_rel_num_word(text: str) -> timedelta | None:
    m = _RE_REL_NUM_WORD.search(text)
    if not m:
        return None
    n = _NUM_WORDS.get(m.group(1))
    if not n or n <= 0:
        return None
    secs = _UNIT_SECONDS.get(m.group(2))
    if not secs:
        return None
    return timedelta(seconds=round(n * secs))


def _match_rel_word(text: str) -> timedelta | None:
    m = _RE_REL_WORD.search(text)
    if not m:
        return None
    secs = _WORD_SECONDS.get(m.group(1))
    return timedelta(seconds=secs) if secs else None


# --- части дня --------------------------------------------------------------

_DAY_PART_HOUR = {
    "утром": 9,
    "утро": 9,
    "утра": 9,
    "днём": 12,
    "днем": 12,
    "дня": 12,
    "вечером": 18,
    "вечер": 18,
    "вечера": 18,
    "ночью": 23,
    "ночь": 23,
    "ночи": 23,
    "в обед": 13,
    "обед": 13,
}
_DAY_PART_KEYS_SORTED = tuple(sorted(_DAY_PART_HOUR.keys(), key=len, reverse=True))
_RE_DAY_PART = re.compile(
    r"\b(?:(завтра|послезавтра|сегодня)\s+)?"
    r"(" + "|".join(re.escape(k) for k in _DAY_PART_KEYS_SORTED) + r")\b"
)


# --- завтра/послезавтра/сегодня --------------------------------------------

_RE_TOMORROW = re.compile(
    r"\b(завтра|послезавтра|сегодня)\b" r"(?:\s+в\s+(\d{1,2})(?::(\d{2}))?)?"
)

# --- абсолютное время -------------------------------------------------------

_RE_CLOCK = re.compile(r"\b(?:в|к)\s+(\d{1,2})(?:[:.](\d{2}))?\b")
_RE_CLOCK_NOPREP = re.compile(r"\b(\d{1,2}):(\d{2})\b")


# --- абсолютные даты --------------------------------------------------------

_MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}
_RE_DATE_WORD = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(_MONTHS.keys()) + r")[а-я]*"
    r"(?:\s+(\d{4}))?"
    r"(?:\s+в\s+(\d{1,2})(?::(\d{2}))?)?"
)
_RE_DATE_NUM = re.compile(
    r"(?<!через )"
    r"\b(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?"
    r"(?:\s+в\s+(\d{1,2})(?::(\d{2}))?)?"
)

_WEEKDAYS = {
    "понедельник": 0,
    "вторник": 1,
    "среду": 2,
    "среда": 2,
    "сред": 2,
    "четверг": 3,
    "пятниц": 4,
    "суббот": 5,
    "воскресень": 6,
    "пн": 0,
    "вт": 1,
    "ср": 2,
    "чт": 3,
    "пт": 4,
    "сб": 5,
    "вс": 6,
}
_RE_WEEKDAY = re.compile(
    r"\bв\s+(?:следующий\s+)?(" + "|".join(_WEEKDAYS.keys()) + r")[а-я]*"
    r"(?:\s+в\s+(\d{1,2})(?::(\d{2}))?)?"
)


# --- helpers ----------------------------------------------------------------


def _at_time(local: datetime, hh: int, mm: int) -> datetime:
    return local.replace(hour=hh, minute=mm, second=0, microsecond=0)


def _valid_time(hh: int, mm: int) -> bool:
    return 0 <= hh <= 23 and 0 <= mm <= 59


def _local_9(local: datetime) -> datetime:
    return local.replace(hour=9, minute=0, second=0, microsecond=0)


# --- парсеры -----------------------------------------------------------------


def _parse_absolute_date(text: str, local_now: datetime):
    m = _RE_DATE_WORD.search(text)
    if m:
        day = int(m.group(1))
        month = _MONTHS.get(m.group(2))
        year = int(m.group(3)) if m.group(3) else None
        hh = int(m.group(4)) if m.group(4) else 9
        mm = int(m.group(5)) if m.group(5) else 0
        if month and 1 <= day <= 31 and _valid_time(hh, mm):
            return _build_date(local_now, day, month, year, hh, mm)

    m = _RE_DATE_NUM.search(text)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else None
        hh = int(m.group(4)) if m.group(4) else 9
        mm = int(m.group(5)) if m.group(5) else 0
        if 1 <= day <= 31 and 1 <= month <= 12 and _valid_time(hh, mm):
            return _build_date(local_now, day, month, year, hh, mm)

    return None


def _build_date(local_now, day, month, year, hh, mm):
    if year is None:
        year = local_now.year
    try:
        candidate = local_now.replace(
            year=year,
            month=month,
            day=day,
            hour=hh,
            minute=mm,
            second=0,
            microsecond=0,
        )
    except ValueError:
        return None
    if year == local_now.year and candidate <= local_now:
        try:
            candidate = candidate.replace(year=year + 1)
        except ValueError:
            return None
    return candidate


def _parse_weekday(text: str, local_now: datetime):
    m = _RE_WEEKDAY.search(text)
    if not m:
        return None
    target_wd = _WEEKDAYS.get(m.group(1))
    if target_wd is None:
        return None
    hh = int(m.group(2)) if m.group(2) else 9
    mm = int(m.group(3)) if m.group(3) else 0
    if not _valid_time(hh, mm):
        return None
    days_ahead = (target_wd - local_now.weekday()) % 7
    return _at_time(local_now + timedelta(days=days_ahead), hh, mm)


def _parse_day_part(text: str, local_now: datetime):
    m = _RE_DAY_PART.search(text)
    if not m:
        return None
    day_word = m.group(1)
    hour = _DAY_PART_HOUR.get(m.group(2))
    if hour is None:
        return None

    if day_word == "завтра":
        base = local_now + timedelta(days=1)
    elif day_word == "послезавтра":
        base = local_now + timedelta(days=2)
    elif day_word == "сегодня":
        candidate = _at_time(local_now, hour, 0)
        if candidate <= local_now:
            return _FALLBACK
        return candidate
    else:
        base = local_now

    return _at_time(base, hour, 0)


def _parse_tomorrow(text: str, local_now: datetime):
    m = _RE_TOMORROW.search(text)
    if not m:
        return None
    word = m.group(1)
    hh_raw = m.group(2)
    mm_raw = m.group(3)

    if word == "сегодня":
        if hh_raw is None:
            return _FALLBACK
        hh = int(hh_raw)
        mm = int(mm_raw) if mm_raw else 0
        if not _valid_time(hh, mm):
            return None
        candidate = _at_time(local_now, hh, mm)
        if candidate <= local_now:
            return _FALLBACK
        return candidate

    days = 1 if word == "завтра" else 2
    base = local_now + timedelta(days=days)
    if hh_raw is None:
        return _local_9(base)
    hh = int(hh_raw)
    mm = int(mm_raw) if mm_raw else 0
    if not _valid_time(hh, mm):
        return None
    return _at_time(base, hh, mm)


def _parse_clock(text: str, local_now: datetime):
    m = _RE_CLOCK.search(text)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2)) if m.group(2) else 0
        if not _valid_time(hh, mm):
            return None
        candidate = _at_time(local_now, hh, mm)
        if candidate <= local_now:
            candidate += timedelta(days=1)
        return candidate

    m = _RE_CLOCK_NOPREP.search(text)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        if not _valid_time(hh, mm):
            return None
        candidate = _at_time(local_now, hh, mm)
        if candidate <= local_now:
            candidate += timedelta(days=1)
        return candidate

    return None


# --- основной парсер --------------------------------------------------------


def parse_due(text: str, now: datetime) -> datetime | None:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not text or not text.strip():
        return None

    normalized = re.sub(r"\s+", " ", text.casefold().replace("ё", "е")).strip()
    local_now = now.astimezone(_LOCAL_TZ)

    # 1. "через N единиц" — самое специфичное
    delta = _match_rel_number(normalized)
    if delta is not None:
        return (now + delta).astimezone(timezone.utc)

        # 2. "через одну/две/... единиц" (числительное прописью)
    delta = _match_rel_num_word(normalized)
    if delta is not None:
        return (now + delta).astimezone(timezone.utc)

    # 2. "через <слово>"
    delta = _match_rel_word(normalized)
    if delta is not None:
        return (now + delta).astimezone(timezone.utc)

    # 3. Абсолютная дата (20 сентября, 20.09, 20.09.2026 [в HH:MM])
    r = _parse_absolute_date(normalized, local_now)
    if r is _FALLBACK:
        return None
    if r is not None:
        return r.astimezone(timezone.utc)

    # 4. День недели (в пятницу, в следующий вторник [в HH:MM])
    r = _parse_weekday(normalized, local_now)
    if r is _FALLBACK:
        return None
    if r is not None:
        return r.astimezone(timezone.utc)

    # 5. Часть дня (утром, завтра вечером, сегодня днём)
    r = _parse_day_part(normalized, local_now)
    if r is _FALLBACK:
        return None
    if r is not None:
        return r.astimezone(timezone.utc)

    # 6. завтра/послезавтра/сегодня [в HH[:MM]]
    r = _parse_tomorrow(normalized, local_now)
    if r is _FALLBACK:
        return None
    if r is not None:
        return r.astimezone(timezone.utc)

    # 7. Голое время (в 18:00, к 18:00, 18.00, 18:00 без предлога)
    r = _parse_clock(normalized, local_now)
    if r is _FALLBACK:
        return None
    if r is not None:
        return r.astimezone(timezone.utc)

    return None
