from aiogram.types import Message as TelegramMessage
from datetime import datetime

from app.ai.factory import get_ai_provider
from app.ai.models import ConversationContext
from app.db.models.message import MessageRole
from app.db.uow import IUnitOfWork
from app.services.conversation_service import ConversationService
from app.services.history_service import HistoryService


class DialogService:
    def __init__(self):
        self.conversation = ConversationService(
            get_ai_provider(),
        )
        self.history_service = HistoryService()

    async def process_message(self, uow: IUnitOfWork, message: TelegramMessage) -> str:
        """
        Processes a message from the user by interacting with the AI provider.

        1. Finds or creates a user.
        2. Saves the user's message.
        3. Fetches conversation history.
        4. Generates a reply using the AI provider.
        5. Saves the bot's reply.
        6. Returns the reply text.
        """
        async with uow:
            # 1. Find or create user
            user = await uow.users.get_or_create(
                telegram_id=message.from_user.id,
                defaults={
                    "username": message.from_user.username,
                    "first_name": message.from_user.first_name,
                    "last_name": message.from_user.last_name,
                },
            )

            # 2. Save user's message
            await uow.messages.create(
                user_id=user.id,
                role=MessageRole.USER,
                text=message.text
            )

            # 2.1 Stop morning reminders once the user replies today
            activity = await uow.daily_activity.get_or_create_today(user.id)
            if activity.first_message_at is None:
                await uow.daily_activity.set_first_message_time(
                    activity,
                    datetime.now(),
                )

            # 3. Fetch conversation history and memories
            history = await uow.messages.get_history(user=user, limit=15)
            history = self.history_service.prepare(history)
            memories = await uow.memories.get_all_for_user(user=user)

            # 4. Generate reply
            context = ConversationContext(
                user=user,
                history=history,
                memories=memories,
                message=message.text,
            )
            ai_response = await self.conversation.reply(
                context,
            )

            # 5. Save bot's reply
            await uow.messages.create(
                user_id=user.id,
                role=MessageRole.ASSISTANT,
                text=ai_response.reply,
            )

            await uow.commit()

            # 6. Return reply text
            return ai_response.reply
