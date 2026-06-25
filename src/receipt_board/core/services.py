"""Domain services (TECH_SPEC §4).

Each write method performs its mutation, runs the cascade where ``done`` is involved,
and records exactly one audit entry — all within the caller's transaction (ADR-0008:
one SQLite transaction per action). The caller (API request scope) commits.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from receipt_board.core import cascade
from receipt_board.core.audit import AuditService
from receipt_board.core.errors import (
    NotFoundError,
    ValidationError,
    VocabularyInUseError,
)
from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM, NodeKind, NodeRef
from receipt_board.core.tree import descendant_category_ids, ordered_children
from receipt_board.persistence.models import (
    Category,
    Checklist,
    ExpenseItem,
    ItemResource,
    ItemTool,
    ResourceType,
    Tool,
)

_VOCAB_MODELS = {"resource_type": ResourceType, "tool": Tool}


def _require_name(name: str) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        raise ValidationError("Name must not be empty")
    return cleaned


def _place(
    session: Session,
    checklist_id: int,
    parent_id: int | None,
    kind: NodeKind,
    node: Category | ExpenseItem,
    position: int | None,
) -> None:
    """Insert ``node`` among its siblings at ``position`` and re-pack positions 0..n.

    ``node`` must already point at ``parent_id``. Reordering writes the affected
    siblings contiguously (TECH_SPEC §3).
    """
    siblings = [
        (kind_, child)
        for kind_, child in ordered_children(session, checklist_id, parent_id)
        if not (kind_ == kind and child.id == node.id)
    ]
    index = len(siblings) if position is None or position >= len(siblings) else max(0, position)
    siblings.insert(index, (kind, node))
    for new_position, (_, child) in enumerate(siblings):
        child.position = new_position


def _repack(session: Session, checklist_id: int, parent_id: int | None) -> None:
    for new_position, (_, child) in enumerate(ordered_children(session, checklist_id, parent_id)):
        child.position = new_position


class ChecklistService:
    def __init__(self, session: Session, audit: AuditService) -> None:
        self.session = session
        self.audit = audit

    # -- checklist lifecycle ------------------------------------------------

    def create_blank(self, name: str) -> Checklist:
        checklist = Checklist(name=_require_name(name))
        self.session.add(checklist)
        self.session.flush()
        self.audit.record(
            action_type="create_checklist",
            target_kind="checklist",
            target_id=checklist.id,
            checklist_id=checklist.id,
            payload={"old": None, "new": {"name": checklist.name}},
        )
        return checklist

    def delete(self, checklist_id: int) -> None:
        checklist = self._get_checklist(checklist_id)
        old_name = checklist.name
        self.session.delete(checklist)
        self.session.flush()
        self.audit.record(
            action_type="delete_checklist",
            target_kind="checklist",
            target_id=checklist_id,
            checklist_id=checklist_id,
            payload={"old": {"name": old_name}, "new": None},
        )

    def clone(self, checklist_id: int, new_name: str) -> Checklist:
        """Deep-copy structure + fields with fresh ids and ``done=False`` (GLOSSARY: Clone)."""
        source = self._get_checklist(checklist_id)
        clone = Checklist(name=_require_name(new_name))
        self.session.add(clone)
        self.session.flush()

        def copy_item(src: ExpenseItem, new_category_id: int) -> None:
            item = ExpenseItem(
                checklist_id=clone.id,
                category_id=new_category_id,
                name=src.name,
                position=src.position,
                done=False,
                data=src.data,
                instructions=src.instructions,
            )
            self.session.add(item)
            self.session.flush()
            for resource in src.resources:
                self.session.add(
                    ItemResource(
                        item_id=item.id,
                        resource_type_id=resource.resource_type_id,
                        value=resource.value,
                        position=resource.position,
                    )
                )
            for link in src.tools:
                self.session.add(
                    ItemTool(item_id=item.id, tool_id=link.tool_id, position=link.position)
                )

        def copy_category(src: Category, new_parent_id: int | None) -> None:
            category = Category(
                checklist_id=clone.id,
                parent_id=new_parent_id,
                name=src.name,
                position=src.position,
                done=False,
            )
            self.session.add(category)
            self.session.flush()
            for item in self.session.scalars(
                select(ExpenseItem).where(ExpenseItem.category_id == src.id)
            ):
                copy_item(item, category.id)
            for sub in self.session.scalars(select(Category).where(Category.parent_id == src.id)):
                copy_category(sub, category.id)

        for top in self.session.scalars(
            select(Category).where(Category.checklist_id == source.id, Category.parent_id.is_(None))
        ):
            copy_category(top, None)

        self.audit.record(
            action_type="clone_checklist",
            target_kind="checklist",
            target_id=clone.id,
            checklist_id=clone.id,
            payload={"old": {"source_id": source.id}, "new": {"name": clone.name}},
        )
        return clone

    # -- structural edits ---------------------------------------------------

    def add_category(
        self,
        checklist_id: int,
        name: str,
        *,
        parent_id: int | None = None,
        position: int | None = None,
    ) -> Category:
        self._get_checklist(checklist_id)
        if parent_id is not None:
            parent = self._get_category(parent_id)
            if parent.checklist_id != checklist_id:
                raise ValidationError("Parent category belongs to a different checklist")
        category = Category(
            checklist_id=checklist_id,
            parent_id=parent_id,
            name=_require_name(name),
            done=False,
            position=0,  # placeholder; _place assigns the real position
        )
        self.session.add(category)
        self.session.flush()
        _place(self.session, checklist_id, parent_id, CATEGORY, category, position)
        changed: list[NodeRef] = []
        cascade.rollup(self.session, parent_id, changed)
        self.session.flush()
        self.audit.record(
            action_type="add_category",
            target_kind=CATEGORY,
            target_id=category.id,
            checklist_id=checklist_id,
            payload={"old": None, "new": {"name": category.name, "parent_id": parent_id}},
            affected=changed,
        )
        return category

    def add_item(
        self,
        checklist_id: int,
        category_id: int,
        name: str,
        *,
        resources: list[dict] | None = None,
        tools: list[str] | None = None,
        data: str | None = None,
        instructions: str | None = None,
        position: int | None = None,
    ) -> ExpenseItem:
        self._get_checklist(checklist_id)
        category = self._get_category(category_id)
        if category.checklist_id != checklist_id:
            raise ValidationError("Category belongs to a different checklist")
        item = ExpenseItem(
            checklist_id=checklist_id,
            category_id=category_id,
            name=_require_name(name),
            done=False,
            data=data,
            instructions=instructions,
            position=0,  # placeholder; _place assigns the real position
        )
        self.session.add(item)
        self.session.flush()
        self._set_resources(item, resources or [])
        self._set_tools(item, tools or [])
        _place(self.session, checklist_id, category_id, EXPENSE_ITEM, item, position)
        changed: list[NodeRef] = []
        cascade.rollup(self.session, category_id, changed)
        self.session.flush()
        self.audit.record(
            action_type="add_item",
            target_kind=EXPENSE_ITEM,
            target_id=item.id,
            checklist_id=checklist_id,
            payload={"old": None, "new": {"name": item.name, "category_id": category_id}},
            affected=changed,
        )
        return item

    def edit_node(self, kind: NodeKind, node_id: int, fields: dict) -> Category | ExpenseItem:
        if kind == CATEGORY:
            return self._edit_category(node_id, fields)
        if kind == EXPENSE_ITEM:
            return self._edit_item(node_id, fields)
        raise ValidationError(f"Unknown node kind: {kind!r}")

    def remove_node(self, kind: NodeKind, node_id: int) -> None:
        if kind == CATEGORY:
            node = self._get_category(node_id)
            parent_id = node.parent_id
        elif kind == EXPENSE_ITEM:
            node = self._get_item(node_id)
            parent_id = node.category_id
        else:
            raise ValidationError(f"Unknown node kind: {kind!r}")
        checklist_id = node.checklist_id
        self.session.delete(node)
        self.session.flush()
        _repack(self.session, checklist_id, parent_id)
        changed: list[NodeRef] = []
        cascade.rollup(self.session, parent_id, changed)
        self.session.flush()
        self.audit.record(
            action_type="remove_node",
            target_kind=kind,
            target_id=node_id,
            checklist_id=checklist_id,
            payload={"old": {"parent_id": parent_id}, "new": None},
            affected=changed,
        )

    def move_node(
        self,
        kind: NodeKind,
        node_id: int,
        *,
        new_parent_id: int | None,
        position: int | None = None,
    ) -> list[NodeRef]:
        if kind == EXPENSE_ITEM:
            item = self._get_item(node_id)
            if new_parent_id is None:
                raise ValidationError("An expense item must live under a category")
            new_parent = self._get_category(new_parent_id)
            if new_parent.checklist_id != item.checklist_id:
                raise ValidationError("Cannot move across checklists")
            old_parent_id = item.category_id
            item.category_id = new_parent_id
            self.session.flush()
            _place(self.session, item.checklist_id, new_parent_id, EXPENSE_ITEM, item, position)
            checklist_id = item.checklist_id
        elif kind == CATEGORY:
            category = self._get_category(node_id)
            if new_parent_id is not None:
                new_parent = self._get_category(new_parent_id)
                if new_parent.checklist_id != category.checklist_id:
                    raise ValidationError("Cannot move across checklists")
                if new_parent_id in descendant_category_ids(self.session, category.id):
                    raise ValidationError("Cannot move a category into its own subtree")
            old_parent_id = category.parent_id
            category.parent_id = new_parent_id
            self.session.flush()
            _place(self.session, category.checklist_id, new_parent_id, CATEGORY, category, position)
            checklist_id = category.checklist_id
        else:
            raise ValidationError(f"Unknown node kind: {kind!r}")

        if old_parent_id != new_parent_id:
            _repack(self.session, checklist_id, old_parent_id)
        changed: list[NodeRef] = []
        cascade.rollup(self.session, old_parent_id, changed)
        cascade.rollup(self.session, new_parent_id, changed)
        self.session.flush()
        self.audit.record(
            action_type="move_node",
            target_kind=kind,
            target_id=node_id,
            checklist_id=checklist_id,
            payload={"old": {"parent_id": old_parent_id}, "new": {"parent_id": new_parent_id}},
            affected=changed,
        )
        return changed

    # -- done toggles -------------------------------------------------------

    def set_item_done(self, item_id: int, done: bool) -> list[NodeRef]:
        """The only externally allowed write (ADR-0003)."""
        item = self._get_item(item_id)
        old = item.done
        changed = cascade.set_node_done(self.session, EXPENSE_ITEM, item_id, done)
        self.session.flush()
        self.audit.record(
            action_type="set_item_done",
            target_kind=EXPENSE_ITEM,
            target_id=item_id,
            checklist_id=item.checklist_id,
            payload={"old": old, "new": done},
            affected=changed,
        )
        return changed

    def set_category_done(self, category_id: int, done: bool) -> list[NodeRef]:
        """Privileged (GUI-only) category toggle; cascades the whole subtree (ADR-0003)."""
        category = self._get_category(category_id)
        old = category.done
        changed = cascade.set_node_done(self.session, CATEGORY, category_id, done)
        self.session.flush()
        self.audit.record(
            action_type="set_category_done",
            target_kind=CATEGORY,
            target_id=category_id,
            checklist_id=category.checklist_id,
            payload={"old": old, "new": done},
            affected=changed,
        )
        return changed

    # -- internals ----------------------------------------------------------

    def _edit_category(self, node_id: int, fields: dict) -> Category:
        category = self._get_category(node_id)
        old = {"name": category.name}
        if "name" in fields:
            category.name = _require_name(fields["name"])
        self.session.flush()
        self.audit.record(
            action_type="edit_node",
            target_kind=CATEGORY,
            target_id=node_id,
            checklist_id=category.checklist_id,
            payload={"old": old, "new": {"name": category.name}},
        )
        return category

    def _edit_item(self, node_id: int, fields: dict) -> ExpenseItem:
        item = self._get_item(node_id)
        old = {"name": item.name, "data": item.data, "instructions": item.instructions}
        if "name" in fields:
            item.name = _require_name(fields["name"])
        if "data" in fields:
            item.data = fields["data"]
        if "instructions" in fields:
            item.instructions = fields["instructions"]
        if "resources" in fields:
            self._set_resources(item, fields["resources"] or [])
        if "tools" in fields:
            self._set_tools(item, fields["tools"] or [])
        self.session.flush()
        self.audit.record(
            action_type="edit_node",
            target_kind=EXPENSE_ITEM,
            target_id=node_id,
            checklist_id=item.checklist_id,
            payload={
                "old": old,
                "new": {"name": item.name, "data": item.data, "instructions": item.instructions},
            },
        )
        return item

    def _set_resources(self, item: ExpenseItem, resources: list[dict]) -> None:
        new_links: list[ItemResource] = []
        for position, resource in enumerate(resources):
            type_name = resource.get("type")
            if not type_name:
                raise ValidationError("Resource is missing its type")
            resource_type = self.session.scalar(
                select(ResourceType).where(ResourceType.name == type_name)
            )
            if resource_type is None:
                raise ValidationError(
                    f"Unknown resource type: {type_name!r}",
                    details={"kind": "resource_type", "name": type_name},
                )
            new_links.append(
                ItemResource(
                    resource_type_id=resource_type.id,
                    value=resource.get("value"),
                    position=position,
                )
            )
        item.resources = new_links

    def _set_tools(self, item: ExpenseItem, tools: list[str]) -> None:
        new_links: list[ItemTool] = []
        seen: set[int] = set()
        for position, tool_name in enumerate(tools):
            tool = self.session.scalar(select(Tool).where(Tool.name == tool_name))
            if tool is None:
                raise ValidationError(
                    f"Unknown tool: {tool_name!r}",
                    details={"kind": "tool", "name": tool_name},
                )
            if tool.id in seen:
                raise ValidationError(f"Duplicate tool: {tool_name!r}")
            seen.add(tool.id)
            new_links.append(ItemTool(tool_id=tool.id, position=position))
        item.tools = new_links

    def _get_checklist(self, checklist_id: int) -> Checklist:
        checklist = self.session.get(Checklist, checklist_id)
        if checklist is None:
            raise NotFoundError(f"Checklist {checklist_id} not found")
        return checklist

    def _get_category(self, category_id: int) -> Category:
        category = self.session.get(Category, category_id)
        if category is None:
            raise NotFoundError(f"Category {category_id} not found")
        return category

    def _get_item(self, item_id: int) -> ExpenseItem:
        item = self.session.get(ExpenseItem, item_id)
        if item is None:
            raise NotFoundError(f"Expense item {item_id} not found")
        return item


class VocabularyService:
    """Controlled-vocabulary maintenance (GLOSSARY: Controlled Vocabulary)."""

    def __init__(self, session: Session, audit: AuditService) -> None:
        self.session = session
        self.audit = audit

    def list(self, kind: str) -> list[dict]:
        model = self._model(kind)
        rows = self.session.scalars(select(model).order_by(model.name)).all()
        return [{"id": row.id, "name": row.name} for row in rows]

    def add(self, kind: str, name: str) -> dict:
        model = self._model(kind)
        cleaned = _require_name(name)
        if self.session.scalar(select(model).where(model.name == cleaned)) is not None:
            raise ValidationError(f"{kind} {cleaned!r} already exists")
        row = model(name=cleaned)
        self.session.add(row)
        self.session.flush()
        self.audit.record(
            action_type="add_vocabulary",
            target_kind="vocabulary",
            target_id=row.id,
            payload={"old": None, "new": {"kind": kind, "name": cleaned}},
        )
        return {"id": row.id, "name": row.name}

    def rename(self, kind: str, vocab_id: int, name: str) -> dict:
        model = self._model(kind)
        row = self.session.get(model, vocab_id)
        if row is None:
            raise NotFoundError(f"{kind} {vocab_id} not found")
        cleaned = _require_name(name)
        clash = self.session.scalar(
            select(model).where(model.name == cleaned, model.id != vocab_id)
        )
        if clash is not None:
            raise ValidationError(f"{kind} {cleaned!r} already exists")
        old_name = row.name
        row.name = cleaned
        self.session.flush()
        self.audit.record(
            action_type="rename_vocabulary",
            target_kind="vocabulary",
            target_id=vocab_id,
            payload={"old": {"name": old_name}, "new": {"name": cleaned}},
        )
        return {"id": row.id, "name": row.name}

    def remove(self, kind: str, vocab_id: int) -> None:
        model = self._model(kind)
        row = self.session.get(model, vocab_id)
        if row is None:
            raise NotFoundError(f"{kind} {vocab_id} not found")
        used_by = self._usage_item_ids(kind, vocab_id)
        if used_by:
            raise VocabularyInUseError(
                f"{kind} {row.name!r} is in use by {len(used_by)} item(s)",
                details={"kind": kind, "id": vocab_id, "item_ids": used_by},
            )
        name = row.name
        self.session.delete(row)
        self.session.flush()
        self.audit.record(
            action_type="remove_vocabulary",
            target_kind="vocabulary",
            target_id=vocab_id,
            payload={"old": {"kind": kind, "name": name}, "new": None},
        )

    def _usage_item_ids(self, kind: str, vocab_id: int) -> list[int]:
        if kind == "resource_type":
            stmt = select(ItemResource.item_id).where(ItemResource.resource_type_id == vocab_id)
        else:
            stmt = select(ItemTool.item_id).where(ItemTool.tool_id == vocab_id)
        return sorted(set(self.session.scalars(stmt).all()))

    @staticmethod
    def _model(kind: str) -> type[ResourceType] | type[Tool]:
        try:
            return _VOCAB_MODELS[kind]
        except KeyError:
            raise ValidationError(f"Unknown vocabulary kind: {kind!r}") from None
