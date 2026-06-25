"""Shared test fixtures.

``engine``/``session`` build the schema in a shared in-memory SQLite DB (fast) and seed
the controlled vocabularies, mirroring a freshly-migrated database.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.models import Base
from receipt_board.persistence.seeds import seed_vocabularies


@pytest.fixture
def engine() -> Engine:
    eng = create_db_engine(None)
    Base.metadata.create_all(eng)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return make_session_factory(engine)


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Session:
    s = session_factory()
    seed_vocabularies(s)
    s.commit()
    try:
        yield s
    finally:
        s.close()
