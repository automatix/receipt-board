# Glossary — Ubiquitous Language

The shared vocabulary of the Receipt Board domain. Terms are refined **as we go** during
domain-modeling sessions. `pinned` = fixed by a resolved decision; `provisional` = not yet
sharpened. Definitions say what a term **is**, not what it does.

| Term | Definition | `_Avoid_` | Status |
| ---- | ---------- | --------- | ------ |
| **Expense Item** | A checklist position representing **one expense source or cost position** (e.g. `Amazon`, `1&1`, `Betreuungskosten`) for which receipts must be gathered for the period. The actionable, checkable element. Carries the action fields `resources`, `tools`, `data`, `instructions` — these exist **only** on Expense Items, never on Categories. Its node type is explicit; an Expense Item **never has children**. | `Item`, `Entry`, `Row`, `Leaf`, `Position`, `Source`, `Receipt` | `pinned` |
| **Category** | A `Node` whose explicit type is *grouping*; carries a `name` and its own `done` checkbox (kept consistent with its subtree via cascade). May be empty, has no action fields, and is never directly editable as an item. | — | `pinned` |
| **Node** | A single element in a Checklist's tree — either a `Category` or an `Expense Item`, fixed by an explicit **node type**. Every Node carries a **globally unique**, stable `id` (the canonical reference, used by the API/CLI), a `name` (not required unique — sibling names may repeat), a `position` (its meaningful order among siblings), and a `done` checkbox. | — | `pinned` |
| **Node Type** | The explicit discriminator on every Node: `Category` or `Expense Item`. Set at creation and stored; only the import infers it from nesting (childless rows → Expense Item, their ancestors → Category). Thereafter it changes only via a deliberate GUI action. | — | `pinned` |
| **Leaf** | Structural description only (a `Node` with no children). Now ambiguous — an empty `Category` is also childless — so prefer the explicit Node Type (`Category` / `Expense Item`). | `Expense Item` (when an actionable node is meant) | `provisional` |
| **Checklist** | A self-contained, hierarchical expense checklist, typically scoped to one accounting period (e.g. `2024`); the top-level container holding a tree of nodes. The app (Receipt Board) manages many Checklists. Created (GUI-only) in one of three ways: **blank**, by **import**, or by **cloning** an existing Checklist. Deletion (like node removal) is GUI-only. | `List`, `Board` | `pinned` |
| **Period** | The accounting timeframe a Checklist informally represents (year or month). In `v1` it is **not** a structured attribute — it is conveyed only via the Checklist's free-text `name`. | — | `pinned` |
| **`done`** | A boolean checkbox present on **every Node**. The application is agnostic to its real-world meaning — it only stores and cascades checkmarks (the "receipt gathered" semantics live outside the tool). | — | `pinned` |
| **`resources`** | The typed Resources of an Expense Item (zero or more) telling where its receipt(s) are found. | — | `pinned` |
| **Resource** | A typed locator for a receipt: a `type` (a Resource Type) plus an **optional** value — e.g. the concrete URL, or the concrete email mailbox to look in. A value-less `Email` resource means "check your email" (mailbox unspecified). | — | `pinned` |
| **Resource Type** | The kind of a Resource, drawn from an extensible **controlled vocabulary** managed in the app via the GUI (currently `URL`, `Email`). | — | `pinned` |
| **`tools`** | The Tools of an Expense Item (zero or more) used to obtain its receipt(s). May be empty; there is **no implicit default** — `Browser` is an ordinary value like any other. | — | `pinned` |
| **Tool** | An instrument used to obtain a receipt, drawn from an extensible **controlled vocabulary** managed in the app via the GUI (currently `Browser`, `Thunderbird`). | — | `pinned` |
| **Controlled Vocabulary** | An **application-wide** (shared across all Checklists), user-extensible set of allowed values (e.g. the Tools, the Resource Types) managed via the GUI. Each entry has a stable `id`; items reference it by `id`, so renaming propagates everywhere. An entry can be removed only when **no item uses it** (otherwise removal is blocked with the list of affected items). Import validates typed tokens against these and aborts on unknown values (see ADR-0005). | — | `pinned` |
| **`data`** | Free-text auxiliary data needed to obtain the receipt (e.g. a login identifier). Attribute of an Expense Item. | — | `pinned` |
| **`instructions`** | Free-text note on how to obtain the receipt. Attribute of an Expense Item. | — | `pinned` |
| **Import** | Seeding a new Checklist from the Markdown checklist format. | — | `provisional` |
| **Clone** | Creating a new Checklist by **deep-copying** an existing one's structure and action fields (with fresh ids) and resetting all `done` to false. GUI-only. | — | `pinned` |
| **Cascade** | The rule that keeps `done` consistent across the tree: setting a Node propagates to its whole subtree, and a child change re-rolls-up its ancestors — maintaining `category.done ⇔ entire subtree done`. | — | `pinned` |
| **Audit Log** | Append-only record of every write action — one entry per caller action: timestamp, origin (`GUI`/`CLI`/`REST`), action type, target `id`, old → new value, and the ids of all nodes affected by the cascade. | — | `pinned` |

> **Receipt / Beleg** is **deliberately not a domain entity in `v1`** — see
> [`adr/0001-receipt-not-modeled-in-v1.md`](./adr/0001-receipt-not-modeled-in-v1.md).
