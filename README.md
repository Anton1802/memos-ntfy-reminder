# memos-ntfy-reminder

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Сервис, который превращает заметки в [Memos](https://usememos.com/) в напоминания с пуш-уведомлениями через [ntfy](https://ntfy.sh/).

Написал заметку `напомни купить хлеб через 15 минут` — получил пуш через 15 минут, а заметка ушла в архив.

---

## Возможности

- 📝 **Триггеры в заметках** — ищет фразы `напомни`, `напоминание` (настраивается), регистронезависимо.
- ⏰ **Парсинг времени на естественном языке:**
  - `через 15 минут`, `через 2 часа`, `через неделю`
  - `завтра в 9`, `послезавтра в 15:30`
  - `в 18:00`, `к 18:00`, `18.00`, `18:00` (без предлога)
  - `20 сентября`, `20.09.2026`, `в пятницу`
  - `утром`, `вечером`, `в обед`, `ночью`, `завтра утром`
  - `полчаса`, `полтора часа`, `сутки`
- 🔔 **Пуши через ntfy** — JSON-режим с топиком, приоритетом и тегами.
- 🗄️ **Состояние в SQLite** — WAL, дедупликация по `memo_id`.
- 📦 **Архивация заметки в Memos** после успешной отправки пуша.
- ❌ **Отмена напоминания** — если заметку удалили или заархивировали вручную до наступления `due`, пуш не отправится.
- 🐳 **Docker Compose** — запуск одной командой.

## Как это работает

```
┌──────────────┐   HTTP    ┌────────┐
│   poller     │ ────────► │ Memos  │
│ (раз в 30с)  │           └────────┘
└──────┬───────┘
       │ пишет reminders, processed
       ▼
   ┌────────┐
   │ SQLite │
   └────┬───┘
        │ читает due
        ▼
┌──────────────┐   HTTP    ┌────────┐
│   worker     │ ────────► │  ntfy  │
│ (раз в 30с)  │           └────────┘
└──────────────┘
```

Два независимых потока в одном процессе:

| Поток | Что делает | Интервал |
|-------|-----------|----------|
| **Poller** | Опрашивает Memos, находит новые заметки с триггерами, парсит время, кладёт в SQLite | `POLL_INTERVAL` (30 сек) |
| **Worker** | Смотрит в SQLite, отправляет назревшие напоминания в ntfy, архивирует заметку | `WORKER_INTERVAL` (30 сек) |

## Быстрый старт

### Docker (рекомендуется)

```bash
git clone https://github.com/<your>/memos-ntfy-reminder.git
cd memos-ntfy-reminder

cp .env.example .env
# отредактируй .env — минимум MEMOS_URL, MEMOS_TOKEN, NTFY_URL, NTFY_TOPIC

docker compose up -d --build
docker compose logs -f
```

Остановить:

```bash
docker compose down
```

Данные (SQLite) живут в Docker volume `memos-data` и сохраняются между перезапусками.

### Без Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# отредактируй .env, раскомментируй DB_PATH=data/reminders.db

python3 run.py
```

## Конфигурация

Все настройки — в `.env` (см. `.env.example`).

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `MEMOS_URL` | `http://127.0.0.1:5230` | Базовый URL Memos, без слэша в конце |
| `MEMOS_TOKEN` | — | Access Token из Memos: Настройки → Access Tokens |
| `NTFY_URL` | `https://ntfy.sh` | Базовый URL ntfy, без слэша |
| `NTFY_TOPIC` | — | Топик, куда слать пуши |
| `NTFY_TOKEN` | — | Bearer-токен ntfy, если сервер с авторизацией |
| `TRIGGER_PHRASES` | `напомни,напоминание` | Фразы через запятую, регистронезависимо |
| `TZ` | `Europe/Moscow` | Часовой пояс для парсинга времени |
| `TRIGGER_DEFAULT_MINUTES` | `60` | Fallback, если время не распознано |
| `POLL_INTERVAL` | `30` | Интервал опроса Memos, сек |
| `WORKER_INTERVAL` | `30` | Интервал проверки due, сек |
| `FIRST_RUN_LOOKBACK` | `3600` | При первом запуске не обрабатывать заметки старше N сек |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

`DB_PATH` задаётся в `docker-compose.yml` (`/data/reminders.db`). Для локального запуска — раскомментируй в `.env`.

## Примеры заметок

| Заметка | Когда сработает |
|---------|-----------------|
| `напомни позвонить маме через 15 минут` | через 15 минут |
| `напомни выпить таблетку завтра в 9` | завтра в 09:00 |
| `напомни про встречу в 15:30` | сегодня в 15:30 или завтра, если уже прошло |
| `напомни оплатить счета 20 сентября` | 20 сентября в 09:00 |
| `напомни забрать посылку в пятницу в 18:00` | в ближайшую пятницу в 18:00 |
| `напомни полить цветы вечером` | сегодня в 18:00 |
| `напомни купить хлеб` | через `TRIGGER_DEFAULT_MINUTES` (60 мин) |

## Тесты

```bash
python3 -m pytest -v
```

Тесты покрывают: парсер времени (все категории фраз), матчер триггеров, клинер текста, слой хранилища (SQLite), ntfy-нотификатор, воркер (отправка, отмена, ошибки).

## Просмотр состояния

### Docker

```bash
docker compose exec memos-ntfy-reminder python -c "
import sqlite3
conn = sqlite3.connect('/data/reminders.db')
conn.row_factory = sqlite3.Row
for r in conn.execute('SELECT id, memo_id, status, attempts, datetime(due_at,\"unixepoch\",\"localtime\") AS due FROM reminders ORDER BY id DESC LIMIT 20'):
    print(dict(r))
"
```

### Локально

```bash
sqlite3 data/reminders.db "SELECT id, memo_id, status, attempts, datetime(due_at,'unixepoch','localtime') AS due FROM reminders ORDER BY id DESC LIMIT 20;"
```

Статусы: `pending` → `sent` | `error` | `cancelled`.

## systemd (альтернатива Docker)

`/etc/systemd/system/memos-ntfy-reminder.service`:

```ini
[Unit]
Description=Memos ntfy reminder
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/memos-ntfy-reminder
ExecStart=/opt/memos-ntfy-reminder/.venv/bin/python run.py
Restart=on-failure
RestartSec=10
User=memos

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now memos-ntfy-reminder
sudo journalctl -u memos-ntfy-reminder -f
```

## Стек

- **Python 3.12**
- [`requests`](https://requests.readthedocs.io/) — HTTP к Memos и ntfy
- [`python-dotenv`](https://github.com/theskumar/python-dotenv) — чтение `.env`
- `sqlite3` — хранилище (стандартная библиотека)
- `threading` — два потока (стандартная библиотека)
- `zoneinfo` — часовые пояса (стандартная библиотека)

Сознательно **без** `apscheduler`, `celery`, `redis` — оверкилл для двух потоков и SQLite.

## Структура проекта

```
memos-ntfy-reminder/
├── app/
│   ├── config.py              # чтение .env, setup_logging
│   ├── memos/
│   │   ├── client.py          # list_memos, archive_memo, get_memo
│   │   └── models.py          # Memo dataclass
│   ├── triggers/
│   │   └── matcher.py         # is_reminder
│   ├── parsing/
│   │   ├── normalize.py       # нормализация (casefold, ё→е)
│   │   ├── clean.py           # чистка текста для пуша
│   │   └── time_parser.py     # parse_due
│   ├── store/
│   │   ├── db.py              # соединение, схема
│   │   └── repo.py            # is_processed, add_reminder, fetch_due, ...
│   ├── notifier/
│   │   └── ntfy.py            # send_reminder
│   ├── poller.py              # цикл «Memos → SQLite»
│   └── worker.py              # цикл «SQLite → ntfy → архив»
├── tests/
├── run.py                     # точка входа, два потока, graceful shutdown
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

## Лицензия

MIT