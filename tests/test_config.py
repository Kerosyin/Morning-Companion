import pytest
from pydantic import ValidationError

from app.config import Settings


def _settings_kwargs(**overrides):
    values = {
        "BOT_TOKEN": "token",
        "ADMIN_ID": 1,
        "MODEL": "model",
        "OPENROUTER_API_KEY": "key",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    }
    values.update(overrides)
    return values


def test_critical_alert_min_severity_is_normalized():
    settings = Settings(**_settings_kwargs(CRITICAL_ALERT_MIN_SEVERITY="HIGH"))

    assert settings.critical_alert_min_severity == "high"


def test_invalid_critical_alert_min_severity_fails_fast():
    with pytest.raises(ValidationError):
        Settings(**_settings_kwargs(CRITICAL_ALERT_MIN_SEVERITY="urgent"))
