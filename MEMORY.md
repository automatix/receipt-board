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
