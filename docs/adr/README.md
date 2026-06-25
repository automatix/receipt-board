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

> Terms used in ADRs are defined in [`../GLOSSARY.md`](../GLOSSARY.md).
