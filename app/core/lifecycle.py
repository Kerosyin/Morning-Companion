import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


async def startup():
    """
    Application startup logic.
    """
    logger.info("Starting application...")
    # Here we will initialize database, bot, scheduler, etc.


async def shutdown():
    """
    Application shutdown logic.
    """
    logger.info("Shutting down application...")
    # Here we will close connections, stop services, etc.


@asynccontextmanager
async def lifespan(app):
    """
    Asynchronous context manager for application lifespan.
    Handles startup and shutdown events.
    """
    await startup()
    try:
        yield
    finally:
        await shutdown()
