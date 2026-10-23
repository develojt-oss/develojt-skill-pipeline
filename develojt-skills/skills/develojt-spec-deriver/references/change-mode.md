# Change Mode — modify/delete existing requirements (non-destructive transition)

The path for **fixing or removing existing requirements** in an already agreed-and-finalized `spec/SPEC.md` (the opposite of incremental=add).
No full regeneration, no negotiation. To avoid silently severing the traceability chain (SPEC↔joblist↔`@spec`),
requirements are **never erased — their state is transitioned** (non-destructive transition L3).

The deriver does **only the SPEC's non-destructive transition** — joblist moves (spliter) and removing `@spec` tags
and dead code (builder) belong downstream. The deriver touches only the SPEC (R&R).

## Entry conditions

- `spec/SPEC.md` already exists (finalized).
- The user requested **modification or deletion of an existing requirement** (e.g., "change FR-09-001 to this", "remove the auto-spin feature").
- The same applies when develojt-code-changer (operations change intake) delegates in (the problem is the requirement, not the code, so the deriver transitions the SPEC).

## Core principles (non-destructive transition)

- **Never delete rows.** The target ID's row is **kept**; only its state transitions (history preservation + detectability).
- **Modification = `[Removed]` + new ID.** A changed meaning is a new tracking target. The old ID is preserved as `[Removed]` (a source-cell tag — notation below) and a new ID is assigned.
  Keeping the ID and editing only the text lets semantic drift slip past **every gate** — by minting a new ID, the stale `@spec`
  still pointing at the old ID is caught by **the existing orphan gate (verify_spec_coverage)**. Non-destructive transition is detectability itself.
- **Deletion = `[Removed]`.** Once a row transitions to `[Removed]`, any joblist row still pointing at that ID becomes a **ghost FAIL** in sync,
  and any code `@spec` becomes an **orphan FAIL** in coverage — forcing downstream cleanup (no new detection scripts needed).
- **The deriver touches only the SPEC.** Never the joblist or code directly.

## `[Removed]` transition notation (source tag convention)

Change the requirement table row as follows (using `[Removed]` from the 6 common-rules source tags — the same form as the ears-guide's `[Removed]` example):

| Cell | After transition |
|---|---|
| ID | `FR-..-...` **as-is** (no strikethrough — the ID is a tracking key, not a verdict key. Only while the row still starts with the ID cell does `verify-sources`' duplicate-ID check keep seeing this row, mechanically blocking reuse of a deleted ID) |
| Source | `[Removed]` (a short reason may follow: `[Removed] replaced by FR-..-...`) — **this tag is the single verdict key for "inactive"** |
| Requirement | Strikethrough on the original text (`~~original~~` — a history mark. `verify-sources` WARNs when a `[Removed]` row has no strikethrough). One line on what was removed/replaced and why |

> `verify-sources` passes `[Removed]` as a valid tag, and the 4 downstream gates (`verify_joblist_spec_sync`, `verify_spec_coverage`,
> `verify-coverage`, `verify-stale`) exclude rows whose source cell is `[Removed]` from the active ID set — that is, `[Removed]` rows are
> automatically treated as "no longer a tracking target". An old SPEC's `~~FR~~` ID-strikethrough rows are excluded by the same gates as-is (a preserved legacy notation — never written anew).

## Procedure

1. **Absorb the existing SPEC** — read `spec/SPEC.md` and grasp the target ID's current text, EARS type, source, owning EP, and behavior-chain involvement.

2. **Decide the change type** — fix it as one of two:
   - **T3 modification** — the requirement's *meaning* changes (behavior, condition, or scope). → 3a.
   - **T4 deletion** — the requirement is *removed* (feature dropped). → 3b.
   > If only the text is polished and the meaning stays (typos, wording), it is not change mode — with meaning invariant, tracing doesn't break, so an in-place edit suffices. When ambiguous, confirm with the user once.

3a. **T3 modification transition** — ① transition the old ID's row to `[Removed]` (notation above). ② **assign a new ID** (that EP's next number; failure cases `-E{nn}`). ③ formalize the new requirement with the existing rigor:
   - EARS type classification + comply with `references/ears-guide.md`.
   - Source: `[Requested]` for a user request, or the relevant `PRD EP-XX` when reflecting a PRD change.
   - Quantitative/enumerable autonomy spots get `[Free: reason]`.
   - In the old row's source, point to the new ID with `[Removed] replaced by {new ID}` to link the history.

3b. **T4 deletion transition** — transition the target ID's row to `[Removed]` (no new ID). Old row's source: `[Removed] {reason}`. If other requirements depended on it (step 5 below), examine those too.

4. **Security surface check** — compare the transition against the '[Required] Security requirement derivation
   checklist' table in `references/common-rules.md` (6 surfaces: authentication, authorization, PII, external input,
   files, requests to user-supplied addresses) — a meaning-changing transition has the same security surfaces as an
   addition, so this mirrors incremental mode's step 4:
   - **T3 modification**: for every surface the new requirement has, add that feature's own observable security behavior with the same rigor (3a's tag rules) — source `[Implicit] derived from {new FR ID}` (the common-rules checklist's back-tracing notation); policy values without grounding get `[Free: reason]`; the checklist's boundary rules apply equally (global principles are never restated in the SPEC). Existing security requirements derived from the old ID (lockout, masking, caps, …) are found via `grep "derived from {old ID}" spec/SPEC.md` (the back-tracing notation — in an older SPEC predating it, compare the same EP's `[Implicit]` security rows instead). If a found row no longer fits the new meaning, transition that row too via this procedure (T3/T4) — left behind, it survives as a stale security requirement posing as valid.
   - **T4 deletion**: compare the target row — and rows losing their meaning with it (the derived security rows found via `grep "derived from {target ID}" spec/SPEC.md`; in an older SPEC predating the notation, compare the same EP's `[Implicit]` security rows) — against the same table; if it is a security-surface behavior, state it separately in the step 9 report as **"N security requirements deleted"** — deleting a security behavior removes a defense, so the human must see it explicitly (the transition is non-destructive, so it can be reverted after judgment).
   If no surface applies, add nothing. State additions and cascaded transitions separately in the step 9 report as **"N security derivations/transitions"** (the human filters any excess).

5. **Impact query (required)** — reverse-query the impact scope with the changed ID to identify **the peers to re-examine together**:
   ```bash
   # Development phase (joblist exists) — bundle, series, behavior chain
   python3 .claude/skills/develojt-spec-deriver/scripts/query_impact.py {changed ID} spec/joblist.md spec/SPEC.md
   # Operations phase (develojt-code-changer delegation — joblist lifecycle over) — SPEC behavior chains only (dedicated tool)
   python3 .claude/skills/develojt-spec-deriver/scripts/query_chain.py {changed ID} spec/SPEC.md
   ```
   (Global install: `~/.claude/skills/...`) In the output, **same bundle** (physical dependency), **same series** (method consistency), and **same behavior chain** (simultaneous outcomes)
   are the change's ripple candidates. **In the operations phase only behavior chains come out deterministically** (bundle/series are not produced), and series is checkable only when a deriver increment left sibling notation in the SPEC (full-generation SPECs carry no series notation).
   Modifying a series' *reference implementation* can skew the whole series, so inform the user of those peers.

6. **Behavior-chain consistency** — if the changed ID appears in any `Observable Behavior Chain` table's `Related IDs`, update that chain non-destructively (the chain is the builder's wiring contract):
   - **T4 deletion**: remove that ID's outcome from the chain and drop it from `Related IDs` (if that outcome is the chain's trigger itself, confirm the chain's survival with the user).
   - **T3 modification**: **replace** the old ID with the new ID in `Related IDs`, and update the outcome cell if its wording changed.

7. **Statistics update** — re-tally `## Summary Statistics` and the distribution by source. Summary statistics count **requirement rows** (`verify-sources` counts rows that start with an ID, and a `[Removed]` row is still a row, so it is included) — a modification (T3) raises the numbers by the new ID rows, and a deletion (T4) leaves them unchanged (skipping the update in T3 makes step 8 verification FAIL).

8. **Verify** — re-run the existing verifications (must still PASS after the transition):
   ```bash
   bash .claude/skills/develojt-spec-deriver/scripts/verify-sections.sh spec/SPEC.md
   bash .claude/skills/develojt-spec-deriver/scripts/verify-sources.sh spec/SPEC.md
   ```

9. **Notify the user + downstream propagation guide** — briefly report what transitioned how, and **what downstream must do** (downstream closes the tracing loop):
   - Transition results: the `[Removed]` old ID, the new ID (for modifications), updated chains. N security derivations/transitions and N security requirements deleted (step 4 — omit if none).
   - Re-examination peers from the impact scope (step 5 query_impact output).
   - Downstream: a **spliter** increment moves `[Removed]` rows to the joblist's `## Past Issues` (resolving ghosts), and **develojt-code-changer (code-only path)** removes the old `@spec` tags and dead code (resolving orphans — under a delegation, the intake lead cleans these up together in its step 4). Until that cleanup, the sync/coverage gates FAIL intentionally — that FAIL is the design that forces the cleanup.

## Forbidden

- Never **physically delete** a requirement row (only the `[Removed]` transition — preserving history and detectability).
- Never **reuse the old ID** or change only the text on a modification (it makes semantic drift undetectable — always `[Removed]` + new ID).
- **Never touch the joblist or code directly** (propagation belongs to spliter/builder — the deriver owns only the SPEC, R&R).
- Never leave an old ID sitting in a behavior chain (the wiring contract would point at a dead ID).
- Never leave the change type (T3/T4) ambiguous — fix modification vs deletion first.
