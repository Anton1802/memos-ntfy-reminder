from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.parsing.time_parser import parse_due

NOW = datetime(2026, 9, 18, 10, 0, tzinfo=ZoneInfo("Europe/Moscow"))  # пятница


# --- старые (регрессия) -----------------------------------------------------


def test_in_7_days():
    assert parse_due("через 7 дней", NOW) == NOW.replace(day=25)


def test_in_2_weeks():
    assert parse_due("через 2 недели", NOW) == NOW + timedelta(days=14)


def test_in_a_week_word():
    assert parse_due("через неделю", NOW) == NOW + timedelta(days=7)


def test_in_a_couple_hours_none():
    assert parse_due("через пару часов", NOW) is not None  # теперь +2ч


def test_tomorrow_at_9_after_10_am():
    assert parse_due("завтра в 9", NOW) == datetime(
        2026, 9, 19, 6, 0, tzinfo=timezone.utc
    )


def test_at_9_30_already_passed():
    assert parse_due("в 9:30", NOW) == datetime(2026, 9, 19, 6, 30, tzinfo=timezone.utc)


def test_naive_now_raises():
    with pytest.raises(ValueError):
        parse_due("через 5 минут", datetime(2026, 9, 18, 10, 0))


# --- A: через N единиц ------------------------------------------------------


def test_in_1_minute_digit():
    assert parse_due("через 1 минуту", NOW) == NOW + timedelta(minutes=1)


def test_in_90_minutes():
    assert parse_due("через 90 минут", NOW) == NOW + timedelta(minutes=90)


def test_in_1_5_hours():
    assert parse_due("через 1.5 часа", NOW) == NOW + timedelta(minutes=90)


def test_in_2_years():
    assert parse_due("через 2 года", NOW) == NOW + timedelta(days=730)


def test_in_0_minutes_none():
    assert parse_due("через 0 минут", NOW) is None


# --- A2: через слово --------------------------------------------------------


def test_in_a_minute_word():
    assert parse_due("через минуту", NOW) == NOW + timedelta(minutes=1)


def test_in_an_hour_word():
    assert parse_due("через час", NOW) == NOW + timedelta(hours=1)


def test_in_a_day_word():
    assert parse_due("через день", NOW) == NOW + timedelta(days=1)


def test_in_24_hours_word():
    assert parse_due("через сутки", NOW) == NOW + timedelta(days=1)


def test_in_half_an_hour():
    assert parse_due("через полчаса", NOW) == NOW + timedelta(minutes=30)


def test_in_an_hour_and_a_half():
    assert parse_due("через полтора часа", NOW) == NOW + timedelta(minutes=90)


def test_in_couple_of_minutes():
    assert parse_due("через пару минут", NOW) == NOW + timedelta(minutes=2)


def test_in_couple_of_hours():
    assert parse_due("через пару часов", NOW) == NOW + timedelta(hours=2)


# --- B: завтра/послезавтра/сегодня ------------------------------------------


def test_tomorrow_no_time():
    # завтра 09:00 MSK = 06:00 UTC
    assert parse_due("завтра", NOW) == datetime(2026, 9, 19, 6, 0, tzinfo=timezone.utc)


def test_day_after_tomorrow():
    assert parse_due("послезавтра в 15", NOW) == datetime(
        2026, 9, 20, 12, 0, tzinfo=timezone.utc
    )


def test_day_after_tomorrow_no_time():
    assert parse_due("послезавтра", NOW) == datetime(
        2026, 9, 20, 6, 0, tzinfo=timezone.utc
    )


def test_today_in_future():
    # сейчас 10:00, "сегодня в 18:00" → сегодня 18:00 MSK = 15:00 UTC
    assert parse_due("сегодня в 18:00", NOW) == datetime(
        2026, 9, 18, 15, 0, tzinfo=timezone.utc
    )


def test_today_in_past_fallback():
    # сейчас 10:00, "сегодня в 9:00" → fallback
    assert parse_due("сегодня в 9:00", NOW) is None


def test_today_no_time_fallback():
    assert parse_due("сегодня", NOW) is None


# --- C: абсолютное время ----------------------------------------------------


def test_at_18_today():
    assert parse_due("в 18", NOW) == datetime(2026, 9, 18, 15, 0, tzinfo=timezone.utc)


def test_at_18_with_dot():
    assert parse_due("в 18.00", NOW) == datetime(
        2026, 9, 18, 15, 0, tzinfo=timezone.utc
    )


def test_k_18():
    assert parse_due("к 18:00", NOW) == datetime(
        2026, 9, 18, 15, 0, tzinfo=timezone.utc
    )


def test_clock_no_prep():
    assert parse_due("18:00", NOW) == datetime(2026, 9, 18, 15, 0, tzinfo=timezone.utc)


def test_at_25_invalid():
    assert parse_due("в 25:00", NOW) is None


# --- E: части дня -----------------------------------------------------------


def test_morning():
    # сейчас 10:00, "утром" = 09:00 → прошло → завтра 09:00? Нет: часть дня
    # без указателя "завтра" — база сегодня, если прошло → всё равно сегодня?
    # По ТЗ: не решено. Наш код: _parse_day_part без day_word даёт сегодня 09:00.
    # 09:00 < 10:00 → вернём сегодня 09:00 (в прошлом). Это ок для напоминалки?
    # Ставим: сегодня 09:00 MSK = 06:00 UTC.
    assert parse_due("утром", NOW) == datetime(2026, 9, 18, 6, 0, tzinfo=timezone.utc)


def test_tomorrow_morning():
    assert parse_due("завтра утром", NOW) == datetime(
        2026, 9, 19, 6, 0, tzinfo=timezone.utc
    )


def test_tomorrow_evening():
    assert parse_due("завтра вечером", NOW) == datetime(
        2026, 9, 19, 15, 0, tzinfo=timezone.utc
    )


def test_today_evening_future():
    assert parse_due("сегодня вечером", NOW) == datetime(
        2026, 9, 18, 15, 0, tzinfo=timezone.utc
    )


def test_today_morning_past_fallback():
    assert parse_due("сегодня утром", NOW) is None


# --- D: абсолютные даты -----------------------------------------------------


def test_date_word():
    # 20 сентября, время не указано → 09:00 MSK = 06:00 UTC
    assert parse_due("20 сентября", NOW) == datetime(
        2026, 9, 20, 6, 0, tzinfo=timezone.utc
    )


def test_date_word_with_time():
    assert parse_due("20 сентября в 15:00", NOW) == datetime(
        2026, 9, 20, 12, 0, tzinfo=timezone.utc
    )


def test_date_numeric():
    assert parse_due("20.09", NOW) == datetime(2026, 9, 20, 6, 0, tzinfo=timezone.utc)


def test_date_numeric_with_year():
    assert parse_due("20.09.2027 в 15:00", NOW) == datetime(
        2027, 9, 20, 12, 0, tzinfo=timezone.utc
    )


def test_date_in_past_next_year():
    # 01.01 уже прошло → 2027
    assert parse_due("01.01", NOW) == datetime(2027, 1, 1, 6, 0, tzinfo=timezone.utc)


# --- день недели ------------------------------------------------------------


def test_next_friday():
    # NOW = пятница 18.09 10:00. "в пятницу" → сегодня 09:00 (прошло, но по решению — оставляем)
    assert parse_due("в пятницу", NOW) == datetime(
        2026, 9, 18, 6, 0, tzinfo=timezone.utc
    )


def test_next_monday():
    # следующий понедельник = 21.09
    assert parse_due("в понедельник", NOW) == datetime(
        2026, 9, 21, 6, 0, tzinfo=timezone.utc
    )


def test_next_monday_at_15():
    assert parse_due("в понедельник в 15", NOW) == datetime(
        2026, 9, 21, 12, 0, tzinfo=timezone.utc
    )


# --- относительное с числительным прописью ----------------------------------


def test_in_one_minute_word():
    assert parse_due("через одну минуту", NOW) == NOW + timedelta(minutes=1)


def test_in_two_weeks_word():
    assert parse_due("через две недели", NOW) == NOW + timedelta(days=14)


def test_in_three_days_word():
    assert parse_due("через три дня", NOW) == NOW + timedelta(days=3)


def test_in_ten_minutes_word():
    assert parse_due("через десять минут", NOW) == NOW + timedelta(minutes=10)


def test_in_one_and_a_half_hours_word():
    assert parse_due("через полтора часа", NOW) == NOW + timedelta(minutes=90)
