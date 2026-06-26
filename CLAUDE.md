# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

**Receipt Board** is a **desktop application** for managing year-/month-end expense
checklists. `v1` is **implemented** (issues `#1`–`#11`): persistence, core services +
cascade, the strict atomic importer, the `FastAPI` REST API, the `CLI`, the `TypeScript`
GUI, and `PyInstaller` packaging. The authoritative design docs live in `docs/`:

- `docs/PROJECT_BRIEF.md` — overview (idea, scope, architecture, NFRs)
- `docs/GLOSSARY.md` — ubiquitous language
- `docs/adr/` — Architecture Decision Records
- `docs/TECH_SPEC.md` — detailed technical specification
- `docs/BACKLOG.md` — deferred ideas

On any conflict, `GLOSSARY.md` + ADRs win.

## Tech stack (decided)

`Python` `3.12+` backend, `FastAPI` (local REST), `SQLite` (WAL) via `Alembic` migrations;
GUI in `TypeScript` + `HTML`/`CSS` (no framework, minimal `esbuild` build) shown in a
`pywebview` window; `CLI` over local HTTP. Tooling: `uv`, `ruff`. Packaged with
`PyInstaller`. See `docs/TECH_SPEC.md` for specifics.

## Conventions

- **Deferred work goes to `docs/BACKLOG.md`** — whenever something is decided to be done
  "later" / "für später", record it there instead of dropping it silently.
- Keep `docs/GLOSSARY.md`, the ADRs, `PROJECT_BRIEF.md`, and `TECH_SPEC.md` consistent as
  decisions evolve.

## Commands

All Python commands run through `uv` (managed `CPython` `3.12`). The GUI build needs
`Node.js`.

```bash
# Setup
uv sync                              # create the venv + install deps (downloads CPython 3.12)

# Lint / format
uv run ruff check .
uv run ruff format .                 # add --check in CI

# Tests
uv run pytest                                            # full suite
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90   # with the CI coverage gate
uv run pytest tests/unit/test_cascade.py::test_no_op_toggle_changes_nothing  # a single test

# GUI build (TypeScript -> src/receipt_board/gui/static via esbuild)
cd gui-src && npm ci && npm run typecheck && npm run build

# Run the app (build the GUI first); first run creates %LOCALAPPDATA%\receipt-board\
uv run receipt-board-app             # or: uv run python -m receipt_board
uv run receipt-board-app --check     # first-run init only, no window (smoke test)

# CLI (needs the app running; reads runtime.json for the port)
uv run receipt-board export [--checklist ID] [--json]
uv run receipt-board search QUERY [--json]
uv run receipt-board item done|undone ID

# Migrations (URL via env var for the CLI; the app migrates automatically at first run)
RECEIPT_BOARD_DB_URL="sqlite:///path/to.sqlite" uv run alembic upgrade head

# Packaging (build the GUI first) -> dist/receipt-board/
uv run pyinstaller receipt_board.spec
```

`RECEIPT_BOARD_HOME` overrides the app-data directory (used by tests and portable installs).

## Architecture

See `docs/PROJECT_BRIEF.md` §5 and the ADRs (notably `0007` aggregate/persistence,
`0008` concurrency, `0009` privilege token, `0010` integer ids, `0011` CLI transport).
