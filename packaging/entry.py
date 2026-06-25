"""PyInstaller entry point — launches the Receipt Board desktop application."""

from receipt_board.bootstrap import main

if __name__ == "__main__":
    raise SystemExit(main())
