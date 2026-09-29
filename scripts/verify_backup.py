"""Validate an application backup without touching the live database."""

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from contextlib import closing
from pathlib import Path

REQUIRED_FILES = (
    "project/.env",
    "project/alembic.ini",
    "project/app/main.py",
    "project/data/morning_companion.db",
)


def verify_archive(archive_path: Path, *, check_migrations: bool = True) -> None:
    with tempfile.TemporaryDirectory(prefix="morning-backup-check-") as directory:
        database = Path(directory) / "morning_companion.db"
        with tarfile.open(archive_path, "r:gz") as archive:
            for name in REQUIRED_FILES:
                try:
                    member = archive.getmember(name)
                except KeyError as exc:
                    raise ValueError(f"Backup is missing {name}") from exc
                if not member.isfile():
                    raise ValueError(f"Backup entry is not a file: {name}")
            source = archive.extractfile("project/data/morning_companion.db")
            if source is None:
                raise ValueError("Backup SQLite database cannot be read")
            with source, database.open("wb") as destination:
                shutil.copyfileobj(source, destination)

        try:
            with closing(sqlite3.connect(database)) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()[0]
                has_users = connection.execute(
                    "SELECT 1 FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'users'"
                ).fetchone()
            if result != "ok" or has_users is None:
                raise ValueError("Backup SQLite database failed validation")
        except sqlite3.DatabaseError as exc:
            raise ValueError("Backup SQLite database is invalid") from exc

        if check_migrations:
            environment = os.environ.copy()
            environment["DATABASE_URL"] = (
                f"sqlite+aiosqlite:///{database.as_posix()}"
            )
            result = subprocess.run(
                [sys.executable, "-m", "app.main", "--init-db"],
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Backup migration check failed (exit {result.returncode})"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    arguments = parser.parse_args()
    verify_archive(arguments.archive)
    print(f"Backup verified: {arguments.archive}")
