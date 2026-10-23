# Mapping-Update Mode (remap) — syncing SPEC transitions (change·deletion) into the existing mapping + applying conflict verdicts (A/B) + appearance release (human-decided)

The path taken **after** deriver change mode has transitioned existing FRs non-destructively to `[Removed]`
(+a new ID on modification). Once a transition happens, the STORYBOARD's mapping for that FR points at a dead ID
(stale — `verify-coverage` catches only **missing** new FRs, not **lingering** old ones). The mapper updates the
mapping using the delegated transition pairs (and, on the conflict path, the verdict lists).
There are three delegation paths — the first two are stage 2 of develojt-code-changer's (operations change intake) delegation:

- **Conflict resolution** — the human has given A (design wins)/B (SPEC wins) verdicts on the design↔SPEC conflicts
  in `design/spec-conflicts.md`. On top of the transition sync, perform conflict-A incorporation and B cleanup (steps 3–4).
- **Base change/deletion** — pure requirement changes/deletions unrelated to any conflict (delegate-mode step 3-b).
  **Transition sync only** (there are no conflict lists, so steps 3–4 don't exist).
- **Appearance release** — the human has decided that a specific element's appearance now departs from the **design
  originals** (requirement invariant — the SPEC unchanged, no deriver stage). No transition sync; only the release
  list's mapping rows are **retired** (step 2-b). The delegating side is develojt-code-changer (operations — revise's
  'appearance-instruction input' section · delegate step 3-b) or develojt-code-builder (a human instruction
  mid-development — its 'when a design change is needed' section). **The design originals (design/) are the project's
  starting baseline and stay frozen — they are never edited.** Without this release record, the stale mapping row keeps
  instructing the next worker to restore the old appearance (the release is what separates silent deviation from
  legitimate deviation).

Where promote is "applying SPEC increments", remap is "syncing SPEC transitions" — the mapper counterpart of the
deriver's `change-mode`. No full regeneration, no negotiation.

> **The order is forced** — the mapper reads the SPEC as a file, so it enters only after the deriver has recorded
> the transitions finalized (verification PASS) (a conflict-B-only intake has no transitions, so it comes straight in
> without the deriver stage).

## Entry conditions

- `design/STORYBOARD.md` **exists** (this mode updates an existing mapping — unlike promote there is no create branch).
  **When conflict lists (incorporation/cleanup) are delegated, `design/spec-conflicts.md` must also exist** (not required
  for the pure-transition delegation of base change/deletion). If absent, the delegation itself is an error — do not enter; return to the delegating lead.
- **If transition pairs exist**, their results actually exist in `spec/SPEC.md`: for a modification (`old FR → new FR`), the new FR exists as an active row (`^| FR-`) + the old FR is in `[Removed]` state (tag in the source cell); for a deletion (`old FR → (deleted)`), the old FR is in `[Removed]` state (no new FR) — confirm by grep. Otherwise it is an **order violation** (deriver incomplete) — stop entry and return to the delegating lead.
- **When a release list is delegated**, its target rows (SB IDs) actually exist in the `design/STORYBOARD.md` body table, and their mapped FRs remain **active as-is** in `spec/SPEC.md` (an appearance release leaves the SPEC unchanged — a requirement deletion that kills the FR too is not this path but the transition pair `old FR → (deleted)`). A `[Decorative]` row has no FR, so only row existence is checked. Otherwise the delegation input is invalid — do not enter; return to the delegating lead.
- **The delegating lead (develojt-code-changer or develojt-code-builder) explicitly passes** the following (the mapper never guess-matches):
  - **Transition pair list**: modification `old FR ID → new FR ID` / deletion `old FR ID → (deleted)` (conflict-A verdicts or base change/deletion)
  - **Conflict incorporation list** (for conflict-A verdicts): `conflict N · UI ID ↔ new FR ID`
  - **Conflict cleanup list** (for conflict-B verdicts): `conflict N (B — SPEC wins)`
  - **Release list** (for an appearance release): `SB-NN-MM (appearance-release — one-line reason)` — human decision only (a decision the delegating lead had the human confirm at its intake/report; the mapper never picks release targets on its own)

## Core principles

- **The SPEC is read-only — never modified.** The mapper only greps the results the deriver already transitioned (the SPEC's change owner is the deriver — common-rules §0, design-philosophy Axis 4).
- **No negotiation.** The transitions were finalized by the deriver, and the conflict verdicts (A/B) and appearance releases by the human; the mapper only **applies** them (the 2-agent 5-round flow is unnecessary — isomorphic to promote. Pure transitions and releases were also human-confirmed at the delegating lead's gate).
- **The sync is mechanical (exhaustive); no semantic rewriting.** Replace every occurrence of the old FR ID (HTML comments excluded) with the new FR (for a deletion, clean it up per step 2). If a row's description clearly contradicts the new requirement, **do not fix it — flag it as `[Caution]` in the completion report** — mapping content is the product of mapping-mode negotiation and is never rewritten unilaterally (the lead relays it to the human).
- **History goes in HTML comments.** Transition/verdict records (`old FR→new FR`, B decision reasons, …) are kept as `<!-- -->` comments — this is why both verifiers (`verify-stale` and `verify-coverage`) exclude comments, and why old FR IDs must never remain outside comments. FR mentions inside comments never count toward coverage either — coverage comes from body mappings and `[No UI]` classifications only.
- **Never look at the joblist.** The operations phase touches only `spec/SPEC.md` and `design/` (same as promote).
- **File relay.** Read the SPEC (and, on the conflict path, spec-conflicts) as files; write the STORYBOARD (and, on the conflict path, spec-conflicts) as files. The delegating lead's session context is not received.

## Procedure

1. **Delegation input validation** — for each transition pair: for a modification, `grep "{new FR}" spec/SPEC.md` to confirm an active row exists + `grep "{old FR}" spec/SPEC.md` to confirm `[Removed]` state; for a deletion, only the old FR's `[Removed]` state. For the incorporation/cleanup lists, confirm the matching sections (including their anchor table rows) in `design/spec-conflicts.md`. For the release list, confirm each SB ID's row exists in the `design/STORYBOARD.md` body table and its mapped FRs are active in the SPEC (an appearance release leaves the SPEC unchanged — entry condition). [Weaker-model support / required] Never Read the SPEC or screen sources whole — confirm **by grep only**.

2. **Transition sync (every transition pair — conflict-A and base change/deletion alike)** — grep the old FR ID exhaustively in `design/STORYBOARD.md` and find every occurrence (body table mapping cells, the `[No UI]` table, screen headers/notice blocks — **HTML comments excluded**):
   - **Modification (`old → new`)**: replace each occurrence with the new FR ID (full form — common-rules §3).
     - Update the `[No UI]` table's "requirement gist" to the new FR's text (it is a SPEC summary, not a mapping judgment).
     - If a body row's description seems to contradict the new requirement, flag `[Caution]` per the principle above (no rewriting).
     - If the old FR **does not appear** (unrecorded before — 0 replacement targets), enroll the new FR in the Orphan List's `[No UI]` table (isomorphic to promote's new-FR enrollment — restoring the coverage contract; state "was previously unrecorded" in the completion report).
   - **Deletion (`old → (deleted)`)**: clean up each occurrence — if the mapping cell holds other FRs too, remove only that FR (keep the row); if it was that FR alone, **remove the row and leave the history as an HTML comment** (a `[No UI]`-table row likewise — removal + comment history; clean up mentions in screen headers/notice blocks too). This applies a deletion the human explicitly decided, so it is not information loss — history goes in comments (the principle above). The design package originals are never touched.

2-b. **Appearance release (release list — only when present)** — for each SB ID in the list, find its row in the body table (if absent, the delegation input is invalid — write nothing and return to the delegating lead) and **retire** it:
   - Remove the row from the body table and leave the **history as an HTML comment** (`release: SB-NN-MM (FR-…) — reason. This element's appearance baseline is now the human instruction and the implemented code, not the originals`). Clean up mentions of that SB ID in screen headers/notice blocks too.
   - For each FR in that row's Mapped FR cell: if it no longer appears anywhere else in the body (HTML comments excluded), enroll it in the Orphan List's `[No UI]` table as **`appearance-autonomy transition (human-decided release, formerly SB-NN-MM)`** (coverage contract maintained — the FR is alive in the SPEC). If it remains in other rows, do not enroll.
   - A `[Decorative]` row is removal + comment history only (no FR — nothing to enroll).
   - The design package originals are never touched (starting baseline — frozen): the old appearance lives on in the originals and the comment history, the new one in the human instruction and the implemented code (no information loss).

3. **Conflict-A incorporation (incorporation list)** — **move the conflict table row as-is into the `SB-NN` body table** of the screen its visual anchor points at (column correspondence: Design Behavior→Description · Violated SPEC→Mapped FR=**new FR ID**).
   - If the body already has a row with the same UI ID (a partial conflict), **update that row** instead of adding a new one (the Mapped FR was replaced in step 2 — relax the description's restriction wording to match the new requirement).
   - **Anchor re-verification**: grep the source anchor in the screen source and confirm at least 1 hit (if not, correct to a more unique identifier; if nothing can be found, `[No source: reason]`).

4. **Conflict notice refresh + conflict file cleanup (every resolved conflict — A and B alike. Only when conflict lists were delegated — this step doesn't exist for a pure-transition delegation)** —
   - **Refresh the `[Needs review]` (conflict) notice in the affected screen header with the decision result** — A: one incorporation-notice line; B: one line "conflict N decided B (SPEC wins) — {UI ID} has no mapping (implement per the SPEC)". Leave no dead references (to conflict sections about to be removed). Detailed history goes in HTML comments.
   - **Remove the resolved conflict sections** from `design/spec-conflicts.md` (consumed — isomorphic to promote's queue cleanup). Unresolved conflicts stay; if all are resolved, leave only the header.

5. **Update Document Info** — re-tally the STORYBOARD Document Info (screen count, UI element count, FR coverage).

6. **Verify (gate)** — **run the scripts yourself** and confirm PASS (self-reporting forbidden):
   ```bash
   bash <skill path>/scripts/verify-anchors.sh design/STORYBOARD.md design/          # body anchors grep (including incorporated rows)
   bash <skill path>/scripts/verify-anchors.sh design/spec-conflicts.md design/      # if the conflict file exists and conflicts remain, their anchors too
   bash <skill path>/scripts/verify-coverage.sh design/STORYBOARD.md spec/SPEC.md    # are the new FRs covered in the body? (forward)
   bash <skill path>/scripts/verify-stale.sh design/STORYBOARD.md spec/SPEC.md       # 0 lingering old FRs? (reverse)
   ```
   On FAIL, fix and re-run. **Never report completion before PASS** (deliverable guarantee — same as promote).

7. **Completion report (file relay)** — briefly, only the result facts the delegating lead will read: replaced `old FR→new FR` pairs, cleaned-up deleted FRs (removed rows · comment history), released rows (appearance release — SB IDs, and whether a `[No UI]` appearance-autonomy transition was enrolled), enrolled FRs (previously-unrecorded restorations — if any), incorporated `UI ID↔FR`, refreshed screen headers, remaining conflict count, the `[Caution]` list (if any), verification PASS.

## Forbidden

- **Never modify the SPEC** — the deriver's territory (R&R). The mapper only reads by grep.
- **Never touch the joblist** — the spliter's territory. The operations phase doesn't even look at it.
- **Never negotiate** — transitions and verdicts are both finalized. Never spawn the 2 agents (Theorist/Practitioner).
- **Never update anything outside the delegated lists** — apply only the passed transition pairs and incorporation/cleanup/release lists (verdicts belong to the human, transitions to the deriver; the mapper never picks or widens release targets on its own).
- **Never rewrite mapping descriptions unilaterally** — report apparent contradictions as `[Caution]` (mapping content is a negotiation product).
- **Never mint new anchors or switch to coordinates/volatile indexes** — reuse the conflict table's anchors as-is (common-rules §2).
- **Never leave old FR IDs outside HTML comments** — history in comments; body, tables, and headers carry active FRs only (`verify-stale` catches it).
- **Never report completion without verification PASS** — the deliverable guarantee comes first (so code never starts on a stale mapping).
