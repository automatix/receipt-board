"""pywebview window host and token injection (TECH_SPEC §7, ADR-0009).

The GUI is served same-origin by the local server at ``/app``; pywebview loads that URL
and, on load, injects the session token into ``window.__RECEIPT_BOARD__`` so only the GUI
page can call privileged endpoints.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from receipt_board import __version__


def static_dir() -> Path:
    """Directory holding the esbuild-bundled GUI assets (built from ``gui-src/``)."""
    return Path(__file__).resolve().parent / "static"


def index_path() -> Path:
    return static_dir() / "index.html"


def config_script(token: str, version: str = __version__) -> str:
    """JS injected after load to hand the session token and app version to the page."""
    return (
        f"window.__RECEIPT_BOARD__ = "
        f"{{ token: {json.dumps(token)}, version: {json.dumps(version)} }};"
    )


def open_window(  # pragma: no cover
    url: str,
    token: str,
    *,
    version: str = __version__,
    title: str = "Receipt Board",
    on_window: Callable[[Any], None] | None = None,
) -> None:
    """Open the native window and inject the token + version once the page has loaded.

    ``text_select=True`` enables document text selection (pywebview disables it by
    default), so text can be selected and copied with ``Ctrl+C`` like in a browser.
    ``on_window`` (if given) receives the window so the caller can wire a shutdown hook
    (e.g. the updater closing the window after launching the installer).
    """
    import webview

    window = webview.create_window(title, url=url, text_select=True)

    def _inject() -> None:
        window.evaluate_js(config_script(token, version))

    window.events.loaded += _inject
    if on_window is not None:
        on_window(window)
    webview.start()
