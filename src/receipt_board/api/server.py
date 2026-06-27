"""Local server runner: bind an ephemeral loopback port and publish it to ``runtime.json``.

The app binds ``127.0.0.1`` on an ephemeral port (TECH_SPEC §9). The chosen port is
written to ``runtime.json`` so the CLI can find the running app (ADR-0011).
"""

from __future__ import annotations

import socket
from collections.abc import Callable
from pathlib import Path

import uvicorn
from sqlalchemy.orm import Session, sessionmaker

from receipt_board import __version__
from receipt_board.api.app import create_app
from receipt_board.api.runtime import write_runtime

HOST = "127.0.0.1"


def pick_ephemeral_port(host: str = HOST) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def build_config(app: Callable, port: int) -> uvicorn.Config:
    """uvicorn config for the local server.

    ``log_config=None`` is essential: a ``--windowed`` PyInstaller build has
    ``sys.stdout``/``sys.stderr`` set to ``None``, and uvicorn's default log formatters
    call ``sys.stdout.isatty()`` at init, which crashes. The desktop app needs no console
    logger.
    """
    return uvicorn.Config(
        app,
        host=HOST,
        port=port,
        log_level="warning",
        lifespan="off",
        log_config=None,
    )


def build_server(
    session_factory: sessionmaker[Session],
    session_token: str,
    *,
    port: int = 0,
    runtime_path: str | Path | None = None,
    app_version: str = __version__,
    gui_dir: str | Path | None = None,
) -> tuple[uvicorn.Server, int]:
    """Build the app, reserve a port, publish ``runtime.json`` and return ``(server, port)``.

    Does everything up to (but not including) the blocking ``server.run()`` so callers can
    run it in the foreground (headless ``serve``) or a thread (tests).
    """
    app = create_app(
        session_factory, session_token=session_token, app_version=app_version, gui_dir=gui_dir
    )
    bound_port = port or pick_ephemeral_port()
    if runtime_path is not None:
        write_runtime(runtime_path, bound_port)
    return uvicorn.Server(build_config(app, bound_port)), bound_port


def serve(
    session_factory: sessionmaker[Session],
    session_token: str,
    *,
    port: int = 0,
    runtime_path: str | Path | None = None,
    app_version: str = __version__,
    gui_dir: str | Path | None = None,
) -> None:
    """Run the local server in the foreground (headless mode — no GUI window).

    Blocks until interrupted (Ctrl+C). The CLI/automation then drives it over REST, exactly
    as it does the windowed app (ADR-0011) — the server stays the sole owner of the DB.
    """
    server, bound_port = build_server(
        session_factory,
        session_token,
        port=port,
        runtime_path=runtime_path,
        app_version=app_version,
        gui_dir=gui_dir,
    )
    print(  # noqa: T201 (headless console output is intentional)
        f"Receipt Board {app_version} serving on http://{HOST}:{bound_port}/  (Ctrl+C to stop)",
        flush=True,
    )
    server.run()  # pragma: no cover (blocking)
