# Morning Companion Roadmap

Статус: **MVP в активной разработке.** Пункты Sprint 1–4 реализованы,
Sprint 5 (Memory, Daily summary) — дорожная карта на будущее.

## Sprint 1 — Bootstrap

- [x] Bootstrap — точка входа `app/main.py`, сборка в `app/core`
- [x] Config — `app/config.py` (.env через pydantic-settings)
- [x] Logging — `app/logger.py`
- [x] Telegram — `app/telegram` (bot, dispatcher, handlers, middleware)

## Sprint 2 — Database

- [x] Database — SQLAlchemy 2.0 async (SQLite)
- [x] SQLAlchemy — модели, engine, session
- [x] Repositories — `app/repositories` (Repository Pattern)
- [x] Unit of Work — `app/db/uow.py`

## Sprint 3 — AI Provider

- [x] AI Provider — интерфейс `AIProvider`
- [x] OpenRouter — `OpenRouterProvider` (chat, simple_chat, ретраи)
- [x] Conversation history — сохранение и чтение истории диалогов
- [x] Прокси для OpenRouter/Telegram

## Sprint 4 — Scheduler

- [x] Scheduler — APScheduler (`app/scheduler`)
- [x] Morning reminders — `MorningWorkflow` + `ReminderProvider`
- [x] Admin notifications — `AdminWorkflow` (уведомление после 12:00)

## Sprint 5 — Memory

- [~] Memory — чтение/использование памяти в контексте реализовано; автозаполнение (`MemoryService`/`MemoryExtractor`) не подключено
- [ ] Daily summary — ежедневная сводка диалога

## Идеи на следующие версии

- Voice — голосовые сообщения
- Web panel — веб-панель