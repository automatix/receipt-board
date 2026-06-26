"""Pydantic request schemas for the REST API (TECH_SPEC §9 E2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SetDoneRequest(BaseModel):
    done: bool


class ResourceIn(BaseModel):
    type: str
    value: str | None = None


class CreateChecklistRequest(BaseModel):
    mode: Literal["blank", "import", "clone"]
    name: str
    text: str | None = None  # for mode=import
    source_id: int | None = None  # for mode=clone


class AddCategoryRequest(BaseModel):
    name: str
    parent_id: int | None = None
    position: int | None = None


class AddItemRequest(BaseModel):
    category_id: int
    name: str
    resources: list[ResourceIn] = []
    tools: list[str] = []
    data: str | None = None
    instructions: str | None = None
    position: int | None = None


class EditCategoryRequest(BaseModel):
    name: str | None = None


class EditItemRequest(BaseModel):
    name: str | None = None
    data: str | None = None
    instructions: str | None = None
    resources: list[ResourceIn] | None = None
    tools: list[str] | None = None


class MoveRequest(BaseModel):
    new_parent_id: int | None = None
    position: int | None = None


class VocabCreateRequest(BaseModel):
    name: str
    value_optional: bool = False  # resource_type only
    value_pattern: str | None = None  # resource_type only


class VocabUpdateRequest(BaseModel):
    name: str | None = None
    value_optional: bool | None = None
    value_pattern: str | None = None


class DuplicateVocabRequest(BaseModel):
    name: str


class ValidateImportRequest(BaseModel):
    text: str
