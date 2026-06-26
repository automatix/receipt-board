# Backlog — deferred ideas

Things deliberately postponed. **Project convention:** whenever something is decided to be
done "later", it is recorded here (not silently dropped). See the project `CLAUDE.md`.

## Deferred

- **DB indexes & search tuning** — add indexes on FK columns (`checklist_id`, `parent_id`,
  `category_id`, `item_id`) and a `name` index; evaluate `FTS5` for search. (`v1` ships a
  minimal schema: PKs + `UNIQUE` on vocabulary names only.)
- **GUI live updates** — reflect external changes (CLI/AI) while the GUI is open, via
  polling or WebSocket/SSE. (`v1` uses after-action reload + a manual refresh button.)
- **Undo** for destructive operations (Category uncheck, node remove, Checklist delete),
  including a dedicated **"Undo" button** in the GUI. (`v1` guards with confirmation
  dialogs; the Audit Log provides traceability.)
- **Headless server mode** — let the CLI/AI operate without the GUI window open. (`v1` CLI
  talks HTTP to the running app — see ADR-0011 — so it currently requires the app to run.)
- **Internationalization (i18n)** — translatable UI strings with a **default language of
  English** (the app currently ships German strings); aligns with the global
  English-as-default decision.
- **Button icons** — add icons to the toolbar/row buttons (distinct from the branded app
  icon above).
- **Clarify / possibly remove the "Vocabulary" button** — its purpose is unclear; evaluate
  folding it into the resource-type / vocabulary management or dropping it.
- **Clarify / possibly remove the "Refresh" button** — once the checklist dropdown stays
  current automatically (#45), the manual refresh may be redundant.

## Out of scope for `v1` (tracked elsewhere)

- **Receipt entity, file handling, Dropbox hand-off, automation** — see
  [`adr/0001-receipt-not-modeled-in-v1.md`](./adr/0001-receipt-not-modeled-in-v1.md) and
  `PROJECT_BRIEF.md` §2.
- **Structured `Period`** attribute — `v1` conveys the period via the Checklist `name`.
