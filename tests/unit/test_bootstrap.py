"""First-run bootstrap and config.toml handling (TECH_SPEC §11)."""

from __future__ import annotations

from sqlalchemy import select

from receipt_board import bootstrap, config
from receipt_board.persistence.models import ResourceType, Tool


def _home(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))


def test_ensure_default_config_creates_toml(tmp_path, monkeypatch):
    _home(tmp_path, monkeypatch)
    path = config.ensure_default_config()
    assert path.exists()
    assert "[server]" in path.read_text(encoding="utf-8")


def test_load_config_defaults(tmp_path, monkeypatch):
    _home(tmp_path, monkeypatch)
    cfg = config.load_config()
    assert cfg.port == 0
    assert cfg.db_path == tmp_path / config.DB_FILENAME


def test_load_config_overrides(tmp_path, monkeypatch):
    _home(tmp_path, monkeypatch)
    custom_db = tmp_path / "custom.sqlite"
    config.config_path().write_text(
        f'[server]\nport = 9123\n[database]\npath = "{custom_db.as_posix()}"\n',
        encoding="utf-8",
    )
    cfg = config.load_config()
    assert cfg.port == 9123
    assert cfg.db_path == custom_db


def test_prepare_initialises_database_and_seeds(tmp_path, monkeypatch):
    _home(tmp_path, monkeypatch)
    prepared = bootstrap.prepare()
    try:
        assert prepared.cfg.db_path.exists()
        assert prepared.token
        with prepared.session_factory() as session:
            assert set(session.scalars(select(ResourceType.name))) == {"URL", "Email"}
            assert set(session.scalars(select(Tool.name))) == {"Browser", "Thunderbird"}
    finally:
        prepared.engine.dispose()


def test_main_check_runs_first_run_and_exits(tmp_path, monkeypatch, capsys):
    _home(tmp_path, monkeypatch)
    assert bootstrap.main(["--check"]) == 0
    assert (tmp_path / config.DB_FILENAME).exists()
    assert (tmp_path / config.CONFIG_FILENAME).exists()
    assert "ready" in capsys.readouterr().out
