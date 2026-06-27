"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, sessionmaker

from receipt_board import __version__
from receipt_board.api.errors import register_error_handlers
from receipt_board.api.routers import privileged_router, public_router
from receipt_board.core.events import EventBus


def create_app(
    session_factory: sessionmaker[Session],
    *,
    session_token: str,
    app_version: str = __version__,
    gui_dir: str | Path | None = None,
) -> FastAPI:
    app = FastAPI(title="Receipt Board", version=app_version)
    app.state.session_factory = session_factory
    app.state.session_token = session_token
    app.state.app_version = app_version
    app.state.event_bus = EventBus()

    register_error_handlers(app)
    app.include_router(public_router)
    app.include_router(privileged_router)

    # Serve the bundled GUI same-origin at /app (only when it has been built).
    if gui_dir is not None and (Path(gui_dir) / "index.html").exists():
        app.mount("/app", StaticFiles(directory=str(gui_dir), html=True), name="gui")

    return app
