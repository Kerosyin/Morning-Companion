import asyncio

from app.config import get_settings
from app.core.application import Application
from app.core.lifecycle import lifespan
from app.logger import setup_logger


async def run():
    logger = setup_logger()

    settings = get_settings()

    app = Application(settings)

    async with lifespan(app):
        logger.info("Morning Companion is running.")

        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(run())
