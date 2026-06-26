<#
.SYNOPSIS
    Build the Receipt Board Windows installer (Inno Setup setup.exe).
.DESCRIPTION
    Reproducible, single-entry build orchestrator:
      1. Build the TypeScript GUI  (npm ci && npm run build in gui-src\).
      2. Freeze the PyInstaller onedir build  (uv run pyinstaller receipt_board.spec),
         from the uv-managed venv so PyInstaller traces the real dependency graph.
      3. Compile packaging\receipt-board.iss with ISCC into dist\installer\.

    Hardened for Windows PowerShell 5.1 (issue #58, mirroring zerobox #120): under PS 5.1
    with $ErrorActionPreference = "Stop", any native tool that merely writes to stderr
    (npm, pip, pyinstaller) is promoted to a terminating error even on exit code 0. So we
    keep $ErrorActionPreference = "Continue" and check $LASTEXITCODE explicitly after every
    native call via Invoke-Native.
.PARAMETER Version
    Version baked into the installer + artifact name. Defaults to the version in
    pyproject.toml.
.PARAMETER SkipGui
    Skip the GUI build (assume gui static assets are already built).
.NOTES
    Prerequisites: uv, Node.js, and Inno Setup (ISCC). If ISCC is missing it is installed
    via winget (JRSoftware.InnoSetup) - pre-authorized by the Inno Setup engine choice. No
    other system software is installed automatically.
#>
[CmdletBinding()]
param(
    [string]$Version,
    [switch]$SkipGui
)

# See the .DESCRIPTION note: never "Stop" here under PS 5.1.
$ErrorActionPreference = "Continue"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Command,
        [Parameter(Mandatory = $true)][string]$What
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$What failed (exit code $LASTEXITCODE)."
    }
}

function Resolve-Iscc {
    # 1. Already on PATH?
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # 2. Well-known install locations (winget installs per-user under LOCALAPPDATA).
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }

    # 3. Install via winget (pre-authorized by the Inno Setup engine choice).
    Write-Host "Inno Setup (ISCC) not found - installing via winget..." -ForegroundColor Yellow
    Invoke-Native {
        winget install --id JRSoftware.InnoSetup --silent `
            --accept-package-agreements --accept-source-agreements
    } "winget install Inno Setup"

    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw "ISCC not found after attempting a winget install of Inno Setup."
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $repoRoot

# Resolve the version from pyproject.toml when not supplied.
if (-not $Version) {
    $match = Select-String -Path (Join-Path $repoRoot "pyproject.toml") `
        -Pattern '^version\s*=\s*"(.+)"' | Select-Object -First 1
    if ($match) { $Version = $match.Matches[0].Groups[1].Value }
    if (-not $Version) { throw "Could not determine the version; pass -Version explicitly." }
}

Write-Host "=== Building Receipt Board installer v$Version ===" -ForegroundColor Cyan

# --- Step 1: GUI -----------------------------------------------------------------------
if (-not $SkipGui) {
    Write-Host "=== Step 1: Build GUI (TypeScript -> esbuild) ===" -ForegroundColor Cyan
    Push-Location (Join-Path $repoRoot "gui-src")
    try {
        Invoke-Native { npm ci } "npm ci"
        Invoke-Native { npm run build } "npm run build"
    }
    finally { Pop-Location }
}
else {
    Write-Host "=== Step 1: Build GUI (skipped) ===" -ForegroundColor DarkGray
}

# --- Step 2: PyInstaller freeze --------------------------------------------------------
Write-Host "=== Step 2: Freeze PyInstaller onedir ===" -ForegroundColor Cyan
Invoke-Native { uv sync } "uv sync"
Invoke-Native { uv run pyinstaller --noconfirm receipt_board.spec } "PyInstaller"

# --- Step 3: Inno Setup ----------------------------------------------------------------
Write-Host "=== Step 3: Compile Inno Setup installer ===" -ForegroundColor Cyan
$iscc = Resolve-Iscc
Write-Host "Using ISCC: $iscc" -ForegroundColor DarkGray
Invoke-Native {
    & $iscc "/DAppVersion=$Version" (Join-Path $repoRoot "packaging\receipt-board.iss")
} "ISCC"

$setup = Join-Path $repoRoot "dist\installer\receipt-board-v$Version-setup.exe"
if (-not (Test-Path $setup)) {
    throw "Expected installer not found at $setup"
}

Write-Host ""
Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "Installer: $setup"
