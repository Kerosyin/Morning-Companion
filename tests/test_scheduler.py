from app.core.clock import app_timezone
from app.scheduler.scheduler import Scheduler


def test_scheduler_uses_app_timezone():
    """Bug 7: the scheduler must run jobs in the configured app timezone,
    not the system/local zone (otherwise cron hour=3 fires at the wrong time)."""
    scheduler = Scheduler()
    assert scheduler.scheduler.timezone == app_timezone()
