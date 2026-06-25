# Task-Breakdown (`v1`)

Abgeleitet aus [`TECH_SPEC.md`](./TECH_SPEC.md) §13. Jede Aufgabe ist ein **GitHub Issue**
(Milestone `v1`, Repo `automatix/receipt-board`). Implementierung erfolgt in einer separaten
Session im Branch-/Ticket-Workflow. Es gibt bewusst **kein** GitHub-Projekt/Board — nur
Issues.

| # | Aufgabe | Area | Abhängig von | Issue |
| - | ------- | ---- | ------------ | ----- |
| 1 | Projekt-Bootstrap & Tooling (`uv`, `ruff`, `pytest`, Layout) | `setup` | — | [#1](https://github.com/automatix/receipt-board/issues/1) |
| 2 | CI-Pipeline (GitHub Actions, Coverage-Gate ≥ `90 %`) | `ci` | #1 | [#2](https://github.com/automatix/receipt-board/issues/2) |
| 3 | Persistenzschicht & Migrations (`SQLAlchemy`/`Alembic`) | `persistence` | #1 | [#3](https://github.com/automatix/receipt-board/issues/3) |
| 4 | Core-Services, Cascade, Fehler-Typen & Audit | `core` | #3 | [#4](https://github.com/automatix/receipt-board/issues/4) |
| 5 | Markdown-Importer (strikt, atomar, typisiert) | `importer` | #4 | [#5](https://github.com/automatix/receipt-board/issues/5) |
| 6 | REST-API (`FastAPI`, public/privileged, Token-Gate) | `api` | #4, #5 | [#6](https://github.com/automatix/receipt-board/issues/6) |
| 7 | CLI (HTTP-Client) | `cli` | #6 | [#7](https://github.com/automatix/receipt-board/issues/7) |
| 8 | GUI-Build-Setup (`TypeScript`/`esbuild`/`pywebview`) | `gui` | #6 | [#8](https://github.com/automatix/receipt-board/issues/8) |
| 9 | GUI-Features (Baum, Inline-Edit, DnD, Vokabular, Suche) | `gui` | #8 | [#9](https://github.com/automatix/receipt-board/issues/9) |
| 10 | Packaging (`PyInstaller`) & First-Run/Config | `packaging` | #7, #9 | [#10](https://github.com/automatix/receipt-board/issues/10) |
| 11 | Doku & Run-Anleitung; finaler Docs-Abgleich | `docs` | #10 | [#11](https://github.com/automatix/receipt-board/issues/11) |

## Empfohlene Reihenfolge

`#1` → (`#2` ∥ `#3`) → `#4` → `#5` → `#6` → (`#7` ∥ `#8` → `#9`) → `#10` → `#11`.

`#2` (CI) kann parallel zur Backend-Arbeit laufen. `#7` (CLI) und der GUI-Strang
(`#8`→`#9`) sind nach `#6` parallelisierbar.
