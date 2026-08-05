from aiogram import Bot, Dispatcher

from app.config import Settings
from app.db.base import Base
from app.db.engine import engine
from app.telegram.bot import create_bot
from app.telegram.dispatcher import create_dispatcher


class Application:

    def __init__(self, settings: Settings):

        self.settings = settings

        self.bot: Bot = create_bot(settings)

        self.dispatcher: Dispatcher = create_dispatcher()

    async def start(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await self.dispatcher.start_polling(self.bot)

    async def stop(self):

        await self.bot.session.close()
