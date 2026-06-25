"""Error mapping to the ``{error: {code, message, details}}`` envelope (TECH_SPEC §9)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from receipt_board.core.errors import (
    DomainError,
    InvalidImportError,
    NotFoundError,
    ValidationError,
    VocabularyInUseError,
)

_DOMAIN_STATUS: dict[type[DomainError], int] = {
    NotFoundError: 404,
    ValidationError: 400,
    VocabularyInUseError: 409,
    InvalidImportError: 400,
}


class ApiError(Exception):
    """API-layer error (e.g. auth) rendered in the same envelope as domain errors."""

    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def _envelope(code: str, message: str, details: dict) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(_request: Request, exc: DomainError) -> JSONResponse:
        status = _DOMAIN_STATUS.get(type(exc), 400)
        return JSONResponse(
            status_code=status, content=_envelope(exc.code, exc.message, exc.details)
        )

    @app.exception_handler(ApiError)
    async def _api(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content=_envelope(exc.code, exc.message, exc.details)
        )
