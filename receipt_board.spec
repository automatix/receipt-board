# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: onedir, windowed Windows build (TECH_SPEC §11, I1).
# Build the GUI first (cd gui-src && npm run build) so the static assets exist, then:
#     uv run pyinstaller receipt_board.spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH)
SRC = ROOT / "src" / "receipt_board"

# Bundle the built GUI and the Alembic migrations (loaded by path at runtime).
datas = [
    (str(SRC / "gui" / "static"), "receipt_board/gui/static"),
    (str(SRC / "persistence" / "migrations"), "receipt_board/persistence/migrations"),
]

# uvicorn imports its protocol/loop backends dynamically; pywebview is handled by a
# pyinstaller-hooks-contrib hook.
hiddenimports = collect_submodules("uvicorn")

_icon = ROOT / "packaging" / "icon.ico"
icon = str(_icon) if _icon.exists() else None

a = Analysis(
    [str(ROOT / "packaging" / "entry.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

# Two executables from the same analysis (same dispatcher entry, see packaging/entry.py):
#   receipt-board.exe      — windowed GUI (Start-menu shortcut).
#   receipt-board-cli.exe  — console; CLI commands + headless `serve` (issue #104).
# Both share the one set of collected binaries/datas below, so the second exe adds ~no size.
exe_gui = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="receipt-board",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon,
)

exe_cli = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="receipt-board-cli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=icon,
)

coll = COLLECT(
    exe_gui,
    exe_cli,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="receipt-board",
)
