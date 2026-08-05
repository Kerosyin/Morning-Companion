# Morning Companion Roadmap

Статус: **MVP.** Sprint 1–5 реализованы (Memory — частично, без ежедневной
сводки). Осталось: Daily summary и идеи на будущее.

## Sprint 1 — Bootstrap

- [x] Bootstrap — точка входа `app/main.py`, сборка в `app/core`
- [x] Config — `app/config.py` (.env через pydantic-settings)
- [x] Logging — `app/logger.py` (+ UTF-8 для логов)
- [x] Telegram — `app/telegram` (bot, dispatcher, handlers, middleware)
- [x] Управление процессом — `scripts/bot.ps1` (start/stop/restart/status/logs/watch/version/bump)
- [x] Версии сборок — git-теги + релизы GitHub (`v0.1.0`)

## Sprint 2 — Database

- [x] Database — SQLAlchemy 2.0 async (SQLite)
- [x] SQLAlchemy — модели, engine, session
- [x] Repositories — `app/repositories` (Repository Pattern)
- [x] Unit of Work — `app/db/uow.py`
- [x] Политика хранения — автоочистка старых сообщений (`MESSAGE_RETENTION_DAYS`, по умолчанию 365)

## Sprint 3 — AI Provider

- [x] AI Provider — интерфейс `AIProvider`
- [x] OpenRouter — `OpenRouterProvider` (chat, simple_chat, ретраи при 429/5xx/сбоях)
- [x] Conversation history — сохранение и чтение истории диалогов
- [x] Прокси для OpenRouter/Telegram (`PROXY` в `.env`)

## Sprint 4 — Scheduler

- [x] Scheduler — APScheduler (`app/scheduler`)
- [x] Morning reminders — `MorningWorkflow` + `ReminderProvider`
- [x] Admin notifications — `AdminWorkflow` (уведомление после 12:00)
- [x] Очистка БД — `CleanupJob` (ежедневно в 03:00)
- [x] Устойчивый поллинг — авто-переподключение при разрыве соединения

## Sprint 5 — Memory

- [x] Memory — чтение памяти в контексте + автозаполнение через `MemoryExtractor`/`MemoryService`
- [x] Фолбэк при сбое ИИ (дружелюбное сообщение вместо тишины)
- [ ] Daily summary — ежедневная сводка диалога

## Dev

- [x] Тесты — `pytest` + `pytest-asyncio` (БД-слой, `uv run pytest`)
- [x] Линтер — `ruff check`

## Идеи на следующие версии

- Daily summary — ежедневная сводка диалога
- Voice — голосовые сообщения
- Web panel — веб-панель