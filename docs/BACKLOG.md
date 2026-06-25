# Backlog — deferred ideas

Things deliberately postponed. **Project convention:** whenever something is decided to be
done "later", it is recorded here (not silently dropped). See the project `CLAUDE.md`.

## Deferred

- **DB indexes & search tuning** — add indexes on FK columns (`checklist_id`, `parent_id`,
  `category_id`, `item_id`) and a `name` index; evaluate `FTS5` for search. (`v1` ships a
  minimal schema: PKs + `UNIQUE` on vocabulary names only.)
- **GUI live updates** — reflect external changes (CLI/AI) while the GUI is open, via
  polling or WebSocket/SSE. (`v1` uses after-action reload + a manual refresh button.)
- **Undo** for destructive operations (Category uncheck, node remove, Checklist delete).
  (`v1` guards with confirmation dialogs; the Audit Log provides traceability.)
- **Headless server mode** — let the CLI/AI operate without the GUI window open. (`v1` CLI
  talks HTTP to the running app — see ADR-0011 — so it currently requires the app to run.)
- **Branded app icon** — ship a real `packaging/icon.ico` (the PyInstaller spec already
  uses it when present; `v1` falls back to the default PyInstaller icon).

## Out of scope for `v1` (tracked elsewhere)

- **Receipt entity, file handling, Dropbox hand-off, automation** — see
  [`adr/0001-receipt-not-modeled-in-v1.md`](./adr/0001-receipt-not-modeled-in-v1.md) and
  `PROJECT_BRIEF.md` §2.
- **Structured `Period`** attribute — `v1` conveys the period via the Checklist `name`.
