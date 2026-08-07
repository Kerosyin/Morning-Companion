# API / Архитектура

*Версия 0.1.0 — актуально для текущей реализации.*

## Общая структура

```
app/
├── main.py                  # Точка входа, парсинг аргументов, запуск
├── config.py                # Конфигурация из .env (pydantic-settings)
├── logger.py                # Настройка логирования
├── core/
│   └── application.py       # Сборка приложения, планировщик, цикл поллинга
├── telegram/
│   ├── bot.py               # Создание Bot (с поддержкой прокси)
│   ├── dispatcher.py        # Сборка Dispatcher и middleware
│   ├── handlers.py          # Обработчики сообщений (/start, /stats, диалог)
│   ├── callback_handlers.py # Callback-кнопки (опрос самочувствия)
│   ├── health_poll.py       # Клавиатура опроса 1-5
│   ├── filters.py           # Пользовательские фильтры
│   └── middleware/          # AccessMiddleware, UoWMiddleware
├── ai/
│   ├── provider.py          # Интерфейс AIProvider
│   ├── openrouter.py        # Реализация провайдера OpenRouter
│   ├── critical_event_detector.py  # Детектор критичных событий
│   ├── memory_extractor.py  # Извлечение долговременных фактов
│   ├── models.py            # AIResponse, ConversationContext
│   └── builders/            # Формирование контекста/истории/памяти
├── services/                # Сервисы бизнес-логики
│   ├── dialog_service.py    # Обработка сообщения пользователя
│   ├── critical_event_service.py  # Дедупликация и сигнал админу
│   ├── health_check_service.py    # Статистика самочувствия
│   ├── conversation_service.py
│   ├── history_service.py
│   └── morning_service.py
├── repositories/            # Доступ к данным (Repository Pattern)
├── db/
│   ├── base.py, engine.py, session.py, init_db.py
│   ├── uow.py               # Unit of Work
│   └── models/              # User, Message, Memory, DailyActivity,
│                            #   CriticalEvent, HealthCheckin
├── scheduler/               # APScheduler: MorningJob, AdminJob
├── workflows/               # MorningWorkflow, AdminWorkflow
└── reminders/               # Провайдер текстов напоминаний
alembic/                     # Миграции БД (Alembic)
    ├── env.py               # Привязка к моделям и async-движку
    ├── alembic.ini          # Конфигурация Alembic
    └── versions/            # Миграции (initial schema)
```

## Конфигурация (`app/config.py`)

Настройки читаются из файла `.env` (см. `.env.example`):

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен Telegram-бота |
| `ADMIN_ID` | Telegram ID администратора |
| `OPENROUTER_API_KEY` | Ключ API OpenRouter |
| `AI_PROVIDER` | Провайдер ИИ (по умолчанию `openrouter`) |
| `MODEL` | Модель OpenRouter (например `openrouter/free`) |
| `TIMEZONE` | Часовой пояс (по умолчанию `Europe/Moscow`) |
| `DATABASE_URL` | DSN базы данных (по умолчанию SQLite) |
| `ALLOWED_USERS` | Список Telegram ID, которым разрешён доступ (через запятую) |
| `PROXY` | Прокси для Telegram/OpenRouter (пусто — без прокси) |
| `CRITICAL_ALERT_ENABLED` | Включить уведомления о критичных событиях (по умолч. `true`) |
| `CRITICAL_ALERT_MIN_SEVERITY` | Мин. уровень тревоги для уведомления: `low`, `high`, `critical` |
| `CRITICAL_ALERT_COOLDOWN_MINUTES` | Пауза между уведомлениями одного пользователя (по умолч. `120`) |

## Телеграм-слой

- `handlers.py`: `/start`, `/stats` и обработка всех сообщений через `DialogService`.
- `callback_handlers.py`: обрабатывает нажатие кнопок опроса самочувствия.
- `health_poll.py`: inline-кнопки 1–5 для ежедневного чекина.
- `middleware/access.py`: пропускает только пользователей из `ALLOWED_USERS`.
- `middleware/uow.py`: инжектирует `UnitOfWork` в контекст.
- `bot.py`: при наличии `PROXY` создаёт `AiohttpSession` с прокси.
- Callback-запросы имеют собственные `AccessMiddleware`/`UoWMiddleware`
  (зарегистрированы в `dispatcher.py`).

## AI-слой

- `OpenRouterProvider` реализует `AIProvider` (`chat`, `simple_chat`).
- Запросы идут через прокси (если задан), с ретраями при `429`/`5xx`/сбоях сети.
- `critical_event_detector.py` классифицирует критичные сообщения: быстрый
  keyword-гейт по категориям (здоровье, пожар, затопление, криминал, ЧП) +
  LLM-проход для неоднозначных сигналов.
- `app/container.py` — лёгкий DI-контейнер: собирает граф зависимостей,
  позволяет подменить провайдера (например, в тестах) через `set_provider`/`reset_container`.

## Слой данных

- SQLAlchemy 2.0 + async (aiosqlite).
- Сущности: `User`, `Message`, `Memory`, `DailyActivity`, `CriticalEvent`,
  `HealthCheckin`.
- Доступ через репозитории (`app/repositories`) и `UnitOfWork` (`app/db/uow.py`).
- Схема БД управляется **Alembic**: `alembic/versions/*.py`. Миграции применяются
  автоматически при каждом запуске бота через `init_db()`.

## Расписание и воркфлоу

- `scheduler/` использует APScheduler с интервалом 1 минута.
- `MorningWorkflow` отправляет напоминания пользователям, не ответившим сегодня,
  и вместе с первым — опрос самочувствия (кнопки 1–5).
- `AdminWorkflow` уведомляет администратора о неактивных пользователях (после 12:00).
- При критичном сообщении пользователя `handlers.py` сразу пишет админу
  (категория, уровень, ссылка на пользователя).

## Запуск

```bash
uv run python -m app.main            # запуск бота (миграции применяются автоматически)
uv run python -m app.main --init-db  # применить миграции и выйти
# или вручную:
uv run alembic upgrade head          # применить миграции до последней
uv run alembic revision --autogenerate -m "описание"  # создать новую миграцию по моделям
```

Тесты: `uv run pytest` (только БД-слой, без сети).