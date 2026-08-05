# Morning Companion

Telegram AI-компаньон: ведёт ежедневные диалоги, запоминает факты о
пользователе, напоминает выйти на связь и уведомляет администратора о
неактивных пользователях.

## Возможности

- Диалоги через ИИ (OpenRouter, `openrouter/free`)
- Автопамять: извлечение и хранение фактов о пользователе
- Утренние напоминания по расписанию (APScheduler)
- Уведомление администратора об неактивных пользователях
- Автоочистка истории сообщений (`MESSAGE_RETENTION_DAYS`, по умолчанию 365)
- Доступ только для whitelist пользователей (`ALLOWED_USERS`)
- Устойчивость: ретраи ИИ, авто-переподключение поллинга, фолбэк при сбое ИИ

## Быстрый старт

Требуется Python 3.12+ и [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Kerosyin/Morning-Companion.git
cd Morning-Companion
cp .env.example .env   # заполните токен бота, ключ OpenRouter и свои ID
uv sync
uv run pytest
scripts/bot-start.bat  # или: uv run python -m app.main
```

Переменные окружения описаны в [`.env.example`](.env.example).

## Управление

Скрипты в `scripts/` (`bot.ps1` и bat-обёртки):

| Команда | Действие |
| --- | --- |
| `bot-start` | запустить бота в фоне |
| `bot-stop` | остановить |
| `bot-restart` | перезапустить |
| `bot-status` | статус процесса |
| `bot-logs` | показать логи |
| `bot-watch` | живой просмотр логов (tail) |
| `bot-version` | текущая версия |
| `bot-bump` | поднять версию в `pyproject.toml` |
| `bot-release` | выпуск: bump + тег + GitHub release |

## Документация

- [Обзор](docs/README.md)
- [API / Архитектура](docs/api.md)
- [Roadmap](docs/roadmap.md)
- [ADR](docs/ADR/ADR-001-architecture.md)

## Разработка

```bash
uv run ruff check app/
uv run pytest
```

## Лицензия

MIT — см. [LICENSE](LICENSE).
