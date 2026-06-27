# Building & testing the Windows installer

Developer guide for producing and testing the Receipt Board Windows installer
(`setup.exe`). End-user install steps are in [`INSTALL.md`](./INSTALL.md) (German).

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) — manages the venv and a pinned CPython `3.12`.
- **Node.js** (`npm`) — to build the TypeScript GUI.
- **Inno Setup** (the `ISCC` compiler). `scripts/build-installer.ps1` installs it via
  `winget` (`JRSoftware.InnoSetup`) if it is not already present.

## Build

```powershell
pwsh scripts/build-installer.ps1                 # version from pyproject.toml
pwsh scripts/build-installer.ps1 -Version 1.2.0  # explicit version
```

The orchestrator (hardened for Windows PowerShell 5.1 — `Invoke-Native` + explicit
`$LASTEXITCODE`) runs three steps:

1. Build the GUI (`npm ci && npm run build` in `gui-src/`).
2. Freeze the PyInstaller `onedir` from the uv-managed venv
   (`uv run pyinstaller receipt_board.spec`).
3. Compile `packaging/receipt-board.iss` with `ISCC`.

Output:

- `dist/receipt-board/` — the frozen `onedir` (also usable as a portable folder).
- `dist/installer/receipt-board-v<VERSION>-setup.exe` — the installer.

The application identity is fixed in `packaging/receipt-board.iss` (AppId GUID
`{6E5EAF6B-4A26-4DCC-AD31-D72D47D602E4}`, reverse-DNS `com.automatix.receipt-board`) and is
**constant across versions**, so upgrades and the uninstall registration match.

## Release (CI)

Pushing a `v*` tag runs `.github/workflows/release.yml` on `windows-latest`, which builds
the installer and attaches `setup.exe` to the GitHub Release for that tag (see #61). The
manual `build-installer.ps1` path keeps working for local builds.

## Testing the installer (install / uninstall)

A per-machine install needs elevation (UAC). Run these from an **elevated** PowerShell:

```powershell
# Silent install, then verify it landed in Program Files and runs first-run init:
Start-Process .\dist\installer\receipt-board-v1.2.0-setup.exe -ArgumentList '/VERYSILENT' -Wait
& "$env:ProgramFiles\Receipt Board\receipt-board.exe" --check

# Silent uninstall (keeps data, no prompt):
Start-Process "$env:ProgramFiles\Receipt Board\unins000.exe" -ArgumentList '/VERYSILENT' -Wait
```

Checks:

- An **interactive** install ends on a final page with **"Launch Receipt Board" checked by
  default**; clicking **Finish** starts the app **as the logged-in, non-elevated user** (Inno
  `runasoriginaluser`), so first-run data lands in *your* `%LOCALAPPDATA%\receipt-board\`. A
  `/VERYSILENT` install never launches it (`skipifsilent`). *(Elevated, interactive — not part
  of the autonomous test path.)*
- The app appears in **Settings → Apps → Installed apps** (and classic Programs and
  Features).
- An **interactive** uninstall shows the **keep-vs-remove** prompt for
  `%LOCALAPPDATA%\receipt-board\` with **keep as the default**; choosing Yes deletes the data
  dir.
- A **silent** uninstall (`/VERYSILENT`) never prompts and never wipes data (this also
  covers an in-place update).

## Resetting per-user state (dev reset — NOT the product uninstaller)

To re-test the first-run flow from zero, use the developer reset CLI (#59) — it deletes only
per-user state, never the installed program:

```powershell
uv run python -m receipt_board.dev_reset --all --yes
scripts/dev-reset.ps1 --db --config
```

It honours `RECEIPT_BOARD_HOME` and a custom `[database].path`, prints a deletion plan, and
confirms unless `--yes` is given. See the "Developer utilities" section of the
[`README.md`](../README.md).
