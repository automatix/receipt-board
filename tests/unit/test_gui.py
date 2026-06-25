"""GUI host: token-injection script, served-app URL, and the /app static mount."""

from __future__ import annotations

from fastapi.testclient import TestClient

from receipt_board.api.app import create_app
from receipt_board.gui.launch import gui_url
from receipt_board.gui.window import config_script, index_path
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.models import Base


def _factory():
    engine = create_db_engine(None)
    Base.metadata.create_all(engine)
    return make_session_factory(engine), engine


def test_config_script_injects_escaped_token():
    script = config_script('a"b\\c')
    assert "window.__RECEIPT_BOARD__" in script
    assert '"a\\"b\\\\c"' in script  # JSON-escaped


def test_index_path_is_in_static_dir():
    path = index_path()
    assert path.name == "index.html"
    assert path.parent.name == "static"


def test_gui_url():
    assert gui_url(1234) == "http://127.0.0.1:1234/app/"


def test_gui_not_mounted_without_dir():
    factory, engine = _factory()
    try:
        app = create_app(factory, session_token="t")
        with TestClient(app) as client:
            assert client.get("/app/").status_code == 404
    finally:
        engine.dispose()


def test_gui_mounted_when_built(tmp_path):
    (tmp_path / "index.html").write_text("<h1>RB</h1>", encoding="utf-8")
    factory, engine = _factory()
    try:
        app = create_app(factory, session_token="t", gui_dir=tmp_path)
        with TestClient(app) as client:
            resp = client.get("/app/")
            assert resp.status_code == 200
            assert "RB" in resp.text
    finally:
        engine.dispose()
