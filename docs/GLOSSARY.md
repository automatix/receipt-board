# Glossary — Ubiquitous Language

The shared vocabulary of the Receipt Board domain. Terms are refined **as we go** during
domain-modeling sessions. `pinned` = fixed by a resolved decision; `provisional` = not yet
sharpened. Definitions say what a term **is**, not what it does.

| Term | Definition | `_Avoid_` | Status |
| ---- | ---------- | --------- | ------ |
| **Expense Item** | A checklist position representing **one expense source or cost position** (e.g. `Amazon`, `1&1`, `Betreuungskosten`) for which receipts must be gathered for the period. The actionable, checkable element. | `Item`, `Entry`, `Row`, `Leaf`, `Position`, `Source`, `Receipt` | `pinned` |
| **Leaf** | Purely *structural*: a `Node` with no children. In this domain a `Leaf` represents an **Expense Item**. | — | `provisional` |
| **Category** | A non-leaf `Node` used for grouping; carries a `name` and its own `done` checkbox (kept consistent with its subtree via cascade). | — | `provisional` |
| **Node** | A single element in a Checklist's tree — either a `Category` or a `Leaf`. Every Node carries a stable `id` (the canonical reference, used by the API/CLI), a `name` (not required unique — sibling names may repeat), and a `done` checkbox. | — | `provisional` |
| **Checklist** | A self-contained, hierarchical expense checklist, typically scoped to one accounting period (e.g. `2024`); the top-level container holding a tree of nodes. The app (Receipt Board) manages many Checklists. | `List`, `Board` | `pinned` |
| **Period** | The accounting timeframe a list represents (year or month). | — | `provisional` |
| **`done`** | A boolean checkbox present on **every Node**. The application is agnostic to its real-world meaning — it only stores and cascades checkmarks (the "receipt gathered" semantics live outside the tool). | — | `pinned` |
| **`resources`** | Where the receipt is found (e.g. a URL, `Email`). Attribute of an Expense Item. | — | `provisional` |
| **`tools`** | Which instrument(s) to use to obtain the receipt (e.g. `Browser`, `Thunderbird`). | — | `provisional` |
| **`data`** | Auxiliary data needed to obtain the receipt (e.g. a login identifier). | — | `provisional` |
| **`instructions`** | A note on how to obtain the receipt. | — | `provisional` |
| **Import** | Seeding a new Checklist from the Markdown checklist format. | — | `provisional` |
| **Clone** | Creating a new Checklist by duplicating an existing one's structure with all `done` reset. | — | `provisional` |
| **Cascade** | The rule that keeps `done` consistent across the tree: setting a Node propagates to its whole subtree, and a child change re-rolls-up its ancestors — maintaining `category.done ⇔ entire subtree done`. | — | `pinned` |
| **Audit Log** | Append-only record of every write action. | — | `provisional` |

> **Receipt / Beleg** is **deliberately not a domain entity in `v1`** — see
> [`adr/0001-receipt-not-modeled-in-v1.md`](./adr/0001-receipt-not-modeled-in-v1.md).
