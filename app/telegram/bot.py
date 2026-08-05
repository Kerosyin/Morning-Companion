from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from app.config import Settings


def create_bot(settings: Settings) -> Bot:
    if settings.proxy:
        session = AiohttpSession(proxy=settings.proxy)
        return Bot(token=settings.bot_token, session=session)
    return Bot(token=settings.bot_token)
