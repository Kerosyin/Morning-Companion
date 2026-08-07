import pytest
from sqlalchemy import select

from app.ai.critical_event_detector import CriticalEventDetector
from app.ai.models import ConversationContext
from app.ai.provider import AIProvider
from app.db.models import CriticalEvent, CriticalSeverity
from app.services.critical_event_service import CriticalEventService

pytestmark = pytest.mark.asyncio


class FakeProvider(AIProvider):
    def __init__(self, response: str = "{}"):
        self.response = response
        self.calls = 0

    async def chat(self, context: ConversationContext):
        raise NotImplementedError

    async def simple_chat(self, system_prompt: str, user_prompt: str):
        self.calls += 1
        return self.response


class FakeUser:
    id = 1


def make_service(provider: FakeProvider, **kwargs) -> CriticalEventService:
    detector = CriticalEventDetector(provider)
    defaults = {"enabled": True, "min_severity": "high", "cooldown_minutes": 120}
    defaults.update(kwargs)
    return CriticalEventService(detector, **defaults)


def make_context(message: str) -> ConversationContext:
    return ConversationContext(
        user=FakeUser(), history=[], memories=[], message=message
    )


async def run(uow, service, message):
    async with uow:
        return await service.process(uow, make_context(message))


async def test_strong_keyword_detected_without_llm(uow):
    provider = FakeProvider()
    service = make_service(provider)
    event = await run(uow, service, "я вызвал скорую, у меня кровь")

    assert event is not None
    assert event.severity == CriticalSeverity.CRITICAL
    assert provider.calls == 0


async def test_llm_classifies_weak_signal(uow):
    provider = FakeProvider(
        '{"critical": true, "severity": "critical", '
        '"event_type": "health_emergency", "description": "Болит сердце"}'
    )
    service = make_service(provider)
    event = await run(uow, service, "у меня сильно болит сердце")

    assert event is not None
    assert event.severity == CriticalSeverity.CRITICAL
    assert provider.calls == 1


async def test_non_critical_message_returns_none(uow):
    provider = FakeProvider('{"critical": false}')
    service = make_service(provider)
    event = await run(uow, service, "у меня немного болит голова")

    assert event is None


async def test_low_severity_below_threshold_not_notified(uow):
    provider = FakeProvider(
        '{"critical": true, "severity": "low", "event_type": "other", '
        '"description": "Просто неважно себя чувствует"}'
    )
    service = make_service(provider)
    event = await run(uow, service, "у меня сегодня небольшая головная боль")

    assert event is None
    assert provider.calls == 1


async def test_disabled_feature_returns_none(uow):
    provider = FakeProvider()
    service = make_service(provider, enabled=False)
    event = await run(uow, service, "я вызвал скорую")

    assert event is None
    assert provider.calls == 0


async def test_dedup_within_cooldown(uow):
    provider = FakeProvider(
        '{"critical": true, "severity": "high", "event_type": "health_concern", '
        '"description": "Очень плохо"}'
    )
    service = make_service(provider, cooldown_minutes=120)

    async with uow:
        first = await service.process(uow, make_context("плохо себя чувствую"))
        second = await service.process(uow, make_context("мне правда очень плохо"))
        result = await uow.session.execute(select(CriticalEvent))
        events = result.scalars().all()

    assert first is not None
    assert second is None
    assert len(events) == 2
    assert events[0].notified_at is not None
    assert events[1].notified_at is None


async def test_escalation_resets_cooldown(uow):
    provider = FakeProvider(
        '{"critical": true, "severity": "high", "event_type": "health_concern", '
        '"description": "Плохо"}'
    )
    service = make_service(provider, cooldown_minutes=120)

    async with uow:
        first = await service.process(uow, make_context("плохо себя чувствую"))
        second = await service.process(uow, make_context("вызвал скорую"))

    assert first is not None
    assert first.severity == CriticalSeverity.HIGH
    assert second is not None
    assert second.severity == CriticalSeverity.CRITICAL


async def test_categorises_non_health_emergencies(uow):
    provider = FakeProvider()
    service = make_service(provider)

    fire = await run(uow, service, "у меня в квартире пожар")
    flood = await run(uow, service, "соседи затопило, вода с потолка")
    crime = await run(uow, service, "меня грабят, вызовите полицию")

    assert fire is not None
    assert fire.severity == CriticalSeverity.CRITICAL
    assert fire.event_type == "fire"
    assert flood is not None
    assert flood.event_type == "flood"
    assert crime is not None
    assert crime.event_type == "crime"


async def test_weak_signal_categories_use_llm(uow):
    provider = FakeProvider(
        '{"critical": true, "severity": "critical", "event_type": "fire", '
        '"description": "Сильный дым"}'
    )
    service = make_service(provider)

    event = await run(uow, service, "в подъезде сильный дым, что делать")

    assert event is not None
    assert event.event_type == "fire"
    assert provider.calls == 1
