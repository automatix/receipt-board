# Glossary — Ubiquitous Language

The shared vocabulary of the Receipt Board domain. Terms are refined **as we go** during
domain-modeling sessions. Entries marked _(provisional)_ are not yet pinned by an ADR.

| Term | Definition | Status |
| ---- | ---------- | ------ |
| **List** | A self-contained expense checklist, typically for one accounting period (e.g. year `2024`). Holds a tree of nodes. | _(provisional)_ |
| **Node** | A single element in a list's tree — either a `Category` or a `Leaf`. | _(provisional)_ |
| **Category** | A non-leaf node used purely for grouping; has children; carries only a `name`; not directly actionable. | _(provisional)_ |
| **Leaf** | A node with no children — the actual actionable entry (a receipt/expense to collect). Carries the action fields. | _(provisional)_ |
| **`done`** | Boolean on a `Leaf`: whether the receipt has been collected/handled. | _(provisional)_ |
| **`resources`** | Where the receipt is found (e.g. a URL, `Email`). | _(provisional)_ |
| **`tools`** | Which instrument(s) to use (e.g. `Browser`, `Thunderbird`); default `"Browser"`. | _(provisional)_ |
| **`data`** | Auxiliary data needed (e.g. a login identifier). | _(provisional)_ |
| **`instructions`** | Step-by-step note on how to obtain the receipt. | _(provisional)_ |
| **Import** | Seeding a new list from the Markdown checklist format (strict bracket-type parsing). GUI-only. | _(provisional)_ |
| **Clone** | Creating a new list by duplicating an existing list's structure with all `done` reset to `false`. GUI-only. | _(provisional)_ |
| **Audit Log** | Append-only record of every write action (origin, target, old → new value, timestamp). | _(provisional)_ |
| **Period** | The accounting timeframe a list represents (year or month). | _(provisional)_ |
