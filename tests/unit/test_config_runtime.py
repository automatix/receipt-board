"""Config paths and runtime.json round-trip."""

from __future__ import annotations

from receipt_board import config
from receipt_board.api import server
from receipt_board.api.runtime import read_port, write_runtime
from receipt_board.api.server import pick_ephemeral_port
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.models import Base


def test_app_dir_honours_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    assert config.app_dir() == tmp_path
    assert config.db_path() == tmp_path / config.DB_FILENAME
    assert config.runtime_path() == tmp_path / config.RUNTIME_FILENAME
    assert config.config_path() == tmp_path / config.CONFIG_FILENAME
    assert config.db_url() == f"sqlite:///{(tmp_path / config.DB_FILENAME).as_posix()}"


def test_app_dir_default_uses_platformdirs(monkeypatch):
    monkeypatch.delenv(config.ENV_HOME, raising=False)
    assert config.APP_NAME in str(config.app_dir())


def test_runtime_roundtrip(tmp_path):
    path = tmp_path / "runtime.json"
    write_runtime(path, 54321)
    assert read_port(path) == 54321


def test_pick_ephemeral_port_is_usable():
    port = pick_ephemeral_port()
    assert 1024 < port < 65536


def test_serve_writes_runtime_and_builds_app(tmp_path, monkeypatch):
    captured = {}
    monkeypatch.setattr(server.uvicorn, "run", lambda app, **kw: captured.update(kw, app=app))
    engine = create_db_engine(None)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    try:
        runtime_file = tmp_path / "runtime.json"
        server.serve(factory, "tok", port=12345, runtime_path=runtime_file)
        assert read_port(runtime_file) == 12345
        assert captured["port"] == 12345
        assert captured["host"] == server.HOST
    finally:
        engine.dispose()
