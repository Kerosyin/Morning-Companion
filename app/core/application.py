from aiogram import Bot, Dispatcher

from app.config import Settings
from app.telegram.bot import create_bot
from app.telegram.dispatcher import create_dispatcher


class Application:

    def __init__(self, settings: Settings):

        self.settings = settings

        self.bot: Bot = create_bot(settings)

        self.dispatcher: Dispatcher = create_dispatcher()

    async def start(self):
        await self.dispatcher.start_polling(self.bot)

    async def stop(self):
        await self.bot.session.close()
