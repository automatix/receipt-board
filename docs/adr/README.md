# Architecture Decision Records (ADRs)

This directory captures the **domain-modeling and architecture decisions** for Receipt
Board, one decision per file. ADRs are produced **as we go** during grilling/design
sessions.

## Format

Each ADR uses a lightweight [MADR](https://adr.github.io/madr/)-style template:

- **Title** — `NNNN-short-slug.md`
- **Status** — `Proposed` | `Accepted` | `Superseded by NNNN` | `Rejected`
- **Context** — the question/forces at play
- **Decision** — what we chose
- **Consequences** — resulting trade-offs, follow-ups

## Index

| ADR | Title | Status |
| --- | ----- | ------ |
| [0001](./0001-receipt-not-modeled-in-v1.md) | Receipt is not a domain entity in v1 | Accepted |
| [0002](./0002-done-stored-on-every-node-with-symmetric-cascade.md) | `done` is stored on every node, kept consistent by a symmetric cascade | Accepted |
| [0003](./0003-external-interface-toggles-leaf-checkboxes-only.md) | The external interface may only toggle leaf checkboxes | Accepted |
| [0004](./0004-audit-logs-one-entry-per-action-with-affected-ids.md) | Audit logs one entry per action, with cascade-affected node ids | Accepted |
| [0005](./0005-import-is-atomic-and-validates-controlled-vocabularies.md) | Import is atomic and validates against the controlled vocabularies | Accepted |
| [0006](./0006-node-type-is-explicit-inferred-only-at-import.md) | Node type (Category vs Expense Item) is explicit, inferred only at import | Accepted |
| [0007](./0007-checklist-aggregate-with-separate-category-and-item-tables.md) | Checklist aggregate with separate Category and Expense Item tables | Accepted |
| [0008](./0008-concurrency-one-transaction-per-action-last-write-wins.md) | Concurrency: one SQLite transaction per action, last-write-wins | Accepted |
| [0009](./0009-gui-only-operations-protected-by-startup-session-token.md) | GUI-only operations are protected by a startup session token | Accepted |
| [0010](./0010-integer-primary-keys-instead-of-uuids.md) | Integer primary keys instead of UUIDs (supersedes the UUID note in 0007) | Accepted |
| [0011](./0011-cli-communicates-over-local-http.md) | The CLI communicates with the app over local HTTP | Accepted |
| [0012](./0012-gui-live-updates-via-sse.md) | GUI live updates via Server-Sent Events (no manual refresh) | Accepted |

> Terms used in ADRs are defined in [`../GLOSSARY.md`](../GLOSSARY.md).
