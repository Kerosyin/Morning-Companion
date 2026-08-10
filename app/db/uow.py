from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    CriticalEventRepository,
    DailyActivityRepository,
    HealthCheckinRepository,
    MemoryRepository,
    MessageRepository,
    NotificationOutboxRepository,
    UserRepository,
)


class IUnitOfWork(ABC):
    users: UserRepository
    messages: MessageRepository
    memories: MemoryRepository
    daily_activity: DailyActivityRepository
    critical_events: CriticalEventRepository
    health_checkins: HealthCheckinRepository
    notifications: NotificationOutboxRepository

    @abstractmethod
    async def __aenter__(self):
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    @abstractmethod
    async def commit(self):
        ...

    @abstractmethod
    async def rollback(self):
        ...


class UnitOfWork(IUnitOfWork):
    def __init__(self, session_factory: Type[AsyncSession]):
        self._session_factory = session_factory

    async def __aenter__(self):
        self.session = self._session_factory()

        self.users = UserRepository(self.session)
        self.messages = MessageRepository(self.session)
        self.memories = MemoryRepository(self.session)
        self.daily_activity = DailyActivityRepository(self.session)
        self.critical_events = CriticalEventRepository(self.session)
        self.health_checkins = HealthCheckinRepository(self.session)
        self.notifications = NotificationOutboxRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
