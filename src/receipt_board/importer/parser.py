"""Strict Markdown checklist parser (TECH_SPEC §6, ADR-0005/0006).

Pure (no DB). Produces a typed node tree plus a list of issues; the service decides
atomicity. Indentation defines hierarchy (tabs/spaces handled via a width stack, so the
indent unit is auto-detected by relative width). Node type is structural: childless rows
are Expense Items, ancestors are Categories.

Fields are strict by bracket type and parsed **only for Expense Items**:
``(...)``→resources, ``{...}``→tools, ``[...]``→data, ``<...>``→instructions; multi-values
in resources/tools split on ``|`` (``data``/``instructions`` are free text, kept verbatim).
Because Categories carry no action fields (ADR-0007), any bracket content on a node that
turns out to be a Category is ignored and reported as a warning.

The eight characters ``()[]{}<>`` are **reserved control characters**: they delimit
fields and are not permitted inside free text (names or field values). A reserved
character appearing inside a field value is a syntax error (and aborts the atomic import).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM, NodeKind

_LINE_RE = re.compile(r"^(?P<indent>[ \t]*)-\s\[(?P<check>[ xX])\]\s+(?P<text>.*)$")

_OPENERS = {"(": ")", "{": "}", "[": "]", "<": ">"}
_FIELD_BY_OPENER = {"(": "resources", "{": "tools", "[": "data", "<": "instructions"}
_RESERVED = set("()[]{}<>")


@dataclass
class ParsedResource:
    type: str
    value: str | None


@dataclass
class ResourceTypeDef:
    """A resource type's matching rules: the name key, value-optionality and value regex."""

    name: str
    value_optional: bool = False
    value_pattern: str | None = None


@dataclass
class ParsedNode:
    line: int
    raw_body: str
    done: bool
    depth: int
    children: list[ParsedNode] = field(default_factory=list)
    kind: NodeKind | None = None
    name: str = ""
    resources: list[ParsedResource] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    data: str | None = None
    instructions: str | None = None


@dataclass
class ImportIssue:
    line: int
    token: str
    kind: str  # syntax | structure | resource_type | tool
    message: str

    def as_dict(self) -> dict:
        return {"line": self.line, "token": self.token, "kind": self.kind, "message": self.message}


@dataclass
class ParseResult:
    roots: list[ParsedNode]
    errors: list[ImportIssue]
    warnings: list[ImportIssue]


def extract_fields(text: str) -> tuple[str, list[tuple[str, str]], list[str]]:
    """Return (name, [(opener, content), ...], problems).

    ``name`` is the text before the first reserved control character. Each field group is
    ``opener content closer`` whose content must contain **no** reserved character (they
    delimit fields and are not allowed in free text). A reserved character inside a value,
    or an unbalanced group, yields a syntax ``problem`` (the import then aborts).
    """
    first = next((i for i, ch in enumerate(text) if ch in _RESERVED), None)
    if first is None:
        return text.strip(), [], []
    name = text[:first].strip()
    groups: list[tuple[str, str]] = []
    problems: list[str] = []
    i, n = first, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch not in _OPENERS:
            # A stray closer / non-opener reserved char outside any group.
            problems.append(f"reserved control character {ch!r} is not allowed in free text")
            break
        closer = _OPENERS[ch]
        content: list[str] = []
        j = i + 1
        bad = terminated = False
        while j < n:
            cj = text[j]
            if cj == closer:
                terminated = True
                break
            if cj in _RESERVED:
                problems.append(f"reserved control character {cj!r} is not allowed in free text")
                bad = True
                break
            content.append(cj)
            j += 1
        if bad:
            break
        if not terminated:
            problems.append(f"unbalanced field group starting with {ch!r}")
            break
        groups.append((ch, "".join(content).strip()))
        i = j + 1
    return name, groups, problems


def _value_matches(rt: ResourceTypeDef, value: str) -> bool:
    if not rt.value_pattern:
        return True
    return re.search(rt.value_pattern, value, re.IGNORECASE) is not None


def type_resource(
    token: str, resource_types: list[ResourceTypeDef]
) -> tuple[ParsedResource | None, str | None]:
    """Type a resource token against the resource-type definitions, case-insensitively.

    Generic (data-driven) — no per-type branching. Accepted forms:
      * ``Key: value`` — the key matches a type name; the value must match its pattern.
      * a bare ``Key`` — when that type's value is optional (e.g. ``Email``).
      * a bare value — typed by the first resource type whose regex matches it.
    Returns ``(resource, None)`` on success, or ``(None, message)`` when a keyed token is
    malformed, or ``(None, None)`` when the token matches no type at all.
    """
    token = token.strip()
    by_key = {rt.name.lower(): rt for rt in resource_types}
    key_part, sep, value_part = token.partition(":")
    keyed = by_key.get(key_part.strip().lower())
    if keyed is not None:
        value = value_part.strip() if sep else ""
        if not value:
            if keyed.value_optional:
                return ParsedResource(keyed.name, None), None
            return None, f"resource type {keyed.name!r} requires a value"
        if not _value_matches(keyed, value):
            return None, f"value {value!r} does not match the {keyed.name} pattern"
        return ParsedResource(keyed.name, value), None
    for rt in resource_types:
        if rt.value_pattern and re.search(rt.value_pattern, token, re.IGNORECASE):
            return ParsedResource(rt.name, token), None
    return None, None


def _parse_item_fields(
    node: ParsedNode,
    groups: list[tuple[str, str]],
    *,
    valid_tools: dict[str, str],
    resource_types: list[ResourceTypeDef],
    errors: list[ImportIssue],
) -> None:
    resource_tokens: list[str] = []
    tool_tokens: list[str] = []
    data_parts: list[str] = []
    instruction_parts: list[str] = []
    for opener, content in groups:
        target = _FIELD_BY_OPENER[opener]
        if target == "resources":
            resource_tokens += [t.strip() for t in content.split("|") if t.strip()]
        elif target == "tools":
            tool_tokens += [t.strip() for t in content.split("|") if t.strip()]
        elif target == "data":
            data_parts.append(content.strip())
        else:
            instruction_parts.append(content.strip())

    for token in resource_tokens:
        typed, problem = type_resource(token, resource_types)
        if typed is None:
            errors.append(
                ImportIssue(
                    line=node.line,
                    token=token,
                    kind="resource_type",
                    message=problem or f"Cannot type resource {token!r}",
                )
            )
        else:
            node.resources.append(typed)

    for token in tool_tokens:
        canonical = valid_tools.get(token.lower())
        if canonical is None:
            errors.append(
                ImportIssue(
                    line=node.line,
                    token=token,
                    kind="tool",
                    message=f"Unknown tool {token!r}; add it to the Tool vocabulary via the GUI",
                )
            )
        else:
            node.tools.append(canonical)

    node.data = " ".join(p for p in data_parts if p) or None
    node.instructions = " ".join(p for p in instruction_parts if p) or None


def parse(
    text: str,
    *,
    valid_tools: dict[str, str],
    resource_types: list[ResourceTypeDef],
) -> ParseResult:
    """Parse Markdown into a typed node tree, collecting all errors and warnings."""
    errors: list[ImportIssue] = []
    warnings: list[ImportIssue] = []
    roots: list[ParsedNode] = []
    width_stack: list[int] = []
    path: list[ParsedNode] = []

    for lineno, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        match = _LINE_RE.match(raw)
        if match is None:
            errors.append(
                ImportIssue(lineno, raw.strip(), "syntax", "Not a '- [ ]' checklist item")
            )
            continue
        body = match.group("text").strip()
        if not body:
            errors.append(ImportIssue(lineno, raw.strip(), "syntax", "Item has no name"))
            continue

        width = len(match.group("indent").expandtabs(8))
        while width_stack and width < width_stack[-1]:
            width_stack.pop()
        if not width_stack or width > width_stack[-1]:
            width_stack.append(width)
        depth = len(width_stack) - 1

        node = ParsedNode(
            line=lineno, raw_body=body, done=match.group("check").lower() == "x", depth=depth
        )
        path = path[:depth]
        if depth == 0:
            roots.append(node)
        else:
            path[depth - 1].children.append(node)
        path.append(node)

    def finalize(node: ParsedNode) -> None:
        name, groups, problems = extract_fields(node.raw_body)
        node.name = name
        for problem in problems:
            errors.append(ImportIssue(node.line, node.raw_body, "syntax", problem))
        if node.children:
            node.kind = CATEGORY
            if groups:
                warnings.append(
                    ImportIssue(
                        node.line,
                        node.raw_body,
                        "structure",
                        "Bracket fields on a category were ignored (categories have no fields)",
                    )
                )
            for child in node.children:
                finalize(child)
        else:
            node.kind = EXPENSE_ITEM
            if not problems:
                _parse_item_fields(
                    node,
                    groups,
                    valid_tools=valid_tools,
                    resource_types=resource_types,
                    errors=errors,
                )

    for root in roots:
        finalize(root)
        if root.kind == EXPENSE_ITEM:
            errors.append(
                ImportIssue(
                    root.line,
                    root.name,
                    "structure",
                    "A top-level entry must be a category (an expense item cannot be top-level)",
                )
            )

    return ParseResult(roots=roots, errors=errors, warnings=warnings)
