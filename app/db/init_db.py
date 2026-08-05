import asyncio
from pathlib import Path

from alembic.config import Config

from alembic import command
from app.config import get_settings


async def init_db():
    """Applies all Alembic migrations to bring the database schema up to date."""
    root = Path(__file__).resolve().parents[2]

    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)

    await asyncio.to_thread(command.upgrade, config, "head")
    print("Database migrations applied.")


if __name__ == "__main__":
    asyncio.run(init_db())
