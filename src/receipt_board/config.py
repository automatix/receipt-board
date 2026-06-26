"""Application paths (TECH_SPEC §11, I2).

Resolves the per-user app-data directory via ``platformdirs``
(``%LOCALAPPDATA%\\receipt-board`` on Windows — ``user_data_dir`` is Local, not Roaming),
overridable with ``RECEIPT_BOARD_HOME`` for tests and portable installs.
Config-file parsing and first-run DB initialisation are layered on in issue #10.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

import platformdirs

APP_NAME = "receipt-board"
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


DEFAULT_CONFIG_TOML = """\
# Receipt Board configuration.
[server]
# Fixed loopback port; 0 = pick an ephemeral port on each start.
port = 0

[database]
# Absolute path to override the SQLite database location.
# path = ""
"""


@dataclass
class Config:
    port: int
    db_path: Path


def ensure_app_dir() -> Path:
    directory = app_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def ensure_default_config() -> Path:
    path = config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
    return path


def load_config() -> Config:
    """Load ``config.toml`` (structured), falling back to defaults for missing keys."""
    data: dict = {}
    path = config_path()
    if path.exists():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    server = data.get("server", {})
    database = data.get("database", {})
    port = int(server.get("port", 0) or 0)
    override = database.get("path")
    resolved_db = Path(override) if override else db_path()
    return Config(port=port, db_path=resolved_db)
