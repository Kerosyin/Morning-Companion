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
- Утренний чекин самочувствия: кнопки 1–5, статистика по команде `/stats`
- Критичные события: уведомление админа о здоровье, пожаре, затоплении,
  криминале и ЧП (детектор по ключевым словам + ИИ, cooldown с эскалацией)
- Автоочистка истории сообщений (`MESSAGE_RETENTION_DAYS`, по умолчанию 365)
- Миграции БД через Alembic (применяются автоматически при запуске)
- Постоянный список доступа: администратор добавляет и отзывает ID командами
  `/allow`, `/deny` и `/allowed`, без перезапуска бота
- Полное удаление пользователя и его данных с двойным подтверждением
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

### Управление доступом и данными

Команды управления доступны только в личном чате администратора:

| Команда | Действие |
| --- | --- |
| `/allow <telegram_id>` | выдать пользователю доступ сразу, без перезапуска |
| `/deny <telegram_id>` | отозвать доступ, сохранив данные пользователя |
| `/allowed` | показать выданные доступы |
| `/delete_user <telegram_id>` | начать полное удаление пользователя и его данных |
| `/confirm_delete <telegram_id>` | подтвердить удаление в течение 5 минут |

Удаление очищает рабочую базу: доступ, диалоги, память, активности,
чекины самочувствия, критичные события и связанные уведомления.
Ранее созданные архивы могут содержать эти данные до замены при ротации.
При необходимости немедленного удаления из резервных копий старые архивы
нужно удалить отдельно на VPS и на компьютере.

### Резервные копии

`scripts/bot-backup.sh` создаёт на VPS консистентную копию приложения, `.env`
и SQLite-базы. Файлы сохраняются в
`/home/bigbrick/backups/morning-companion`; systemd timer запускает задачу раз
в неделю и хранит три последних архива. На Windows
`scripts/fetch-vps-backup.ps1` забирает свежую копию в
`secret/vps-backups`, также оставляя три последних файла.
Перед сохранением сервер проверяет архив, целостность базы и возможность
применить миграции к её временной копии. Существующий архив можно проверить
вручную командой `uv run python scripts/verify_backup.py <путь-к-архиву>`.

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
