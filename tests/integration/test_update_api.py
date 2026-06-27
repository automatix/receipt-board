"""Update-check endpoint tests (issue #81): token gate, success, network failure."""

from __future__ import annotations

import threading
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

ASSET = (
    "https://github.com/automatix/receipt-board/releases/download/"
    "v1.4.0/receipt-board-v1.4.0-setup.exe"
)


def _available_info(asset: str | None = ASSET) -> UpdateInfo:
    return UpdateInfo(
        current="1.3.0",
        latest="1.4.0",
        update_available=True,
        notes_url="https://github.com/automatix/receipt-board/releases/tag/v1.4.0",
        asset_url=asset,
    )


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


# -- POST /update/install (issue #82) -----------------------------------------


def test_install_requires_token(client):
    assert client.post("/update/install").status_code == 401


def test_install_launches_and_schedules_shutdown(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        update_api.updates, "check_for_update", lambda current, *, client: _available_info()
    )
    captured: dict = {}

    def fake_download(url, dest_dir, *, client):
        captured["url"] = url
        return tmp_path / "receipt-board-v1.4.0-setup.exe"

    launched: dict = {}
    monkeypatch.setattr(update_api.updates, "download_installer", fake_download)
    monkeypatch.setattr(
        update_api.updates, "launch_installer", lambda path: launched.setdefault("path", path)
    )
    fired = threading.Event()
    client.app.state.shutdown_hook = fired.set
    monkeypatch.setattr(update_api, "SHUTDOWN_DELAY_SECONDS", 0.01)

    resp = client.post("/update/install", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["launched"] is True and body["version"] == "1.4.0"
    assert captured["url"] == ASSET
    assert launched["path"].name == "receipt-board-v1.4.0-setup.exe"
    assert fired.wait(2) is True


def test_install_409_when_up_to_date(client, monkeypatch):
    info = UpdateInfo("1.3.0", "1.3.0", False, "notes", None)
    monkeypatch.setattr(update_api.updates, "check_for_update", lambda current, *, client: info)
    resp = client.post("/update/install", headers=AUTH)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "no_update_available"


def test_install_400_on_untrusted_asset(client, monkeypatch):
    info = _available_info(asset="https://evil.example.com/receipt-board-v1.4.0-setup.exe")
    monkeypatch.setattr(update_api.updates, "check_for_update", lambda current, *, client: info)
    resp = client.post("/update/install", headers=AUTH)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "untrusted_asset"


def test_install_502_on_download_error(client, monkeypatch):
    monkeypatch.setattr(
        update_api.updates, "check_for_update", lambda current, *, client: _available_info()
    )

    def boom(url, dest_dir, *, client):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(update_api.updates, "download_installer", boom)
    resp = client.post("/update/install", headers=AUTH)
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "update_download_failed"


def test_schedule_shutdown_noop_without_hook():
    app = type("A", (), {"state": type("S", (), {})()})()
    assert update_api.schedule_shutdown(app) is False
