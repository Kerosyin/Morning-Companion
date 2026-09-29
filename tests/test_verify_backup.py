import io
import sqlite3
import tarfile

import pytest

from scripts.verify_backup import verify_archive


def make_archive(path, database_bytes, *, include_env=True):
    files = {
        "project/app/main.py": b"# app\n",
        "project/alembic.ini": b"[alembic]\n",
        "project/data/morning_companion.db": database_bytes,
    }
    if include_env:
        files["project/.env"] = b"BOT_TOKEN=test\n"
    with tarfile.open(path, "w:gz") as archive:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))


def test_verify_backup_accepts_valid_sqlite_archive(tmp_path):
    database = tmp_path / "source.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    archive = tmp_path / "backup.tar.gz"
    make_archive(archive, database.read_bytes())

    verify_archive(archive, check_migrations=False)


def test_verify_backup_rejects_archive_without_env(tmp_path):
    archive = tmp_path / "backup.tar.gz"
    make_archive(archive, b"not a database", include_env=False)

    with pytest.raises(ValueError, match="project/.env"):
        verify_archive(archive, check_migrations=False)


def test_verify_backup_rejects_corrupt_database(tmp_path):
    archive = tmp_path / "backup.tar.gz"
    make_archive(archive, b"not a database")

    with pytest.raises(ValueError, match="SQLite"):
        verify_archive(archive, check_migrations=False)
