"""Dev-only reset-state CLI (``receipt_board.dev_reset``)."""

from __future__ import annotations

from receipt_board import config, dev_reset


def _seed_state(home):
    """Create all four state files under ``home`` and return their paths."""
    db = home / config.DB_FILENAME
    cfg = home / config.CONFIG_FILENAME
    runtime = home / config.RUNTIME_FILENAME
    log = home / dev_reset.LOG_FILENAME
    for path in (db, runtime, log):
        path.write_text("x", encoding="utf-8")
    # config.toml must stay valid TOML: _resolve_targets() parses it.
    cfg.write_text("# seed\n", encoding="utf-8")
    return db, cfg, runtime, log


def test_plan_markers_and_full_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    # Only the config file exists -> it gets [*], everything else [ ].
    (tmp_path / config.CONFIG_FILENAME).write_text("# seed\n", encoding="utf-8")

    targets = dev_reset._resolve_targets()
    dev_reset._print_plan(targets)
    out = capsys.readouterr().out

    assert "The following will be deleted:" in out
    assert f"[*] config   {tmp_path / config.CONFIG_FILENAME}" in out
    assert f"[ ] runtime  {tmp_path / config.RUNTIME_FILENAME}" in out
    # Full paths are printed, not just file names.
    assert str(tmp_path) in out


def test_db_target_honours_custom_database_path(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    custom_db = tmp_path / "elsewhere" / "custom.sqlite"
    custom_db.parent.mkdir()
    config_path = tmp_path / config.CONFIG_FILENAME
    config_path.write_text(f'[database]\npath = "{custom_db.as_posix()}"\n', encoding="utf-8")

    targets = dev_reset._resolve_targets()

    assert targets["db"] == custom_db


def test_selective_deletion_removes_only_config(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    db, cfg, runtime, log = _seed_state(tmp_path)

    rc = dev_reset.run(["--config", "--yes"])

    assert rc == 0
    assert not cfg.exists()
    assert db.exists()
    assert runtime.exists()
    assert log.exists()


def test_all_removes_every_present_target(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    db, cfg, runtime, log = _seed_state(tmp_path)

    rc = dev_reset.run(["--all", "--yes"])

    assert rc == 0
    for path in (db, cfg, runtime, log):
        assert not path.exists()


def test_confirm_abort_deletes_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    db, cfg, runtime, log = _seed_state(tmp_path)

    rc = dev_reset.run(["--all"], input_fn=lambda _prompt: "n")

    assert rc == 0
    for path in (db, cfg, runtime, log):
        assert path.exists()


def test_confirm_yes_deletes(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    db, cfg, runtime, log = _seed_state(tmp_path)

    rc = dev_reset.run(["--all"], input_fn=lambda _prompt: "y")

    assert rc == 0
    for path in (db, cfg, runtime, log):
        assert not path.exists()


def test_yes_flag_skips_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    _seed_state(tmp_path)

    def _boom(_prompt):
        raise AssertionError("prompt must not be called when --yes is passed")

    rc = dev_reset.run(["--config", "--yes"], input_fn=_boom)

    assert rc == 0


def test_db_wal_shm_sidecars_removed(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    db = tmp_path / config.DB_FILENAME
    wal = tmp_path / (config.DB_FILENAME + "-wal")
    shm = tmp_path / (config.DB_FILENAME + "-shm")
    for path in (db, wal, shm):
        path.write_text("x", encoding="utf-8")

    rc = dev_reset.run(["--db", "--yes"])

    assert rc == 0
    assert not db.exists()
    assert not wal.exists()
    assert not shm.exists()


def test_interactive_selection(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    db, cfg, runtime, log = _seed_state(tmp_path)

    # Interactive per-target prompts (db, config, runtime, logs) then the final
    # "Proceed?" confirmation. Select only "config".
    answers = iter(["n", "y", "n", "n", "y"])

    rc = dev_reset.run([], input_fn=lambda _prompt: next(answers))

    assert rc == 0
    assert not cfg.exists()
    assert db.exists()
    assert runtime.exists()
    assert log.exists()


def test_interactive_nothing_selected_exits_zero(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    _seed_state(tmp_path)

    rc = dev_reset.run([], input_fn=lambda _prompt: "n")

    assert rc == 0
    assert "Nothing selected" in capsys.readouterr().out


def test_deletion_error_returns_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_HOME, str(tmp_path))
    _seed_state(tmp_path)

    def _raise(_path):
        raise OSError("locked")

    monkeypatch.setattr(dev_reset, "_delete", _raise)

    rc = dev_reset.run(["--config", "--yes"])

    assert rc == 1
