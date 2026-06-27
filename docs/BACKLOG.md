# Backlog — deferred ideas

Things deliberately postponed. **Project convention:** whenever something is decided to be
done "later", it is recorded here (not silently dropped). See the project `CLAUDE.md`.

## Deferred

- **DB indexes & search tuning** — add indexes on FK columns (`checklist_id`, `parent_id`,
  `category_id`, `item_id`) and a `name` index; evaluate `FTS5` for search. (`v1` ships a
  minimal schema: PKs + `UNIQUE` on vocabulary names only.)
- **Undo** for destructive operations (Category uncheck, node remove, Checklist delete),
  including a dedicated **"Undo" button** in the GUI. (`v1` guards with confirmation
  dialogs; the Audit Log provides traceability.)
- **Clarify / possibly remove the "Vocabulary" button** — its purpose is unclear; evaluate
  folding it into the resource-type / vocabulary management or dropping it.
- **Home button** — a toolbar button that returns to a default view (the active checklist's
  tree, with search/overlays closed). Complements the back/forward navigation (issue #107).

## Out of scope for `v1` (tracked elsewhere)

- **Receipt entity, file handling, Dropbox hand-off, automation** — see
  [`adr/0001-receipt-not-modeled-in-v1.md`](./adr/0001-receipt-not-modeled-in-v1.md) and
  `PROJECT_BRIEF.md` §2.
- **Structured `Period`** attribute — `v1` conveys the period via the Checklist `name`.
