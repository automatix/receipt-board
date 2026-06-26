# Receipt Board

A desktop application for managing year-/month-end **expense checklists**: a structured,
hierarchical store of the expense sources whose receipts must be gathered, with a desktop
GUI and a small local programmatic interface (REST + CLI).

`v1` is the structured store plus its interface — receipt acquisition/automation is out of
scope (see [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) §2).

## End-user docs (German)

- **Download (Windows)** — [Releases](https://github.com/automatix/receipt-board/releases) → `receipt-board-vX.Y.Z-windows.zip` (private repo: access required)
- **Installation** — [`docs/INSTALL.md`](docs/INSTALL.md)
- **Bedienungsanleitung** (user guide) — [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)

The rest of this README is the **developer** setup (build/run from source, tests, packaging).

## Architecture

`GUI (pywebview)` → `FastAPI (127.0.0.1, loopback)` → `core/services` → `repository` →
`SQLite (WAL)`. The GUI is a framework-free `TypeScript` app bundled with `esbuild` and
served same-origin by the local server at `/app`; the `CLI` is a thin HTTP client over the
public surface. Writes beyond the leaf `done`-toggle are GUI-only, enforced by a
startup session token. See [`docs/TECH_SPEC.md`](docs/TECH_SPEC.md) and the
[ADRs](docs/adr/README.md).

## Requirements

- **Python `3.12+`** and **[`uv`](https://docs.astral.sh/uv/)** (manages the venv and a
  pinned CPython).
- **Node.js** (`npm`) — only to build the `TypeScript` GUI.
- Windows is the `v1` focus (the packaged app uses Edge WebView2).

## Setup

```bash
uv sync   # creates .venv and installs dependencies (downloads CPython 3.12 if needed)
```

## Build the GUI

The bundled GUI assets (`src/receipt_board/gui/static/`) are generated, not committed:

```bash
cd gui-src
npm ci
npm run typecheck   # strict TypeScript check
npm run build       # esbuild -> ../src/receipt_board/gui/static
```

## Run (development)

Build the GUI first, then:

```bash
uv run receipt-board-app          # opens the native window
# or
uv run python -m receipt_board
```

First run creates the app-data directory (`%LOCALAPPDATA%\receipt-board\` on Windows), writes a
default `config.toml`, migrates the database to `head`, and seeds the controlled
vocabularies. Use `--check` to run first-run initialisation without opening a window:

```bash
uv run receipt-board-app --check
```

## CLI

The CLI talks HTTP to the **running** app (it reads the port from `runtime.json`):

```bash
uv run receipt-board export [--checklist ID] [--json]
uv run receipt-board search "QUERY" [--json]
uv run receipt-board item done ID
uv run receipt-board item undone ID
uv run receipt-board validate PATH [--json]   # dry-run: is a Markdown file importable?
```

Exit code `0` on success, non-zero on error (e.g. the app is not running).

## Tests & linting

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov --cov-report=term-missing --cov-fail-under=90
```

CI (GitHub Actions) runs ruff + pytest with the **≥ 90 %** coverage gate, plus a GUI
typecheck/build job.

## Developer utilities

**`dev-reset` — developer-only, NOT the product uninstaller.** It selectively wipes the
per-user state (`receipt_board.sqlite` + WAL/SHM sidecars, `config.toml`, `runtime.json`,
`receipt-board.log`) so the first-run flow can be re-tested from zero. It honours
`RECEIPT_BOARD_HOME` and any custom `[database].path` in `config.toml`, prints a deletion
plan, and asks for confirmation unless `--yes` is given:

```bash
uv run python -m receipt_board.dev_reset --all --yes    # wipe everything, no prompt
uv run python -m receipt_board.dev_reset --db --config  # only DB + config, with confirmation
scripts/dev-reset.ps1 --all                             # PowerShell wrapper (forwards args)
```

With no category flag (`--db`/`--config`/`--runtime`/`--logs`/`--all`) it offers an
interactive y/N selection per target.

## Packaging

Build the GUI, then create a `onedir`, windowed Windows build:

```bash
uv run pyinstaller receipt_board.spec   # -> dist/receipt-board/receipt-board.exe
```

The GUI assets and Alembic migrations are bundled via the spec. A branded icon can be
added at `packaging/icon.ico` (otherwise the default PyInstaller icon is used).

## Configuration & data

Stored in the app-data directory (override with the `RECEIPT_BOARD_HOME` environment
variable):

- `receipt_board.sqlite` — the database (WAL).
- `config.toml` — `server.port` (`0` = ephemeral) and an optional `database.path`.
- `runtime.json` — the ephemeral port the running server bound to.

## Project layout

```
src/receipt_board/
  core/         domain model, services, cascade, audit, errors, queries
  persistence/  SQLAlchemy models, engine/pragmas, Alembic migrations
  importer/     strict atomic Markdown importer
  api/          FastAPI app, routers (public/privileged), token gate, server
  cli/          HTTP-client CLI
  gui/          window host + bundled static assets (built from gui-src/)
  bootstrap.py  first-run init + app launch
gui-src/        TypeScript GUI sources (esbuild)
tests/          unit + integration
docs/           brief, glossary, ADRs, tech spec, backlog
```

## Documentation

End-user (German): `docs/INSTALL.md`, `docs/USER_GUIDE.md`. Design/spec:
`docs/PROJECT_BRIEF.md`, `docs/GLOSSARY.md`, `docs/adr/`, `docs/TECH_SPEC.md`,
`docs/BACKLOG.md`. On any conflict, the glossary and ADRs win.

## License

MIT.
