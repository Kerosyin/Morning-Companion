import asyncio
import argparse

from app.config import get_settings
from app.core.application import Application
from app.db.init_db import init_db


async def main():
    parser = argparse.ArgumentParser(description="Morning Companion Bot")
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize the database tables.",
    )
    args = parser.parse_args()

    if args.init_db:
        await init_db()
        return

    settings = get_settings()
    app = Application(settings)
    await app.start()


if __name__ == "__main__":
    asyncio.run(main())
