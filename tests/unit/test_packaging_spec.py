"""The packaging spec resolves a real application icon (issue #58).

Guards against regressing to the old behaviour where ``packaging/icon.ico`` was missing
and ``receipt_board.spec`` fell back to ``icon = None`` (the default PyInstaller icon).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ICON_ICO = REPO_ROOT / "packaging" / "icon.ico"
ICON_PNG = REPO_ROOT / "packaging" / "icon.png"
SPEC = REPO_ROOT / "receipt_board.spec"


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
