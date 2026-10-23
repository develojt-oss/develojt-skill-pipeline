# Findings Archive — {project name} (resolved-history ledger)

> The store of rows archived from `spec/findings.md` at the Record stage (Resolved defects · past cycle-log rows) — append at table ends only (no edits, no deletions of existing lines).
> The loop never reads this file (archival is a context-saving device) — only the verification script reads it, for ID/cycle uniqueness-continuity and type tallies.
> `Rejected` (the memory that prevents duplicate checker reports) and `Needs review` (awaiting a human decision) are never archived — they stay in findings.md.

## Cycle Log History

> Ledger cycle-log rows beyond the latest 5 are moved here for preservation — every verdict (quiescence, lens, changed-bundle) reads only the latest rows left in the ledger.

| Cycle | Date | Scope | New | Resolved | Rejected | Notes |
|---|---|---|---|---|---|---|

## Resolved History

| ID | Status | Type | Target | Symptom | Evidence | Action Log |
|---|---|---|---|---|---|---|
