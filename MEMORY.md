# MEMORY

## Initialization — `2026-06-24`

- **Request** — User ran `/init` on the empty `Receipt Board` directory. After clarification, chose to initialize an empty repository only (no app scaffolding), with the project intended as a **desktop application**.
- **Done** — Ran the standard init sequence, one commit per step:
  1. `git init` (default branch `main`)
  2. Added `.gitignore` with common exclusions
  3. Added placeholder `README.md`
  4. Added placeholder `CLAUDE.md` (no invented architecture — repo has no code yet)
  5. Added this `MEMORY.md`
- **Result** — Repository initialized with `4` commits of scaffolding plus this record. No tech stack chosen yet; `CLAUDE.md` commands/architecture sections are placeholders awaiting the first real code.

## GitHub remote — `2026-06-24`

- **Request** — Create a GitHub repo `receipt-board` in the personal account namespace; no GitHub Project/board.
- **Done** — Created `private` repo `automatix/receipt-board` via `gh`, added it as `origin` (SSH), pushed `main`.
- **Result** — All init commits are on GitHub at `https://github.com/automatix/receipt-board`. No GitHub Project created.

## Local scratch directory — `2026-06-24`

- **Request** — Create a `local` directory, add it to `.gitignore`, and record it as a global instruction.
- **Done** — Created `local/` (no placeholder file inside), added `local/` to `.gitignore`, committed and pushed. Added a "Local scratch directory" subsection to the global `CLAUDE.md`.
- **Result** — `local/` is fully ignored (verified via `git check-ignore`); the convention now applies to all projects globally.
