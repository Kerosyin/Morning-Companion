import argparse
import asyncio

from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from app.config import get_settings
from app.core.application import Application
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.db.uow import UnitOfWork
from app.logger import setup_logger
from app.telegram.bot import create_bot
from app.telegram.dispatcher import create_dispatcher


def uow_factory():
    return UnitOfWork(SessionLocal)


async def _setup_commands(bot, admin_id: int) -> None:
    """Register bot commands in Telegram's '/' menu."""
    common = [BotCommand(command="start", description="Запустить бота")]
    admin_cmds = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="stats", description="📊 График самочувствия"),
    ]
    await bot.set_my_commands(common, scope=BotCommandScopeDefault())
    await bot.set_my_commands(
        admin_cmds, scope=BotCommandScopeChat(chat_id=admin_id)
    )


async def main():
    parser = argparse.ArgumentParser(description="Morning Companion Bot")
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Apply database migrations and exit.",
    )
    args = parser.parse_args()

    if args.init_db:
        await init_db()
        return

    await init_db()

    # Configure logging AFTER init_db: alembic's env.py runs fileConfig()
    # which resets the root logger (disable_existing_loggers=True). Setting
    # up here makes sure our console + file handlers win and INFO logs of
    # the bot are not silently dropped after migrations.
    logger = setup_logger()
    logger.info("Database migrations applied.")

    settings = get_settings()
    bot = create_bot(settings)
    dispatcher = create_dispatcher(settings.allowed_users)
    app = Application(
        bot=bot,
        dispatcher=dispatcher,
        uow_factory=uow_factory,
        admin_id=settings.admin_id,
        retention_days=settings.message_retention_days,
    )
    logger.info(
        "Bot starting (model=%s, provider=%s)",
        settings.model,
        settings.ai_provider,
    )
    await _setup_commands(bot, settings.admin_id)
    await app.start()


if __name__ == "__main__":
    asyncio.run(main())
