"""Тесты парсера напоминаний. Запуск: python -m pytest tests/test_time_parser.py -v"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.parsing.time_parser import parse_due

MSK = ZoneInfo("Europe/Moscow")
NOW = datetime(2026, 9, 18, 10, 0, tzinfo=MSK)  # пятница


def utc(year, month, day, hour=6, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# Относительное время: цифры
@pytest.mark.parametrize(
    "phrase,minutes",
    [
        ("через 1 минуту", 1),
        ("через 5 минут", 5),
        ("через 90 минут", 90),
        ("через 1.5 часа", 90),
        ("через 1,5 часа", 90),
        ("через 2 часа", 120),
        ("через 7 дней", 7 * 24 * 60),
        ("через 2 недели", 14 * 24 * 60),
    ],
)
def test_relative_digits(phrase, minutes):
    assert parse_due(phrase, NOW) == NOW + timedelta(minutes=minutes)


# Относительное время: слова
@pytest.mark.parametrize(
    "phrase,minutes",
    [
        ("через минуту", 1),
        ("через час", 60),
        ("через день", 24 * 60),
        ("через сутки", 24 * 60),
        ("через неделю", 7 * 24 * 60),
        ("через полчаса", 30),
        ("через полтора часа", 90),
        ("через пару минут", 2),
        ("через пару часов", 120),
        ("через одну минуту", 1),
        ("через две недели", 14 * 24 * 60),
        ("через три дня", 3 * 24 * 60),
        ("через десять минут", 10),
    ],
)
def test_relative_words(phrase, minutes):
    assert parse_due(phrase, NOW) == NOW + timedelta(minutes=minutes)


# Календарные месяцы и годы (не фиксированные 30/365 дней)
@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("через месяц", utc(2026, 10, 18, 7)),
        ("через 1 месяц", utc(2026, 10, 18, 7)),
        ("через 2 месяца", utc(2026, 11, 18, 7)),
        ("через 5 месяцев", utc(2027, 2, 18, 7)),
        ("через три месяца", utc(2026, 12, 18, 7)),
        ("через год", utc(2027, 9, 18, 7)),
        ("через 2 года", utc(2028, 9, 18, 7)),
        ("через пять лет", utc(2031, 9, 18, 7)),
    ],
)
def test_calendar_relative(phrase, expected):
    assert parse_due(phrase, NOW) == expected


def test_end_of_month():
    now = datetime(2026, 1, 31, 10, 0, tzinfo=MSK)
    assert parse_due("через месяц", now) == utc(2026, 2, 28, 7)


def test_leap_year_calendar():
    now = datetime(2024, 2, 29, 10, 0, tzinfo=MSK)
    assert parse_due("через год", now) == utc(2025, 2, 28, 7)


@pytest.mark.parametrize(
    "phrase",
    [
        "через 0 минут",
        "через 0 дней",
        "через 0 месяцев",
        "через 1.5 месяца",
        "через 1.5 года",
    ],
)
def test_invalid_relative(phrase):
    assert parse_due(phrase, NOW) is None


# Завтра, послезавтра, сегодня
@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("завтра", utc(2026, 9, 19)),
        ("завтра в 9", utc(2026, 9, 19)),
        ("послезавтра", utc(2026, 9, 20)),
        ("послезавтра в 15", utc(2026, 9, 20, 12)),
        ("сегодня в 18:00", utc(2026, 9, 18, 15)),
    ],
)
def test_relative_day(phrase, expected):
    assert parse_due(phrase, NOW) == expected


@pytest.mark.parametrize("phrase", ["сегодня в 9:00", "сегодня", "сегодня утром"])
def test_past_or_unspecified_today(phrase):
    assert parse_due(phrase, NOW) is None


# Часы
@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("в 18", utc(2026, 9, 18, 15)),
        ("в 18.00", utc(2026, 9, 18, 15)),
        ("к 18:00", utc(2026, 9, 18, 15)),
        ("18:00", utc(2026, 9, 18, 15)),
        ("в 9:30", utc(2026, 9, 19, 6, 30)),
    ],
)
def test_clock(phrase, expected):
    assert parse_due(phrase, NOW) == expected


def test_invalid_clock():
    assert parse_due("в 25:00", NOW) is None


# Части дня
@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("завтра утром", utc(2026, 9, 19)),
        ("завтра вечером", utc(2026, 9, 19, 15)),
        ("сегодня вечером", utc(2026, 9, 18, 15)),
    ],
)
def test_day_parts(phrase, expected):
    assert parse_due(phrase, NOW) == expected


@pytest.mark.xfail(
    reason="Текущий парсер возвращает прошедшее утро; поведение нужно определить"
)
def test_morning_without_day_should_not_be_past():
    assert parse_due("утром", NOW) == utc(2026, 9, 19)


# Абсолютные даты и _build_date
@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("20 сентября", utc(2026, 9, 20)),
        ("20 сентября в 15:00", utc(2026, 9, 20, 12)),
        ("20.09", utc(2026, 9, 20)),
        ("20.09.2027 в 15:00", utc(2027, 9, 20, 12)),
        ("01.01", utc(2027, 1, 1)),
        ("10 сентября", utc(2027, 9, 10)),
        ("10 сентября 2027", utc(2027, 9, 10)),
    ],
)
def test_absolute_dates(phrase, expected):
    assert parse_due(phrase, NOW) == expected


@pytest.mark.parametrize(
    "phrase",
    [
        "10 сентября 2026",
        "10.09.2026",
        "31 февраля 2027",
    ],
)
def test_past_explicit_year_or_invalid_date(phrase):
    assert parse_due(phrase, NOW) is None


# Дни недели
@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("в пятницу", utc(2026, 9, 25)),  # сегодня 09:00 уже прошло
        ("в понедельник", utc(2026, 9, 21)),
        ("в понедельник в 15", utc(2026, 9, 21, 12)),
        ("в субботу", utc(2026, 9, 19)),
        ("в воскресенье", utc(2026, 9, 20)),
    ],
)
def test_weekdays(phrase, expected):
    assert parse_due(phrase, NOW) == expected


# Общие проверки
def test_naive_now_raises():
    with pytest.raises(ValueError):
        parse_due("через 5 минут", datetime(2026, 9, 18, 10, 0))


@pytest.mark.parametrize("phrase", ["", "   ", "напомни что-нибудь"])
def test_no_time_expression(phrase):
    assert parse_due(phrase, NOW) is None
