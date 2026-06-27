"""Update-check endpoint tests (issue #81): token gate, success, network failure."""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from receipt_board.api import updates as update_api
from receipt_board.api.app import create_app
from receipt_board.core.updates import UpdateInfo
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.models import Base

TOKEN = "secret-token"
AUTH = {"X-Session-Token": TOKEN}


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_db_engine(None)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    app = create_app(factory, session_token=TOKEN, app_version="1.3.0")
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()


def test_update_check_requires_token(client):
    assert client.get("/update/check").status_code == 401


def test_update_check_reports_available(client, monkeypatch):
    def fake_check(current: str, *, client: httpx.Client) -> UpdateInfo:
        return UpdateInfo(
            current=current,
            latest="1.4.0",
            update_available=True,
            notes_url="https://example/notes",
            asset_url="https://example/receipt-board-v1.4.0-setup.exe",
        )

    monkeypatch.setattr(update_api.updates, "check_for_update", fake_check)
    resp = client.get("/update/check", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["update_available"] is True
    assert body["current"] == "1.3.0" and body["latest"] == "1.4.0"
    assert body["asset_url"].endswith("-setup.exe")


def test_update_check_502_on_network_error(client, monkeypatch):
    def boom(current: str, *, client: httpx.Client) -> UpdateInfo:
        raise httpx.ConnectError("down")

    monkeypatch.setattr(update_api.updates, "check_for_update", boom)
    resp = client.get("/update/check", headers=AUTH)
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "update_check_failed"
