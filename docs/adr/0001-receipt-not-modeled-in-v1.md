# Receipt is not a domain entity in v1

Although the product is called **Receipt Board**, `v1` deliberately models only the
*checklist* of expense positions to be evidenced — the **Expense Item** and its `done`
state — and **not** the receipt artifacts themselves. There is no file storage, naming,
or handling of actual receipts in `v1`. A future iteration may introduce a `Receipt`
entity once file handling enters scope. Recorded because the absence of a "Receipt"
concept is surprising given the product name.
