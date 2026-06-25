"""Application paths (TECH_SPEC §11, I2).

Resolves the per-user app-data directory via ``platformdirs`` (``%APPDATA%\\ReceiptBoard``
on Windows), overridable with ``RECEIPT_BOARD_HOME`` for tests and portable installs.
Config-file parsing and first-run DB initialisation are layered on in issue #10.
"""

from __future__ import annotations

import os
from pathlib import Path

import platformdirs

APP_NAME = "ReceiptBoard"
DB_FILENAME = "receipt_board.sqlite"
RUNTIME_FILENAME = "runtime.json"
CONFIG_FILENAME = "config.toml"

ENV_HOME = "RECEIPT_BOARD_HOME"


def app_dir() -> Path:
    override = os.environ.get(ENV_HOME)
    if override:
        return Path(override)
    return Path(platformdirs.user_data_dir(APP_NAME, appauthor=False))


def db_path() -> Path:
    return app_dir() / DB_FILENAME


def db_url() -> str:
    return f"sqlite:///{db_path().as_posix()}"


def runtime_path() -> Path:
    return app_dir() / RUNTIME_FILENAME


def config_path() -> Path:
    return app_dir() / CONFIG_FILENAME
