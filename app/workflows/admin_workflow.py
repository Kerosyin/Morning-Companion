from __future__ import annotations

from datetime import datetime

from aiogram import Bot


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

        now = datetime.now()

        if now.hour < self.CHECK_HOUR:
            return

        async with self.uow_factory() as uow:

            users = await uow.users.get_all()

            for user in users:

                activity = await (
                    uow.daily_activity.get_or_create_today(
                        user.id
                    )
                )

                if activity.first_message_at:
                    continue

                if activity.admin_notified:
                    continue

                await self.bot.send_message(
                    chat_id=self.admin_id,
                    text=self._build_message(user),
                )

                activity.admin_notified = True

            await uow.commit()

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
