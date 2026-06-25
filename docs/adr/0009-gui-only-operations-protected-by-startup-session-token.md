# GUI-only operations are protected by a startup session token

The local FastAPI binds to `127.0.0.1` only and exposes two tiers. The **public** surface
— reads (export / search / get) and the single write (leaf `done`-toggle) — needs no auth.
**GUI-privileged** operations (add / edit / remove nodes, Category `done` toggles,
import / clone / delete Checklists, vocabulary maintenance) require a **session token**
generated at app startup and injected **only** into the GUI page (pywebview).

External CLI/AI callers do not have the token and are therefore confined to the public
surface — technically enforcing ADR-0003.

Considered and rejected: separate ports (more setup for no real gain); convention-only
with no enforcement (would not actually prevent a local process from invoking privileged
endpoints).
