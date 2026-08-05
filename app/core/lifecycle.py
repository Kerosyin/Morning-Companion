from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    await app.start()

    try:
        yield
    finally:
        await app.stop()
