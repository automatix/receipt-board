"""CLI tests against a real (threaded) server, plus offline error paths."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from types import SimpleNamespace

import httpx
import pytest
import uvicorn
from sqlalchemy import select

from receipt_board.api.app import create_app
from receipt_board.api.runtime import write_runtime
from receipt_board.api.server import pick_ephemeral_port
from receipt_board.cli import main as cli
from receipt_board.core.audit import AuditService
from receipt_board.core.services import ChecklistService
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.models import AuditEntry, Base
from receipt_board.persistence.seeds import seed_vocabularies


def _eventually(check, *, tries: int = 100, delay: float = 0.05):
    """Retry ``check`` until truthy (covers the API's commit-after-response window)."""
    result = None
    for _ in range(tries):
        result = check()
        if result:
            return result
        time.sleep(delay)
    return result


def _find_node(tree: dict, node_id: int):
    for child in tree.get("children", []):
        if child["kind"] == "expense_item" and child["id"] == node_id:
            return child
        found = _find_node(child, node_id)
        if found:
            return found
    return None


@pytest.fixture
def live(tmp_path, monkeypatch) -> Iterator[SimpleNamespace]:
    monkeypatch.setenv("RECEIPT_BOARD_HOME", str(tmp_path))
    # A file DB (not the shared in-memory StaticPool): the uvicorn thread and the
    # verifying test thread then use independent connections, so there is no shared
    # transaction-state race ("cannot rollback - no transaction is active").
    engine = create_db_engine(tmp_path / "test.sqlite")
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
        yield SimpleNamespace(
            factory=factory,
            item_id=item_id,
            checklist_id=checklist_id,
            base_url=f"http://127.0.0.1:{port}",
        )
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


def test_json_flag_accepted_after_subcommand(live, capsys):
    # --json must work trailing (as documented), not only before the subcommand.
    assert cli.main(["search", "1&1", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["name"] == "1&1"

    assert cli.main(["export", "--json"]) == 0
    assert isinstance(json.loads(capsys.readouterr().out), list)

    assert cli.main(["item", "done", str(live.item_id), "--json"]) == 0
    assert "affected_ids" in json.loads(capsys.readouterr().out)


def test_search_human_empty(live, capsys):
    assert cli.main(["search", "zzz-nomatch"]) == 0
    assert "(no matches)" in capsys.readouterr().out


def _item_done(live, *, expected: bool) -> bool:
    tree = httpx.get(f"{live.base_url}/checklists/{live.checklist_id}").json()
    node = _find_node(tree, live.item_id)
    return node is not None and node["done"] is expected


def test_item_done_and_undone(live):
    assert cli.main(["item", "done", str(live.item_id)]) == 0
    assert _eventually(lambda: _item_done(live, expected=True))

    assert cli.main(["item", "undone", str(live.item_id)]) == 0
    assert _eventually(lambda: _item_done(live, expected=False))


def test_item_done_uses_cli_origin(live):
    assert cli.main(["item", "done", str(live.item_id)]) == 0

    def origin() -> str | None:
        with live.factory() as s:
            entry = s.scalar(select(AuditEntry).where(AuditEntry.action_type == "set_item_done"))
            return entry.origin if entry else None

    assert _eventually(lambda: origin() == "CLI")


def test_http_error_is_friendly(live, capsys):
    assert cli.main(["item", "done", "99999"]) == 1
    assert "error:" in capsys.readouterr().err


def test_validate_command(live, tmp_path, capsys):
    good = tmp_path / "good.md"
    good.write_text("- [ ] Top\n\t- [ ] Leaf\n", encoding="utf-8")
    assert cli.main(["validate", str(good)]) == 0
    assert "importierbar" in capsys.readouterr().out.lower()

    bad = tmp_path / "bad.md"
    bad.write_text("- [ ] Top\n\t- [ ] Leaf {Photoshop}\n", encoding="utf-8")
    assert cli.main(["validate", str(bad)]) == 1
    assert "Photoshop" in capsys.readouterr().out


def test_validate_missing_file(live, capsys):
    assert cli.main(["validate", "does-not-exist.md"]) == 1
    assert "Cannot read" in capsys.readouterr().err


def test_audit_command(live, capsys):
    assert cli.main(["--json", "audit"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows
    assert {"create_checklist", "add_category", "add_item"} <= {r["action_type"] for r in rows}

    assert cli.main(["audit", "--checklist", str(live.checklist_id), "--limit", "10"]) == 0
    assert "add_item" in capsys.readouterr().out


# -- serve (headless) parsing -------------------------------------------------


def test_serve_subcommand_parses():
    args = cli.build_parser().parse_args(["serve"])
    assert args.command == "serve"
    assert args.port == 0  # ephemeral by default

    args = cli.build_parser().parse_args(["serve", "--port", "8123"])
    assert args.port == 8123


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
