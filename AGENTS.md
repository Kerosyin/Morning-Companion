# AGENTS.md

Morning Companion is an async Python (3.12+, uv) Telegram AI companion: daily AI dialogues, auto-memory of user facts, scheduled morning reminders (APScheduler), admin notification for inactive users, and message cleanup.

## Commands (use `uv run`)

```bash
uv sync               # install deps (incl. dev group: pytest, ruff)
uv run pytest          # run tests
uv run pytest tests/test_dialog_service.py -k test_name   # single test
uv run ruff check app/ tests/
uv run python -m app.main --init-db   # apply migrations, then exit
uv run python -m app.main             # run the bot
uv run alembic revision --autogenerate -m "desc"
uv run alembic upgrade head
```

- Lint and tests both run in CI on push to `main`/PR: `ruff check app/` then `pytest -q`.
- Formatter: `black` (88 cols) and `ruff` (88 cols, rules `E,F,I,W`) are both configured; keep lines ≤ 88.
- ruff is not a formatter here (`ruff format` is not in CI) — matches the current `black` style used in the repo.

## Config (gotchas)

- All settings come from `.env` via `app/config.py`. Fields use **uppercase aliases** matching env names (`BOT_TOKEN`, `ADMIN_ID`, `MODEL`, `OPENROUTER_API_KEY`, `DATABASE_URL`, `ALLOWED_USERS`, ...). Use the alias names when adding/reading config.
- `.env` is required to run the app (`BOT_TOKEN`, `ADMIN_ID`, `MODEL`, `OPENROUTER_API_KEY`, `DATABASE_URL` have no defaults). Copy `.env.example`.
- `ALLOWED_USERS` is a comma-separated string of ints; the pydantic validator splits it. Leave empty to block everyone.
- `get_settings()` is `@lru_cache`d — a single process uses one settings snapshot.

## Database & migrations

- Async SQLAlchemy 2.0 + aiosqlite. SQLite engine sets WAL, busy_timeout, `synchronous=NORMAL`, `foreign_keys=ON` (see `app/db/engine.py`).
- Alembic `env.py` is async; it injects the URL from settings and imports `app.db.models` so all tables register on `Base.metadata` (needed for `--autogenerate`).
- Migrations are applied automatically on bot startup; `--init-db` runs the same and exits.
- Schema changes -> commit an Alembic migration, don't just edit models.

## Architecture (layered: services orchestrate, workflows run jobs)

```
app/telegram/    aiogram handlers/middleware (access gate, UoW injection)
app/services/    business logic (dialog, morning, memory, history, reminder_generation, critical_event)
app/workflows/   scheduled/admin/cleanup jobs
app/repositories/ + app/db/uow.py   data access; UnitOfWork exposes .users/.messages/.memories/.daily_activity/.critical_events
app/ai/          AI provider interface, OpenRouter impl, prompt/history/memory builders
app/scheduler/   APScheduler job registration
app/container.py lightweight DI container; swappable AI provider (swap via set_provider in tests)
```

- Critical-event alerts: `DialogService` runs a `CriticalEventService` (best-effort, never breaks the reply) after each message. `CriticalEventDetector` uses per-category keyword gates (health, fire, flood, crime, accident) plus an LLM pass for weak signals; `CriticalEventService` dedups by cooldown (with escalation) and returns the event to `handlers.py`, which pings the admin. Settings: `CRITICAL_ALERT_*`.
- Daily health check: `MorningWorkflow` sends an inline 1-5 rating poll (see `app/telegram/health_poll.py`) on the first reminder; tap is handled by `app/telegram/callback_handlers.py` and stored in `health_checkins` (one per user/day via unique `date+user_id`). `/stats` shows the emoji-bar trend; the admin can pass a `telegram_id`. Callback queries have their own UoW/Access middleware registered in `dispatcher.py`.

- Follow the existing three layers (handler/service or workflow/repository) when adding features. `Container` is a module-level singleton with `get_container()` / `reset_container()` (the latter used in tests).
- New models must be imported through `app.db.models` (each model also has its own `__init__` in `app/db/models/`) so Alembic sees them.

## Tests specifics

- Pytest configured with `asyncio_mode = "auto"` and `pythonpath = ["."]` — async tests run without explicit markers (some files still add `pytest.mark.asyncio`; harmless either way).
- Tests use an **in-memory SQLite** engine (see `tests/conftest.py`) and real `UnitOfWork` repos per test function. They never touch the on-disk `data/morning_companion.db`.
- Service-level tests use hand-rolled mocks (e.g. `test_morning_service.py`); don't introduce a mocking framework unless needed.
- CI runs on Linux; keep tests platform-independent (no `windows `-specific assumptions).

## Ops / deployment

- `scripts/bot-*.bat`/`bot.ps1` for Windows run-and-log management; `scripts/bot-*.sh` + systemd for the VPS. `deploy/morning-companion.service` is the systemd unit created by `deploy/install.sh`.
- Release flow (Windows) `scripts/bot-release.bat` bumps the version in `pyproject.toml`, tags, and creates a GitHub release. `bot-update.sh`/`bot-deploy.sh` do `git pull` + `uv sync` + restart on the server.
- The repo's actual runtime DB (`data/*.db*`) and logs live under `data/` and are local runtime artifacts, not part of source control.