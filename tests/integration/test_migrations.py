"""Migration tests: a fresh DB at ``head`` has the full schema and the vocab seeds."""

from __future__ import annotations

from alembic import command
from sqlalchemy import create_engine, inspect, text

from receipt_board.persistence.migrate import make_alembic_config, run_migrations

EXPECTED_TABLES = {
    "checklists",
    "categories",
    "expense_items",
    "resource_types",
    "tools",
    "item_resources",
    "item_tools",
    "audit_log",
    "alembic_version",
}


def _db_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'receipt_board.sqlite').as_posix()}"


def test_run_migrations_creates_schema_and_seeds(tmp_path):
    url = _db_url(tmp_path)
    run_migrations(url)

    engine = create_engine(url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert tables >= EXPECTED_TABLES

        with engine.connect() as conn:
            rtypes = set(conn.execute(text("SELECT name FROM resource_types")).scalars())
            tools = set(conn.execute(text("SELECT name FROM tools")).scalars())
        assert rtypes == {"URL", "Email"}
        assert tools == {"Browser", "Thunderbird"}
    finally:
        engine.dispose()


def test_downgrade_to_base_removes_schema(tmp_path):
    url = _db_url(tmp_path)
    cfg = make_alembic_config(url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = create_engine(url)
    try:
        tables = set(inspect(engine).get_table_names())
        assert "checklists" not in tables
        assert "audit_log" not in tables
    finally:
        engine.dispose()


def test_select_after_migration_works(tmp_path):
    url = _db_url(tmp_path)
    run_migrations(url)
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            count = conn.execute(text("SELECT count(*) FROM checklists")).scalar()
            assert count == 0
    finally:
        engine.dispose()
