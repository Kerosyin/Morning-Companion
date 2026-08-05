from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.engine import engine

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
