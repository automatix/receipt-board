"""SQLAlchemy ORM models for the Receipt Board schema.

Mirrors ``docs/TECH_SPEC.md`` §3. Primary keys are per-table integers (ADR-0010);
``done`` is a boolean stored as ``INTEGER`` 0/1. Parent/Checklist deletes cascade;
vocabulary references are ``RESTRICT`` so an in-use vocabulary entry cannot be deleted.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative base; ``Base.metadata`` is the schema used by Alembic."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )


class Checklist(TimestampMixin, Base):
    __tablename__ = "checklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    categories: Mapped[list[Category]] = relationship(
        back_populates="checklist", cascade="all, delete-orphan", passive_deletes=True
    )
    items: Mapped[list[ExpenseItem]] = relationship(
        back_populates="checklist", cascade="all, delete-orphan", passive_deletes=True
    )


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checklist_id: Mapped[int] = mapped_column(
        ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    checklist: Mapped[Checklist] = relationship(back_populates="categories")
    parent: Mapped[Category | None] = relationship(remote_side="Category.id")


class ExpenseItem(TimestampMixin, Base):
    __tablename__ = "expense_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checklist_id: Mapped[int] = mapped_column(
        ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    checklist: Mapped[Checklist] = relationship(back_populates="items")
    resources: Mapped[list[ItemResource]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ItemResource.position",
    )
    tools: Mapped[list[ItemTool]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ItemTool.position",
    )


class ResourceType(Base):
    __tablename__ = "resource_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # ``name`` is the type key (e.g. "URL", "Email").
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    # Whether a resource of this type may omit its value (e.g. a bare "Email").
    value_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Regex a provided value must match (case-insensitive); also used to type a bare token.
    value_pattern: Mapped[str | None] = mapped_column(String, nullable=True)


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class ItemResource(Base):
    __tablename__ = "item_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("expense_items.id", ondelete="CASCADE"), nullable=False
    )
    resource_type_id: Mapped[int] = mapped_column(
        ForeignKey("resource_types.id", ondelete="RESTRICT"), nullable=False
    )
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    item: Mapped[ExpenseItem] = relationship(back_populates="resources")
    resource_type: Mapped[ResourceType] = relationship()


class ItemTool(Base):
    __tablename__ = "item_tools"
    __table_args__ = (UniqueConstraint("item_id", "tool_id", name="uq_item_tools_item_tool"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("expense_items.id", ondelete="CASCADE"), nullable=False
    )
    tool_id: Mapped[int] = mapped_column(
        ForeignKey("tools.id", ondelete="RESTRICT"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    item: Mapped[ExpenseItem] = relationship(back_populates="tools")
    tool: Mapped[Tool] = relationship()


class AuditEntry(Base):
    """One row per caller action (ADR-0004); see ``docs/TECH_SPEC.md`` §8."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[str] = mapped_column(String, nullable=False)  # ISO-8601
    origin: Mapped[str] = mapped_column(String, nullable=False)  # GUI | CLI | REST
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    target_kind: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checklist_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"old":..,"new":..}
    affected_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    app_version: Mapped[str | None] = mapped_column(String, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)
