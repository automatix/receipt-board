"""Public and privileged routers (TECH_SPEC §9).

Public surface = reads + the single ``POST /items/{id}/done`` write (ADR-0003). Everything
else is privileged and guarded by the session-token dependency (ADR-0009).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from receipt_board.api.deps import (
    get_checklist_service,
    get_session,
    get_vocab_service,
    require_token,
)
from receipt_board.api.errors import ApiError
from receipt_board.api.schemas import (
    AddCategoryRequest,
    AddItemRequest,
    CreateChecklistRequest,
    EditCategoryRequest,
    EditItemRequest,
    MoveRequest,
    SetDoneRequest,
    VocabNameRequest,
)
from receipt_board.core import queries
from receipt_board.core.refs import CATEGORY, EXPENSE_ITEM
from receipt_board.core.services import ChecklistService, VocabularyService

public_router = APIRouter(tags=["public"])
privileged_router = APIRouter(tags=["privileged"], dependencies=[Depends(require_token)])


def _affected(refs) -> dict:
    return {"affected_ids": [ref.as_dict() for ref in refs]}


# -- public -------------------------------------------------------------------


@public_router.get("/checklists")
def list_checklists(session=Depends(get_session)) -> list[dict]:
    return queries.list_checklists(session)


@public_router.get("/checklists/{checklist_id}")
def export_checklist(checklist_id: int, session=Depends(get_session)) -> dict:
    return queries.export_checklist(session, checklist_id)


@public_router.get("/search")
def search(q: str, checklist_id: int | None = None, session=Depends(get_session)) -> list[dict]:
    return queries.search(session, q, checklist_id=checklist_id)


@public_router.post("/items/{item_id}/done")
def set_item_done(
    item_id: int, body: SetDoneRequest, svc: ChecklistService = Depends(get_checklist_service)
) -> dict:
    return _affected(svc.set_item_done(item_id, body.done))


# -- privileged: checklists ---------------------------------------------------


@privileged_router.post("/checklists", status_code=201)
def create_checklist(
    body: CreateChecklistRequest, svc: ChecklistService = Depends(get_checklist_service)
) -> dict:
    if body.mode == "blank":
        checklist = svc.create_blank(body.name)
    elif body.mode == "import":
        if body.text is None:
            raise ApiError(400, "validation_error", "'text' is required for an import")
        checklist = svc.import_markdown(body.name, body.text)
    else:  # clone
        if body.source_id is None:
            raise ApiError(400, "validation_error", "'source_id' is required for a clone")
        checklist = svc.clone(body.source_id, body.name)
    return {"id": checklist.id, "name": checklist.name}


@privileged_router.delete("/checklists/{checklist_id}", status_code=204)
def delete_checklist(
    checklist_id: int, svc: ChecklistService = Depends(get_checklist_service)
) -> Response:
    svc.delete(checklist_id)
    return Response(status_code=204)


# -- privileged: categories ---------------------------------------------------


@privileged_router.post("/checklists/{checklist_id}/categories", status_code=201)
def add_category(
    checklist_id: int,
    body: AddCategoryRequest,
    svc: ChecklistService = Depends(get_checklist_service),
) -> dict:
    category = svc.add_category(
        checklist_id, body.name, parent_id=body.parent_id, position=body.position
    )
    return {"id": category.id, "kind": CATEGORY}


@privileged_router.patch("/categories/{category_id}")
def edit_category(
    category_id: int,
    body: EditCategoryRequest,
    svc: ChecklistService = Depends(get_checklist_service),
) -> dict:
    node = svc.edit_node(CATEGORY, category_id, body.model_dump(exclude_unset=True))
    return {"id": node.id, "kind": CATEGORY}


@privileged_router.delete("/categories/{category_id}", status_code=204)
def remove_category(
    category_id: int, svc: ChecklistService = Depends(get_checklist_service)
) -> Response:
    svc.remove_node(CATEGORY, category_id)
    return Response(status_code=204)


@privileged_router.post("/categories/{category_id}/done")
def set_category_done(
    category_id: int,
    body: SetDoneRequest,
    svc: ChecklistService = Depends(get_checklist_service),
) -> dict:
    return _affected(svc.set_category_done(category_id, body.done))


# -- privileged: items --------------------------------------------------------


@privileged_router.post("/checklists/{checklist_id}/items", status_code=201)
def add_item(
    checklist_id: int,
    body: AddItemRequest,
    svc: ChecklistService = Depends(get_checklist_service),
) -> dict:
    item = svc.add_item(
        checklist_id,
        body.category_id,
        body.name,
        resources=[r.model_dump() for r in body.resources],
        tools=body.tools,
        data=body.data,
        instructions=body.instructions,
        position=body.position,
    )
    return {"id": item.id, "kind": EXPENSE_ITEM}


@privileged_router.patch("/items/{item_id}")
def edit_item(
    item_id: int, body: EditItemRequest, svc: ChecklistService = Depends(get_checklist_service)
) -> dict:
    fields = body.model_dump(exclude_unset=True)
    node = svc.edit_node(EXPENSE_ITEM, item_id, fields)
    return {"id": node.id, "kind": EXPENSE_ITEM}


@privileged_router.delete("/items/{item_id}", status_code=204)
def remove_item(item_id: int, svc: ChecklistService = Depends(get_checklist_service)) -> Response:
    svc.remove_node(EXPENSE_ITEM, item_id)
    return Response(status_code=204)


# -- privileged: move ---------------------------------------------------------


@privileged_router.post("/nodes/{kind}/{node_id}/move")
def move_node(
    kind: str,
    node_id: int,
    body: MoveRequest,
    svc: ChecklistService = Depends(get_checklist_service),
) -> dict:
    return _affected(
        svc.move_node(kind, node_id, new_parent_id=body.new_parent_id, position=body.position)
    )


# -- privileged: vocabulary ---------------------------------------------------


@privileged_router.get("/vocab/{kind}")
def list_vocab(kind: str, vs: VocabularyService = Depends(get_vocab_service)) -> list[dict]:
    return vs.list(kind)


@privileged_router.post("/vocab/{kind}", status_code=201)
def add_vocab(
    kind: str, body: VocabNameRequest, vs: VocabularyService = Depends(get_vocab_service)
) -> dict:
    return vs.add(kind, body.name)


@privileged_router.patch("/vocab/{kind}/{vocab_id}")
def rename_vocab(
    kind: str,
    vocab_id: int,
    body: VocabNameRequest,
    vs: VocabularyService = Depends(get_vocab_service),
) -> dict:
    return vs.rename(kind, vocab_id, body.name)


@privileged_router.delete("/vocab/{kind}/{vocab_id}", status_code=204)
def remove_vocab(
    kind: str, vocab_id: int, vs: VocabularyService = Depends(get_vocab_service)
) -> Response:
    vs.remove(kind, vocab_id)
    return Response(status_code=204)
