import asyncio

from app.db.base import Base
from app.db.engine import engine


async def init_db():
    """Initializes the database and creates tables."""
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Use for dropping tables if needed
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized.")


if __name__ == "__main__":
    asyncio.run(init_db())
