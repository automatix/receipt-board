"""PyInstaller entry point.

One frozen entry, shipped as two executables (see ``receipt_board.spec``):
  * ``receipt-board.exe``      — windowed; the desktop GUI (default).
  * ``receipt-board-cli.exe``  — console; the CLI + headless ``serve``.

Both run this dispatcher: a known CLI subcommand routes to the CLI (which needs a console
for its output), anything else launches the desktop app. Distribution then only differs by
the console flag of each exe — the windowed one for the Start-menu shortcut, the console one
for the terminal.
"""

import sys

from receipt_board.bootstrap import main as app_main

# Keep in sync with the subcommands in receipt_board.cli.main.build_parser.
CLI_COMMANDS = frozenset({"serve", "export", "search", "item", "validate", "audit"})


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] in CLI_COMMANDS:
        from receipt_board.cli.main import main as cli_main

        return cli_main(argv)
    return app_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
