from datetime import datetime
from zoneinfo import ZoneInfo
from app.parsing.time_parser import parse_due

NOW = datetime(2026, 9, 18, 10, 0, tzinfo=ZoneInfo("Europe/Moscow"))


def test_in_7_days():
    assert parse_due("через 7 дней", NOW) == NOW.replace(day=25)  # 25.09 10:00 MSK


def test_in_2_weeks():
    from datetime import timedelta

    assert parse_due("через 2 недели", NOW) == NOW + timedelta(days=14)


def test_in_a_week_word():
    from datetime import timedelta

    assert parse_due("через неделю", NOW) == NOW + timedelta(days=7)


def test_in_a_couple_hours_none():
    assert parse_due("через пару часов", NOW) is None


def test_tomorrow_at_9_after_10_am():
    # now = 18.09 10:00 MSK → "завтра в 9" = 19.09 09:00 MSK = 06:00 UTC
    from datetime import timezone

    assert parse_due("завтра в 9", NOW) == datetime(
        2026, 9, 19, 6, 0, tzinfo=timezone.utc
    )


def test_at_9_30_already_passed():
    # now = 10:00, "в 9:30" прошло → завтра 9:30 MSK = 19.09 06:30 UTC
    from datetime import timezone

    assert parse_due("в 9:30", NOW) == datetime(2026, 9, 19, 6, 30, tzinfo=timezone.utc)


def test_naive_now_raises():
    import pytest

    with pytest.raises(ValueError):
        parse_due("через 5 минут", datetime(2026, 9, 18, 10, 0))
