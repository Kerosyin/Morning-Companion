from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:

    def __init__(self):

        self.scheduler = AsyncIOScheduler()

    def add_job(
        self,
        func,
        trigger,
        **kwargs,
    ):

        self.scheduler.add_job(
            func,
            trigger,
            **kwargs,
        )

    def start(self):

        self.scheduler.start()

    async def shutdown(self):

        self.scheduler.shutdown()