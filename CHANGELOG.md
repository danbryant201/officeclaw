# Changelog

All notable changes to OfficeClaw are documented here.

## [1.0.6] — 2026-04-18

### Added
- **Calendar body/description** — `calendar create` now accepts `--body` to set an event description (matches existing `calendar update` behaviour).
- **All-day events** — `calendar create` and `calendar update` now accept `--all-day` flag to mark events as all-day.

## [1.0.5] — 2026-04-17

### Added
- **Calendar attendees** — `calendar create` and `calendar update` now accept `--attendee` (repeatable) to invite attendees to events.
- **Attendee allowlist enforcement** — `OFFICECLAW_ALLOWED_RECIPIENTS` now applies to calendar attendees as well as email recipients. Blocked attempts are logged to `calendar-blocked.log` and `calendar-alert.json`.

### Changed
- Extracted shared allowlist logic into `_enforce_recipient_allowlist()` helper, eliminating duplicated code across `mail send`, `calendar create`, and `calendar update`.

## [1.0.4] — 2026-04-04

### Added
- **Recipient Allowlist** (`OFFICECLAW_ALLOWED_RECIPIENTS`) — restrict outbound email to a configurable list of allowed addresses. Blocked attempts are logged and trigger alerts. Critical for AI agent workflows where LLMs control email sending.
- **Runtime warning** when `OFFICECLAW_ENABLE_SEND` is enabled but no recipient allowlist is configured.
- **Blocked email logging** — unauthorized send attempts are written to `email-blocked.log` and an `email-alert.json` file for monitoring integration.

## [1.0.3] — 2026-04-01

### Added
- `--html` flag on `mail send` for sending HTML-formatted email bodies (content type `text/html`).
- Capability gates now load `.env` file before checking environment variables.

## [1.0.2] — 2026-03-16

### Added
- Initial public release on PyPI.
- Email operations: list, get, search, send, reply, forward, archive, move, delete, mark-read.
- Calendar operations: list events, create, update, delete.
- Task operations: list, create, complete.
- Device code OAuth flow (no client secret required).
- Write operations disabled by default (`OFFICECLAW_ENABLE_SEND`, `OFFICECLAW_ENABLE_DELETE`).
- JSON output mode (`--json`).
- OpenClaw skill integration.
