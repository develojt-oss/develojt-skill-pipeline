# Screen Review — {project name} (screen-review ledger)

> The waiting list of screen comparisons the builder registers when an appearance-comparison target bundle completes — **one row per screen**; never delete rows, update only the Status cell.
> When a later bundle creates or changes the same screen again, do not add a new row — append to that row's Registered bundles and reset its Status to `Unchecked` (re-comparison).
> The comparison itself (running screen ↔ design baseline, by human eye) does not happen per bundle — it happens one item at a time in the **screen-comparison session**
> the builder requests after full implementation completion (all joblist rows checked + the last bundle's pdca quiescence); the human may start it earlier after any bundle.
> While `Unchecked`/`Reinforcing` rows remain, **development-draft completion cannot be declared** (a scope-completion condition — never skipped even under an "all" instruction).
> Status vocabulary: `Unchecked` (default) → `Reinforcing` (a mismatch/defect was flagged; under repair) → `Confirmed` (passed human-eye comparison) / `Confirmed (auto)`
> (passed the browser auto-comparison the human explicitly delegated — side-by-side screenshot evidence in the report is mandatory).
> **No full reads during the development phase** — registration is write + screen-name grep; the backlog is a Status-cell count grep only. Row contents are read only
> for the row being presented in the session (context frugality — the same discipline as findings-archive). pdca and checkers never read this file.

## Awaiting comparison

| Screen (how to reach it) | Design baseline | Reproduced anchors | Registered bundles | Notes | Status |
|---|---|---|---|---|---|
