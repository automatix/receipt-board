"""REST API tests via FastAPI TestClient (TECH_SPEC §9; ADR-0003/0009)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from receipt_board.api.app import create_app
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.models import AuditEntry, Base
from receipt_board.persistence.seeds import seed_vocabularies

TOKEN = "secret-token"
AUTH = {"X-Session-Token": TOKEN}
VALID_FIXTURE = (
    Path(__file__).resolve().parent.parent / "fixtures" / "valid_checklist.md"
).read_text("utf-8")


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_db_engine(None)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as setup:
        seed_vocabularies(setup)
        setup.commit()
    app = create_app(factory, session_token=TOKEN, app_version="test")
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()


def _blank(client: TestClient, name: str = "CL") -> int:
    resp = client.post("/checklists", json={"mode": "blank", "name": name}, headers=AUTH)
    assert resp.status_code == 201
    return resp.json()["id"]


# -- token gate ---------------------------------------------------------------


def test_public_reads_need_no_token(client):
    assert client.get("/checklists").status_code == 200
    assert client.get("/checklists").json() == []


def test_privileged_requires_valid_token(client):
    body = {"mode": "blank", "name": "X"}
    assert client.post("/checklists", json=body).status_code == 401
    assert (
        client.post("/checklists", json=body, headers={"X-Session-Token": "wrong"}).status_code
        == 403
    )
    assert client.post("/checklists", json=body, headers=AUTH).status_code == 201


# -- structural flow ----------------------------------------------------------


def test_create_add_and_nested_export(client):
    cid = _blank(client)
    cat = client.post(f"/checklists/{cid}/categories", json={"name": "Cat"}, headers=AUTH).json()
    item = client.post(
        f"/checklists/{cid}/items",
        json={
            "category_id": cat["id"],
            "name": "1&1",
            "resources": [{"type": "URL", "value": "https://x"}, {"type": "Email"}],
            "tools": ["Browser"],
            "data": "Login",
        },
        headers=AUTH,
    ).json()

    tree = client.get(f"/checklists/{cid}").json()
    assert tree["children"][0]["name"] == "Cat"
    node = tree["children"][0]["children"][0]
    assert node["id"] == item["id"]
    assert node["resources"] == [
        {"type": "URL", "value": "https://x"},
        {"type": "Email", "value": None},
    ]
    assert node["tools"] == ["Browser"]


def test_item_done_is_public_and_cascades(client):
    cid = _blank(client)
    cat = client.post(f"/checklists/{cid}/categories", json={"name": "Cat"}, headers=AUTH).json()
    item = client.post(
        f"/checklists/{cid}/items", json={"category_id": cat["id"], "name": "a"}, headers=AUTH
    ).json()

    resp = client.post(f"/items/{item['id']}/done", json={"done": True})  # no token = public
    assert resp.status_code == 200
    assert {"kind": "category", "id": cat["id"]} in resp.json()["affected_ids"]

    tree = client.get(f"/checklists/{cid}").json()
    assert tree["children"][0]["done"] is True


def test_category_done_is_privileged(client):
    cid = _blank(client)
    cat = client.post(f"/checklists/{cid}/categories", json={"name": "Cat"}, headers=AUTH).json()
    assert client.post(f"/categories/{cat['id']}/done", json={"done": True}).status_code == 401
    assert (
        client.post(f"/categories/{cat['id']}/done", json={"done": True}, headers=AUTH).status_code
        == 200
    )


def test_move_and_edit_and_remove(client):
    cid = _blank(client)
    src = client.post(f"/checklists/{cid}/categories", json={"name": "Src"}, headers=AUTH).json()
    dst = client.post(f"/checklists/{cid}/categories", json={"name": "Dst"}, headers=AUTH).json()
    item = client.post(
        f"/checklists/{cid}/items", json={"category_id": src["id"], "name": "x"}, headers=AUTH
    ).json()

    moved = client.post(
        f"/nodes/expense_item/{item['id']}/move",
        json={"new_parent_id": dst["id"]},
        headers=AUTH,
    )
    assert moved.status_code == 200

    edited = client.patch(f"/items/{item['id']}", json={"name": "y", "data": "d"}, headers=AUTH)
    assert edited.status_code == 200

    assert client.delete(f"/items/{item['id']}", headers=AUTH).status_code == 204


def test_search_returns_flat_hits(client):
    cid = _blank(client)
    cat = client.post(
        f"/checklists/{cid}/categories", json={"name": "Verbindung"}, headers=AUTH
    ).json()
    client.post(
        f"/checklists/{cid}/items", json={"category_id": cat["id"], "name": "1&1"}, headers=AUTH
    )
    hits = client.get("/search", params={"q": "1&1"}).json()
    assert len(hits) == 1
    assert hits[0]["kind"] == "expense_item"
    assert hits[0]["path"] == ["Verbindung"]


# -- import / clone -----------------------------------------------------------


def test_import_via_api(client):
    resp = client.post(
        "/checklists",
        json={"mode": "import", "name": "Imported", "text": VALID_FIXTURE},
        headers=AUTH,
    )
    assert resp.status_code == 201
    tree = client.get(f"/checklists/{resp.json()['id']}").json()
    assert tree["children"]  # imported structure present


def test_import_failure_returns_envelope(client):
    resp = client.post(
        "/checklists",
        json={"mode": "import", "name": "Bad", "text": "- [ ] Top\n\t- [ ] Leaf {Photoshop}\n"},
        headers=AUTH,
    )
    assert resp.status_code == 400
    error = resp.json()["error"]
    assert error["code"] == "invalid_import"
    assert any(e["kind"] == "tool" for e in error["details"]["errors"])


def test_create_checklist_missing_fields(client):
    no_text = client.post("/checklists", json={"mode": "import", "name": "X"}, headers=AUTH)
    assert no_text.status_code == 400
    no_source = client.post("/checklists", json={"mode": "clone", "name": "X"}, headers=AUTH)
    assert no_source.status_code == 400


def test_remove_category_via_api(client):
    cid = _blank(client)
    cat = client.post(f"/checklists/{cid}/categories", json={"name": "Cat"}, headers=AUTH).json()
    edited = client.patch(f"/categories/{cat['id']}", json={"name": "Renamed"}, headers=AUTH)
    assert edited.status_code == 200
    assert client.delete(f"/categories/{cat['id']}", headers=AUTH).status_code == 204
    assert client.get(f"/checklists/{cid}").json()["children"] == []


def test_clone_via_api(client):
    cid = _blank(client, "Source")
    cat = client.post(f"/checklists/{cid}/categories", json={"name": "Cat"}, headers=AUTH).json()
    client.post(
        f"/checklists/{cid}/items", json={"category_id": cat["id"], "name": "x"}, headers=AUTH
    )
    clone = client.post(
        "/checklists", json={"mode": "clone", "name": "Copy", "source_id": cid}, headers=AUTH
    )
    assert clone.status_code == 201
    assert clone.json()["name"] == "Copy"


# -- vocabulary ---------------------------------------------------------------


def test_vocab_crud_and_in_use_block(client):
    assert {r["name"] for r in client.get("/vocab/tool", headers=AUTH).json()} == {
        "Browser",
        "Thunderbird",
    }
    added = client.post("/vocab/tool", json={"name": "Photoshop"}, headers=AUTH).json()
    client.patch(f"/vocab/tool/{added['id']}", json={"name": "GIMP"}, headers=AUTH)
    assert client.delete(f"/vocab/tool/{added['id']}", headers=AUTH).status_code == 204

    # Block removal of an in-use tool.
    cid = _blank(client)
    cat = client.post(f"/checklists/{cid}/categories", json={"name": "Cat"}, headers=AUTH).json()
    client.post(
        f"/checklists/{cid}/items",
        json={"category_id": cat["id"], "name": "x", "tools": ["Browser"]},
        headers=AUTH,
    )
    browser_id = next(
        r["id"] for r in client.get("/vocab/tool", headers=AUTH).json() if r["name"] == "Browser"
    )
    blocked = client.delete(f"/vocab/tool/{browser_id}", headers=AUTH)
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "vocabulary_in_use"


# -- errors -------------------------------------------------------------------


def test_not_found_envelope(client):
    resp = client.get("/checklists/999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_validation_error_envelope(client):
    cid = _blank(client)
    cat = client.post(f"/checklists/{cid}/categories", json={"name": "Cat"}, headers=AUTH).json()
    resp = client.post(
        f"/checklists/{cid}/items",
        json={"category_id": cat["id"], "name": "x", "tools": ["Nope"]},
        headers=AUTH,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"


# -- origin detection ---------------------------------------------------------


def test_origin_detection_in_audit(client):
    cid = _blank(client)
    cat = client.post(f"/checklists/{cid}/categories", json={"name": "Cat"}, headers=AUTH).json()
    item = client.post(
        f"/checklists/{cid}/items", json={"category_id": cat["id"], "name": "a"}, headers=AUTH
    ).json()

    client.post(f"/items/{item['id']}/done", json={"done": True}, headers=AUTH)  # GUI
    client.post(
        f"/items/{item['id']}/done",
        json={"done": False},
        headers={"X-Receipt-Board-Client": "cli"},
    )  # CLI
    client.post(f"/items/{item['id']}/done", json={"done": True})  # REST

    factory = client.app.state.session_factory
    with factory() as s:
        origins = [
            e.origin
            for e in s.scalars(
                select(AuditEntry)
                .where(AuditEntry.action_type == "set_item_done")
                .order_by(AuditEntry.id)
            )
        ]
    assert origins == ["GUI", "CLI", "REST"]
