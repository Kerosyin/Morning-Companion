import sqlite3
from pathlib import Path

from alembic.config import Config

from alembic import command
from app.config import get_settings


def test_existing_admin_outbox_rows_gain_subject_user_id(tmp_path, monkeypatch):
    database = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database.as_posix()}")
    get_settings.cache_clear()
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    try:
        command.upgrade(config, "d4e5f6071829")
        with sqlite3.connect(database) as connection:
            connection.execute(
                "INSERT INTO notification_outbox "
                "(kind, dedupe_key, chat_id, text) VALUES (?, ?, ?, ?)",
                ("admin_inactive_user", "2026-09-29:42", 900, "old row"),
            )
        command.upgrade(config, "head")
        with sqlite3.connect(database) as connection:
            subject_id = connection.execute(
                "SELECT subject_user_id FROM notification_outbox "
                "WHERE text = 'old row'"
            ).fetchone()[0]
        assert subject_id == 42
    finally:
        get_settings.cache_clear()
