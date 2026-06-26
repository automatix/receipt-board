"""ChecklistService / VocabularyService behavior, positions, validation, audit form."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from receipt_board.core.errors import (
    NotFoundError,
    ValidationError,
    VocabularyInUseError,
)
from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM
from receipt_board.persistence.models import AuditEntry, Category, ExpenseItem


def _positions(session, checklist_id, parent_id):
    from receipt_board.core.tree import ordered_children

    return [
        (kind, node.position) for kind, node in ordered_children(session, checklist_id, parent_id)
    ]


# -- structural ---------------------------------------------------------------


def test_create_blank_requires_name(svc):
    with pytest.raises(ValidationError):
        svc.create_blank("   ")


def test_add_category_and_item_interleave_positions(svc, session):
    cl = svc.create_blank("CL")
    parent = svc.add_category(cl.id, "Parent")
    c1 = svc.add_category(cl.id, "C1", parent_id=parent.id)
    i1 = svc.add_item(cl.id, parent.id, "I1")
    c2 = svc.add_category(cl.id, "C2", parent_id=parent.id)
    assert c1.position == 0
    assert i1.position == 1
    assert c2.position == 2
    assert _positions(session, cl.id, parent.id) == [
        (CATEGORY, 0),
        (EXPENSE_ITEM, 1),
        (CATEGORY, 2),
    ]


def test_insert_item_at_position_shifts_siblings(svc, session):
    cl = svc.create_blank("CL")
    parent = svc.add_category(cl.id, "Parent")
    svc.add_item(cl.id, parent.id, "first")
    svc.add_item(cl.id, parent.id, "second")
    inserted = svc.add_item(cl.id, parent.id, "middle", position=1)
    assert inserted.position == 1
    names_by_pos = {
        node.position: node.name
        for node in session.scalars(select(ExpenseItem).where(ExpenseItem.category_id == parent.id))
    }
    assert names_by_pos == {0: "first", 1: "middle", 2: "second"}


def test_add_item_with_resources_and_tools(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(
        cl.id,
        cat.id,
        "1&1",
        resources=[{"type": "URL", "value": "https://x"}, {"type": "Email", "value": None}],
        tools=["Browser", "Thunderbird"],
        data="Login 1",
        instructions="open link",
    )
    session.refresh(item)
    assert [r.resource_type.name for r in item.resources] == ["URL", "Email"]
    assert item.resources[0].value == "https://x"
    assert [t.tool.name for t in item.tools] == ["Browser", "Thunderbird"]


def test_add_item_unknown_resource_type_rejected(svc):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    with pytest.raises(ValidationError) as exc:
        svc.add_item(cl.id, cat.id, "x", resources=[{"type": "Fax"}])
    assert exc.value.details.get("name") == "Fax"


def test_resource_value_must_match_pattern(svc):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    with pytest.raises(ValidationError):
        svc.add_item(cl.id, cat.id, "x", resources=[{"type": "URL", "value": "not-a-url"}])


def test_resource_value_required_when_not_optional(svc):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    with pytest.raises(ValidationError):
        svc.add_item(cl.id, cat.id, "x", resources=[{"type": "URL"}])  # URL needs a value


def test_optional_resource_value_allowed(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "x", resources=[{"type": "Email"}])  # value optional
    session.refresh(item)
    assert item.resources[0].value is None


def test_add_item_unknown_tool_rejected(svc):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    with pytest.raises(ValidationError):
        svc.add_item(cl.id, cat.id, "x", tools=["Photoshop"])


def test_add_item_duplicate_tool_rejected(svc):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    with pytest.raises(ValidationError):
        svc.add_item(cl.id, cat.id, "x", tools=["Browser", "Browser"])


def test_add_category_wrong_checklist_parent_rejected(svc):
    a = svc.create_blank("A")
    b = svc.create_blank("B")
    parent = svc.add_category(a.id, "P")
    with pytest.raises(ValidationError):
        svc.add_category(b.id, "child", parent_id=parent.id)


def test_edit_category_rename(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Old")
    svc.edit_node(CATEGORY, cat.id, {"name": "New"})
    assert session.get(Category, cat.id).name == "New"


def test_edit_item_replaces_resources(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "x", resources=[{"type": "URL", "value": "https://a"}])
    svc.edit_node(
        EXPENSE_ITEM,
        item.id,
        {"data": "d", "instructions": "i", "resources": [{"type": "Email"}], "tools": ["Browser"]},
    )
    session.refresh(item)
    assert item.data == "d"
    assert [r.resource_type.name for r in item.resources] == ["Email"]
    assert [t.tool.name for t in item.tools] == ["Browser"]


def test_edit_unknown_kind_rejected(svc):
    with pytest.raises(ValidationError):
        svc.edit_node("bogus", 1, {})


def test_remove_node_repacks_siblings(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    a = svc.add_item(cl.id, cat.id, "a")
    b = svc.add_item(cl.id, cat.id, "b")
    c = svc.add_item(cl.id, cat.id, "c")
    svc.remove_node(EXPENSE_ITEM, b.id)
    remaining = {
        node.name: node.position
        for node in session.scalars(select(ExpenseItem).where(ExpenseItem.category_id == cat.id))
    }
    assert remaining == {"a": 0, "c": 1}
    assert a.id and c.id


def test_move_item_reparents_and_rolls_up_both(svc, session):
    cl = svc.create_blank("CL")
    src = svc.add_category(cl.id, "Src")
    dst = svc.add_category(cl.id, "Dst")
    a = svc.add_item(cl.id, src.id, "a")
    svc.set_item_done(a.id, True)  # src done True, dst empty
    assert session.get(Category, src.id).done is True

    svc.move_node(EXPENSE_ITEM, a.id, new_parent_id=dst.id)
    session.refresh(a)
    assert a.category_id == dst.id
    # dst now has a done item -> dst True; src emptied -> left unchanged (True)
    assert session.get(Category, dst.id).done is True


def test_move_category_into_own_subtree_rejected(svc):
    cl = svc.create_blank("CL")
    top = svc.add_category(cl.id, "Top")
    mid = svc.add_category(cl.id, "Mid", parent_id=top.id)
    with pytest.raises(ValidationError):
        svc.move_node(CATEGORY, top.id, new_parent_id=mid.id)


def test_move_item_to_top_level_rejected(svc):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "x")
    with pytest.raises(ValidationError):
        svc.move_node(EXPENSE_ITEM, item.id, new_parent_id=None)


def test_move_reorders_within_same_parent(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    a = svc.add_item(cl.id, cat.id, "a")
    b = svc.add_item(cl.id, cat.id, "b")
    c = svc.add_item(cl.id, cat.id, "c")
    svc.move_node(EXPENSE_ITEM, c.id, new_parent_id=cat.id, position=0)
    order = {
        node.position: node.name
        for node in session.scalars(select(ExpenseItem).where(ExpenseItem.category_id == cat.id))
    }
    assert order == {0: "c", 1: "a", 2: "b"}
    assert a.id and b.id


def test_edit_category_without_name_is_noop(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Keep")
    svc.edit_node(CATEGORY, cat.id, {})
    assert session.get(Category, cat.id).name == "Keep"


def test_move_category_to_top_level(svc, session):
    cl = svc.create_blank("CL")
    top = svc.add_category(cl.id, "Top")
    mid = svc.add_category(cl.id, "Mid", parent_id=top.id)
    svc.move_node(CATEGORY, mid.id, new_parent_id=None)
    assert session.get(Category, mid.id).parent_id is None


def test_remove_unknown_kind_rejected(svc):
    with pytest.raises(ValidationError):
        svc.remove_node("bogus", 1)


def test_clone_deep_copies_and_resets_done(svc, session):
    cl = svc.create_blank("Source")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(
        cl.id, cat.id, "x", resources=[{"type": "URL", "value": "https://u"}], tools=["Browser"]
    )
    svc.set_item_done(item.id, True)

    clone = svc.clone(cl.id, "Copy")
    assert clone.id != cl.id
    clone_items = session.scalars(
        select(ExpenseItem).where(ExpenseItem.checklist_id == clone.id)
    ).all()
    assert len(clone_items) == 1
    copied = clone_items[0]
    assert copied.id != item.id
    assert copied.done is False
    assert [r.resource_type.name for r in copied.resources] == ["URL"]
    assert [t.tool.name for t in copied.tools] == ["Browser"]


def test_delete_checklist(svc, session):
    cl = svc.create_blank("CL")
    svc.add_category(cl.id, "Cat")
    svc.delete(cl.id)
    from receipt_board.persistence.models import Checklist

    assert session.get(Checklist, cl.id) is None


def test_operations_on_missing_entities_raise_not_found(svc):
    with pytest.raises(NotFoundError):
        svc.add_category(999, "x")
    with pytest.raises(NotFoundError):
        svc.add_item(999, 999, "x")
    with pytest.raises(NotFoundError):
        svc.edit_node(CATEGORY, 999, {"name": "x"})
    with pytest.raises(NotFoundError):
        svc.delete(999)
    with pytest.raises(NotFoundError):
        svc.clone(999, "x")


# -- vocabulary ---------------------------------------------------------------


def test_vocab_add_rename_list(vocab):
    added = vocab.add("tool", "Photoshop")
    assert added["name"] == "Photoshop"
    vocab.update("tool", added["id"], {"name": "GIMP"})
    names = [row["name"] for row in vocab.list("tool")]
    assert "GIMP" in names and "Photoshop" not in names


def test_vocab_add_duplicate_rejected(vocab):
    with pytest.raises(ValidationError):
        vocab.add("tool", "Browser")


def test_vocab_rename_clash_rejected(vocab):
    added = vocab.add("tool", "Photoshop")
    with pytest.raises(ValidationError):
        vocab.update("tool", added["id"], {"name": "Browser"})


def test_resource_type_list_carries_metadata(vocab):
    by_name = {row["name"]: row for row in vocab.list("resource_type")}
    assert by_name["URL"]["value_optional"] is False
    assert by_name["URL"]["value_pattern"] == r"^https?://"
    assert by_name["Email"]["value_optional"] is True
    # tools have no extra fields
    assert set(vocab.list("tool")[0]) == {"id", "name"}


def test_resource_type_add_and_update_fields(vocab):
    added = vocab.add("resource_type", "FTP", value_optional=True, value_pattern=r"^ftps?://\S+$")
    assert added["value_optional"] is True
    assert added["value_pattern"] == r"^ftps?://\S+$"
    updated = vocab.update(
        "resource_type", added["id"], {"value_optional": False, "value_pattern": None}
    )
    assert updated["value_optional"] is False
    assert updated["value_pattern"] is None


def test_resource_type_invalid_pattern_rejected(vocab):
    with pytest.raises(ValidationError):
        vocab.add("resource_type", "Bad", value_pattern="[unterminated")


def test_vocab_duplicate_copies_fields(vocab):
    source = next(r for r in vocab.list("resource_type") if r["name"] == "URL")
    copy = vocab.duplicate("resource_type", source["id"], "Link")
    assert copy["name"] == "Link"
    assert copy["value_pattern"] == source["value_pattern"]
    assert copy["value_optional"] == source["value_optional"]


def test_vocab_remove_unused(vocab, session):
    added = vocab.add("resource_type", "FTP")
    vocab.remove("resource_type", added["id"])
    assert "FTP" not in [row["name"] for row in vocab.list("resource_type")]


def test_vocab_remove_in_use_blocked(svc, vocab, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "x", tools=["Browser"])
    browser_id = next(r["id"] for r in vocab.list("tool") if r["name"] == "Browser")
    with pytest.raises(VocabularyInUseError) as exc:
        vocab.remove("tool", browser_id)
    assert item.id in exc.value.details["item_ids"]


def test_vocab_unknown_kind_and_missing_id(vocab):
    with pytest.raises(ValidationError):
        vocab.add("color", "Red")
    with pytest.raises(NotFoundError):
        vocab.update("tool", 999, {"name": "X"})
    with pytest.raises(NotFoundError):
        vocab.remove("tool", 999)


# -- audit --------------------------------------------------------------------


def test_audit_entry_shape_for_done_toggle(svc, session):
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "a")
    svc.set_item_done(item.id, True)

    entry = session.scalars(
        select(AuditEntry).where(AuditEntry.action_type == "set_item_done")
    ).one()
    assert entry.origin == "REST"
    assert entry.session_id == "test-session"
    assert entry.target_kind == EXPENSE_ITEM
    assert entry.target_id == item.id
    assert entry.checklist_id == cl.id
    assert entry.payload == {"old": False, "new": True}
    assert {"kind": CATEGORY, "id": cat.id} in entry.affected_ids
    assert entry.app_version
    assert entry.ts


def test_audit_one_entry_per_action(svc, session):
    cl = svc.create_blank("CL")  # 1
    cat = svc.add_category(cl.id, "Cat")  # 2
    svc.add_item(cl.id, cat.id, "a")  # 3
    count = len(session.scalars(select(AuditEntry)).all())
    assert count == 3
