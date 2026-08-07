from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.ai.critical_event_detector import (
    SEVERITY_RANK,
    CriticalEvent,
    CriticalEventDetector,
)
from app.config import get_settings
from app.db.models.critical_event import CriticalSeverity
from app.db.uow import IUnitOfWork

logger = logging.getLogger("morning_companion")


class CriticalEventService:
    """
    Detects critical health-related messages, deduplicates alerts per episode,
    and signals which events the admin should be notified about.
    """

    def __init__(
        self,
        detector: CriticalEventDetector,
        *,
        enabled: bool | None = None,
        min_severity: str | None = None,
        cooldown_minutes: int | None = None,
    ):
        self.detector = detector
        # Overrides allow deterministic tests without touching the cached settings.
        self._enabled = enabled
        self._min_severity = min_severity
        self._cooldown_minutes = cooldown_minutes

    def _config(self):
        settings = get_settings()
        return (
            self._enabled
            if self._enabled is not None
            else settings.critical_alert_enabled,
            self._min_severity
            if self._min_severity is not None
            else settings.critical_alert_min_severity,
            self._cooldown_minutes
            if self._cooldown_minutes is not None
            else settings.critical_alert_cooldown_minutes,
        )

    async def process(self, uow: IUnitOfWork, context) -> CriticalEvent | None:
        """
        Detects and persists a critical event. Returns the event when the admin
        should be notified now (subject to cooldown and escalation), else None.
        """
        enabled, min_severity, cooldown_minutes = self._config()
        if not enabled:
            return None

        detection = await self.detector.detect(context)
        if detection is None:
            return None

        min_rank = SEVERITY_RANK[CriticalSeverity(min_severity)]
        if SEVERITY_RANK[detection.severity] < min_rank:
            return None

        now = datetime.now(timezone.utc)
        last = await uow.critical_events.get_last_for_user(context.user.id)
        should_notify = self._should_notify(last, detection, now, cooldown_minutes)

        event = await uow.critical_events.create_event(
            user_id=context.user.id,
            severity=detection.severity.value,
            event_type=detection.event_type,
            description=detection.description,
            message_text=context.message,
            created_at=now.replace(tzinfo=None),
            notified_at=now.replace(tzinfo=None) if should_notify else None,
        )

        logger.info(
            "Критичное событие: user=%s severity=%s notify=%s",
            context.user.id,
            detection.severity.value,
            should_notify,
        )
        return event if should_notify else None

    @staticmethod
    def _should_notify(
        last,
        detection: CriticalEvent,
        now: datetime,
        cooldown_minutes: int,
    ) -> bool:
        if last is None:
            return True
        if SEVERITY_RANK[detection.severity] > SEVERITY_RANK[
            CriticalSeverity(last.severity)
        ]:
            return True
        last_created = last.created_at
        if last_created.tzinfo is None:
            last_created = last_created.replace(tzinfo=timezone.utc)
        elapsed_minutes = (now - last_created).total_seconds() / 60
        return elapsed_minutes >= cooldown_minutes
