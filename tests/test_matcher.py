from app.triggers.matcher import is_reminder


def test_trigger_reminder():
    assert is_reminder("напомни через 10 минут") is True


def test_not_reminder():
    assert is_reminder("#работа просто заметка") is False


def test_null_str():
    assert is_reminder("") is False
