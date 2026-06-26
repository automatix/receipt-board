"""First-run initialisation and app launch (TECH_SPEC §11).

On start: create the app-data directory, write a default ``config.toml`` if missing,
load it, migrate the database to ``head`` (which also seeds the vocabularies on a fresh
DB), seed idempotently for safety, mint a session token, then open the GUI window.

``--check`` performs the first-run initialisation and exits without opening the window —
used to smoke-test the packaged executable (it creates the app folder + DB end-to-end).
"""

from __future__ import annotations

import argparse
import contextlib
import os
import secrets
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from receipt_board import __version__, config
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.migrate import run_migrations
from receipt_board.persistence.seeds import seed_vocabularies


def ensure_writable_streams() -> None:
    """Redirect ``sys.stdout``/``sys.stderr`` to a log file when they are ``None``.

    A ``--windowed`` PyInstaller build has no console, so both streams are ``None``;
    anything that writes to them (uvicorn logging, ``print``) would crash. Point them at
    ``receipt-board.log`` in the app dir (falling back to the null device).
    """
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        sink = open(  # noqa: SIM115 (kept open for the app's lifetime)
            config.app_dir() / "receipt-board.log", "a", encoding="utf-8", buffering=1
        )
    except OSError:
        sink = open(os.devnull, "w")  # noqa: SIM115
    if sys.stdout is None:
        sys.stdout = sink
    if sys.stderr is None:
        sys.stderr = sink


def unblock_bundle() -> None:
    """Strip the Mark-of-the-Web (``Zone.Identifier``) from the frozen bundle.

    A downloaded+extracted onedir build carries the Internet-zone tag on every file; the
    .NET CLR then refuses to load the managed ``Python.Runtime.dll`` (pywebview → pythonnet)
    and the app crashes at startup. Removing the tag before the GUI loads .NET — the same
    thing ``Unblock-File`` does — fixes it. Frozen builds only; per-file failures (e.g. a
    read-only install directory, or a file in use) are ignored.
    """
    if not getattr(sys, "frozen", False):
        return
    meipass = getattr(sys, "_MEIPASS", None)
    base = Path(meipass) if meipass else Path(sys.executable).resolve().parent
    for path in base.rglob("*"):
        with contextlib.suppress(OSError):
            os.remove(f"{path}:Zone.Identifier")


@dataclass
class Prepared:
    engine: Engine
    session_factory: sessionmaker[Session]
    cfg: config.Config
    token: str


def prepare() -> Prepared:
    """Run first-run initialisation and return everything needed to serve the app."""
    config.ensure_app_dir()
    config.ensure_default_config()
    cfg = config.load_config()

    db_url = f"sqlite:///{cfg.db_path.as_posix()}"
    run_migrations(db_url)

    engine = create_db_engine(cfg.db_path)
    factory = make_session_factory(engine)
    with factory() as session:
        seed_vocabularies(session)
        session.commit()

    return Prepared(
        engine=engine, session_factory=factory, cfg=cfg, token=secrets.token_urlsafe(32)
    )


def main(argv: Sequence[str] | None = None) -> int:
    config.ensure_app_dir()
    ensure_writable_streams()
    unblock_bundle()

    parser = argparse.ArgumentParser(
        prog="receipt-board-app", description="Receipt Board desktop application."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="initialise the app data + database and exit (no window)",
    )
    args = parser.parse_args(argv)

    prepared = prepare()

    if args.check:
        print(
            f"Receipt Board {__version__} ready. "
            f"App dir: {config.app_dir()} | DB: {prepared.cfg.db_path}"
        )
        prepared.engine.dispose()
        return 0

    from receipt_board.gui.launch import launch  # pragma: no cover

    launch(  # pragma: no cover
        prepared.session_factory,
        prepared.token,
        port=prepared.cfg.port,
        runtime_path=config.runtime_path(),
        app_version=__version__,
    )
    return 0  # pragma: no cover
