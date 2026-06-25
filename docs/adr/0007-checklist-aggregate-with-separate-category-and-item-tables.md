# Checklist aggregate with separate Category and Expense Item tables

The **Checklist** is the aggregate root and invariant boundary (node-type rules, the
cascade invariant, sibling `position`, parent-child confined to one Checklist).
Persistence is a flat **adjacency list**, and writes are **targeted, transactional
mutations**: a change touches only the affected rows, their cascade-affected ancestors,
and one audit row — all in a single DB transaction (no load/save of the whole tree).

Categories and Expense Items are stored in **two separate tables**: `categories` holds the
category tree (self-referencing `parent_id`), and `expense_items` holds the leaves, each
referencing its parent category (`category_id`, `NOT NULL`). A Category may contain both
sub-categories and Expense Items, interleaved by `position` (which therefore spans both
tables); the cascade likewise spans both tables.

## Consequences

- Every Expense Item lives **under a Category** — items cannot be direct children of the
  Checklist root. A brand-new blank Checklist needs a Category before its first item.
- The unified **Node** concept is realised physically as two tables; the external interface
  addresses Expense Items by their id. (Ids are **per-table integers**, not UUIDs — see
  ADR-0010, which supersedes the original UUID note here.)
- The multi-valued typed fields (`resources`, `tools`) live in their own child tables
  referencing the Expense Item; `data`/`instructions` are columns on `expense_items`.
