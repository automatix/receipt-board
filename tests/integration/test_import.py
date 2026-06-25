"""ImportService tests.

Policy (decided with the user): the importer is **fully strict** — an untypable
``(...)`` resource token aborts the import (ADR-0005). The real reference file
``expenses_checklist_2024_v02.md`` therefore does **not** import unmodified, because it
contains ``Taxi (klassisch)`` (parentheses used as a name qualifier, not a resource): the
importer rejects it atomically with a precise report. The success path is exercised
against the notation-compliant ``valid_checklist.md``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import func, select

from receipt_board.core.errors import InvalidImportError
from receipt_board.core.queries import export_checklist
from receipt_board.importer.service import ImportService
from receipt_board.persistence.models import AuditEntry, Category, Checklist, ExpenseItem

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
VALID = FIXTURES / "valid_checklist.md"
REAL = FIXTURES / "expenses_checklist_2024_v02.md"


def _find_item(tree: dict, name: str) -> dict | None:
    for child in tree.get("children", []):
        if child["kind"] == "expense_item" and child["name"] == name:
            return child
        found = _find_item(child, name)
        if found:
            return found
    return None


def test_imports_valid_fixture_with_typed_fields(session, audit):
    checklist = ImportService(session, audit).import_markdown(
        "Expenses 2024", VALID.read_text("utf-8")
    )
    session.commit()
    tree = export_checklist(session, checklist.id)

    one_and_one = _find_item(tree, "1&1")
    assert one_and_one["resources"] == [
        {"type": "URL", "value": "https://control-center.1und1.de/invoice.html#/current"},
        {"type": "Email", "value": None},
    ]
    assert one_and_one["tools"] == ["Browser", "Thunderbird"]
    assert one_and_one["data"] == "Login 588791127"
    assert "öffne den Link" in one_and_one["instructions"]


def test_url_in_square_brackets_is_data_not_resource(session, audit):
    checklist = ImportService(session, audit).import_markdown("X", VALID.read_text("utf-8"))
    tree = export_checklist(session, checklist.id)
    youtube = _find_item(tree, "YouTube Premium")
    assert youtube["resources"] == []
    assert youtube["data"] == "https://payments.google.com"


def test_reserved_control_char_in_free_text_is_rejected(session, audit):
    # '<' inside the [...] data value is a reserved control character -> syntax error.
    before = session.scalar(select(func.count()).select_from(Checklist))
    bad = "- [ ] Top\n\t- [ ] Leaf [http://x/<DOMAN>/y]\n"
    with pytest.raises(InvalidImportError) as exc:
        ImportService(session, audit).import_markdown("Bad", bad)
    assert any(e["kind"] == "syntax" for e in exc.value.details["errors"])
    session.rollback()
    assert session.scalar(select(func.count()).select_from(Checklist)) == before


def test_category_with_bracket_fields_records_warning(session, audit):
    # LinkedIn has children -> Category; its [...] is ignored and counted as a warning.
    ImportService(session, audit).import_markdown("X", VALID.read_text("utf-8"))
    entry = session.scalars(
        select(AuditEntry).where(AuditEntry.action_type == "import_checklist")
    ).one()
    assert entry.payload["new"]["warnings"] >= 1


def test_import_writes_exactly_one_audit_entry(session, audit):
    ImportService(session, audit).import_markdown("X", VALID.read_text("utf-8"))
    entries = session.scalars(
        select(AuditEntry).where(AuditEntry.action_type == "import_checklist")
    ).all()
    assert len(entries) == 1


def test_imported_done_state_is_consistent(session, audit):
    checklist = ImportService(session, audit).import_markdown("X", VALID.read_text("utf-8"))
    done_categories = session.scalars(
        select(Category).where(Category.checklist_id == checklist.id, Category.done.is_(True))
    ).all()
    assert done_categories == []


def test_checklist_service_import_delegates(svc, session):
    checklist = svc.import_markdown("Via service", VALID.read_text("utf-8"))
    session.commit()
    items = session.scalar(
        select(func.count())
        .select_from(ExpenseItem)
        .where(ExpenseItem.checklist_id == checklist.id)
    )
    assert items > 0


def test_real_reference_file_is_rejected_strictly(session, audit):
    before = session.scalar(select(func.count()).select_from(Checklist))
    with pytest.raises(InvalidImportError) as exc:
        ImportService(session, audit).import_markdown("Real", REAL.read_text("utf-8"))
    errors = exc.value.details["errors"]
    klassisch = next(e for e in errors if e["token"] == "klassisch")
    assert klassisch["kind"] == "resource_type"
    assert klassisch["line"] == 36
    assert "recommendation" in exc.value.details
    session.rollback()
    assert session.scalar(select(func.count()).select_from(Checklist)) == before


def test_import_unknown_tool_aborts_atomically(session, audit):
    before = session.scalar(select(func.count()).select_from(Checklist))
    bad = "- [ ] Top\n\t- [ ] Leaf {Photoshop}\n"
    with pytest.raises(InvalidImportError) as exc:
        ImportService(session, audit).import_markdown("Bad", bad)
    assert any(e["kind"] == "tool" for e in exc.value.details["errors"])
    session.rollback()
    assert session.scalar(select(func.count()).select_from(Checklist)) == before


def test_import_empty_name_rejected(session, audit):
    with pytest.raises(InvalidImportError):
        ImportService(session, audit).import_markdown("   ", "- [ ] Top\n\t- [ ] x\n")
