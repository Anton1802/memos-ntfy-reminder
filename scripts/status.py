import sqlite3
import sys
from contextlib import closing
from collections.abc import Iterable, Sequence
from typing import Any, TextIO

from app.config import DB_PATH

STATUS = frozenset({"pending", "sent", "error", "cancelled"})


SELECT_REMINDERS = """
    SELECT id, memo_id, text, due_at, status, created_at, sent_at, attempts
    FROM reminders
"""


def get_data_from_database(
    db_path: str,
    statuses: Iterable[str],
) -> tuple[list[str], dict[str, list[sqlite3.Row]]]:
    """Загружает напоминания из БД, сгруппированные по статусу.

    ИЗМЕНЕНО: возвращает кортеж (columns, data), где columns — имена
    колонок из SELECT. Так print_table не нужно знать список колонок
    отдельно — он берётся прямо из запроса.

    Args:
        db_path: путь к файлу SQLite.
        statuses: допустимые статусы (ключи результата).

    Returns:
        (columns, {status: [row, row, ...]}).

    Raises:
        sqlite3.Error: при ошибке работы с БД.
        KeyError: если в БД встретился статус вне `statuses`.
    """
    # ИЗМЕНЕНО: statuses теперь Iterable, но внутри нам нужен set для O(1).
    statuses_set = set(statuses)
    result: dict[str, list[sqlite3.Row]] = {s: [] for s in statuses_set}
    columns: list[str] = []

    # ИЗМЕНЕНО: closing(...) вместо простого with.
    #   with sqlite3.connect(...) управляет транзакцией (commit/rollback),
    #   но НЕ закрывает соединение — оно закроется только при GC.
    #   closing гарантирует con.close() даже при исключении.
    with closing(sqlite3.connect(db_path)) as con:
        con.row_factory = sqlite3.Row  # доступ по имени: row["status"]
        cur = con.execute(SELECT_REMINDERS)  # ИЗМЕНЕНО: без отдельного cursor()

        # ИЗМЕНЕНО: берём имена колонок из метаданных результата запроса.
        # cur.description = [(name, type_code, ...), ...] — нам нужен name.
        columns = [d[0] for d in cur.description]

        for row in cur:
            status = row["status"]
            if status not in statuses_set:
                raise KeyError(f"Неизвестный статус в БД: {status!r}")
            result[status].append(row)

    return columns, result


def _format_cell(value: Any) -> str:
    """Приводит значение ячейки к строке для вывода.

    ИЗМЕНЕНО: вынесено отдельно, чтобы None печатался как "-", а не "None".
    """
    return "-" if value is None else str(value)


def print_table(
    data: dict[str, list[Iterable[Any]]],
    *,
    headers: Sequence[str] | None = None,
    sep: str = "  ",
    file: TextIO = sys.stdout,
) -> None:
    """Печатает данные, сгруппированные по статусам.

    Args:
        data: словарь вида {status: [row, row, ...]}.
        headers: названия колонок; если None — заголовок не печатается.
        sep: разделитель между полями в строке.
        file: поток вывода (по умолчанию stdout).

    Raises:
        TypeError: если data не словарь.
        ValueError: если data пуст.
    """
    if not isinstance(data, dict):
        raise TypeError(f"Ожидался dict, получено {type(data).__name__}")
    if not data:
        raise ValueError("Входной словарь пуст")

    for status, rows in data.items():
        if not rows:
            continue

        # ИЗМЕНЕНО: заранее приводим все ячейки к строкам один раз.
        # Раньше str() вызывался в момент печати — теперь ширина
        # считается по уже готовым строкам.
        rows = [[_format_cell(c) for c in row] for row in rows]

        # ИЗМЕНЕНО (главное): ширины колонок считаются как максимум из
        # заголовка И всех ячеек этой колонки. Раньше разделитель рисовался
        # по длине заголовка — из-за этого колонки «плыли».
        if headers is not None:
            widths = [
                max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)
            ]
        else:
            widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]

        print(status.upper(), len(rows), file=file)

        # ИЗМЕНЕНО: заголовки и ячейки печатаются через .ljust(w),
        # чтобы все колонки были выровнены по левому краю.
        if headers is not None:
            print(sep.join(h.ljust(w) for h, w in zip(headers, widths)), file=file)
            print(sep.join("-" * w for w in widths), file=file)

        for row in rows:
            print(sep.join(c.ljust(w) for c, w in zip(row, widths)), file=file)

        print(file=file)


def main() -> int:
    # ИЗМЕНЕНО: main возвращает код выхода (0 — успех), чтобы
    # можно было использовать паттерн sys.exit(main()).
    columns, data = get_data_from_database(db_path=DB_PATH, statuses=STATUS)
    print_table(data, headers=columns)
    return 0


if __name__ == "__main__":
    sys.exit(main())
