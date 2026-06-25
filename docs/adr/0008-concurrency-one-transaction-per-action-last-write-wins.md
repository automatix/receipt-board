# Concurrency: one SQLite transaction per action, last-write-wins

Every write action runs in a single SQLite transaction (WAL mode), making the mutation
and its cascade atomic. There is **no** application-level locking or optimistic
versioning: with genuinely concurrent writers (GUI + CLI/AI), the **last committed write
wins**. The GUI refreshes its view after each action (or reloads) to reflect external
changes.

Rationale: a single-user, local app; this keeps the parallel CLI/AI operation the user
explicitly wants, at the acceptable cost of rare lost-update races on the same field.

Considered and rejected: optimistic locking with version checks (unnecessary complexity
for a single user); a single-writer lock (would block the desired parallel CLI/AI use).
