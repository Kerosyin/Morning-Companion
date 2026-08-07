from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.ai.models import ConversationContext
from app.ai.provider import AIProvider
from app.db.models.critical_event import CriticalSeverity

logger = logging.getLogger(__name__)

SEVERITY_RANK = {
    CriticalSeverity.LOW: 1,
    CriticalSeverity.HIGH: 2,
    CriticalSeverity.CRITICAL: 3,
}


@dataclass
class CriticalEvent:
    """A detected critical (health-related) event reported by a user."""

    severity: CriticalSeverity
    event_type: str
    description: str


class CriticalEventDetector:
    """
    Detects critical messages: health emergencies ("I am dying", "I can't
    breathe", "I called an ambulance"), fires, flooding, crime, accidents, and
    strong distress — so the caregiver can reach the user.

    Deterministic keyword gates decide the category and severity for the most
    unambiguous phrases without an extra LLM call. Only messages with a weak
    signal are classified by a second LLM request, mirroring the
    MemoryExtractor pattern.
    """

    # Category -> keywords. The first match wins; dict order is priority.
    CRITICAL_CATEGORIES: dict[str, list[str]] = {
        "health_emergency": [
            "скорую",
            "скорая",
            "умираю",
            "умирает",
            "не могу дышать",
            "не дышу",
            "задыхаюсь",
            "задыхается",
            "не хватает воздуха",
            "кровотечение",
            "сильно кровит",
            "потерял сознание",
            "потеряла сознание",
            "без сознания",
            "сердечный приступ",
            "инфаркт",
            "инсульт",
            "вызовите скорую",
            "вызови скорую",
            "позвони в скорую",
            "отравл",
            "передозиров",
        ],
        "fire": [
            "пожар",
            "загорелось",
            "загорелся",
            "загорелась",
            "горит",
            "горитм",
            "утечка газа",
            "пахнет газом",
            "газом пахнет",
            "задымлени",
            "я в огне",
        ],
        "flood": [
            "затопило",
            "затопила",
            "потоп",
            "заливает",
            "прорвало трубу",
            "прорвало",
            "протекает",
            "льётся вода",
            "потекла вода",
        ],
        "crime": [
            "грабят",
            "ограбили",
            "ограбление",
            "ворвались",
            "взлом",
            "угрожает",
            "угрожают",
            "преследуют",
            "меня преследует",
            "хотят убить",
            "убивает",
            "напали",
            "насилие",
            "нож",
            "пистолет",
            "выстрел",
            "стрельба",
            "стреляли",
            "избивают",
            "меня бьют",
            "вор в доме",
        ],
        "accident": [
            "авария",
            "дтп",
            "разбился",
            "перелом",
            "под машину",
            "сбили",
            "выпал из окна",
            "упал с лестницы",
            "порезался",
            "глубокий порез",
            "обжёг",
        ],
    }

    # Not immediately life-threatening, but clearly needs a caregiver's help.
    HIGH_CATEGORIES: dict[str, list[str]] = {
        "health_concern": [
            "очень плохо",
            "мне плохо",
            "плохо себя чувствую",
            "неважно себя чувствую",
            "нужна помощь",
            "нужна ваша помощь",
            "помогите мне",
            "помоги мне",
            "не могу встать",
            "высокая температура",
            "сильная боль",
            "очень болит",
        ],
        "crisis_concern": [
            "случилась беда",
            "произошло что-то страшное",
            "случилось что-то серьёзное",
            "мне срочно нужна помощь",
            "у нас серьёзн",
        ],
    }

    WEAK_SIGNAL_KEYWORDS = [
        # health
        "болит",
        "боль",
        "врач",
        "больниц",
        "помощ",
        "скора",
        "плохо",
        "сердц",
        "груд",
        "дыш",
        "температур",
        "приступ",
        "сознан",
        "кров",
        "таблетк",
        "лекарств",
        "давлен",
        "аптек",
        # fire / water / crime signals
        "дым",
        "газ",
        "пламя",
        "огн",
        "затоп",
        "протеч",
        "потоп",
        "соседи",
        "полици",
        "опасн",
        "угроз",
        "преслед",
        "взлом",
        "пострад",
        "спас",
        "труба",
    ]

    SYSTEM_PROMPT = """
You analyze a single user message from a Telegram companion bot and decide
whether it reports an emergency or a serious crisis that a caregiver must be
told about.

Return ONLY valid JSON, one of:

{"critical": false}

{"critical": true, "severity": "high", "event_type": "<type>",
 "description": "one short sentence"}

{"critical": true, "severity": "critical", "event_type": "<type>",
 "description": "one short sentence"}

event_type is one of: health_emergency, health_concern, fire, flood, crime,
accident, crisis_concern, other.

Rules:
- severity "critical": urgent, life-threatening or safety-threatening — an
  ambulance, a fire, danger to life, serious injury, paramedics, etc.
- severity "high": clearly serious and calls for help, but not immediately
  dangerous.
- health_emergency: urgent health danger (can't breathe, unconscious, calling
  an ambulance). health_concern: clearly unwell but not immediately dangerous.
- Minor health complaints (a cold, a headache) are NOT critical.
- Do NOT flag minor complaints (a cold, a headache, being tired), jokes,
  sarcasm, or hypotheticals ("what if I...").
- description: one short sentence in the user's language.
"""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    @staticmethod
    def _match(categories: dict[str, list[str]], text: str) -> tuple[str, str] | None:
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category, keyword
        return None

    async def detect(self, context: ConversationContext) -> CriticalEvent | None:
        text = (context.message or "").lower()

        match = self._match(self.CRITICAL_CATEGORIES, text)
        if match is not None:
            category, _ = match
            return CriticalEvent(
                severity=CriticalSeverity.CRITICAL,
                event_type=category,
                description=f"Сообщение: «{context.message}»",
            )

        match = self._match(self.HIGH_CATEGORIES, text)
        if match is not None:
            category, _ = match
            return CriticalEvent(
                severity=CriticalSeverity.HIGH,
                event_type=category,
                description=f"Сообщение: «{context.message}»",
            )

        if not any(keyword in text for keyword in self.WEAK_SIGNAL_KEYWORDS):
            return None

        response = await self.provider.simple_chat(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=context.message,
        )

        try:
            data = json.loads(response)
        except Exception:  # noqa: BLE001
            logger.warning("Critical event detector returned invalid JSON.")
            return None

        if not data.get("critical"):
            return None

        try:
            severity = CriticalSeverity(data.get("severity", "high"))
        except ValueError:
            logger.warning("Unknown severity from critical event detector.")
            return None

        return CriticalEvent(
            severity=severity,
            event_type=data.get("event_type", "other"),
            description=data.get("description", context.message),
        )
