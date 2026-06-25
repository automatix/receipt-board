"""Symmetric done-cascade (ADR-0002).

Invariant: ``category.done`` reflects whether its entire subtree is done. Setting a node
forces its whole subtree to the same value; then ancestors are re-rolled-up
(``ancestor.done = AND(direct children)``).

Empty-category rule: rolling up a category that has **no** children leaves its ``done``
unchanged. The ``AND(children)`` invariant addresses non-empty subtrees; we do not
vacuously force an empty category to *done* (e.g. removing a category's last child must
not silently complete it). A deliberate toggle of an empty category still sets it.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from receipt_board.core.errors import NotFoundError, ValidationError
from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM, NodeKind, NodeRef
from receipt_board.core.tree import child_categories, child_items, descendant_category_ids
from receipt_board.persistence.models import Category, ExpenseItem


def _recompute_done(session: Session, category: Category) -> bool | None:
    """``AND`` of direct children's done, or ``None`` when the category has no children."""
    children_done: list[bool] = [c.done for c in child_categories(session, category.id)]
    children_done += [i.done for i in child_items(session, category.id)]
    if not children_done:
        return None
    return all(children_done)


def rollup(session: Session, start_category_id: int | None, changed: list[NodeRef]) -> None:
    """Re-roll-up ancestors starting at ``start_category_id`` (a category id or None)."""
    current_id = start_category_id
    while current_id is not None:
        category = session.get(Category, current_id)
        if category is None:
            break
        new_value = _recompute_done(session, category)
        if new_value is None or new_value == category.done:
            # No children (leave unchanged) or no change -> ancestors are unaffected.
            break
        category.done = new_value
        changed.append(NodeRef(CATEGORY, category.id))
        current_id = category.parent_id


def set_node_done(session: Session, kind: NodeKind, node_id: int, value: bool) -> list[NodeRef]:
    """Set a node's done, cascade to its subtree, roll up ancestors.

    Returns the references of all nodes whose ``done`` actually changed.
    """
    changed: list[NodeRef] = []

    if kind == EXPENSE_ITEM:
        item = session.get(ExpenseItem, node_id)
        if item is None:
            raise NotFoundError(f"Expense item {node_id} not found")
        if item.done != value:
            item.done = value
            changed.append(NodeRef(EXPENSE_ITEM, item.id))
        rollup(session, item.category_id, changed)
        return changed

    if kind == CATEGORY:
        category = session.get(Category, node_id)
        if category is None:
            raise NotFoundError(f"Category {node_id} not found")
        category_ids = descendant_category_ids(session, category.id)
        for cid in category_ids:
            sub = session.get(Category, cid)
            if sub is not None and sub.done != value:
                sub.done = value
                changed.append(NodeRef(CATEGORY, sub.id))
        subtree_items = session.scalars(
            select(ExpenseItem).where(ExpenseItem.category_id.in_(category_ids))
        )
        for item in subtree_items:
            if item.done != value:
                item.done = value
                changed.append(NodeRef(EXPENSE_ITEM, item.id))
        rollup(session, category.parent_id, changed)
        return changed

    raise ValidationError(f"Unknown node kind: {kind!r}")
