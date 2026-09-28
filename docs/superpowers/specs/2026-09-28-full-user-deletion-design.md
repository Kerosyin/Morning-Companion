# Full User Deletion Design

## Goal

Only the administrator can permanently remove one Telegram user and all data
associated with that user.

## Flow

The administrator sends `/delete_user <telegram_id>`. The bot reports that
the action is irreversible and asks for `/confirm_delete <telegram_id>`.
Confirmation must match the same ID. A confirmation without a pending request,
or one for another ID, is rejected.

## Deletion Scope

The operation removes the access grant, the user record, messages, memories,
daily activities, health check-ins, critical events, and pending notification
outbox entries addressed to that Telegram ID. User-owned relations are removed
through their existing delete-orphan cascades; outbox records are deleted by
`chat_id`.

No personal content is retained. The administrator receives a completion
message; standard service logs may record only the Telegram ID and deletion
time.

## Authorization And Safety

Both commands require an exact `ADMIN_ID` match. The administrator's own ID
cannot be deleted. Pending confirmations are held in process memory with a
short expiry and are cleared after success or mismatch.

## Tests

Repository tests prove full deletion and outbox cleanup. Handler tests cover
non-admin rejection, invalid IDs, pending confirmation, mismatch, expiry, and
successful deletion. Existing access tests confirm a deleted user no longer
passes middleware.
