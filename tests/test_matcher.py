from app.triggers.matcher import is_reminder


def test_trigger_напомни():
    assert is_reminder("напомни через 10 минут") is True


def test_не_заметка():
    assert is_reminder("#работа просто заметка") is False


def test_пустая_строка():
    assert is_reminder("") is False
