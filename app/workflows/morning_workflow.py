from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.core.clock import now_in_timezone
from app.reminders.provider import ReminderProvider
from app.services.morning_service import MorningService

logger = logging.getLogger("morning_companion")


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

        now = now_in_timezone()

        async with self.uow_factory() as uow:

            users = await uow.users.get_all()
            # Snapshot the ids: a rollback below expires every ORM instance
            # of this session, so `user.id` would otherwise trigger a lazy
            # load on the next iteration. Re-fetch each user fresh instead.
            user_ids = [u.id for u in users]

            for user_id in user_ids:

                try:
                    user = await uow.users.get(user_id)
                    if user is None:
                        continue

                    decision = await self.morning_service.evaluate(
                        uow,
                        user,
                        now,
                    )

                    if decision.should_send:
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

                    # Commit per user so a failure on one user does not roll
                    # back the reminders/poll already sent to the others.
                    await uow.commit()
                except TelegramAPIError as exc:
                    logger.warning(
                        "Не удалось отправить напоминание user=%s: %s",
                        user_id,
                        exc,
                    )
                    await uow.rollback()
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "Ошибка при обработке напоминаний user=%s",
                        user_id,
                    )
                    await uow.rollback()
