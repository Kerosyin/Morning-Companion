#!/usr/bin/env bash
set -euo pipefail

SERVICE="morning-companion"

usage() {
    echo "Usage: bot.sh {start|stop|restart|status|logs|watch|version|update|deploy|doctor}"
    echo
    echo "  start     Запустить бота (systemd)"
    echo "  stop      Остановить бота"
    echo "  restart   Перезапустить бота"
    echo "  status    Статус службы"
    echo "  logs [N]  Последние N строк логов (по умолчанию 50)"
    echo "  watch     Живой просмотр логов (tail -f)"
    echo "  version   Текущая версия"
    echo "  update    Обновить код с GitHub (git pull + uv sync + restart)"
    echo "  deploy    Деплой: pull + установка службы + restart + статус + логи"
    echo "  doctor    Диагностика: окружение, .env, БД, служба, диск, память"
}

get_version() {
    sed -n 's/^version\s*=\s*"\([^"]*\)"/\1/p' "$(dirname "$0")/../pyproject.toml" | head -n 1
}

project_root() {
    cd "$(dirname "$0")/.." && pwd
}

case "${1:-}" in
    start)
        echo "[start] Запускаю службу $SERVICE..."
        sudo systemctl start "$SERVICE"
        sudo systemctl status "$SERVICE" --no-pager
        ;;
    stop)
        echo "[stop] Останавливаю службу $SERVICE..."
        sudo systemctl stop "$SERVICE"
        sudo systemctl status "$SERVICE" --no-pager || true
        ;;
    restart)
        echo "[restart] Перезапуск $SERVICE..."
        sudo systemctl restart "$SERVICE"
        sudo systemctl status "$SERVICE" --no-pager
        ;;
    status)
        sudo systemctl status "$SERVICE" --no-pager
        ;;
    logs)
        journalctl -u "$SERVICE" -n "${2:-50}" --no-pager
        ;;
    watch)
        echo "[watch] Слежу за логами. Для выхода нажмите Ctrl+C."
        journalctl -u "$SERVICE" -f
        ;;
    version)
        v="$(get_version)"
        if [ -n "$v" ]; then
            echo "[version] $v"
        else
            echo "[version] Версия не найдена в pyproject.toml"
            exit 1
        fi
        ;;
    update)
        ROOT="$(project_root)"
        echo "[update] Обновляю код из репозитория..."
        git -C "$ROOT" pull
        echo "[update] Обновляю зависимости..."
        cd "$ROOT"
        uv sync
        echo "[update] Перезапускаю службу..."
        sudo systemctl restart "$SERVICE"
        sudo systemctl status "$SERVICE" --no-pager
        ;;
    deploy)
        ROOT="$(project_root)"
        echo "[deploy] Обновляю код из репозитория..."
        git -C "$ROOT" pull
        echo "[deploy] Устанавливаю окружение и службу..."
        bash "$ROOT/deploy/install.sh"
        echo "[deploy] Перезапускаю службу..."
        sudo systemctl restart "$SERVICE"
        sudo systemctl status "$SERVICE" --no-pager
        echo "[deploy] Последние строки логов:"
        journalctl -u "$SERVICE" -n 20 --no-pager
        ;;
    doctor)
        echo "[doctor] Проверяю окружение..."
        for cmd in git uv python3; do
            if command -v "$cmd" >/dev/null 2>&1; then
                echo "  OK   $cmd: $($cmd --version 2>&1 | head -n 1)"
            else
                echo "  FAIL $cmd: не установлен"
            fi
        done

        ROOT="$(project_root)"
        echo "[doctor] Проверяю файл .env..."
        if [ -f "$ROOT/.env" ]; then
            echo "  OK   .env существует"
            for key in BOT_TOKEN ADMIN_ID OPENROUTER_API_KEY; do
                val=$(grep -E "^$key=" "$ROOT/.env" | head -n 1 | cut -d= -f2-)
                if [ -n "$val" ] && [ "$val" != "0" ]; then
                    echo "  OK   $key заполнен"
                else
                    echo "  FAIL $key пуст — заполните в .env"
                fi
            done
        else
            echo "  FAIL .env отсутствует — скопируйте .env.example"
        fi

        echo "[doctor] Проверяю службу..."
        if systemctl list-unit-files | grep -q "^$SERVICE"; then
            echo "  OK   служба $SERVICE зарегистрирована"
            systemctl is-active --quiet "$SERVICE" \
                && echo "  OK   служба запущена" \
                || echo "  WARN служба не запущена (bot-start.sh)"
        else
            echo "  FAIL служба $SERVICE не зарегистрирована — запустите bot-deploy.sh"
        fi

        echo "[doctor] Проверяю зависимости (uv sync)..."
        if cd "$ROOT" && uv sync --frozen >/dev/null 2>&1; then
            echo "  OK   зависимости на месте"
        else
            echo "  WARN зависимости не синхронизированы — запустите bot-update.sh"
        fi

        echo "[doctor] Проверяю базу данных..."
        DB_FILE="$ROOT/data/morning_companion.db"
        if [ -f "$DB_FILE" ]; then
            SIZE=$(du -h "$DB_FILE" | cut -f1)
            echo "  OK   БД существует ($SIZE)"
            if command -v sqlite3 >/dev/null 2>&1; then
                if sqlite3 "$DB_FILE" "PRAGMA quick_check;" >/dev/null 2>&1; then
                    echo "  OK   БД целостность в порядке"
                else
                    echo "  FAIL БД повреждена"
                fi
            fi
        else
            echo "  WARN БД ещё не создана (создастся при первом запуске)"
        fi

        echo "[doctor] Проверяю диск и память..."
        df -h "$ROOT" | tail -n 1 | awk '{print "  DISK "$1" всего: "$2", занято: "$3", свободно: "$4" ("$5")"}'
        free -h | awk '/Mem:/{print "  RAM всего: "$2", свободно: "$4" ("$3" занято)"}'

        echo "[doctor] Последние ошибки из журнала..."
        ERRORS=$(journalctl -u "$SERVICE" -p err --since "24 hours ago" --no-pager 2>/dev/null | tail -n 10)
        if [ -n "$ERRORS" ]; then
            echo "$ERRORS" | sed 's/^/  /'
        else
            echo "  OK   ошибок за последние 24 часа нет"
        fi
        ;;
    *)
        usage
        exit 1
        ;;
esac
