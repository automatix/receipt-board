"""Receipt Board CLI (TECH_SPEC §10, ADR-0011).

Read-only plus the leaf done-toggle (public surface). Commands::

    receipt-board export [--checklist ID]
    receipt-board search QUERY
    receipt-board item done ID
    receipt-board item undone ID
    receipt-board validate PATH        # dry-run: is a Markdown file importable?

``--json`` switches to machine-readable output. Exit code 0 on success, non-zero on error
(``validate`` exits 1 when the file is not importable).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from receipt_board import config
from receipt_board.cli.client import ApiClient, CliError


def build_parser() -> argparse.ArgumentParser:
    # --json is accepted both before the subcommand (global) and after it: a shared
    # parent carries it onto each subcommand with default=SUPPRESS so it never clobbers
    # the global flag when given up front.
    json_flag = argparse.ArgumentParser(add_help=False)
    json_flag.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="machine-readable JSON output",
    )

    parser = argparse.ArgumentParser(
        prog="receipt-board",
        description="Receipt Board CLI — read and toggle expense-item checkboxes.",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable JSON output")
    sub = parser.add_subparsers(dest="command", required=True)

    export = sub.add_parser(
        "export", parents=[json_flag], help="export checklists (all, or one nested tree)"
    )
    export.add_argument("--checklist", type=int, default=None, metavar="ID")

    search = sub.add_parser("search", parents=[json_flag], help="search node names (flat hits)")
    search.add_argument("query")

    item = sub.add_parser("item", help="toggle an expense item's done checkbox")
    item_sub = item.add_subparsers(dest="item_command", required=True)
    item_sub.add_parser("done", parents=[json_flag]).add_argument("id", type=int)
    item_sub.add_parser("undone", parents=[json_flag]).add_argument("id", type=int)

    validate = sub.add_parser(
        "validate", parents=[json_flag], help="dry-run: check if a Markdown file is importable"
    )
    validate.add_argument("path", help="path to the Markdown checklist file")

    return parser


def _emit(as_json: bool, data: object, human: str) -> None:
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(human)


def _format_checklist_list(rows: list[dict]) -> str:
    if not rows:
        return "(no checklists)"
    return "\n".join(f"{row['id']}\t{row['name']}" for row in rows)


def _format_tree(tree: dict, indent: int = 0) -> str:
    pad = "  " * indent
    mark = "x" if tree.get("done") else " "
    if indent == 0:
        lines = [f"# {tree['name']} (checklist {tree['id']})"]
        for child in tree.get("children", []):
            lines.append(_format_tree(child, indent + 1))
        return "\n".join(lines)
    lines = [f"{pad}- [{mark}] {tree['name']} ({tree['kind']} {tree['id']})"]
    for child in tree.get("children", []):
        lines.append(_format_tree(child, indent + 1))
    return "\n".join(lines)


def _format_hits(hits: list[dict]) -> str:
    if not hits:
        return "(no matches)"
    lines = []
    for hit in hits:
        path = " / ".join(hit["path"]) if hit["path"] else "(top level)"
        lines.append(f"{hit['kind']}\t{hit['id']}\t{hit['name']}\t[{path}]")
    return "\n".join(lines)


def _format_report(report: dict) -> str:
    summary = report["summary"]
    lines: list[str] = []
    if report["valid"]:
        lines.append(
            f"OK — importierbar: {summary['categories']} Kategorien, {summary['items']} Einträge"
        )
    else:
        lines.append(f"UNGÜLTIG — {len(report['errors'])} Fehler:")
        for issue in report["errors"]:
            lines.append(f"  Zeile {issue['line']} · {issue['token']} · {issue['message']}")
    for warning in report["warnings"]:
        lines.append(f"  Warnung Zeile {warning['line']}: {warning['message']}")
    return "\n".join(lines)


def _dispatch(args: argparse.Namespace, client: ApiClient) -> int:
    if args.command == "export":
        if args.checklist is None:
            rows = client.list_checklists()
            _emit(args.json, rows, _format_checklist_list(rows))
        else:
            tree = client.export(args.checklist)
            _emit(args.json, tree, _format_tree(tree))
    elif args.command == "search":
        hits = client.search(args.query)
        _emit(args.json, hits, _format_hits(hits))
    elif args.command == "item":
        done = args.item_command == "done"
        result = client.set_item_done(args.id, done)
        affected = len(result.get("affected_ids", []))
        human = (
            f"Item {args.id} marked {'done' if done else 'undone'} ({affected} node(s) affected)"
        )
        _emit(args.json, result, human)
    elif args.command == "validate":
        try:
            text = Path(args.path).read_text(encoding="utf-8")
        except OSError as exc:
            raise CliError(f"Cannot read {args.path}: {exc}") from exc
        report = client.validate_import(text)
        _emit(args.json, report, _format_report(report))
        return 0 if report["valid"] else 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with ApiClient.from_runtime(config.runtime_path()) as client:
            return _dispatch(args, client)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
