# Node type (Category vs Expense Item) is explicit, inferred only at import

Each Node stores an **explicit** type discriminator — `Category` or `Expense Item` —
rather than deriving it from whether it has children. An Expense Item never has children;
a Category may be empty yet remains a non-actionable grouping (no action fields).

Only the Markdown **import** infers the type structurally — childless rows become Expense
Items, their ancestors become Categories — and then stores it explicitly. Thereafter the
type changes only via a deliberate GUI action.

Considered and rejected: deriving the type from child count — adding or removing children
would silently flip a node's nature and make its action fields appear or vanish.
