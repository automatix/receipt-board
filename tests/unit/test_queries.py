"""Read queries: list, nested export, flat search."""

from __future__ import annotations

import pytest

from receipt_board.core.errors import NotFoundError
from receipt_board.core.queries import export_checklist, list_audit, list_checklists, search


def _sample(svc):
    cl = svc.create_blank("Expenses 2024")
    top = svc.add_category(cl.id, "Verbindung")
    sub = svc.add_category(cl.id, "Festnetz&DSL", parent_id=top.id)
    item = svc.add_item(
        cl.id,
        sub.id,
        "1&1",
        resources=[{"type": "URL", "value": "https://x"}, {"type": "Email", "value": None}],
        tools=["Browser"],
        data="Login 1",
        instructions="open link",
    )
    return cl, top, sub, item


def test_list_audit_newest_first_filter_and_limit(svc):
    cl, _top, _sub, item = _sample(svc)
    svc.set_item_done(item.id, True)
    svc.create_blank("Other")

    rows = list_audit(svc.session)
    assert rows
    ids = [r["id"] for r in rows]
    assert ids == sorted(ids, reverse=True)  # newest first
    assert rows[0]["action_type"] == "create_checklist"  # the most recent action

    cl_rows = list_audit(svc.session, checklist_id=cl.id)
    assert cl_rows and all(r["checklist_id"] == cl.id for r in cl_rows)
    assert any(r["action_type"] == "set_item_done" for r in cl_rows)

    assert len(list_audit(svc.session, limit=1)) == 1


def test_list_checklists(svc):
    svc.create_blank("A")
    svc.create_blank("B")
    rows = list_checklists(svc.session)
    assert [r["name"] for r in rows] == ["A", "B"]
    assert "created_at" in rows[0]


def test_export_is_nested_with_all_fields(svc):
    cl, top, sub, item = _sample(svc)
    tree = export_checklist(svc.session, cl.id)
    assert tree["name"] == "Expenses 2024"
    top_node = tree["children"][0]
    assert top_node["kind"] == "category"
    assert top_node["name"] == "Verbindung"
    sub_node = top_node["children"][0]
    item_node = sub_node["children"][0]
    assert item_node["kind"] == "expense_item"
    assert item_node["name"] == "1&1"
    assert item_node["data"] == "Login 1"
    assert item_node["resources"] == [
        {"type": "URL", "value": "https://x"},
        {"type": "Email", "value": None},
    ]
    assert item_node["tools"] == ["Browser"]


def test_export_not_found(svc):
    with pytest.raises(NotFoundError):
        export_checklist(svc.session, 999)


def test_search_returns_flat_hits_with_ancestor_path(svc):
    cl, top, sub, item = _sample(svc)
    hits = search(svc.session, "1&1")
    assert len(hits) == 1
    hit = hits[0]
    assert hit["kind"] == "expense_item"
    assert hit["id"] == item.id
    assert hit["checklist_id"] == cl.id
    assert hit["path"] == ["Verbindung", "Festnetz&DSL"]


def test_search_matches_categories_case_insensitively(svc):
    cl, top, sub, item = _sample(svc)
    hits = search(svc.session, "verbindung")
    assert any(h["kind"] == "category" and h["id"] == top.id for h in hits)


def test_search_can_scope_to_checklist(svc):
    a = svc.create_blank("A")
    cat_a = svc.add_category(a.id, "Shared")
    b = svc.create_blank("B")
    svc.add_category(b.id, "Shared")
    hits = search(svc.session, "Shared", checklist_id=a.id)
    assert {h["id"] for h in hits} == {cat_a.id}


def test_search_empty_query_returns_empty(svc):
    _sample(svc)
    assert search(svc.session, "   ") == []
