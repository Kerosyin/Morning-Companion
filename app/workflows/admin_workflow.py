from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.core.clock import now_in_timezone
from app.db.models import NotificationStatus

logger = logging.getLogger("morning_companion")


class AdminWorkflow:
    """
    Notifies the administrator about users
    who did not respond before noon.
    """

    CHECK_HOUR = 12

    def __init__(
        self,
        bot: Bot,
        admin_id: int,
        uow_factory,
    ) -> None:

        self.bot = bot
        self.admin_id = admin_id
        self.uow_factory = uow_factory

    async def execute(self) -> None:

        now = now_in_timezone()

        if now.hour < self.CHECK_HOUR:
            return

        async with self.uow_factory() as uow:

            users = await uow.users.get_all()
            # Snapshot the ids: a rollback below expires every ORM instance
            # of this session, so `user.id` would otherwise trigger a lazy
            # load on the next iteration. Re-fetch each user fresh instead.
            user_ids = [u.id for u in users]

            for user_id in user_ids:
                notification = None

                try:
                    user = await uow.users.get(user_id)
                    if user is None:
                        continue

                    activity = await (
                        uow.daily_activity.get_or_create_today(
                            user.id
                        )
                    )

                    if (
                        not activity.first_message_at
                        and not activity.admin_notified
                    ):
                        text = self._build_message(user)
                        notification = await uow.notifications.get_or_create(
                            kind="admin_inactive_user",
                            dedupe_key=f"{now.date()}:{user.id}",
                            chat_id=self.admin_id,
                            text=text,
                        )
                        await uow.commit()

                        if notification.status == NotificationStatus.SENT:
                            activity.admin_notified = True
                            await uow.commit()
                            continue

                        await self.bot.send_message(
                            chat_id=self.admin_id,
                            text=text,
                        )

                        await uow.notifications.mark_sent(notification)
                        activity.admin_notified = True

                    # Commit per user so a send failure does not roll back the
                    # admin_notified flag already set for the others (which
                    # would otherwise produce duplicate notifications).
                    await uow.commit()
                except TelegramAPIError as exc:
                    logger.warning(
                        "Не удалось уведомить админа по user=%s: %s",
                        user_id,
                        exc,
                    )
                    if notification is not None:
                        await uow.notifications.mark_failed(
                            notification,
                            str(exc),
                        )
                        await uow.commit()
                        continue
                    await uow.rollback()
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "Ошибка admin-уведомления user=%s",
                        user_id,
                    )
                    await uow.rollback()

    @staticmethod
    def _build_message(user) -> str:

        username = (
            f"@{user.username}"
            if user.username
            else "не указан"
        )

        return (
            "⚠️ Пользователь не вышел на связь.\n\n"
            f"Имя: {user.first_name}\n"
            f"Username: {username}\n"
            f"Telegram ID: {user.telegram_id}"
        )
