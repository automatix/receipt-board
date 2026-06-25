# `done` is stored on every node, kept consistent by a symmetric cascade

Every `Node` (Categories included) stores its own `done` checkbox rather than deriving
category state from its children. A **symmetric cascade** maintains the invariant
`category.done ⇔ entire subtree done`: setting a node to `true`/`false` forces all
descendants to the same value, and changing a child re-rolls-up its ancestors
(`ancestor.done = AND(direct children)`). The tool executes this cascade unconditionally
and is **agnostic** to the checkmark's real-world meaning.

Considered and rejected: deriving category state from leaves — the user wants categories
to be first-class, independently addressable, auditable checkboxes.

Consequence: unchecking a Category clears its whole subtree, so an accidental click is
destructive. Guarding against this (confirmation/undo) is a **GUI** concern, not domain
logic.
