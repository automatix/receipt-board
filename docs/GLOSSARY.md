# Glossary — Ubiquitous Language

The shared vocabulary of the Receipt Board domain. Terms are refined **as we go** during
domain-modeling sessions. `pinned` = fixed by a resolved decision; `provisional` = not yet
sharpened. Definitions say what a term **is**, not what it does.

| Term | Definition | `_Avoid_` | Status |
| ---- | ---------- | --------- | ------ |
| **Expense Item** | A checklist position representing **one expense source or cost position** (e.g. `Amazon`, `1&1`, `Betreuungskosten`) for which receipts must be gathered for the period. The actionable, checkable element. | `Item`, `Entry`, `Row`, `Leaf`, `Position`, `Source`, `Receipt` | `pinned` |
| **Leaf** | Purely *structural*: a `Node` with no children. In this domain a `Leaf` represents an **Expense Item**. | — | `provisional` |
| **Category** | A non-leaf `Node` used purely for grouping; carries only a `name`. | — | `provisional` |
| **Node** | A single element in a list's tree — either a `Category` or a `Leaf`. | — | `provisional` |
| **List** | A self-contained expense checklist, typically scoped to one accounting period. Holds a tree of nodes. | — | `provisional` |
| **Period** | The accounting timeframe a list represents (year or month). | — | `provisional` |
| **`done`** | State on an Expense Item: the receipt(s) for this position have been gathered. | — | `provisional` |
| **`resources`** | Where the receipt is found (e.g. a URL, `Email`). Attribute of an Expense Item. | — | `provisional` |
| **`tools`** | Which instrument(s) to use to obtain the receipt (e.g. `Browser`, `Thunderbird`). | — | `provisional` |
| **`data`** | Auxiliary data needed to obtain the receipt (e.g. a login identifier). | — | `provisional` |
| **`instructions`** | A note on how to obtain the receipt. | — | `provisional` |
| **Import** | Seeding a new list from the Markdown checklist format. | — | `provisional` |
| **Clone** | Creating a new list by duplicating an existing list's structure with all `done` reset. | — | `provisional` |
| **Audit Log** | Append-only record of every write action. | — | `provisional` |

> **Receipt / Beleg** is **deliberately not a domain entity in `v1`** — see
> [`adr/0001-receipt-not-modeled-in-v1.md`](./adr/0001-receipt-not-modeled-in-v1.md).
