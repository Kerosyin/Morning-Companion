from __future__ import annotations

from datetime import datetime

from aiogram import Bot

from app.reminders.provider import ReminderProvider
from app.services.morning_service import MorningService
from app.telegram.health_poll import POLL_TEXT, build_rating_keyboard


class MorningWorkflow:
    """
    Executes the complete morning reminder flow.
    """

    def __init__(
        self,
        bot: Bot,
        uow_factory,
    ) -> None:

        self.bot = bot
        self.uow_factory = uow_factory

        self.morning_service = MorningService()
        self.provider = ReminderProvider()

    async def execute(self) -> None:

        now = datetime.now()

        async with self.uow_factory() as uow:

            users = await uow.users.get_all()

            for user in users:

                decision = await self.morning_service.evaluate(
                    uow,
                    user,
                    now,
                )

                if not decision.should_send:
                    continue

                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=self.provider.get(
                        decision.reminder_number,
                    ),
                )

                activity = (
                    await uow.daily_activity.get_or_create_today(
                        user.id,
                    )
                )

                await uow.daily_activity.increment_reminders_sent(
                    activity,
                )

                if not activity.health_check_sent:
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=POLL_TEXT,
                        reply_markup=build_rating_keyboard(),
                    )
                    await uow.daily_activity.mark_health_check_sent(
                        activity,
                    )

            await uow.commit()
