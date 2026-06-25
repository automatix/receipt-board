"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from receipt_board import __version__
from receipt_board.api.errors import register_error_handlers
from receipt_board.api.routers import privileged_router, public_router


def create_app(
    session_factory: sessionmaker[Session],
    *,
    session_token: str,
    app_version: str = __version__,
) -> FastAPI:
    app = FastAPI(title="Receipt Board", version=app_version)
    app.state.session_factory = session_factory
    app.state.session_token = session_token
    app.state.app_version = app_version

    register_error_handlers(app)
    app.include_router(public_router)
    app.include_router(privileged_router)
    return app
