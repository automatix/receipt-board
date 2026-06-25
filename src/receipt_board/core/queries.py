"""Read-only domain queries: list checklists, nested export, flat search.

Used by the public REST/CLI surface (GLOSSARY: Export, Search). No audit, no writes.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from receipt_board.core.errors import NotFoundError
from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM
from receipt_board.core.tree import ancestor_path, ordered_children, top_level_categories
from receipt_board.persistence.models import Category, Checklist, ExpenseItem


def list_checklists(session: Session) -> list[dict]:
    checklists = session.scalars(select(Checklist).order_by(Checklist.id)).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in checklists
    ]


def _serialize_item(item: ExpenseItem) -> dict:
    return {
        "kind": EXPENSE_ITEM,
        "id": item.id,
        "name": item.name,
        "position": item.position,
        "done": item.done,
        "data": item.data,
        "instructions": item.instructions,
        "resources": [
            {"type": resource.resource_type.name, "value": resource.value}
            for resource in item.resources
        ],
        "tools": [link.tool.name for link in item.tools],
    }


def _serialize_category(session: Session, category: Category) -> dict:
    children = [
        _serialize_category(session, node) if kind == CATEGORY else _serialize_item(node)
        for kind, node in ordered_children(session, category.checklist_id, category.id)
    ]
    return {
        "kind": CATEGORY,
        "id": category.id,
        "name": category.name,
        "position": category.position,
        "done": category.done,
        "children": children,
    }


def export_checklist(session: Session, checklist_id: int) -> dict:
    """Full nested JSON tree of a checklist (all node fields)."""
    checklist = session.get(Checklist, checklist_id)
    if checklist is None:
        raise NotFoundError(f"Checklist {checklist_id} not found")
    children = [
        _serialize_category(session, category)
        for category in top_level_categories(session, checklist_id)
    ]
    return {
        "id": checklist.id,
        "name": checklist.name,
        "created_at": checklist.created_at.isoformat(),
        "updated_at": checklist.updated_at.isoformat(),
        "children": children,
    }


def search(session: Session, query: str, *, checklist_id: int | None = None) -> list[dict]:
    """Free-text match over node ``name`` at all levels; flat hits with ancestor path."""
    needle = query.strip().lower()
    if not needle:
        return []
    pattern = f"%{needle}%"

    hits: list[dict] = []

    cat_stmt = select(Category).where(func.lower(Category.name).like(pattern))
    if checklist_id is not None:
        cat_stmt = cat_stmt.where(Category.checklist_id == checklist_id)
    for category in session.scalars(cat_stmt):
        hits.append(
            {
                "id": category.id,
                "name": category.name,
                "kind": CATEGORY,
                "checklist_id": category.checklist_id,
                "path": ancestor_path(session, category.parent_id),
            }
        )

    item_stmt = select(ExpenseItem).where(func.lower(ExpenseItem.name).like(pattern))
    if checklist_id is not None:
        item_stmt = item_stmt.where(ExpenseItem.checklist_id == checklist_id)
    for item in session.scalars(item_stmt):
        hits.append(
            {
                "id": item.id,
                "name": item.name,
                "kind": EXPENSE_ITEM,
                "checklist_id": item.checklist_id,
                "path": ancestor_path(session, item.category_id),
            }
        )

    return hits
