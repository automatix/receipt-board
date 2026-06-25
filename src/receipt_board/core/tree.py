"""Tree-navigation helpers shared by the cascade, services and read queries.

The children of a category interleave sub-categories and expense items by ``position``
(positions span both tables — ADR-0007); top-level children of a checklist are
categories only (items always live under a category).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM, NodeKind
from receipt_board.persistence.models import Category, ExpenseItem


def child_categories(session: Session, parent_id: int) -> list[Category]:
    return list(
        session.scalars(
            select(Category).where(Category.parent_id == parent_id).order_by(Category.position)
        )
    )


def child_items(session: Session, category_id: int) -> list[ExpenseItem]:
    return list(
        session.scalars(
            select(ExpenseItem)
            .where(ExpenseItem.category_id == category_id)
            .order_by(ExpenseItem.position)
        )
    )


def top_level_categories(session: Session, checklist_id: int) -> list[Category]:
    return list(
        session.scalars(
            select(Category)
            .where(Category.checklist_id == checklist_id, Category.parent_id.is_(None))
            .order_by(Category.position)
        )
    )


def ordered_children(
    session: Session, checklist_id: int, parent_id: int | None
) -> list[tuple[NodeKind, Category | ExpenseItem]]:
    """Children under ``parent_id`` (or the checklist root when None), position-ordered."""
    if parent_id is None:
        cats = top_level_categories(session, checklist_id)
        items: list[ExpenseItem] = []
    else:
        cats = child_categories(session, parent_id)
        items = child_items(session, parent_id)
    combined: list[tuple[NodeKind, Category | ExpenseItem]] = [(CATEGORY, c) for c in cats]
    combined += [(EXPENSE_ITEM, i) for i in items]
    combined.sort(key=lambda pair: pair[1].position)
    return combined


def descendant_category_ids(session: Session, root_id: int) -> list[int]:
    """All category ids in the subtree rooted at ``root_id`` (inclusive)."""
    ids = [root_id]
    stack = [root_id]
    while stack:
        parent_id = stack.pop()
        children = session.scalars(select(Category.id).where(Category.parent_id == parent_id)).all()
        ids.extend(children)
        stack.extend(children)
    return ids


def ancestor_path(session: Session, start_parent_id: int | None) -> list[str]:
    """Names of the ancestor categories, root-first, starting at ``start_parent_id``."""
    names: list[str] = []
    current_id = start_parent_id
    while current_id is not None:
        category = session.get(Category, current_id)
        if category is None:
            break
        names.append(category.name)
        current_id = category.parent_id
    names.reverse()
    return names
