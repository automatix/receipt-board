"""CLI tests against a real (threaded) server, plus offline error paths."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from types import SimpleNamespace

import pytest
import uvicorn

from receipt_board.api.app import create_app
from receipt_board.api.runtime import write_runtime
from receipt_board.api.server import pick_ephemeral_port
from receipt_board.cli import main as cli
from receipt_board.core.audit import AuditService
from receipt_board.core.services import ChecklistService
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.models import Base, ExpenseItem
from receipt_board.persistence.seeds import seed_vocabularies


@pytest.fixture
def live(tmp_path, monkeypatch) -> Iterator[SimpleNamespace]:
    monkeypatch.setenv("RECEIPT_BOARD_HOME", str(tmp_path))
    engine = create_db_engine(None)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)

    with factory() as setup:
        seed_vocabularies(setup)
        svc = ChecklistService(setup, AuditService(setup, origin="GUI"))
        checklist = svc.create_blank("Demo 2024")
        category = svc.add_category(checklist.id, "Verbindung")
        item = svc.add_item(checklist.id, category.id, "1&1", tools=["Browser"])
        setup.commit()
        item_id, checklist_id = item.id, checklist.id

    port = pick_ephemeral_port()
    write_runtime(tmp_path / "runtime.json", port)
    app = create_app(factory, session_token="tok", app_version="test")
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="off")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    try:
        yield SimpleNamespace(factory=factory, item_id=item_id, checklist_id=checklist_id)
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        engine.dispose()


def test_export_list_human(live, capsys):
    assert cli.main(["export"]) == 0
    assert "Demo 2024" in capsys.readouterr().out


def test_export_list_json(live, capsys):
    assert cli.main(["--json", "export"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["name"] == "Demo 2024"


def test_export_single_nested(live, capsys):
    assert cli.main(["--json", "export", "--checklist", str(live.checklist_id)]) == 0
    tree = json.loads(capsys.readouterr().out)
    assert tree["children"][0]["name"] == "Verbindung"


def test_export_single_human_tree(live, capsys):
    assert cli.main(["export", "--checklist", str(live.checklist_id)]) == 0
    out = capsys.readouterr().out
    assert "Verbindung" in out and "1&1" in out


def test_search(live, capsys):
    assert cli.main(["--json", "search", "1&1"]) == 0
    hits = json.loads(capsys.readouterr().out)
    assert hits[0]["name"] == "1&1"


def test_search_human_empty(live, capsys):
    assert cli.main(["search", "zzz-nomatch"]) == 0
    assert "(no matches)" in capsys.readouterr().out


def test_item_done_and_undone(live, capsys):
    assert cli.main(["item", "done", str(live.item_id)]) == 0
    with live.factory() as s:
        assert s.get(ExpenseItem, live.item_id).done is True

    assert cli.main(["item", "undone", str(live.item_id)]) == 0
    with live.factory() as s:
        assert s.get(ExpenseItem, live.item_id).done is False


def test_item_done_uses_cli_origin(live):
    cli.main(["item", "done", str(live.item_id)])
    from sqlalchemy import select

    from receipt_board.persistence.models import AuditEntry

    with live.factory() as s:
        entry = s.scalars(select(AuditEntry).where(AuditEntry.action_type == "set_item_done")).one()
    assert entry.origin == "CLI"


def test_http_error_is_friendly(live, capsys):
    assert cli.main(["item", "done", "99999"]) == 1
    assert "error:" in capsys.readouterr().err


# -- offline error paths (no fixture / no server) -----------------------------


def test_missing_runtime_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RECEIPT_BOARD_HOME", str(tmp_path))  # empty -> no runtime.json
    assert cli.main(["export"]) == 1
    assert "does not appear to be running" in capsys.readouterr().err


def test_connection_refused(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RECEIPT_BOARD_HOME", str(tmp_path))
    write_runtime(tmp_path / "runtime.json", pick_ephemeral_port())  # nothing listens there
    assert cli.main(["export"]) == 1
    assert "Could not connect" in capsys.readouterr().err


def test_invalid_runtime_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RECEIPT_BOARD_HOME", str(tmp_path))
    (tmp_path / "runtime.json").write_text("not json", encoding="utf-8")
    assert cli.main(["export"]) == 1
    assert "invalid" in capsys.readouterr().err
