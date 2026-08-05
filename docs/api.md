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
│   ├── handlers.py          # Обработчики сообщений Telegram
│   ├── filters.py           # Пользовательские фильтры
│   └── middleware/          # AccessMiddleware, UoWMiddleware
├── ai/
│   ├── provider.py          # Интерфейс AIProvider
│   ├── openrouter.py        # Реализация провайдера OpenRouter
│   ├── factory.py           # Фабрика-синглтон провайдера
│   ├── prompts.py           # Системные промпты
│   ├── models.py            # AIResponse, ConversationContext
│   └── builders/            # Формирование контекста/истории/памяти
├── services/                # Сервисы бизнес-логики
│   ├── dialog_service.py    # Обработка сообщения пользователя
│   ├── conversation_service.py
│   ├── history_service.py
│   └── morning_service.py
├── repositories/            # Доступ к данным (Repository Pattern)
├── db/
│   ├── base.py, engine.py, session.py, init_db.py
│   ├── uow.py               # Unit of Work
│   └── models/              # User, Message, Memory, DailyActivity
├── scheduler/               # APScheduler: MorningJob, AdminJob
├── workflows/               # MorningWorkflow, AdminWorkflow
└── reminders/               # Провайдер текстов напоминаний
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

## Телеграм-слой

- `handlers.py`: `/start` и обработка всех сообщений через `DialogService`.
- `middleware/access.py`: пропускает только пользователей из `ALLOWED_USERS`.
- `middleware/uow.py`: инжектирует `UnitOfWork` в контекст.
- `bot.py`: при наличии `PROXY` создаёт `AiohttpSession` с прокси.

## AI-слой

- `OpenRouterProvider` реализует `AIProvider` (`chat`, `simple_chat`).
- Запросы идут через прокси (если задан), с ретраями при `429`/`5xx`/сбоях сети.
- `factory.get_ai_provider()` — синглтон, подменяется в тестах.

## Слой данных

- SQLAlchemy 2.0 + async (aiosqlite).
- Сущности: `User`, `Message`, `Memory`, `DailyActivity`.
- Доступ через репозитории (`app/repositories`) и `UnitOfWork` (`app/db/uow.py`).

## Расписание и воркфлоу

- `scheduler/` использует APScheduler с интервалом 1 минута.
- `MorningWorkflow` отправляет напоминания пользователям, не ответившим сегодня.
- `AdminWorkflow` уведомляет администратора о неактивных пользователях (после 12:00).

## Запуск

```bash
uv run python -m app.main            # запуск бота
uv run python -m app.main --init-db  # инициализация БД (создание таблиц)
```

Тесты: `uv run pytest` (только БД-слой, без сети).