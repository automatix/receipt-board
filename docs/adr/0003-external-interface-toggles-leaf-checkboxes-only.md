# The external interface may only toggle leaf checkboxes

The CLI / REST / AI surface is **read-only except for toggling `done` on Leaves**
(Expense Items), in both directions. A Category's `done` is **never set directly from
outside** — it changes externally only as a side effect of the roll-up cascade when its
leaves change.

This keeps the destructive operation of unchecking a Category (which clears its whole
subtree, per ADR-0002) inside the **GUI**, where it can be guarded by confirmation/undo,
and matches the deliberately minimal external write surface: no add / edit / remove /
import / clone from outside — those are GUI-only.

Considered and rejected: allowing any node's checkbox to be set externally — a
category-uncheck via CLI/AI would silently wipe a subtree with no guard.
