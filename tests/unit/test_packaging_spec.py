"""Static guards on the packaging definitions (issues #58, #98).

* The PyInstaller spec must resolve a real application icon (issue #58): guards against
  regressing to the old behaviour where ``packaging/icon.ico`` was missing and
  ``receipt_board.spec`` fell back to ``icon = None`` (the default PyInstaller icon).
* The Inno Setup script must offer a default-checked "Launch Receipt Board" checkbox on
  the final wizard page (issue #98).
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ICON_ICO = REPO_ROOT / "packaging" / "icon.ico"
ICON_PNG = REPO_ROOT / "packaging" / "icon.png"
SPEC = REPO_ROOT / "receipt_board.spec"
ISS = REPO_ROOT / "packaging" / "receipt-board.iss"


def _iss_section(name: str) -> str:
    """Return the body of an Inno Setup ``[Section]`` (lines until the next ``[...]`` header)."""
    text = ISS.read_text(encoding="utf-8")
    match = re.search(rf"^\[{name}\]\s*$(.*?)(?=^\[|\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, f"[{name}] section not found in {ISS.name}"
    return match.group(1)


def _run_postinstall_entry() -> str:
    """The single non-comment ``[Run]`` directive carrying the ``postinstall`` flag."""
    entries = [
        line.strip()
        for line in _iss_section("Run").splitlines()
        if line.strip() and not line.strip().startswith(";") and "postinstall" in line.lower()
    ]
    assert len(entries) == 1, f"expected exactly one postinstall [Run] entry, got: {entries}"
    return entries[0]


def test_icon_ico_exists_and_is_a_real_ico() -> None:
    assert ICON_ICO.exists(), "packaging/icon.ico must exist so the spec never falls back to None"
    # ICO header: reserved(0x0000) + image type 1 (icon), little-endian.
    assert ICON_ICO.read_bytes()[:4] == b"\x00\x00\x01\x00"


def test_icon_png_source_exists() -> None:
    assert ICON_PNG.exists()


def test_spec_resolves_icon_not_none() -> None:
    # Mirror receipt_board.spec: icon = str(path) if path.exists() else None.
    icon = str(ICON_ICO) if ICON_ICO.exists() else None
    assert icon is not None


def test_spec_references_packaging_icon() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert 'ROOT / "packaging" / "icon.ico"' in text


def test_iss_run_entry_launches_the_app() -> None:
    entry = _run_postinstall_entry()
    # Launches the installed executable from the final wizard page.
    assert "{#AppExeName}" in entry
    assert "postinstall" in entry.lower()


def test_iss_run_checkbox_is_checked_by_default() -> None:
    # No `unchecked` flag => the "Launch Receipt Board" checkbox is ticked by default (#98).
    entry = _run_postinstall_entry()
    assert "unchecked" not in entry.lower()


def test_iss_run_entry_uses_safe_flags() -> None:
    entry = _run_postinstall_entry().lower()
    # Run as the non-elevated user, don't block the wizard, and stay silent on /VERYSILENT.
    for flag in ("runasoriginaluser", "nowait", "skipifsilent"):
        assert flag in entry, f"[Run] entry should carry the {flag!r} flag"
