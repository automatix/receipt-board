# Integer primary keys instead of UUIDs

Supersedes the UUID note in ADR-0007. Primary keys are **per-table auto-increment
integers** (`checklists.id`, `categories.id`, `expense_items.id`, and the vocabulary
tables), not UUIDs.

Consequence: node ids are unique **within their table** but **not** across the two node
tables (`categories` vs `expense_items`). Every reference therefore carries a `kind`
(`category` | `expense_item`) alongside the `id`; the external interface addresses Expense
Items by their item id, and the Audit Log records `target_kind` + `target_id`.

Rationale: simpler, smaller, human-readable ids for a single-user local SQLite app;
cross-table global uniqueness is unnecessary because every reference already knows its
kind.
