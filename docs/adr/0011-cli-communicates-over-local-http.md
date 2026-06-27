# The CLI communicates with the app over local HTTP

The CLI is an **HTTP client** of the running app's local REST API — the public surface only
(reads + leaf `done`-toggle, per ADR-0003) — discovering the port via `runtime.json`
(ADR-0009). It does **not** open the SQLite database in-process.

Consequence: the CLI (and other HTTP/AI clients) **require a server to be running** — either
the desktop app or the **headless server** (below).

Rationale: all writes flow through a single running server process, giving one
concurrency point and a clear audit origin.

## Headless server mode

`receipt-board-cli serve` runs the same REST server **without** opening the GUI window
(foreground, `Ctrl+C` to stop); it initialises the app data/DB exactly like the desktop app
and publishes `runtime.json`, so the CLI and any HTTP/AI client can drive it. This keeps the
**server as the sole DB owner** — the CLI never opens SQLite in-process, even in `serve`
(the command *is* the server; every other command stays a REST client).

The CLI ships in the normal install as a **console** executable (`receipt-board-cli.exe`,
built alongside the windowed `receipt-board.exe` from one PyInstaller spec) and the install
directory is added to `PATH`, so `receipt-board-cli ...` works from any terminal.

Considered and not chosen: an in-process CLI on the same SQLite file (WAL-safe and would
reuse the shared core, but introduces a second writer process and a separate entry point
outside the server).

Considered and not chosen: an in-process CLI on the same SQLite file (WAL-safe and would
reuse the shared core, but introduces a second writer process and a separate entry point
outside the server).
