# Admin-Managed Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Only the Telegram administrator can grant, revoke, and inspect persistent user access without restarting the bot.

**Architecture:** A new `access_grants` table stores Telegram IDs. The migration imports the current `ALLOWED_USERS` once, middleware permits `ADMIN_ID` directly or checks that table, and handlers mutate it. Telegram command scope exposes management commands only in the administrator's chat.

**Tech Stack:** Python 3.12+, aiogram 3, SQLAlchemy 2 async, Alembic, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-09-28-admin-managed-access-design.md`

## Global Constraints

- `ADMIN_ID` is always allowed and cannot be denied.
- `ALLOWED_USERS` is only a one-time migration source for existing deployments.
- Telegram IDs use `BigInteger`; grants have a unique constraint.
- Every management handler checks `message.from_user.id == ADMIN_ID`.
- `/allow`, `/deny`, and `/allowed` only exist in `BotCommandScopeChat(admin_id)`.
- Keep lines at 88 characters and pass `uv run ruff check app/ tests/`.

---

### Task 1: Add persistent grant storage and migration

**Files:**
- Create: `app/db/models/access_grant.py`
- Create: `app/repositories/access_grant_repository.py`
- Create: `alembic/versions/d4e5f6071829_add_access_grants.py`
- Modify: `app/db/models/__init__.py`, `app/repositories/__init__.py`, `app/db/uow.py`
- Create: `tests/test_access_grant_repository.py`

**Interfaces:**
- Produces `AccessGrant(telegram_id: int, granted_by: int, created_at: datetime)`.
- Produces `is_granted(id) -> bool`, `grant(id, granted_by) -> bool`, `revoke(id) -> bool`, and `list_all() -> list[AccessGrant]` on `uow.access_grants`.

- [ ] **Step 1: Write failing repository tests**

```python
async def test_grant_is_idempotent_and_persistent(uow):
    async with uow:
        assert await uow.access_grants.grant(1001, granted_by=1) is True
        assert await uow.access_grants.grant(1001, granted_by=1) is False
        await uow.commit()
    async with uow:
        assert await uow.access_grants.is_granted(1001) is True

async def test_revoke_reports_whether_a_grant_existed(uow):
    async with uow:
        assert await uow.access_grants.revoke(1001) is False
        await uow.access_grants.grant(1001, granted_by=1)
        assert await uow.access_grants.revoke(1001) is True
```

- [ ] **Step 2: Run `uv run pytest tests/test_access_grant_repository.py -v`**

Expected: FAIL because `uow.access_grants` does not exist.

- [ ] **Step 3: Implement model, repository, and UoW wiring**

```python
async def grant(self, telegram_id: int, granted_by: int) -> bool:
    if await self.is_granted(telegram_id):
        return False
    await self.create(telegram_id=telegram_id, granted_by=granted_by)
    return True
```

Use a unique/indexed `telegram_id`, UTC `created_at`, and delete the matching
model in `revoke`. Import the model through `app.db.models`, export the
repository, and instantiate it in `UnitOfWork.__aenter__`.

- [ ] **Step 4: Create the migration**

Create `access_grants`; then use `get_settings().allowed_users` and
`get_settings().admin_id` to `op.bulk_insert` every distinct configured ID
except the administrator. Downgrade drops its index and table.

- [ ] **Step 5: Run focused tests and `uv run alembic upgrade head`**

Expected: repository tests pass and the configured database migrates.

- [ ] **Step 6: Commit**

```bash
git add app/db/models app/repositories app/db/uow.py alembic/versions tests/test_access_grant_repository.py
git commit -m "feat: persist access grants"
```

### Task 2: Enforce grants in middleware

**Files:**
- Modify: `app/telegram/middleware/access.py`, `app/telegram/dispatcher.py`, `app/main.py`
- Modify: `tests/test_middleware_access.py`

**Interfaces:**
- Consumes `uow.access_grants.is_granted(telegram_id)`.
- Produces `AccessMiddleware(admin_id: int)` and parameterless `create_dispatcher()`.

- [ ] **Step 1: Write failing middleware tests**

```python
async def test_admin_reaches_handler_without_a_database_grant(uow):
    middleware = AccessMiddleware(admin_id=1)
    result = await middleware(_handler, FakeEvent(), {
        "event_from_user": FakeUser(1), "uow": uow,
    })
    assert result == "reached"

async def test_database_grant_reaches_handler(uow):
    async with uow:
        await uow.access_grants.grant(111, granted_by=1)
        await uow.commit()
    middleware = AccessMiddleware(admin_id=1)
    assert await middleware(_handler, FakeEvent(), {
        "event_from_user": FakeUser(111), "uow": uow,
    }) == "reached"
```

- [ ] **Step 2: Run `uv run pytest tests/test_middleware_access.py -v`**

Expected: FAIL because the constructor still accepts `allowed_users`.

- [ ] **Step 3: Implement database authorization**

Permit the administrator before any database lookup. For other users, enter the
injected UoW and call `is_granted`; keep the current private-bot reply for a
missing user, missing UoW, or absent grant. Make the dispatcher read `ADMIN_ID`
internally and update `main.py` to call `create_dispatcher()`.

- [ ] **Step 4: Run focused tests and commit**

```bash
uv run pytest tests/test_middleware_access.py -v
git add app/telegram/middleware/access.py app/telegram/dispatcher.py app/main.py tests/test_middleware_access.py
git commit -m "feat: enforce persistent access grants"
```

### Task 3: Add protected commands and restricted Telegram menu

**Files:**
- Modify: `app/telegram/handlers.py`, `app/main.py`, `tests/test_handlers.py`
- Create: `tests/test_main_commands.py`

**Interfaces:**
- Produces `/allow <telegram_id>`, `/deny <telegram_id>`, and `/allowed`.
- Consumes the four repository methods from Task 1.

- [ ] **Step 1: Write failing handler and menu tests**

```python
async def test_allow_rejects_non_admin(message, uow):
    message.from_user.id = 2
    message.text = "/allow 123"
    await allow_access(message, uow)
    assert "только администратору" in message.answers[0]

async def test_setup_commands_scopes_management_to_admin(bot):
    await _setup_commands(bot, admin_id=1)
    call = bot.set_my_commands.await_args_list[-1]
    assert isinstance(call.kwargs["scope"], BotCommandScopeChat)
    assert {item.command for item in call.args[0]} >= {"allow", "deny", "allowed"}
```

- [ ] **Step 2: Run `uv run pytest tests/test_handlers.py tests/test_main_commands.py -v`**

Expected: FAIL because management handlers and menu entries do not exist.

- [ ] **Step 3: Implement exact command behavior**

Parse exactly one positive integer. Every handler first checks `ADMIN_ID`.
`/allow` reports added or already allowed. `/deny` refuses `ADMIN_ID`, then
reports removed or absent. `/allowed` lists persistent IDs or an empty-list
reply. Add the three commands to only the existing administrator chat scope;
never add them to the default command list.

- [ ] **Step 4: Run focused tests and commit**

```bash
uv run pytest tests/test_handlers.py tests/test_main_commands.py -v
git add app/telegram/handlers.py app/main.py tests/test_handlers.py tests/test_main_commands.py
git commit -m "feat: add admin access commands"
```

### Task 4: Verify the full feature

**Files:**
- Verify: all access-control files from Tasks 1-3.

- [ ] **Step 1: Run migrations**

Run: `uv run python -m app.main --init-db`

Expected: `Database migrations applied.` with no traceback.

- [ ] **Step 2: Run complete tests and lint**

```bash
uv run pytest
uv run ruff check app/ tests/
git diff --check
```

Expected: all tests and lint checks pass; no whitespace errors.

- [ ] **Step 3: Commit the completed feature if earlier task commits were not made**

```bash
git add app alembic tests
git commit -m "feat: let admin manage user access"
```

