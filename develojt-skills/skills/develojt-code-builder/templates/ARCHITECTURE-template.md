# Structure Contract (Architecture Contract) — {project name}

> The **baseline of this project's structural decisions**. develojt-code-builder carries the draft in a new
> project's first implementation report, and **human approval finalizes it** (a project that has progressed
> without a contract adopts one mid-project via a human instruction — `references/architecture-lifecycle.md`,
> the same finalization gate); thereafter every code work
> (builder bundle implementation, pdca Act, develojt-code-changer operations changes) re-reads this file at
> the start of each unit of work and follows it — the device that lets every session start from the same
> structural baseline even as sessions change.
>
> **Write invariants** — not the current file listing (a snapshot) but **growth rules** that never go stale as
> the project scales (e.g., "a new feature gets one feature folder" is the same rule at 10 features and at 500 —
> everyday additions, changes, and deletions are absorbed *inside* the contract without a revision). Write
> machine-checkable sentences with concrete paths and directions — a wish sentence like "keep coupling low"
> is not a contract.
>
> **Revisions only through human approval** — the AI (the builder's or changer's lead) never changes this file
> on its own. When implementation meets code that has no place in the contract, it never places it silently —
> it reports a revision proposal (builder 'when a design change is needed'). On a finalized revision, add one
> line to the revision history, then edit the body (history rows are never deleted).

| Baseline SPEC | Finalized | Last revision |
|---|---|---|
| spec/SPEC.md | {YYYY-MM-DD} | — |

---

## 1. Layer map

> This project's layers (module partitions) and each one's remit. Layer names map 1:1 to actual paths under `src/`.
> Coexisting layers that actually exist (recorded coexistence with an old structure) are also enrolled as rows,
> annotated `(coexistence — revision history #N)` — unrecorded coexistence is the rot (the machine check
> pdca C4 reads this table verbatim — an unenrolled place keeps printing as a violation candidate).
>
> **Machine-readable grammar**: write the actual `src/` path verbatim in each row's first cell (backtick/bold
> decoration is harmless — a name alone without the path is unreadable to the machine). Never enroll the
> `src/` root itself as one layer (it disables the sub-partition checks).

| Layer (src/ path) | Remit (what lives here) | What must not live here |
|---|---|---|
| {e.g., src/ui/} | {e.g., screens, components, presentation logic} | {e.g., business rules, data access} |

## 2. Dependency directions

> **Enumerate allowed directions only** — any import/reference in a direction not listed here is forbidden
> (including reverse directions and layer skipping).
> An arrow chain allows adjacent pairs only (in `A → B → C`, a direct A→C reference is allowed only by its own row).
> Old directions allowed as coexistence are also enrolled as rows, annotated `(coexistence — revision history #N)` —
> the machine check (pdca C4) reads this table verbatim.
>
> **Machine-readable grammar (one row = one chain)**: never pack several chains or several targets into one
> cell with `·` or commas — split them into rows. A token is a §1 `src/` path verbatim or its last segment
> name alone (when the same name exists in two layers, the full path is the only way — the machine drops a
> row whose name match is ambiguous). Anything in parentheses is treated as a note and stripped by the
> machine — never put tokens inside parentheses (backticks/bold are harmless). Prose that is not an arrow
> chain is unreadable to the machine — put prohibition statements in the Forbidden-examples cell or §3
> (by this table's grammar an unlisted direction is already forbidden, so prohibition holds without prose).

| Allowed | Forbidden examples |
|---|---|
| {e.g., ui → service → data (one direction)} | {e.g., data imports ui / ui imports data directly} |

## 3. Placement rules

> The growth rules for "where does newly written code live" — fixing the home of new features, shared code,
> and cross-cutting concerns. Paired with same-feature-reinvention prevention: with a single home for shared
> code, there is also a single place to look before building.
> Write the shared-code home as an invariant down to its partitioning, not as one unpartitioned folder
> (e.g., `src/core/{concern}/`) — the grammar that prevents home bloat (legal dumping-ground rot; observation
> via `verify_architecture.py --metrics`, judgment by the human).

- **New features**: {e.g., one folder per feature under src/features/{feature}/}
- **Shared code** (constants/utilities/types used by two or more features): {e.g., src/core/ only — direct cross-references between feature folders forbidden}
- **Definitions** (states, codes, classification enumerations, named constants, data structures): {e.g., declared and changed only in src/core/model/ — other layers only reference them; restating the values as literals is forbidden}
- **Cross-cutting concerns** (logging, error handling, configuration, …): {e.g., exactly one home under src/core/{concern}/ — per-feature reimplementation forbidden}
- **External integration** (APIs, DB, files — system boundaries): {e.g., always through src/data/ — direct calls from other layers forbidden}

## 4. Revision history (human approval only — rows are never deleted)

> Written only when a structural decision itself changes (growth inside the contract is not a revision).
> **The application scope is mandatory** — `from new code onward` (existing code coexists under the old
> structure — recorded coexistence is not rot; unrecorded coexistence is) or `full migration` (migrating the
> existing code is a separate intake — develojt-code-changer).

| Date | Revision (what → what) | Reason | Application scope | Approval |
|---|---|---|---|---|
