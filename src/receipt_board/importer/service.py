"""Atomic Markdown import (TECH_SPEC §6, ADR-0005).

Two phases: parse + validate fully (collecting **all** errors); on any error abort
without writing and raise ``InvalidImportError`` carrying the report. Otherwise insert
the whole tree in one transaction and record a single audit entry (the import is one
caller action). Category ``done`` is computed bottom-up so the cascade invariant holds.

Policy: **fully strict** (decided with the user). An untypable ``(...)`` resource token
or unknown ``{...}`` tool aborts the import. Consequently the real reference file
``tests/fixtures/expenses_checklist_2024_v02.md`` does not import unmodified — it uses
parentheses as a name qualifier (``Taxi (klassisch)``) which is not valid resource
notation — and is rejected atomically with a precise, line-referenced report.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from receipt_board.core.audit import AuditService
from receipt_board.core.errors import InvalidImportError
from receipt_board.core.refs import CATEGORY
from receipt_board.importer.parser import ParsedNode, ParseResult, ResourceTypeDef, parse
from receipt_board.persistence.models import (
    Category,
    Checklist,
    ExpenseItem,
    ItemResource,
    ItemTool,
    ResourceType,
    Tool,
)


def _parse_with_vocab(session: Session, text: str) -> ParseResult:
    valid_tools = {t.name.lower(): t.name for t in session.scalars(select(Tool))}
    resource_types = [
        ResourceTypeDef(r.name, r.value_optional, r.value_pattern)
        for r in session.scalars(select(ResourceType).order_by(ResourceType.name))
    ]
    return parse(text, valid_tools=valid_tools, resource_types=resource_types)


def _count_nodes(roots: list[ParsedNode]) -> tuple[int, int]:
    categories = items = 0
    stack = list(roots)
    while stack:
        node = stack.pop()
        if node.kind == CATEGORY:
            categories += 1
            stack.extend(node.children)
        else:
            items += 1
    return categories, items


def build_import_report(session: Session, text: str) -> dict:
    """Dry-run: parse + validate ``text`` and return a report (writes nothing).

    Shared with the GUI/CLI/REST so a user can check whether a file is importable
    (and what is wrong) without importing.
    """
    result = _parse_with_vocab(session, text)
    categories, items = _count_nodes(result.roots)
    return {
        "valid": not result.errors,
        "errors": [issue.as_dict() for issue in result.errors],
        "warnings": [issue.as_dict() for issue in result.warnings],
        "summary": {"categories": categories, "items": items},
    }


class ImportService:
    def __init__(self, session: Session, audit: AuditService) -> None:
        self.session = session
        self.audit = audit

    def import_markdown(self, name: str, text: str) -> Checklist:
        if not (name or "").strip():
            raise InvalidImportError("Checklist name must not be empty")

        result = _parse_with_vocab(self.session, text)
        if result.errors:
            raise InvalidImportError(
                f"Import aborted: {len(result.errors)} validation error(s)",
                details={
                    "errors": [issue.as_dict() for issue in result.errors],
                    "warnings": [issue.as_dict() for issue in result.warnings],
                    "recommendation": (
                        "Fix the listed tokens, or extend the controlled vocabularies via "
                        "the GUI, then re-import. Nothing was written."
                    ),
                },
            )

        type_ids = {r.name: r.id for r in self.session.scalars(select(ResourceType))}
        tool_ids = {t.name: t.id for t in self.session.scalars(select(Tool))}

        checklist = Checklist(name=name.strip())
        self.session.add(checklist)
        self.session.flush()

        def insert(node: ParsedNode, parent_category_id: int | None, position: int) -> bool:
            if node.kind == CATEGORY:
                category = Category(
                    checklist_id=checklist.id,
                    parent_id=parent_category_id,
                    name=node.name,
                    position=position,
                    done=False,
                )
                self.session.add(category)
                self.session.flush()
                child_done = [
                    insert(child, category.id, index) for index, child in enumerate(node.children)
                ]
                category.done = all(child_done) if child_done else False
                return category.done
            item = ExpenseItem(
                checklist_id=checklist.id,
                category_id=parent_category_id,
                name=node.name,
                position=position,
                done=node.done,
                data=node.data,
                instructions=node.instructions,
            )
            self.session.add(item)
            self.session.flush()
            for index, resource in enumerate(node.resources):
                self.session.add(
                    ItemResource(
                        item_id=item.id,
                        resource_type_id=type_ids[resource.type],
                        value=resource.value,
                        position=index,
                    )
                )
            for index, tool_name in enumerate(node.tools):
                self.session.add(
                    ItemTool(item_id=item.id, tool_id=tool_ids[tool_name], position=index)
                )
            return item.done

        for position, root in enumerate(result.roots):
            insert(root, None, position)

        self.session.flush()
        self.audit.record(
            action_type="import_checklist",
            target_kind="checklist",
            target_id=checklist.id,
            checklist_id=checklist.id,
            payload={
                "old": None,
                "new": {"name": checklist.name, "warnings": len(result.warnings)},
            },
        )
        return checklist
