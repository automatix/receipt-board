"""Programmatic Alembic runner.

Used at first-run (issue #10) and in tests to bring a DB to ``head`` without relying
on a working-directory-relative ``alembic.ini``. Resolves the migrations directory
relative to this package so it also works inside a PyInstaller bundle.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def _migrations_dir() -> Path:
    return Path(__file__).resolve().parent / "migrations"


def make_alembic_config(db_url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_migrations_dir()))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def run_migrations(db_url: str, revision: str = "head") -> None:
    """Upgrade the database at ``db_url`` to ``revision`` (default ``head``)."""
    command.upgrade(make_alembic_config(db_url), revision)
