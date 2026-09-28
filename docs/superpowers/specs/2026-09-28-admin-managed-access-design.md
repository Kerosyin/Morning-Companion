# Admin-Managed Access Design

## Goal

Only `ADMIN_ID` can grant, revoke, and view bot access by Telegram ID. The
change takes effect immediately and survives restarts. Non-admin users cannot
see the management commands in Telegram's command menu or execute them.

## Data Model

Add an `access_grants` table with a unique `telegram_id`, creation timestamp,
and the administrator ID that granted access. Add an Alembic migration that
copies the current `ALLOWED_USERS` entries into this table exactly once, so
existing users retain access after deployment. `ADMIN_ID` is never stored as a
grant because it is always allowed directly.

## Request Flow

`AccessMiddleware` permits a request when its sender is `ADMIN_ID` or has a
matching `access_grants` row. It receives the request UoW already created by
`UoWMiddleware`, so the lookup shares the handler's database session. The
middleware otherwise returns the current private-bot message.

Admin handlers add `/allow <telegram_id>`, `/deny <telegram_id>`, and
`/allowed`. Each checks `ADMIN_ID` independently before touching the
repository. Invalid IDs receive usage text; adding an existing ID and removing
an absent ID report an explicit no-op result.

At startup, Telegram command definitions for these three commands are set only
for the administrator's private chat. They are not registered in the global
command menu. A user who manually sends one is still rejected by the handler.

## Components

- `app/db/models/access_grant.py`, repository, and UoW exposure own persistent
  grants.
- An Alembic migration creates the table and imports the existing configured
  allowlist.
- `AccessMiddleware` queries grants and always permits the administrator.
- Telegram handlers own validation, authorization, and response text.
- Dispatcher/startup setup owns the administrator-only command scope.

## Failure Handling

Database errors follow the normal handler/UoW rollback path. The migration has
a unique constraint and uses idempotent inserts, preventing duplicate grants.
Command-menu setup is logged; a failure must not stop the bot, because command
authorization remains enforced server-side.

## Tests

Repository tests cover grant, idempotent add, revoke, and list operations.
Middleware tests cover administrator bypass, granted user access, and blocked
users. Handler tests cover admin-only commands, validation, and no-op replies.
Dispatcher tests cover the administrator-only command scope. Migration is
verified against the existing test database configuration.
