"""First-run initialisation and app launch (TECH_SPEC §11).

On start: create the app-data directory, write a default ``config.toml`` if missing,
load it, migrate the database to ``head`` (which also seeds the vocabularies on a fresh
DB), seed idempotently for safety, mint a session token, then open the GUI window.

``--check`` performs the first-run initialisation and exits without opening the window —
used to smoke-test the packaged executable (it creates the app folder + DB end-to-end).
"""

from __future__ import annotations

import argparse
import secrets
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from receipt_board import __version__, config
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.migrate import run_migrations
from receipt_board.persistence.seeds import seed_vocabularies


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
