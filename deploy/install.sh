#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[install] Устанавливаю python3, git, uv..."
apt update
apt install -y python3 python3-venv git
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "[install] Устанавливаю файл службы..."
sed "s|/opt/Morning-Companion|$APP_DIR|g" "$APP_DIR/deploy/morning-companion.service" > /etc/systemd/system/morning-companion.service
systemctl daemon-reload

echo "[install] Копирую .env.example -> .env (заполните токены!)"
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
fi

echo "[install] Ставлю зависимости проекта..."
cd "$APP_DIR"
uv sync

echo "[install] Делаю скрипты исполняемыми..."
chmod +x "$APP_DIR/scripts/"*.sh

echo "[install] Включаю автозапуск..."
systemctl enable morning-companion

echo
echo "[install] Готово."
echo "  1) Отредактируйте $APP_DIR/.env"
echo "  2) Запустите:  $APP_DIR/scripts/bot-start.sh"
echo "  3) Логи:       $APP_DIR/scripts/bot-watch.sh"