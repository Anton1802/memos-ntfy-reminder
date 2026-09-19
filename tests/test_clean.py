from app.parsing.clean import clean_reminder_text


def test_trigger_and_time_kept():
    assert clean_reminder_text("напомни позвонить маме через 15 минут") == (
        "позвонить маме через 15 минут"
    )


def test_tag_removed():
    assert clean_reminder_text("напомни купить хлеб #быт") == "купить хлеб"


def test_only_trigger_gives_empty():
    assert clean_reminder_text("напомни") == ""


def test_empty_string():
    assert clean_reminder_text("") == ""


def test_uppercase_trigger():
    assert clean_reminder_text("Напомни полить цветы") == "полить цветы"


def test_multiple_tags_and_newlines():
    text = "напомни\nсделать зарядку #утро #здоровье\nчерез час"
    assert clean_reminder_text(text) == "сделать зарядку через час"


def test_yo_normalization_in_trigger():
    # «ё» в триггере → вырезаем как «напомни»
    assert clean_reminder_text("напомни позвонить") == "позвонить"


def test_yo_kept_in_rest():
    # «ё» в остатке не трогаем
    assert clean_reminder_text("напомни позвонить Лёше") == "позвонить Лёше"


def test_custom_phrases():
    assert clean_reminder_text("ping купить хлеб", phrases=["ping"]) == "купить хлеб"


def test_no_trigger_returns_original_trimmed():
    assert clean_reminder_text("  просто заметка  ") == "просто заметка"
