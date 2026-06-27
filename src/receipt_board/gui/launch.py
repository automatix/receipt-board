"""Run the local server and open the GUI window (TECH_SPEC §7).

Serves the app (with the GUI mounted at ``/app``) on an ephemeral loopback port in a
background thread, publishes the port to ``runtime.json``, then opens the native window.
The blocking pieces (uvicorn, pywebview) are not exercised in CI.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import uvicorn
from sqlalchemy.orm import Session, sessionmaker

from receipt_board import __version__
from receipt_board.api.app import create_app
from receipt_board.api.runtime import write_runtime
from receipt_board.api.server import HOST, build_config, pick_ephemeral_port
from receipt_board.gui.window import open_window, static_dir


def gui_url(port: int) -> str:
    return f"http://{HOST}:{port}/app/"


def launch(  # pragma: no cover
    session_factory: sessionmaker[Session],
    session_token: str,
    *,
    port: int = 0,
    runtime_path: str | Path | None = None,
    app_version: str = __version__,
    title: str = "Receipt Board",
) -> None:
    app = create_app(
        session_factory,
        session_token=session_token,
        app_version=app_version,
        gui_dir=static_dir(),
    )
    bound_port = port or pick_ephemeral_port()
    if runtime_path is not None:
        write_runtime(runtime_path, bound_port)

    server = uvicorn.Server(build_config(app, bound_port))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)

    def _register_shutdown(window: object) -> None:
        # Let the updater (POST /update/install) close the window after launching the
        # installer, so the running app releases its files for replacement.
        app.state.shutdown_hook = window.destroy

    try:
        open_window(gui_url(bound_port), session_token, title=title, on_window=_register_shutdown)
    finally:
        server.should_exit = True
        thread.join(timeout=5)
