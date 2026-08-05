from __future__ import annotations

from aiogram import Bot, Dispatcher

from app.scheduler.admin_job import AdminJob
from app.scheduler.scheduler import Scheduler
from app.scheduler.morning_job import MorningJob
from app.workflows.admin_workflow import AdminWorkflow
from app.workflows.morning_workflow import MorningWorkflow


class Application:

    def __init__(
        self,
        bot: Bot,
        dispatcher: Dispatcher,
        uow_factory,
        admin_id: int,
    ):
        self.bot = bot
        self.dispatcher = dispatcher
        self.uow_factory = uow_factory
        self.admin_id = admin_id

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

        self.scheduler.start()

        await self.dispatcher.start_polling(
            self.bot
        )

    async def stop(self):

        await self.scheduler.shutdown()

        await self.bot.session.close()