"""Headless server wiring (issue #104, ADR-0011).

``build_server`` is the non-blocking core of the CLI ``serve`` command: it builds the app,
reserves a port, publishes ``runtime.json`` and mounts the GUI — everything up to the
blocking ``server.run()``. Driving it over HTTP here proves the headless path works without
a GUI window, with the server still the sole DB owner (the CLI just speaks REST).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator

import httpx
import pytest

from receipt_board.api.runtime import read_port
from receipt_board.api.server import build_server
from receipt_board.gui.window import static_dir
from receipt_board.persistence.db import create_db_engine, make_session_factory
from receipt_board.persistence.models import Base
from receipt_board.persistence.seeds import seed_vocabularies


@pytest.fixture
def headless(tmp_path) -> Iterator[str]:
    engine = create_db_engine(tmp_path / "test.sqlite")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as setup:
        seed_vocabularies(setup)
        setup.commit()

    runtime = tmp_path / "runtime.json"
    server, port = build_server(
        factory,
        session_token="tok",
        runtime_path=runtime,
        app_version="test",
        gui_dir=static_dir(),
    )
    assert read_port(runtime) == port  # runtime.json published for the CLI

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        engine.dispose()


def test_headless_serves_public_api(headless: str) -> None:
    response = httpx.get(f"{headless}/checklists")
    assert response.status_code == 200
    assert response.json() == []


def test_headless_mounts_the_gui(headless: str) -> None:
    # The GUI is served same-origin at /app even headless (a browser could connect).
    response = httpx.get(f"{headless}/app/")
    assert response.status_code == 200
    assert "Receipt Board" in response.text
