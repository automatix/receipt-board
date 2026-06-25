"""Domain error types (TECH_SPEC §4 C3), mapped centrally to REST/CLI errors."""

from __future__ import annotations


class DomainError(Exception):
    """Base class; carries a stable ``code`` and optional ``details`` for the API."""

    code = "domain_error"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(DomainError):
    code = "not_found"


class ValidationError(DomainError):
    code = "validation_error"


class VocabularyInUseError(DomainError):
    code = "vocabulary_in_use"


class InvalidImportError(DomainError):
    code = "invalid_import"
