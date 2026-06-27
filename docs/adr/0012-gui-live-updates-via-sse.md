# GUI live updates via Server-Sent Events

The GUI reflects state changes **live** by subscribing to a Server-Sent Events stream
(`GET /events`), instead of relying on after-action reloads plus a manual refresh button.
This supersedes the v1 approach noted in TECH_SPEC §7/§8 (and retires the "GUI live updates"
and "Refresh button" backlog items).

How it works: every mutation records exactly one audit entry (ADR-0004), so the audit write
is the single chokepoint. The request scope bumps a process-wide, monotonic **revision** on
an in-process event bus after the per-action transaction commits (ADR-0008: one transaction
per action). Open subscribers receive the new revision and reload; a burst is coalesced into
one refresh. Because all writes flow through the one running server (ADR-0011), external
changes (CLI/REST/automation) trigger the same events as GUI actions — so the window stays
current with no user action.

The `/events` endpoint is **public** (not token-gated, unlike privileged writes — ADR-0009):
the browser `EventSource` API cannot send custom headers, so it cannot carry the session
token, and the payload is a non-sensitive revision marker only (never content). The actual
reload uses the existing endpoints. The GUI keeps the revision to catch up after a reconnect,
and `EventSource` reconnects on its own.

Consequence: no manual refresh anywhere; the single SSE-driven reload path also removes the
double-render that a per-action reload plus an echoing event would cause. Trade-off: the
in-memory revision resets when the app restarts — harmless, since the GUI restarts with it
and reloads on connect. The bus is single-process and in-memory (the app is one local
process with typically one window); a multi-process design was unnecessary.

Considered and not chosen: client polling (simpler, but periodic network churn and higher
latency than a pushed event) and WebSockets (bidirectional and heavier than needed for a
one-way change signal).
