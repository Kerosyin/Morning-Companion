# Morning Companion

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/Kerosyin/Morning-Companion/actions/workflows/ci.yml/badge.svg)](https://github.com/Kerosyin/Morning-Companion/actions)

Telegram AI-компаньон: ведёт ежедневные диалоги, запоминает факты о
пользователе, напоминает выйти на связь и уведомляет администратора о
неактивных пользователях.

## Возможности

- Диалоги через ИИ (OpenRouter, `openrouter/free`)
- Автопамять: извлечение и хранение фактов о пользователе
- Утренние напоминания по расписанию (APScheduler)
- Уведомление администратора об неактивных пользователях
- Автоочистка истории сообщений (`MESSAGE_RETENTION_DAYS`, по умолчанию 365)
- Миграции БД через Alembic (применяются автоматически при запуске)
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

Скрипты в `scripts/`:

**Windows** (`bot.ps1` и bat-обёртки):

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

**Linux (VPS)** (`bot.sh` и `.sh`-обёртки, управление через systemd):

| Команда | Действие |
| --- | --- |
| `bot-start` | запустить службу `morning-companion` |
| `bot-stop` | остановить |
| `bot-restart` | перезапустить |
| `bot-status` | статус службы |
| `bot-logs [N]` | последние N строк логов (по умолчанию 50) |
| `bot-watch` | живой просмотр логов |
| `bot-version` | текущая версия |
| `bot-update` | `git pull` + `uv sync` + restart |
| `bot-deploy` | деплой: pull + установка службы + restart + статус + логи |
| `bot-doctor` | диагностика: окружение, `.env`, БД, служба, диск, память, ошибки |

На сервере сделайте скрипты исполняемыми: `chmod +x scripts/*.sh`.

### Деплой на VPS (Ubuntu)

```bash
git clone https://github.com/Kerosyin/Morning-Companion.git /opt/Morning-Companion
cd /opt/Morning-Companion
sudo bash deploy/install.sh     # установит python/uv, службу systemd и зависимости
nano .env                        # заполните токены
./scripts/bot-start.sh           # запустить бота
```

Файл службы — [`deploy/morning-companion.service`](deploy/morning-companion.service).
Управление — через `scripts/bot-*.sh` (systemd + journalctl).

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

### Миграции БД

```bash
uv run alembic revision --autogenerate -m "описание"  # создать миграцию по моделям
uv run alembic upgrade head                           # применить
```

Миграции применяются автоматически при каждом запуске бота.

## Лицензия

MIT — см. [LICENSE](LICENSE).
