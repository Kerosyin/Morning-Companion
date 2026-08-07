import logging
from dataclasses import dataclass

from aiogram.types import Message as TelegramMessage

from app.ai.critical_event_detector import CriticalEvent, CriticalEventDetector
from app.ai.memory_extractor import MemoryExtractor
from app.ai.models import ConversationContext
from app.ai.provider import AIProvider
from app.config import get_settings
from app.core.clock import now_in_timezone
from app.db.models.message import MessageRole
from app.db.uow import IUnitOfWork
from app.services.conversation_service import ConversationService
from app.services.critical_event_service import CriticalEventService
from app.services.history_service import HistoryService
from app.services.memory_service import MemoryService

logger = logging.getLogger("morning_companion")

AI_UNAVAILABLE_REPLY = (
    "Извини, я на мгновение отвлёкся 😅 Попробуй написать ещё раз."
)


@dataclass
class DialogResult:
    reply: str
    critical_event: CriticalEvent | None = None


class DialogService:
    def __init__(self, provider: AIProvider | None = None):
        if provider is None:
            from app.ai.openrouter import OpenRouterProvider

            provider = OpenRouterProvider()
        self.conversation = ConversationService(provider)
        self.history_service = HistoryService()
        self.memory_service = MemoryService(MemoryExtractor(provider))
        self.critical_events = CriticalEventService(CriticalEventDetector(provider))

    async def process_message(
        self, uow: IUnitOfWork, message: TelegramMessage
    ) -> DialogResult:
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

            # 2. Fetch conversation history BEFORE saving the current message.
            # Otherwise autoflush would include it in the history, and
            # ContextBuilder appends the current message separately, so it
            # would reach the LLM twice.
            history = await uow.messages.get_history(user=user, limit=15)
            history = self.history_service.prepare(history)
            memories = await uow.memories.get_all_for_user(user=user)

            # Cap the message length sent to the LLM. The full message is
            # still persisted below; only the LLM context gets a truncated
            # copy (token-burn / abuse protection).
            max_len = get_settings().message_max_length
            context = ConversationContext(
                user=user,
                history=history,
                memories=memories,
                message=message.text[:max_len],
            )

            # 3. Save the user's message and mark today's first reply so the
            # morning reminders stop. Done before the AI call so that a
            # provider failure still persists this data (committed below).
            await uow.messages.create(
                user_id=user.id,
                role=MessageRole.USER,
                text=message.text,
            )

            activity = await uow.daily_activity.get_or_create_today(user.id)
            if activity.first_message_at is None:
                await uow.daily_activity.set_first_message_time(
                    activity,
                    now_in_timezone().replace(tzinfo=None),
                )

            # 3.1 Detect critical events BEFORE the AI reply. The keyword gate
            # is local (no LLM needed), so an alert must still reach the admin
            # even if the AI provider is down.
            critical_event = None
            try:
                critical_event = await self.critical_events.process(uow, context)
            except Exception:  # noqa: BLE001
                logger.exception("Обработка критичного события не удалась")

            # 4. Generate reply
            logger.info(
                "Запрашиваю ответ у ИИ (OpenRouter, model=%s)",
                getattr(self.conversation.provider, "model", "n/a"),
            )
            try:
                ai_response = await self.conversation.reply(context)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ИИ не ответил (%s). Отправляю фолбэк.", exc)
                await uow.commit()
                return DialogResult(
                    reply=AI_UNAVAILABLE_REPLY,
                    critical_event=critical_event,
                )
            logger.info("ИИ ответил: %.100s", ai_response.reply)

            # 5. Save bot's reply
            await uow.messages.create(
                user_id=user.id,
                role=MessageRole.ASSISTANT,
                text=ai_response.reply,
            )

            # 5.1 Best-effort memory extraction (must not break the reply)
            try:
                await self.memory_service.update(uow, context)
            except Exception:  # noqa: BLE001
                logger.exception("Извлечение памяти не удалось")

            await uow.commit()

            # 6. Return reply text
            return DialogResult(
                reply=ai_response.reply,
                critical_event=critical_event,
            )
