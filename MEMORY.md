# MEMORY

## Initialization — `2026-06-24`

- **Request** — User ran `/init` on the empty `Receipt Board` directory. After clarification, chose to initialize an empty repository only (no app scaffolding), with the project intended as a **desktop application**.
- **Done** — Ran the standard init sequence, one commit per step:
  1. `git init` (default branch `main`)
  2. Added `.gitignore` with common exclusions
  3. Added placeholder `README.md`
  4. Added placeholder `CLAUDE.md` (no invented architecture — repo has no code yet)
  5. Added this `MEMORY.md`
- **Result** — Repository initialized with `4` commits of scaffolding plus this record. No tech stack chosen yet; `CLAUDE.md` commands/architecture sections are placeholders awaiting the first real code.

## GitHub remote — `2026-06-24`

- **Request** — Create a GitHub repo `receipt-board` in the personal account namespace; no GitHub Project/board.
- **Done** — Created `private` repo `automatix/receipt-board` via `gh`, added it as `origin` (SSH), pushed `main`.
- **Result** — All init commits are on GitHub at `https://github.com/automatix/receipt-board`. No GitHub Project created.

## Local scratch directory — `2026-06-24`

- **Request** — Create a `local` directory, add it to `.gitignore`, and record it as a global instruction.
- **Done** — Created `local/` (no placeholder file inside), added `local/` to `.gitignore`, committed and pushed. Added a "Local scratch directory" subsection to the global `CLAUDE.md`.
- **Result** — `local/` is fully ignored (verified via `git check-ignore`); the convention now applies to all projects globally.

## Project brief — `2026-06-24`

- **Request** — Analyze the initial project context (Python desktop app for managing year-end receipts/checklists with SQLite + HTML/CSS/JS GUI), ask clarifying questions, then produce a structured project description (idea, architecture, functionality, NFRs) as the kickoff for a later technical-design session.
- **Done** — Read the source checklist (`local/Expenses Checklist 2024_v02.md`) and the init prompt. Asked two rounds of clarifying questions plus one contradiction-resolution question. Wrote `docs/PROJECT_BRIEF.md` capturing all decisions.
- **Result** — Key decisions: `FastAPI` + `pywebview` GUI; `REST` + `CLI` surfaces; `PyInstaller` Windows packaging; `v1` scope = structured store + interface only (no acquisition/file handling); independent lists creatable via import **or** clone; leaf fields `done`/`name`/`resources`/`tools` (default `Browser`)/`data`/`instructions`; **strict** bracket-type import parsing; external write surface limited to **`done`-toggle + read only** (all other writes incl. import/clone are GUI-only) — a deliberate, documented narrowing of the original spec; audit log for all writes; ≥ `90 %` test coverage.

## Domain-modeling grilling session — `2026-06-25`

- **Request** — Run `/grill-with-docs` (grilling interview + domain-modeling skill): relentlessly sharpen the domain model, writing a glossary and ADRs as we go.
- **Done** — Resolved Q1–Q14 one at a time. Maintained `docs/GLOSSARY.md` as the live glossary (deliberately in place of the skill's root `CONTEXT.md` for now, per user) and wrote ADRs `0001`–`0006` in `docs/adr/`. Each decision committed and pushed individually.
- **Result** — Pinned model: actionable leaf = **`Expense Item`**; **`Receipt` not modeled in v1** (ADR-0001); top container = **`Checklist`** (avoid List/Board); **`done` on every node**, semantics external, tool is checkbox-only (ADR-0002) with a **symmetric cascade** keeping `category.done ⇔ whole subtree done`; external interface may **only toggle leaf checkboxes** (ADR-0003); nodes addressed by **globally unique stable `id`** (names need not be unique); action fields are **typed** — `resources` = list of `Resource{type: URL|Email, value}`, `tools` = list of `Tool` (Browser/Thunderbird), `data`/`instructions` free text, all leaf-only; `Tool` & `Resource Type` are **app-wide, GUI-managed controlled vocabularies**; **import is atomic**, validates vocabularies, aborts with a precise report recommending GUI vocab extension (ADR-0005); audit logs **one entry per action + affected ids** (ADR-0004); full GUI structural editing incl. reorder/re-parent (`position` is meaningful); checklist **delete is GUI-only**, clone = deep-copy with `done=false`; **`Period` is name-only** in v1; **node type is explicit**, inferred structurally only at import (ADR-0006). Open for the technical-design session: aggregate/persistence boundary, concurrency, GUI rendering, vocab entry removal/rename integrity, blank-checklist creation, REST contract + GUI-privilege token, detailed import typing rules. `PROJECT_BRIEF.md` now lags these decisions (notably `done`-on-all-nodes and Category semantics) — reconciliation pending.

## Open points grilled + brief alignment — `2026-06-25`

- **Request** — Continue grilling the open points (groups A + B), then align the docs.
- **Done** — Resolved Q15–Q22 (one at a time, interactive). Wrote ADRs `0007`–`0009`, extended the glossary, then rewrote `docs/PROJECT_BRIEF.md` to match glossary + ADRs.
- **Result** — Added decisions: `Resource.value` optional; `tools` has **no** implicit default (supersedes earlier `Browser` default); vocabularies — rename propagates by id, remove only when unused; **blank** is a third checklist-creation path (with import/clone); Export = full nested JSON, Search = flat hits with ancestor path; **Checklist aggregate** with **two tables** (`categories` + `expense_items`, `category_id NOT NULL` so items always live under a category; UUID ids) — ADR-0007; **one SQLite transaction per action, WAL, last-write-wins** — ADR-0008; **GUI session token** protects privileged ops, public surface = read + leaf-toggle — ADR-0009. `PROJECT_BRIEF.md` reconciled and cross-references the glossary + 9 ADRs. Group B (technical) is done too; remaining for the technical session: concrete DB schema, REST contract, import typing details, packaging.

## Technical spec digested — `2026-06-25`

- **Request** — Answer the technical-session agenda en bloc (a `Question:Option` map); digest into a spec.
- **Done** — Resolved blocks A–I. Wrote `docs/TECH_SPEC.md`, `docs/BACKLOG.md` (+ project convention in `CLAUDE.md` that deferred work goes there), and ADRs `0010`/`0011`. Reconciled three conflicts explicitly: integer PKs (override of UUID — ADR-0010, supersedes that note in 0007; ids unique per table, not globally); TypeScript GUI ⇒ a minimal `esbuild` build step (resolves the "no build" vs "TS" conflict, adds Node as a build dep); CLI over local HTTP needs the app running (ADR-0011).
- **Result** — Stack: `Python 3.12+`, `uv`, `ruff` (no `mypy`), `FastAPI`, `SQLite`/`Alembic`, `TypeScript` GUI (no framework, `esbuild`), `pywebview`, `PyInstaller` (`onedir`). Two node tables with integer PKs; minimal indexes in `v1` (FK/`name` indexes + `FTS5` deferred to BACKLOG); audit schema extended with `app_version`/`session_id`; CI coverage gate ≥ `90 %` in GitHub Actions. `TECH_SPEC.md` ends with a task breakdown. Now 11 ADRs total.

## Task breakdown + GitHub issues — `2026-06-25`

- **Request** — Produce the task breakdown and create GitHub issues; implementation in a separate session.
- **Done** — Created milestone `v1` and `area:*` labels; opened **11 issues** (`#1`–`#11`) with scope/acceptance/refs/dependencies. Added `docs/TASKS.md` (issue map + recommended order) and pointed `TECH_SPEC.md` §13 to it.
- **Result** — Issues `automatix/receipt-board#1`–`#11`: bootstrap, CI, persistence, core/cascade/audit, importer, REST API, CLI, GUI build, GUI features, packaging, docs. Order: `#1` → (`#2`∥`#3`) → `#4` → `#5` → `#6` → (`#7`∥`#8`→`#9`) → `#10` → `#11`. No GitHub Project/board (issues only). Implementation to follow in a separate session via the branch/ticket workflow.

## `v1` implementation — `2026-06-25`

- **Request** — Implement all 11 issues end-to-end, verify, and close them via the branch/ticket workflow (one branch+PR per issue, squash-merged).
- **Done** — Installed `uv` (user-space). Shipped, each as its own PR (`#12`–`#22` on GitHub): bootstrap+tooling, GitHub-Actions CI (coverage gate ≥ `90 %` + GUI build job), persistence (SQLAlchemy models, pragmas, Alembic + initial migration with seeds; fixed a pysqlite transaction quirk in `env.py`), core (services, symmetric cascade incl. empty-category rule, audit, errors, read queries), the strict atomic Markdown importer, the `FastAPI` REST API (public/privileged, `X-Session-Token` gate, origin detection, `runtime.json`), the `CLI`, the `TypeScript`/`esbuild` GUI served same-origin at `/app` with token injection, the full GUI features, and `PyInstaller` packaging + first-run/config. Verified the packaged `exe --check` creates the app dir + DB end-to-end. Reconciled the docs (README, `CLAUDE.md` Commands, `TECH_SPEC`, brief UUID→integer).
- **Result** — All `#1`–`#11` closed; CI green; coverage ~`98 %`. **Two user decisions during `#5`:** the importer is **fully strict** (the real reference file is rejected unmodified — `Taxi (klassisch)` / `<DOMAN>`), and the eight bracket chars `()[]{}<>` are **reserved control characters** not allowed in free text (documented in `TECH_SPEC` §6). Deviation: no branded app icon (default used; in `BACKLOG`). `pywebview` window render not headless-verifiable here; served-bundle + CLI-vs-live-server paths are.

## `v1.1` features + release — `2026-06-26`

- **Request** — Implement, test and release 6 issues (`#43`–`#47`, `#49`) autonomously, then cut `v1.1.0` with an EXE artifact.
- **Done** — Shipped each as its own CI-gated PR (squash-merged): `#43` resource-type management (`resource_types` gains `value_optional`/`value_pattern`, migration `0002`, data-driven `VocabularyService` CRUD + duplicate + regex validation, GUI screen); `#44` generic resource notation (`type_resource` is data-driven over `ResourceTypeDef` — `Key:` / bare value / bare key, case-insensitive — and `_set_resources` validates the value vs pattern/optionality); `#45` the checklist dropdown self-refreshes (`act()` reloads checklists); `#46` the add-item dialog reuses the full item editor; `#47` audit read access (`queries.list_audit`, public `GET /audit`, `receipt-board audit`, GUI "Audit" view); `#49` app-data dir renamed `ReceiptBoard` → `receipt-board` (docstring/docs fixed to `%LOCALAPPDATA%`, not Roaming).
- **Result** — All six closed, CI green, coverage ~`97 %`. Verified end-to-end on the packaged build under simulated Mark-of-the-Web: the windowed exe self-unblocks and opens, and the CLI drives the live server (export/search/item-done cascade/audit/validate incl. the new flexible notation). Resource types stay application-wide (GLOSSARY). Released **`v1.1.0`** with `receipt-board-v1.1.0-windows.zip`; `v1.0.x` marked superseded. New backlog ideas (PR `#48`): i18n (default EN), button icons, clarify/remove the Vocabulary + Refresh buttons, an Undo button, installer/uninstaller wizards.
