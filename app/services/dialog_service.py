from aiogram.types import Message as TelegramMessage

from app.db.models.message import MessageRole
from app.db.uow import IUnitOfWork
from app.ai.factory import get_ai_provider
from app.ai.models import ConversationContext


class DialogService:
    def __init__(self):
        # In the future, this could be injected.
        self.ai_provider = get_ai_provider()

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

            # 3. Fetch conversation history and memories
            history = await uow.messages.get_history(user=user, limit=15)
            memories = await uow.memories.get_all_for_user(user=user)

            # 4. Generate reply
            context = ConversationContext(
                user=user,
                history=history,
                memories=memories,
                message=message.text,
            )
            ai_response = await self.ai_provider.chat(context)

            # 5. Save bot's reply
            await uow.messages.create(
                user_id=user.id,
                role=MessageRole.ASSISTANT,
                text=ai_response.reply,
            )

            await uow.commit()

            # 6. Return reply text
            return ai_response.reply
