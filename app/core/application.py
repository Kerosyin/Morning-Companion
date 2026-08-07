from __future__ import annotations

import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError

from app.scheduler.admin_job import AdminJob
from app.scheduler.cleanup_job import CleanupJob
from app.scheduler.morning_job import MorningJob
from app.scheduler.scheduler import Scheduler
from app.workflows.admin_workflow import AdminWorkflow
from app.workflows.cleanup_workflow import CleanupWorkflow
from app.workflows.morning_workflow import MorningWorkflow

logger = logging.getLogger("morning_companion")


class Application:

    def __init__(
        self,
        bot: Bot,
        dispatcher: Dispatcher,
        uow_factory,
        admin_id: int,
        retention_days: int,
    ):
        self.bot = bot
        self.dispatcher = dispatcher
        self.uow_factory = uow_factory
        self.admin_id = admin_id
        self.retention_days = retention_days

        self.scheduler = Scheduler()

    async def start(self):

        morning_job = MorningJob(
            workflow=MorningWorkflow(
                bot=self.bot,
                uow_factory=self.uow_factory,
            ),
        )

        self.scheduler.add_job(
            morning_job.run,
            trigger="interval",
            minutes=1,
            id="morning-job",
            replace_existing=True,
        )

        admin_job = AdminJob(
            workflow=AdminWorkflow(
                bot=self.bot,
                admin_id=self.admin_id,
                uow_factory=self.uow_factory,
            ),
        )

        self.scheduler.add_job(
            admin_job.run,
            trigger="interval",
            minutes=1,
            id="admin-job",
            replace_existing=True,
        )

        cleanup_job = CleanupJob(
            workflow=CleanupWorkflow(
                uow_factory=self.uow_factory,
                retention_days=self.retention_days,
            ),
        )

        self.scheduler.add_job(
            cleanup_job.run,
            trigger="cron",
            hour=3,
            id="cleanup-job",
            replace_existing=True,
        )

        self.scheduler.start()

        try:
            await self._polling_loop()
        finally:
            await self.stop()

    async def _polling_loop(self):
        while True:
            try:
                await self.dispatcher.start_polling(self.bot)
            except (TelegramAPIError, OSError, aiohttp.ClientError) as exc:
                logger.warning("Поллинг прерван (%s). Перезапускаю через 5с...", exc)
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.exception("Поллинг упал: %s", exc)
                await asyncio.sleep(5)

    async def stop(self):

        logger.info("Application stopping...")

        await self.scheduler.shutdown()
        await self.bot.session.close()

        logger.info("Scheduler stopped, bot session closed")
