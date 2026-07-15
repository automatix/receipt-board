"""Markdown exporter tests (issue #171): canonical notation, byte-identical roundtrip."""

from __future__ import annotations

from pathlib import Path

from receipt_board.core.refs import EXPENSE_ITEM
from receipt_board.exporter.markdown import export_markdown

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_fixture_roundtrips_byte_identical(svc, session):
    """An unmodified import of the notation-conformant fixture exports 1:1."""
    text = (FIXTURES / "roundtrip_checklist.md").read_text(encoding="utf-8")
    checklist = svc.import_markdown("Fixture", text)
    assert export_markdown(session, checklist.id) == text


def test_ignored_category_fields_do_not_roundtrip(svc, session):
    """Bracket fields on a category are dropped at import (warning, ADR-0007), so a file
    carrying them exports without them — the documented exception to the 1:1 rule."""
    text = (FIXTURES / "valid_checklist.md").read_text(encoding="utf-8")
    checklist = svc.import_markdown("Lossy", text)
    exported = export_markdown(session, checklist.id)
    assert "- [ ] LinkedIn\n" in exported
    assert exported == text.replace(
        "- [ ] LinkedIn [https://www.linkedin.com/manage/purchases-payments/transactions]\n",
        "- [ ] LinkedIn\n",
    )


def test_manually_markers_and_done_roundtrip(svc, session):
    text = (
        "- [ ] Mobility\n"
        "\t- [x] Taxi ~manually~\n"
        "\t- [ ] Bolt (https://bolt.eu ~manually~ | Email) {Browser} [note] <do it>\n"
    )
    checklist = svc.import_markdown("Marked", text)
    assert export_markdown(session, checklist.id) == text


def test_done_category_exports_checked(svc, session):
    # The category's done is derived bottom-up on import, so an all-done subtree
    # exports with [x] on the category line and re-imports identically (idempotent).
    text = "- [ ] Top\n\t- [x] Leaf\n"
    checklist = svc.import_markdown("Done", text)
    exported = export_markdown(session, checklist.id)
    assert exported == "- [x] Top\n\t- [x] Leaf\n"
    again = svc.import_markdown("Done2", exported)
    assert export_markdown(session, again.id) == exported


def test_patternless_type_uses_keyed_token(svc, session, vocab):
    # A value that no pattern types bare must fall back to `Type: value` — and that
    # keyed form re-imports to the same resource.
    vocab.add("resource_type", "Login", value_optional=False, value_pattern=None)
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    svc.add_item(cl.id, cat.id, "x", resources=[{"type": "Login", "value": "acct-123"}])
    exported = export_markdown(session, cl.id)
    assert "(Login: acct-123)" in exported
    again = svc.import_markdown("Again", exported)
    assert export_markdown(session, again.id) == exported


def test_newlines_in_fields_collapse_to_spaces(svc, session):
    # GUI-entered multiline instructions cannot survive the line-based grammar.
    cl = svc.create_blank("CL")
    cat = svc.add_category(cl.id, "Cat")
    item = svc.add_item(cl.id, cat.id, "x", instructions="line one\nline two")
    svc.edit_node(EXPENSE_ITEM, item.id, {"data": "a\nb"})
    exported = export_markdown(session, cl.id)
    assert "[a b]" in exported
    assert "<line one line two>" in exported


def test_empty_checklist_exports_empty_string(svc, session):
    cl = svc.create_blank("Empty")
    assert export_markdown(session, cl.id) == ""
