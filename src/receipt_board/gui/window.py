"""pywebview window host and token injection (TECH_SPEC §7, ADR-0009).

The GUI is served same-origin by the local server at ``/app``; pywebview loads that URL
and, on load, injects the session token into ``window.__RECEIPT_BOARD__`` so only the GUI
page can call privileged endpoints.
"""

from __future__ import annotations

import json
from pathlib import Path


def static_dir() -> Path:
    """Directory holding the esbuild-bundled GUI assets (built from ``gui-src/``)."""
    return Path(__file__).resolve().parent / "static"


def index_path() -> Path:
    return static_dir() / "index.html"


def config_script(token: str) -> str:
    """JS injected after load to hand the session token to the page."""
    return f"window.__RECEIPT_BOARD__ = {{ token: {json.dumps(token)} }};"


def open_window(url: str, token: str, *, title: str = "Receipt Board") -> None:  # pragma: no cover
    """Open the native window and inject the token once the page has loaded."""
    import webview

    window = webview.create_window(title, url=url)

    def _inject() -> None:
        window.evaluate_js(config_script(token))

    window.events.loaded += _inject
    webview.start()
