import asyncio

from app.config import get_settings
from app.core.application import Application


async def main():

    settings = get_settings()

    app = Application(settings)

    await app.start()


if __name__ == "__main__":

    asyncio.run(main())
