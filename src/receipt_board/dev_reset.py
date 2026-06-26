"""Dev-only CLI: selectively wipe Receipt Board's per-user state.

DEVELOPER-ONLY tool -- this is **NOT** the product uninstaller. It deletes the
local app-data files (database, config, runtime, log) so the first-run flow can
be re-tested from a clean slate.

Run it via the ``scripts/dev-reset.ps1`` wrapper, or directly::

    python -m receipt_board.dev_reset [flags]

Targets honour ``RECEIPT_BOARD_HOME`` and the custom ``[database].path`` from
``config.toml``. With no category flag it falls back to an interactive y/N
selection per target.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from receipt_board import config

LOG_FILENAME = "receipt-board.log"

TARGET_DESCRIPTIONS: dict[str, str] = {
    "db": "receipt_board.sqlite (database + WAL/SHM sidecars)",
    "config": "config.toml (settings)",
    "runtime": "runtime.json (bound server port)",
    "logs": "receipt-board.log (application log)",
}


def _resolve_targets() -> dict[str, Path]:
    """Map category -> concrete path, honouring env override and custom DB path."""
    return {
        "db": config.load_config().db_path,
        "config": config.config_path(),
        "runtime": config.runtime_path(),
        "logs": config.app_dir() / LOG_FILENAME,
    }


def _sidecars(db_path: Path) -> list[Path]:
    """SQLite WAL/SHM sidecars that sit next to the database file."""
    return [
        db_path.with_name(db_path.name + "-wal"),
        db_path.with_name(db_path.name + "-shm"),
    ]


def _delete(path: Path) -> bool:
    """Remove ``path``. Returns True if something was deleted, False if missing."""
    if not path.exists():
        return False
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return True


def _print_plan(targets: dict[str, Path]) -> None:
    print("The following will be deleted:")
    for name, path in targets.items():
        marker = "*" if path.exists() else " "
        print(f"  [{marker}] {name:<8} {path}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="receipt-board-dev-reset",
        description="Developer-only: wipe Receipt Board's per-user state to re-test first run.",
    )
    parser.add_argument("--all", action="store_true", help="Select every target below.")
    parser.add_argument(
        "--db",
        action="store_true",
        help="Remove the SQLite database (and its WAL/SHM sidecars).",
    )
    parser.add_argument("--config", action="store_true", help="Remove config.toml.")
    parser.add_argument("--runtime", action="store_true", help="Remove runtime.json.")
    parser.add_argument("--logs", action="store_true", help="Remove receipt-board.log.")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip the confirmation prompt.")
    return parser


def _collect_from_flags(args: argparse.Namespace) -> list[str]:
    if args.all:
        return list(TARGET_DESCRIPTIONS.keys())
    return [name for name in TARGET_DESCRIPTIONS if getattr(args, name)]


def _collect_interactive(all_targets: dict[str, Path], input_fn=input) -> list[str]:
    print("Receipt Board dev-reset (interactive)")
    print("Answer y/N for each target:")
    selected: list[str] = []
    for name, path in all_targets.items():
        state = "exists" if path.exists() else "missing"
        ans = (
            input_fn(f"  Reset {name} ({TARGET_DESCRIPTIONS[name]}) -- {path} [{state}]? [y/N] ")
            .strip()
            .lower()
        )
        if ans == "y":
            selected.append(name)
    return selected


def _targets_to_remove(name: str, path: Path) -> list[Path]:
    """All paths to delete for one selected category (DB also wipes its sidecars)."""
    if name == "db":
        return [path, *_sidecars(path)]
    return [path]


def run(argv: list[str] | None = None, *, input_fn=input) -> int:
    args = _build_parser().parse_args(argv)
    all_targets = _resolve_targets()

    selected = _collect_from_flags(args)
    if not selected:
        selected = _collect_interactive(all_targets, input_fn=input_fn)

    if not selected:
        print("Nothing selected, exiting.")
        return 0

    targets = {name: all_targets[name] for name in selected}

    print()
    _print_plan(targets)
    print()

    if not args.yes:
        confirm = input_fn("Proceed? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 0

    failures = 0
    for name, path in targets.items():
        for target in _targets_to_remove(name, path):
            try:
                if _delete(target):
                    print(f"  removed: {target}")
                else:
                    print(f"  skipped (not present): {target}")
            except OSError as exc:
                print(f"  ERROR removing {target}: {exc}", file=sys.stderr)
                failures += 1

    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run())
