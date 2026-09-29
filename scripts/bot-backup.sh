#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/morning-companion}"
PYTHON_BIN="${PYTHON_BIN:-$APP_DIR/.venv/bin/python}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
ARCHIVE="$BACKUP_DIR/morning-companion-$TIMESTAMP.tar.gz"
STAGING_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "$STAGING_DIR"
    rm -f "$ARCHIVE.partial"
}
trap cleanup EXIT

mkdir -p "$BACKUP_DIR" "$STAGING_DIR/project/data"

tar \
    --exclude='./.git' \
    --exclude='./.venv' \
    --exclude='./.pytest_cache' \
    --exclude='./.ruff_cache' \
    --exclude='./__pycache__' \
    --exclude='./morning_companion.egg-info' \
    --exclude='./data' \
    --exclude='./secret' \
    -C "$APP_DIR" -cf - . | tar -C "$STAGING_DIR/project" -xf -

"$PYTHON_BIN" - "$APP_DIR/data/morning_companion.db" \
    "$STAGING_DIR/project/data/morning_companion.db" <<'PY'
import sqlite3
import sys

source = sqlite3.connect(sys.argv[1])
destination = sqlite3.connect(sys.argv[2])
try:
    source.backup(destination)
finally:
    destination.close()
    source.close()
PY

tar -C "$STAGING_DIR" -czf "$ARCHIVE.partial" project
"$PYTHON_BIN" "$APP_DIR/scripts/verify_backup.py" "$ARCHIVE.partial"
mv "$ARCHIVE.partial" "$ARCHIVE"
chmod 600 "$ARCHIVE"

mapfile -t outdated_archives < <(
    find "$BACKUP_DIR" -maxdepth 1 -type f -name 'morning-companion-*.tar.gz' \
        -printf '%T@ %p\n' | sort -rn | tail -n +4 | cut -d' ' -f2-
)
if ((${#outdated_archives[@]})); then
    rm -f -- "${outdated_archives[@]}"
fi

printf 'Created %s\n' "$ARCHIVE"
