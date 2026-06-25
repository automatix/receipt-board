"""Persistence-layer tests: pragmas, FK cascade/restrict, unique constraints."""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from receipt_board.persistence.db import (
    create_db_engine,
    make_session_factory,
    session_scope,
)
from receipt_board.persistence.models import (
    Base,
    Category,
    Checklist,
    ExpenseItem,
    ItemResource,
    ItemTool,
    ResourceType,
    Tool,
)
from receipt_board.persistence.seeds import seed_vocabularies


def _vocab(session, model, name):
    return session.scalars(select(model).where(model.name == name)).one()


def test_pragmas_foreign_keys_and_busy_timeout(session):
    assert session.execute(text("PRAGMA foreign_keys")).scalar() == 1
    assert session.execute(text("PRAGMA busy_timeout")).scalar() == 5000


def test_wal_enabled_on_file_db(tmp_path):
    engine = create_db_engine(tmp_path / "wal.sqlite")
    try:
        with engine.connect() as conn:
            assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
            assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
    finally:
        engine.dispose()


def _make_full_item(session) -> ExpenseItem:
    cl = Checklist(name="CL")
    session.add(cl)
    session.flush()
    cat = Category(checklist_id=cl.id, name="Cat", position=0)
    session.add(cat)
    session.flush()
    item = ExpenseItem(checklist_id=cl.id, category_id=cat.id, name="Item", position=0)
    session.add(item)
    session.flush()
    url = _vocab(session, ResourceType, "URL")
    browser = _vocab(session, Tool, "Browser")
    session.add(ItemResource(item_id=item.id, resource_type_id=url.id, value="x", position=0))
    session.add(ItemTool(item_id=item.id, tool_id=browser.id, position=0))
    session.commit()
    return item


def test_delete_checklist_cascades_to_subtree(session):
    item = _make_full_item(session)
    checklist = session.get(Checklist, item.checklist_id)
    session.delete(checklist)
    session.commit()

    assert session.scalar(select(Category).limit(1)) is None
    assert session.scalar(select(ExpenseItem).limit(1)) is None
    assert session.scalar(select(ItemResource).limit(1)) is None
    assert session.scalar(select(ItemTool).limit(1)) is None
    # Vocabulary entries survive (they are app-wide, not owned by a checklist).
    assert session.scalar(select(ResourceType).where(ResourceType.name == "URL")) is not None


def test_delete_category_cascades_items(session):
    item = _make_full_item(session)
    category = session.get(Category, item.category_id)
    session.delete(category)
    session.commit()
    assert session.scalar(select(ExpenseItem).limit(1)) is None


def test_resource_type_in_use_cannot_be_deleted(session):
    item = _make_full_item(session)
    url = _vocab(session, ResourceType, "URL")
    assert item is not None
    session.delete(url)
    with pytest.raises(IntegrityError):
        session.commit()


def test_tool_in_use_cannot_be_deleted(session):
    _make_full_item(session)
    browser = _vocab(session, Tool, "Browser")
    session.delete(browser)
    with pytest.raises(IntegrityError):
        session.commit()


def test_vocabulary_name_is_unique(session):
    session.add(ResourceType(name="URL"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_item_tools_pair_is_unique(session):
    item = _make_full_item(session)
    browser = _vocab(session, Tool, "Browser")
    session.add(ItemTool(item_id=item.id, tool_id=browser.id, position=1))
    with pytest.raises(IntegrityError):
        session.commit()


def test_session_scope_commits_on_success(session_factory):
    with session_scope(session_factory) as s:
        s.add(Checklist(name="committed"))
    with session_scope(session_factory) as s:
        assert s.scalar(select(Checklist).where(Checklist.name == "committed")) is not None


def test_session_scope_rolls_back_on_error(session_factory):
    with pytest.raises(RuntimeError), session_scope(session_factory) as s:  # noqa: PT012
        s.add(Checklist(name="rolled-back"))
        s.flush()
        raise RuntimeError("boom")
    with session_scope(session_factory) as s:
        assert s.scalar(select(Checklist).where(Checklist.name == "rolled-back")) is None


def test_seed_vocabularies_is_idempotent():
    engine = create_db_engine(None)
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    s = factory()
    seed_vocabularies(s)
    seed_vocabularies(s)  # second call must not duplicate
    s.commit()
    assert len(s.scalars(select(ResourceType)).all()) == 2
    assert len(s.scalars(select(Tool)).all()) == 2
    s.close()
    engine.dispose()
