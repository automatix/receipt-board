"""Pure parser tests (no DB)."""

from __future__ import annotations

from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM
from receipt_board.importer.parser import (
    extract_fields,
    parse,
    type_resource,
)

VALID_TOOLS = {"browser": "Browser", "thunderbird": "Thunderbird"}
VALID_TYPES = {"URL", "Email"}


def _parse(text):
    return parse(text, valid_tools=VALID_TOOLS, valid_resource_types=VALID_TYPES)


def test_extract_fields_all_types():
    name, groups, problems = extract_fields("1&1 (a | b) {Browser} [login] <do it>")
    assert name == "1&1"
    assert groups == [("(", "a | b"), ("{", "Browser"), ("[", "login"), ("<", "do it")]
    assert problems == []


def test_reserved_bracket_inside_field_is_flagged():
    name, groups, problems = extract_fields("Squarespace [http://x/<DOMAN>/y]")
    assert name == "Squarespace"
    assert problems  # the '<' inside [...] is a reserved control character
    assert any("reserved control character" in p for p in problems)


def test_unbalanced_group_is_flagged():
    _, _, problems = extract_fields("Leaf [unterminated")
    assert any("unbalanced" in p for p in problems)


def test_extract_fields_no_groups():
    name, groups, problems = extract_fields("Just a name")
    assert name == "Just a name"
    assert groups == []
    assert problems == []


def test_type_resource_url_email_and_unknown():
    assert type_resource("https://x").type == "URL"
    assert type_resource("https://x").value == "https://x"
    email = type_resource("Email box@x.de")
    assert email.type == "Email"
    assert email.value == "box@x.de"
    assert type_resource("Email").value is None
    assert type_resource("ftp://nope") is None


def test_parse_builds_hierarchy_and_types():
    text = "- [ ] Top\n\t- [ ] Sub\n\t\t- [x] Leaf (https://x) {Browser} [d] <i>\n"
    result = _parse(text)
    assert not result.errors
    top = result.roots[0]
    assert top.kind == CATEGORY and top.name == "Top"
    sub = top.children[0]
    assert sub.kind == CATEGORY
    leaf = sub.children[0]
    assert leaf.kind == EXPENSE_ITEM
    assert leaf.done is True
    assert [r.type for r in leaf.resources] == ["URL"]
    assert leaf.tools == ["Browser"]
    assert leaf.data == "d"
    assert leaf.instructions == "i"


def test_space_indentation_is_handled():
    text = "- [ ] Top\n    - [ ] Sub\n        - [ ] Leaf\n"
    result = _parse(text)
    assert result.roots[0].children[0].children[0].name == "Leaf"


def test_category_with_brackets_warns_and_keeps_name_before_bracket():
    text = "- [ ] Bankkosten (Gebühren)\n\t- [ ] Child\n"
    result = _parse(text)
    assert not result.errors
    assert len(result.warnings) == 1
    assert result.roots[0].kind == CATEGORY
    assert result.roots[0].name == "Bankkosten"


def test_data_is_not_split_on_pipe():
    text = "- [ ] Top\n\t- [ ] Leaf [a | b]\n"
    result = _parse(text)
    assert result.roots[0].children[0].data == "a | b"


def test_top_level_leaf_is_an_error():
    result = _parse("- [ ] Lonely\n")
    assert any(e.kind == "structure" for e in result.errors)


def test_unknown_tool_and_resource_collected_not_raised():
    text = "- [ ] Top\n\t- [ ] Leaf (mailto:x) {Photoshop}\n"
    result = _parse(text)
    kinds = {e.kind for e in result.errors}
    assert kinds == {"resource_type", "tool"}
    tokens = {e.token for e in result.errors}
    assert tokens == {"mailto:x", "Photoshop"}


def test_syntax_error_for_non_list_line():
    result = _parse("This is not a list item\n")
    assert result.errors[0].kind == "syntax"
