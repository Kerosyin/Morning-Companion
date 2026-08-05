import asyncio
import argparse

from app.config import get_settings
from app.core.application import Application
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.db.uow import UnitOfWork
from app.telegram.bot import create_bot
from app.telegram.dispatcher import create_dispatcher


def uow_factory():
    return UnitOfWork(SessionLocal)


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
    bot = create_bot(settings)
    dispatcher = create_dispatcher()
    app = Application(
        bot=bot,
        dispatcher=dispatcher,
        uow_factory=uow_factory,
        admin_id=settings.admin_id,
    )
    await app.start()


if __name__ == "__main__":
    asyncio.run(main())