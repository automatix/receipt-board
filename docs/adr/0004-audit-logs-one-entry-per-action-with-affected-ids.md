# Audit logs one entry per action, with cascade-affected node ids

Every write action produces exactly **one** append-only Audit Log entry capturing the
caller's *intent* — timestamp, origin (`GUI` / `CLI` / `REST`), action type, target
node/checklist `id`, and old → new value — **plus** the list of all node ids changed by
the resulting cascade.

Considered and rejected: one entry per affected node (verbose, and the intent is lost —
it would have to be reconstructed by grouping on a transaction id); logging only the
action without its effects (the cascade's concrete effects would not be recorded).
