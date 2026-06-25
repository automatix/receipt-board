"""Node references and kinds.

Ids are per-table integers (ADR-0010), so a reference always carries its ``kind``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CATEGORY = "category"
EXPENSE_ITEM = "expense_item"

NodeKind = Literal["category", "expense_item"]


@dataclass(frozen=True)
class NodeRef:
    kind: NodeKind
    id: int

    def as_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "id": self.id}
