"""Markdown checklist export (issue #171) — the inverse of the importer.

Renders a checklist back into the strict import notation (TECH_SPEC §6), so a checklist
imported from a notation-conformant file and left unmodified exports **byte-identical**.
The output is the canonical form of the grammar:

* one tab per nesting level, ``- [ ]`` / ``- [x]`` checkboxes;
* the item-level ``~manually~`` marker directly after the name;
* field groups in the order ``(resources) {tools} [data] <instructions>``, multi-values
  separated by `` | ``;
* resource tokens in the shortest form that re-imports to the same type: the bare type
  name when the value is empty (``Email``), the bare value when pattern typing already
  resolves it to the same type (``https://…``, ``a@b.de``), else ``Type: value``; a
  per-resource ``~manually~`` marker is appended inside the token.

Fidelity caveats: a file written with space indentation or redundant ``Type: value``
tokens re-exports normalized (it re-imports identically). Newlines in data/instructions
(possible via the GUI textarea, never via import) become spaces — the grammar is
line-based. Names containing reserved control characters (possible via GUI edits only)
export as-is but will not re-import.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from receipt_board.core.queries import export_checklist
from receipt_board.core.refs import EXPENSE_ITEM
from receipt_board.importer.parser import ResourceTypeDef, type_resource
from receipt_board.persistence.models import ResourceType


def _one_line(text: str) -> str:
    """Collapse newlines to spaces: the import grammar is strictly line-based."""
    return " ".join(part.strip() for part in text.splitlines())


def _resource_token(resource: dict, type_defs: list[ResourceTypeDef]) -> str:
    value = resource["value"]
    if not value:
        token = resource["type"]
    else:
        typed, _ = type_resource(value, type_defs)
        if typed is not None and (typed.type, typed.value) == (resource["type"], value):
            token = value
        else:
            token = f"{resource['type']}: {value}"
    return f"{token} ~manually~" if resource.get("manually") else token


def _item_fields(node: dict, type_defs: list[ResourceTypeDef]) -> list[str]:
    parts: list[str] = []
    if node.get("manually"):
        parts.append("~manually~")
    if node.get("resources"):
        tokens = [_resource_token(resource, type_defs) for resource in node["resources"]]
        parts.append(f"({' | '.join(tokens)})")
    if node.get("tools"):
        parts.append(f"{{{' | '.join(node['tools'])}}}")
    if node.get("data"):
        parts.append(f"[{_one_line(node['data'])}]")
    if node.get("instructions"):
        parts.append(f"<{_one_line(node['instructions'])}>")
    return parts


def export_markdown(session: Session, checklist_id: int) -> str:
    """Render the checklist ``checklist_id`` in the canonical import notation."""
    tree = export_checklist(session, checklist_id)
    type_defs = [
        ResourceTypeDef(r.name, r.value_optional, r.value_pattern)
        for r in session.scalars(select(ResourceType).order_by(ResourceType.name))
    ]
    lines: list[str] = []

    def emit(node: dict, depth: int) -> None:
        mark = "x" if node["done"] else " "
        parts = [node["name"]]
        if node["kind"] == EXPENSE_ITEM:
            parts += _item_fields(node, type_defs)
        lines.append("\t" * depth + f"- [{mark}] " + " ".join(parts))
        for child in node.get("children") or []:
            emit(child, depth + 1)

    for root in tree["children"]:
        emit(root, 0)
    return "".join(f"{line}\n" for line in lines)
