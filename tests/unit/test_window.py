"""The GUI config injection hands the page both the session token and the app version.

The version feeds the GUI status bar (issue #101); the token gates privileged calls
(ADR-0009). ``config_script`` is the only unit-testable part of ``gui/window.py`` (the
pywebview ``open_window`` is ``# pragma: no cover``).
"""

from __future__ import annotations

import json
import re

from receipt_board import __version__
from receipt_board.gui.window import config_script


def test_config_script_injects_token_and_version() -> None:
    script = config_script("secret-token", "9.9.9")
    assert "window.__RECEIPT_BOARD__" in script
    assert json.dumps("secret-token") in script
    assert json.dumps("9.9.9") in script


def test_config_script_defaults_to_the_app_version() -> None:
    assert json.dumps(__version__) in config_script("t")


def test_config_script_is_a_single_assignment_statement() -> None:
    # Guards the injected snippet stays a plain object assignment (no stray syntax).
    script = config_script("t", "1.2.3")
    assert re.fullmatch(r"window\.__RECEIPT_BOARD__ = \{.*\};", script)
