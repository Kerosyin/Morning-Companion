from __future__ import annotations


class ReminderProvider:
    """
    Provides reminder texts.

    In the future these messages will be generated
    by AI once every morning.
    """

    _MESSAGES = (
        "☀️ Доброе утро! Как твои дела сегодня?",
        "😊 Напоминаю, что буду рад получить от тебя сообщение.",
        "👋 Надеюсь, день начинается хорошо. Напиши пару слов.",
        "🌿 Всё ли у тебя в порядке?",
        "💬 Если появится минутка — обязательно напиши.",
        "🙂 Просто дружеское напоминание 😊",
        "☕ Надеюсь, день проходит отлично.",
        "📩 Всё ещё жду твоего сообщения.",
        "🌞 Не забывай про наш ежедневный диалог.",
        "👀 Всё хорошо?",
        "🤝 Я всё ещё здесь и жду твоего сообщения.",
        "⚠️ Если до 12:00 ответа не будет, мне придётся сообщить администратору.",
    )

    def get(self, reminder_number: int) -> str:

        reminder_number = max(reminder_number, 1)

        if reminder_number > len(self._MESSAGES):
            reminder_number = len(self._MESSAGES)

        return self._MESSAGES[reminder_number - 1]
