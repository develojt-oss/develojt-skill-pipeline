# Findings — {project name} (PDCA ledger)

> The single state store of the inspect-and-reinforce loop. "Where the loop is now" is restored entirely from this file.
> Rows are never deleted — only state transitions exist. The sole exception is Record-stage archival: `Resolved` rows and the
> cycle log's rows beyond the latest 5 are moved as-is into `findings-archive.md` (the resolved-history ledger) and preserved there —
> the ledger keeps only active rows (unresolved, Needs review, Rejected) and the latest cycle log.
> The history itself is the raw material for process improvement.
> Numbering: the next F-number = the header's 'Last F-number' + 1 (update it on assignment — never count from the ledger's maximum ID).

| Base SPEC | Base joblist | Updated | Last F-number | Current cycle |
|---|---|---|---|---|
| spec/SPEC.md | spec/joblist.md | {YYYY-MM-DD} | — | 0 |

---

## Status & Type Definitions

- **Status**: `New` (checker-reported, awaiting Act) → `Fixing` (Act in progress) → `Awaiting recheck` (fix done, awaiting re-Check)
  → `Resolved` / `Rejected` (counter-evidence required) / `Needs review` (awaiting human decision — the loop leaves it untouched until decided.
  After the decision: fix instruction → back to `New` / rejection decision → `Rejected` / SPEC addition needed → `Resolved` after a deriver increment)
- **Type**: `M1` coverage gap / `W1` missing wiring / `W2` incorrect wiring / `W3` uncalled provider / `F1` missing failure behavior / `C1` constraint violation / `C2` security rule violation / `C3` enforced-rule violation / `C4` structure-contract violation / `S1` series deviation

---

## Defect Ledger

> The Evidence cell can never be empty (`file:line` quote required). Every status other than `New` must have a non-empty Action Log.

| ID | Status | Type | Target | Symptom | Evidence | Action Log |
|---|---|---|---|---|---|---|

---

## Process Improvement Proposals (awaiting human approval)

> When 3+ defects of the same type accumulate, propose here a rule addition that would catch that class.
> The tally comes from verify_findings_integrity.py's PASS output 'Type tally' (archived resolved rows included, Rejected excluded).
> Proposals only — actually modifying skill/checker rules is separate work after human approval.
> That separate work is done in the pipeline originals, not this project's `.claude/` copies, and reaches the project via redeployment (`/develojt-init`) — a fix made only to the copy is overwritten and lost at the next re-initialization.

| Proposal | Basis (recurring defect IDs) | Target (skill/rule file) | Status |
|---|---|---|---|

---

## Checker Calibration (once per project + on human request)

> The record of mutation-injection calibration — synthetic defects are never written to the defect ledger. This table is the only record.
> If detection is below 3/3, note the need to reinforce checker rules in Process Improvement Proposals.

| Date | Scope | Planted mutations (type · SPEC ID · location) | Detected | Notes |
|---|---|---|---|---|

---

## Cycle Log

> Write the unresolved (carryover) N at cycle end in Notes — the quiescence verdict (0 new · 0 carryover for 2 consecutive cycles) is read from this table.
> Only the latest 5 rows stay — the Record-stage archival script moves the excess to the resolved-history ledger (every verdict reads only the latest rows).

| Cycle | Date | Scope | New | Resolved | Rejected | Notes |
|---|---|---|---|---|---|---|
| 0 | {YYYY-MM-DD} | Ledger created | 0 | 0 | 0 | |
