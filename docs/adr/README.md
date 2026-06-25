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

> Terms used in ADRs are defined in [`../GLOSSARY.md`](../GLOSSARY.md).
