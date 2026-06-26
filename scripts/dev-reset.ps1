<#
.SYNOPSIS
    Developer-only: wipe Receipt Board's per-user state to re-test first run.
.DESCRIPTION
    Thin wrapper around `python -m receipt_board.dev_reset`. Forwards every
    argument to the Python module. This is NOT the product uninstaller.
    See the "Developer utilities" section in README.md for flags and usage.
#>

$ErrorActionPreference = "Stop"

uv run python -m receipt_board.dev_reset @args
exit $LASTEXITCODE
