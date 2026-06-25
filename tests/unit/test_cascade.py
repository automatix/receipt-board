"""Cascade invariant and edge cases (ADR-0002)."""

from __future__ import annotations

import pytest

from receipt_board.core.errors import NotFoundError, ValidationError
from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM
from receipt_board.persistence.models import Category, ExpenseItem


def _done(session, model, node_id) -> bool:
    return session.get(model, node_id).done


def test_item_done_rolls_up_only_when_all_siblings_done(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    a = svc.add_item(cl.id, cat.id, "a")
    b = svc.add_item(cl.id, cat.id, "b")

    svc.set_item_done(a.id, True)
    assert _done(session, Category, cat.id) is False  # b still open

    changed = svc.set_item_done(b.id, True)
    assert _done(session, Category, cat.id) is True
    kinds = {(r.kind, r.id) for r in changed}
    assert (EXPENSE_ITEM, b.id) in kinds
    assert (CATEGORY, cat.id) in kinds


def test_unchecking_item_unrolls_ancestor(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    a = svc.add_item(cl.id, cat.id, "a")
    svc.set_item_done(a.id, True)
    assert _done(session, Category, cat.id) is True

    svc.set_item_done(a.id, False)
    assert _done(session, Category, cat.id) is False


def test_nested_rollup_through_multiple_levels(svc, session):
    cl = svc.create_blank("CL")
    top = svc.add_category(cl.id, "Top")
    mid = svc.add_category(cl.id, "Mid", parent_id=top.id)
    leaf = svc.add_item(cl.id, mid.id, "leaf")

    svc.set_item_done(leaf.id, True)
    assert _done(session, Category, mid.id) is True
    assert _done(session, Category, top.id) is True


def test_category_toggle_cascades_whole_subtree(svc, session):
    cl = svc.create_blank("CL")
    top = svc.add_category(cl.id, "Top")
    mid = svc.add_category(cl.id, "Mid", parent_id=top.id)
    leaf = svc.add_item(cl.id, mid.id, "leaf")

    changed = svc.set_category_done(top.id, True)
    assert _done(session, ExpenseItem, leaf.id) is True
    assert _done(session, Category, mid.id) is True
    assert _done(session, Category, top.id) is True
    assert {(r.kind, r.id) for r in changed} == {
        (CATEGORY, top.id),
        (CATEGORY, mid.id),
        (EXPENSE_ITEM, leaf.id),
    }


def test_category_uncheck_clears_subtree(svc, session):
    cl = svc.create_blank("CL")
    top = svc.add_category(cl.id, "Top")
    leaf = svc.add_item(cl.id, top.id, "leaf")
    svc.set_category_done(top.id, True)

    svc.set_category_done(top.id, False)
    assert _done(session, ExpenseItem, leaf.id) is False
    assert _done(session, Category, top.id) is False


def test_empty_category_not_silently_completed_on_last_child_removal(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "only")  # cat is False (open child)
    assert _done(session, Category, cat.id) is False

    svc.remove_node(EXPENSE_ITEM, item.id)
    # Now empty: rollup leaves done unchanged -> still False (not vacuously True).
    assert _done(session, Category, cat.id) is False


def test_empty_category_keeps_done_true_when_all_children_removed(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "only")
    svc.set_item_done(item.id, True)  # cat True
    svc.remove_node(EXPENSE_ITEM, item.id)
    assert _done(session, Category, cat.id) is True


def test_no_op_toggle_changes_nothing(svc):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "a")
    changed = svc.set_item_done(item.id, False)  # already False
    assert changed == []


def test_set_done_not_found(svc):
    with pytest.raises(NotFoundError):
        svc.set_item_done(999, True)
    with pytest.raises(NotFoundError):
        svc.set_category_done(999, True)


def test_set_node_done_unknown_kind(session):
    from receipt_board.core import cascade

    with pytest.raises(ValidationError):
        cascade.set_node_done(session, "bogus", 1, True)


def test_cascade_missing_nodes_raise(session):
    from receipt_board.core import cascade

    with pytest.raises(NotFoundError):
        cascade.set_node_done(session, EXPENSE_ITEM, 999, True)
    with pytest.raises(NotFoundError):
        cascade.set_node_done(session, CATEGORY, 999, True)
