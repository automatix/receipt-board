# The CLI communicates with the app over local HTTP

The CLI is an **HTTP client** of the running app's local REST API — the public surface only
(reads + leaf `done`-toggle, per ADR-0003) — discovering the port via `runtime.json`
(ADR-0009). It does **not** open the SQLite database in-process.

Consequence: the CLI (and other HTTP/AI clients) **require the app to be running**.

Rationale: all writes flow through a single running server process, giving one
concurrency point and a clear audit origin. Trade-off: no offline CLI use while the app is
closed — a **headless server mode** is recorded in the backlog.

Considered and not chosen: an in-process CLI on the same SQLite file (WAL-safe and would
reuse the shared core, but introduces a second writer process and a separate entry point
outside the server).
