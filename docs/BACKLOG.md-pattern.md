# The "Deferred Ideas Backlog" Pattern

A generic, project-independent description of a lightweight documentation pattern: a
single Markdown file that records things a project has **deliberately postponed**,
distinct from its decision journal, its ticket system, and its git history.

This document is reusable as-is in any project. It contains no reference to any specific
project's name, tech stack, or concrete backlog content.

## Purpose

Every project accumulates ideas, improvements, and scope cuts that come up mid-work but
aren't worth acting on right now. Without a dedicated place to catch them, they go one of
two ways: they get silently dropped (forgotten the moment the conversation or session
ends), or they get promoted straight into the ticket system, cluttering it with
speculative, unprioritized, not-yet-actionable items.

The backlog file solves this by giving deferred ideas a durable, low-ceremony home. It is
deliberately **not** any of the following:

- **The requirements/decisions journal** (e.g. a running `MEMORY.md`, changelog, or a
  session log). That journal is a chronological record of what was *decided and done* —
  requests, actions taken, outcomes. The backlog instead records what was *consciously
  not done* — a forward-looking list of open ideas, not a history of closed ones. An
  entry can live in the backlog indefinitely without ever appearing in the journal, and
  a journal entry never needs to reference the backlog to be complete.
- **The ticket system** (GitHub Issues, Jira, Linear, or similar). Tickets represent
  committed, scheduled, actionable work — they carry status, assignees, and process
  overhead. Backlog entries are *pre-ticket*: ideas not yet worth that overhead, or
  explicit scope cuts that may never warrant a ticket at all. A backlog entry graduates
  into a ticket when someone decides to actually act on it — at which point the entry
  typically stays in the backlog (referencing the ticket) rather than being deleted, so
  the "we considered this" record survives independently of ticket-system retention.
- **Git history / commit log.** Commits record what *was* built. They cannot answer "did
  we ever think about X, and if so, why didn't we do it?" — that reasoning would
  otherwise be lost the moment the conversation that produced it ends. The backlog is the
  place that question can always be answered from.

## Structure

A generic skeleton for the file (adapt section names/wording to the host project's
voice, but keep the shape):

```markdown
# Backlog — deferred ideas

Things deliberately postponed. **Project convention:** whenever something is decided to
be done "later" (or explicitly placed out of scope), it is recorded here instead of being
silently dropped. See `<link to the project's conventions/onboarding doc>`.

## Deferred

- **<Short title>** — <what the idea is, and why it was deferred rather than done now>.
  (<optional: interim behavior, workaround, or the constraint that will be revisited>)
- **<Short title>** — <...>

## Out of scope (tracked elsewhere)

- **<Short title>** — see [`<decision-record-title>`](<path/to/decision-record>) and
  `<other-doc>` §<section>.
- **<Short title>** — <...>
```

Two sections are useful once a project also keeps a decision record (an ADR log, an RFC
directory, a design-decisions doc): "Deferred" holds ideas without a separate written
rationale yet; "Out of scope" holds ones where the rationale is already captured
elsewhere and the backlog entry is just a pointer. A small project without a separate
decision record can collapse this to a single "Deferred" section.

**ID scheme (optional).** Small or single-contributor backlogs can identify entries by
their bold-title text alone — informal enough as long as titles stay unique. Once other
documents need to reference a backlog entry by a stable handle independent of wording
(e.g. from a ticket, a commit message, or another doc), introduce a short stable id per
entry, assigned once, incrementing, never reused or renumbered — e.g. `BL-014`. Don't add
this machinery before it's needed; retrofitting ids onto an existing informally-titled
backlog is a mechanical one-time pass (assign in file order, then never reorder existing
ids again).

## Core rules

1. **Record the moment something is deferred, not later.** The trigger is the decision
   itself ("we're not doing this now") — captured in the same work session, not deferred
   to memory or a future cleanup pass.
2. **Entries persist past ticket creation.** When a backlog item is promoted to a ticket,
   leave the backlog entry in place (optionally annotated with the ticket reference)
   rather than deleting it. The backlog is the durable record that the idea was
   considered; the ticket system's own retention policy is a separate concern.
3. **No workflow state.** A backlog entry has exactly one bit of state: "it's in the
   backlog." Assignees, due dates, sprints, and priority fields belong in the ticket
   system, not here — if an entry needs that machinery, it's no longer a backlog item,
   it's a ticket.
4. **One entry, one idea.** Don't bundle unrelated deferred ideas into a single bullet;
   each must be independently referenceable (whether by title or by id).
5. **Cross-link instead of duplicating rationale.** If a decision record already explains
   *why* something is deferred or out of scope, link to it rather than restating the
   reasoning in the backlog entry.
6. **Consistent entry formatting.** Bold short title as the lead-in, a terse one- to
   few-sentence rationale, technical identifiers/paths formatted as inline code.
7. **IDs, once introduced, are permanent.** Never renumber or reuse an id, even after the
   entry it names is removed — stability of the reference is the entire point.

## Adaptation checklist

1. Create the file (commonly `BACKLOG.md`) at whatever documentation root the host
   project already uses for durable, non-code docs — alongside its README, changelog, or
   decision-record directory, matching that project's existing naming conventions.
2. Add one explicit line to the project's contributor/onboarding doc (a `CONTRIBUTING.md`,
   an agent-instructions file, or equivalent) stating the recording convention: *whenever
   something is decided to be "for later" or "out of scope," write it here instead of
   letting it drop.*
3. Decide up front whether one section suffices or whether a project needs the
   "Deferred" / "Out of scope (tracked elsewhere)" split — the latter only pays for
   itself once a separate decision record exists to link to.
4. Decide whether a stable id scheme is needed now, or can be deferred until the first
   time another document needs to reference an entry (see "ID scheme (optional)" above).
5. Link the file from wherever the project's other documentation is indexed (a docs
   README, a table of contents, a project brief) so it's discoverable, not just
   discoverable-by-accident.
6. Optionally, revisit the backlog at natural checkpoints (releases, planning sessions)
   to promote ready items into tickets — this is a review cadence, not a rule the file
   itself needs to enforce.

## Ready-to-use bootstrap prompt

Copy-paste the block below into a fresh Claude Code (or similar coding-agent) session, in
any project, to introduce this pattern and lock in its maintenance rules going forward.

```text
Introduce a "deferred ideas backlog" file in this project, following this pattern:

PURPOSE: A single Markdown file that records ideas and scope cuts the project has
deliberately postponed — distinct from (a) any requirements/decisions journal or
changelog this project keeps (which records what WAS decided and done, not what was
postponed), (b) the actual ticket system (GitHub Issues/Jira/Linear/etc — tickets are
committed, scheduled work; backlog entries are pre-ticket ideas not yet worth that
overhead), and (c) git history (which records what was built, not what was consciously
deferred).

STRUCTURE: Create the file at whatever documentation root this project already uses for
durable docs (match its existing naming convention — often `BACKLOG.md`). Use this
skeleton, adapted to the project's voice:

    # Backlog — deferred ideas

    Things deliberately postponed. Project convention: whenever something is decided to
    be done "later" (or explicitly out of scope), it is recorded here instead of being
    silently dropped.

    ## Deferred

    - **<Short title>** — <what the idea is, and why it was deferred>.

    ## Out of scope (tracked elsewhere)

    - **<Short title>** — see <link to the decision record that explains why>.

Only include the "Out of scope" section if this project keeps a separate decision record
(ADRs, RFCs, a design-decisions doc) to link to; otherwise use a single "Deferred"
section. Do not invent a stable id scheme (e.g. `BL-001`) unless the project already has
a clear present need for one — add it later, retrofitted in file order, if that need
arises.

CORE RULES to establish and follow from now on:
1. Record a deferred/out-of-scope decision in this file in the same session it's made —
   never postpone the recording itself.
2. When a backlog entry is later promoted to a ticket, keep the backlog entry (optionally
   noting the ticket reference) instead of deleting it.
3. Never add workflow state (assignee, due date, priority) to an entry — that belongs in
   the ticket system; if an idea needs that, it's no longer a backlog item.
4. One entry per idea; never bundle.
5. Link to existing decision records instead of duplicating their rationale.
6. If an id scheme is later introduced, ids are permanent — never reused or renumbered,
   even after the entry they name is removed.

TASKS:
1. Check whether this project already has an established location/convention for
   durable, non-code documentation (a docs folder, a README section, a docs index) and
   place the new file consistently with it. If nothing like that exists, ask me where to
   put it before deciding.
2. Add one line to this project's contributor/onboarding doc (whichever file governs
   working conventions here) stating the recording convention above.
3. Create the backlog file itself. If there are already known deferred ideas or
   explicit scope cuts from prior conversations, seed the file with them now; otherwise
   leave it with just the header and empty sections.
4. Follow this project's normal change workflow for adding these files (ticket, branch,
   commit, PR/merge — whatever this project's conventions prescribe). If it has no such
   workflow, just save the files and tell me the paths.

Confirm the chosen file location and section structure with me before writing, if this
project has no existing precedent to follow unambiguously.
```
