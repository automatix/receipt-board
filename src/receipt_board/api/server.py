"""Local server runner: bind an ephemeral loopback port and publish it to ``runtime.json``.

The app binds ``127.0.0.1`` on an ephemeral port (TECH_SPEC §9). The chosen port is
written to ``runtime.json`` so the CLI can find the running app (ADR-0011).
"""

from __future__ import annotations

import socket
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


def serve(
    session_factory: sessionmaker[Session],
    session_token: str,
    *,
    port: int = 0,
    runtime_path: str | Path | None = None,
    app_version: str = __version__,
) -> None:
    """Build the app, reserve a port, publish ``runtime.json``, then run uvicorn (blocking)."""
    app = create_app(session_factory, session_token=session_token, app_version=app_version)
    bound_port = port or pick_ephemeral_port()
    if runtime_path is not None:
        write_runtime(runtime_path, bound_port)
    uvicorn.run(app, host=HOST, port=bound_port, log_level="warning")  # pragma: no cover
