# Incremental Update Procedure (incremental)

The procedure for adding only new IDs to the joblist after additional features entered the SPEC as new IDs, **while preserving the existing progress state and bundle composition**. This is not a full regeneration. Already-checked completions, notes, and bundle boundaries are never touched.

## Entry conditions

- `spec/joblist.md` already exists.
- SPEC.md was updated and new SPEC IDs absent from the joblist now exist (added by a deriver increment).

## Procedure

1. **Confirm preservation of the existing** — read the current joblist (scaffolding + bundle tables) as-is. Preserve completion checks, notes, order, and bundle composition in memory. From here on, existing rows and bundle headers change by not a single character.

2. **Identify new IDs** — run `verify_joblist_spec_sync.py` and take the ID list reported as "omissions" (in the SPEC, not in the joblist).

3. **Decide ownership — judged by physical dependency.**
   Decide where each new ID goes.
   - **Scaffolding-grade** (a foundation multiple bundles share — a code foundation such as config, types, events, initialization, and the runtime base (containers/runtime, storage startup, middleware, resident services, shared contracts/libraries)) → add to `## 0. Scaffolding`.
   - **Physically dependent on an existing bundle's tags** (calls/references that tag's code, or uses its outcome per a behavior chain) → add to that bundle.
   - **No physical dependency on anything existing** → add as a new `### Bundle N`.
   Series is judged **for the new ID only, against the existing joblist's series definitions** — if it's built the same way, that series name; otherwise `—`. **Existing rows' series are never re-judged** (double judgment creates divergence).

4. **Insertion position** — order is dependency order. If the new item depends on an existing one, it goes after; if an existing one depends on the new item, before. A plain addition goes at the end of that bundle/table. **The relative order of existing rows/bundles never changes.**

5. **Add rows** — added unchecked (`[ ]`). Never pre-check the Done cell (before implementation). Update the document header's 'Updated' cell to this increment's date (the header table is not a preserved work row). If `design/STORYBOARD.md` exists, record appearance anchors (`Appearance: SB-…` — every UI ID mapped to that FR, confirmed by FR ID grep) **in new rows' Notes only**, by the same rule as fresh-flow step 6 — a UI ID mapped to multiple FRs is never re-carried if it already rides on an existing row, and if it rides nowhere in the ledger it goes only on the front-most of this increment's new rows. If the new row's screen (SB-NN) has `[Decorative]` IDs not yet carried on any ledger row (when that screen's first FR row is this new row), they ride along on the new row (one SB ID on exactly one row across the whole ledger). **No backfilling existing rows' Notes.**

5-1. **Update the parallel candidates (if present)** — if `## Parallel Candidates` exists and this increment created a **new bundle**, leave the existing groups unchanged and judge only whether the new bundle is listed, by the 5 listing conditions (SKILL 'joblist structure' 4) — add to an existing group / a new group / not listed. Never re-judge existing bundles against each other (the same principle as no series re-judgment). If rows were only added to an existing bundle and the new rows break the listing conditions of the group that bundle belongs to (a new deferral, a newly shared screen, etc.), **remove** that bundle from the group (never leave it in a state that violates the listing conditions — if unsure whether to remove it, remove it).

6. **Verify** — re-run the verification scripts and confirm PASS. In particular, consistency "omissions" must be 0 (every new ID made it in).
   ```bash
   python3 .claude/skills/develojt-spec-spliter/scripts/verify_joblist_integrity.py spec/joblist.md
   python3 .claude/skills/develojt-spec-spliter/scripts/verify_joblist_spec_sync.py spec/joblist.md spec/SPEC.md
   python3 .claude/skills/develojt-spec-spliter/scripts/verify_anchor_sync.py spec/joblist.md design/STORYBOARD.md  # auto-SKIP when no STORYBOARD
   ```
   (Global install: `~/.claude/skills/develojt-spec-spliter/scripts/...`)

## Deletion propagation — moving `[Removed]` IDs to `## Past Issues` (T4)

When deriver change mode **deletes** a requirement, it transitions that ID's row in the SPEC to `[Removed]` (strikethrough) (the row is preserved).
The sync gate excludes `[Removed]`/strikethrough rows from the SPEC's active ID set, so **if that ID still sits in a joblist bundle table,
it is caught as a "ghost".** The spliter resolves this ghost by **moving it to `## Past Issues`, not physically deleting it** (non-destructive transition L3).

1. **Identify and classify ghosts** — for each "ghost" ID reported by `verify_joblist_spec_sync.py`, check the SPEC:
   - If the ID **exists in the SPEC as a `[Removed]`/`~~strikethrough~~` row** → an intended deletion (T4). Proceed to the move in step 2.
   - If the ID **is entirely absent from the SPEC** (not even a strikethrough row) → this is not deletion propagation. With massive ghosts, it's a full SPEC regeneration (the re-split branch of the SKILL's incremental flow); with a few, stop and confirm with the user (the ledger points at a requirement that doesn't exist).

2. **Move to Past Issues** — remove that ID's work row from the bundle (or scaffolding) table and move it as one row into the `## Past Issues` table (history preserved — outright deletion forbidden):
   ```
   | {SPEC ID} | {removal reason — read from the SPEC's [Removed] row} | removed |
   ```
   - Remove only that row from the bundle table. **The remaining rows, completion checks, notes, order, and bundle boundaries stay invariant.**
   - If that row was the **recipient of another row's intentional deferral** (a deferral handoff written in its Notes), clean up that deferral together or inform the user (preventing a deferral that lost its address).

3. **Re-verify** — run sync again and confirm "ghosts 0" (the move took it out of the bundle table, so it resolves. IDs in `## Past Issues` are not sync-counted).

> **Downstream closure**: even after the move, the old `@spec` tags remain in the code, and the builder's `verify_spec_coverage` catches them as **orphans** —
> develojt-code-changer (code-only path) removes those `@spec` tags and the dead code to close the chain. The spliter goes only as far as the joblist (R&R).

## Forbidden

- Never uncheck existing completions; never edit/delete existing notes.
- Never reorder existing rows/bundles — only line shifts from inserting new rows are allowed; existing rows' text and relative order stay invariant.
- Never re-cut existing bundle boundaries — only decide the new items' ownership.
- Never add IDs absent from the SPEC (ghost rows).
- Never re-judge existing rows' series — only the new IDs' series is decided, against the existing joblist's series definitions.
- **Never fully delete a `[Removed]` ID's row** — move it to `## Past Issues` to preserve history (non-destructive transition).
