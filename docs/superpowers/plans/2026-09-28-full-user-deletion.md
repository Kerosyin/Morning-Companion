# Full User Deletion Implementation Plan

Goal: Let the administrator permanently delete a user and all related personal data after a matching confirmation.

Architecture: Repository methods delete the user and queued outbox records in one UnitOfWork. Existing model cascades remove child records. Handlers retain a five-minute pending confirmation keyed by administrator ID.

Tech Stack: Python, aiogram, SQLAlchemy, pytest, ruff.

Spec: docs/superpowers/specs/2026-09-28-full-user-deletion-design.md

## Task 1: Repository deletion

Files: app/repositories/user_repository.py, app/repositories/notification_outbox_repository.py, tests/test_user_deletion.py.

- [ ] Write a failing test that creates a user and grant, invokes delete_by_telegram_id, clears its access grant and notification outbox records, commits, then asserts the user and grant are absent.
- [ ] Run uv run pytest tests/test_user_deletion.py -v and confirm missing methods fail.
- [ ] Add UserRepository.delete_by_telegram_id(telegram_id) returning False for an absent user and deleting a found user; add NotificationOutboxRepository.delete_by_chat_id(chat_id) using a SQLAlchemy delete statement.
- [ ] Run the focused test and commit feat: delete all user data.

## Task 2: Confirmed admin commands

Files: app/telegram/handlers.py, app/main.py, tests/test_handlers.py.

- [ ] Write failing tests for non-admin rejection, invalid ID, self-deletion refusal, pending confirmation, mismatched ID, expiry, and successful deletion.
- [ ] Run uv run pytest tests/test_handlers.py -v and confirm the absent handlers fail.
- [ ] Add /delete_user ID and /confirm_delete ID. Store the pending tuple of requested ID and creation time by administrator ID. Confirmation clears the pending tuple before deleting grant, queued notifications, and user in one commit.
- [ ] Register both commands only in the existing administrator Chat command scope.
- [ ] Run focused tests and commit feat: add confirmed user deletion.

## Task 3: Verification

- [ ] Run uv run pytest.
- [ ] Run uv run ruff check app/ tests/.
- [ ] Run git diff --check.

