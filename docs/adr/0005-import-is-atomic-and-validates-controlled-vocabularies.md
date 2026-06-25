# Import is atomic and validates against the controlled vocabularies

The strict Markdown import is **all-or-nothing**: if any token cannot be typed — in
particular a `tool` or resource-type value outside the current controlled vocabulary
(e.g. a tool other than `Browser`/`Thunderbird`) — the import writes **nothing**, aborts,
and returns a precise report of the offending values.

When an unrecognized value looks like a legitimate new member of a static domain, the
report names it explicitly and **recommends extending that vocabulary via the GUI** before
re-importing.

Rationale: avoids a half-populated checklist and surfaces vocabulary gaps explicitly.

Implication: **Tool** and **Resource Type** are user-extensible controlled vocabularies
managed in the app, not hardcoded enums.
