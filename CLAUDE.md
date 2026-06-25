# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

**Receipt Board** is a **desktop application** for managing year-/month-end expense
checklists. The design is specified but **application code has not started yet**. The
authoritative design docs live in `docs/`:

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

_None yet._ Populate with build, lint, test (including how to run a single test), and
run/dev commands once tooling is added.

## Architecture

See `docs/PROJECT_BRIEF.md` §5 and the ADRs (notably `0007` aggregate/persistence,
`0008` concurrency, `0009` privilege token, `0010` integer ids, `0011` CLI transport).
