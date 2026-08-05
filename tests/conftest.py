import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db.base import Base
from app.db.uow import UnitOfWork

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_engine():
    """Fixture to create a new in-memory SQLite engine for each test function."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session_factory(test_engine):
    """Fixture to create a session factory for the test engine."""
    yield async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
    )


@pytest.fixture(scope="function")
async def uow(test_session_factory):
    """Fixture to provide a UnitOfWork instance for tests."""
    yield UnitOfWork(test_session_factory)
