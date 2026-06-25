"""Alembic migration environment.

The DB URL comes from (in order): the ``sqlalchemy.url`` main option set
programmatically, the ``RECEIPT_BOARD_DB_URL`` environment variable, or the
``alembic.ini`` value. ``foreign_keys=ON`` is enabled on the migration connection.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, event, pool

from receipt_board.persistence.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        url = os.environ.get("RECEIPT_BOARD_DB_URL", "")
    if not url:
        raise RuntimeError(
            "No database URL configured. Set sqlalchemy.url or RECEIPT_BOARD_DB_URL."
        )
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _resolve_url()
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)

    # pysqlite mismanages implicit transactions (DDL auto-commits, DML can be lost).
    # Hand transaction control to SQLAlchemy/Alembic so schema + seeds commit atomically.
    @event.listens_for(connectable, "connect")
    def _sqlite_on_connect(dbapi_connection, _record):  # noqa: ANN001
        dbapi_connection.isolation_level = None
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @event.listens_for(connectable, "begin")
    def _sqlite_on_begin(connection):  # noqa: ANN001
        connection.exec_driver_sql("BEGIN")

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
