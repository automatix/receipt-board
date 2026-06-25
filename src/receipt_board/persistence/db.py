"""Engine/session factory and SQLite pragmas (TECH_SPEC §3, ADR-0008).

Every connection gets ``foreign_keys=ON``, ``journal_mode=WAL`` and
``busy_timeout=5000`` so cascades and referential integrity behave as specified and
concurrent GUI/CLI writers do not immediately error on a busy DB.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def _install_pragmas(engine: Engine, *, wal: bool) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        if wal:
            cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


def create_db_engine(db_path: str | Path | None = None, *, echo: bool = False) -> Engine:
    """Create an engine for a file DB (or a shared in-memory DB when ``db_path`` is None).

    The in-memory variant is for tests; it disables WAL (not meaningful in memory) and
    keeps a single shared connection so the schema persists across sessions.
    """
    if db_path is None:
        engine = create_engine(
            "sqlite://",
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        _install_pragmas(engine, wal=False)
        return engine

    url = f"sqlite:///{Path(db_path).as_posix()}"
    engine = create_engine(url, echo=echo, connect_args={"check_same_thread": False})
    _install_pragmas(engine, wal=True)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Transactional scope: commit on success, rollback on error (ADR-0008)."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
