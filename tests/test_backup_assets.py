from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_backup_script_creates_a_consistent_database_snapshot_and_keeps_three_archives(
):
    script = (ROOT / "scripts" / "bot-backup.sh").read_text(encoding="utf-8")

    assert "source.backup(destination)" in script
    assert 'find "$BACKUP_DIR"' in script
    assert "tail -n +4" in script


def test_backup_timer_runs_weekly_as_the_application_user():
    timer = (
        ROOT / "deploy" / "morning-companion-backup.timer"
    ).read_text(encoding="utf-8")
    service = (
        ROOT / "deploy" / "morning-companion-backup.service"
    ).read_text(encoding="utf-8")

    assert "OnCalendar=weekly" in timer
    assert "User=bigbrick" in service
    assert "scripts/bot-backup.sh" in service


def test_local_fetch_script_downloads_and_retains_three_vps_archives():
    script = (ROOT / "scripts" / "fetch-vps-backup.ps1").read_text(encoding="utf-8")

    assert "scp.exe" in script
    assert "vps-backups" in script
    assert "Select-Object -Skip 3" in script
