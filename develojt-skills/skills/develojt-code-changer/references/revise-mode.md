# Review-Fix Mode (revise) — fixing code by applying review comments/refactoring (requirements invariant)

The path that fixes **only the code, keeping the requirements as-is**, on already-implemented and reviewed code (the opposite of new implementation).
The input is code review comments, static defects, and human instructions for appearance changes, and develojt-code-builder's five essentials (@spec, wiring, constraints, leanness, separation) apply as-is.

This mode handles only the **four requirement-invariant kinds**:

| Kind | What | SPEC impact | Input |
|---|---|---|---|
| **T1 code quality** | Naming, duplication, structure cleanup | None | Review comments + `.claude/rules/` |
| **T5 refactoring** | Structural improvement with requirements/behavior invariant | None | Review comments |
| **Appearance change** | Applying a human instruction for an appearance different from the design/ originals | None (appearance is not the SPEC) | Human instruction (+ if a mapping row hits, the release in the 'appearance-instruction input' section comes first) |
| **Structure instruction** | Mid-project adoption · revision · migration of the structure contract (`spec/ARCHITECTURE.md`) | None (the contract is not the SPEC — the code-organization baseline) | Human instruction (the 'structure-instruction input' section — the procedure lives in builder `references/architecture-lifecycle.md`) |

> **If the requirement must change, this is not the mode.** Meaning-changing modifications/deletions are classification 'change/deletion', new requirement additions are classification 'addition' →
> go to **delegation mode (`delegate-mode.md`)** (the SPEC's change owner is the deriver — R1). The lead spawns a subagent that
> transitions the SPEC via the deriver procedures, then builds the resulting IDs into code with the builder's five essentials (operations phase — SPEC only, no joblist).

## Entry conditions

- `spec/SPEC.md` and `src/` already exist (post-implementation, post-review).
- Entered under intake classification **code-only** (including `--review <instruction>`-form input). The input is review comments, refactoring requests, appearance-change instructions, and structure-contract instructions (T1, T5, appearance change, structure instruction).

## Core principles

- **Requirements don't change.** Never touch SPEC FR texts, IDs, or behavior chains (if they must change, delegate under the 'change/deletion' classification).
- **Only what was flagged.** This is reinforcement mode — fix only the flagged parts and leave healthy code alone (identical to the reinforcement rule of develojt-code-builder workflow 6).
- **No self-grading (essential 5).** Never judge whether the code runs as intended *by executing it* — this path goes as far as code edits and self-checks (existence/format) (behavior judgment is outside the pipeline. The boot gate is not a behavior judgment but a deterministic check of the releasable state — the same family as the builder's self-checks, an explicit exception under philosophy Axis 6).

## `@spec` relocation rules (the heart of T5 refactoring — P4)

When refactoring changes declarations, the traceability chain easily scatters, duplicates, or vanishes. There is one rule:

> **`@spec` tags move with the declarations that implement the requirement. One ID attaches, across the whole ledger, exactly to the declaration(s) implementing that requirement.**

| Refactoring | `@spec` handling |
|---|---|
| Function **split** (one→many) | The tag follows the side(s) actually implementing the requirement. If the requirement spans several new declarations, tag them all (essential 1) |
| Function **merge** (many→one) | Gather the related tags on the merged declaration — **without duplicates** (never tag the same ID twice) |
| Function **move/rename** | Move the tag above the new declaration (leave no empty/ghost tags at the old location) |
| Code **deletion** (dead code) | Remove that declaration's `@spec` too — but if the ID is alive in the SPEC, another implementing declaration must exist (coverage forces it) |

**Loss** (untagged declarations → `verify_refs`), **duplication** (the same ID within one declaration → `verify_refs`), and **orphans** (references to `[Removed]`/absent IDs → `verify_spec_coverage`) are caught by the gates — they must PASS after relocation.

But **semantic scattering — sprinkling the same ID over several unrelated declarations — is a gate blind spot**: indistinguishable from legitimate multi-tagging (one requirement spanning several declarations, essential 1), it looks PASS to set-based coverage. Here **the model directly guarantees** the rule above (one ID = only that requirement's implementing declarations) (see Forbidden).

## Procedure

1. **Absorb the input** — read the received review comments:
   - Grasp what to fix and why. If `.claude/rules/` exists, follow its standards.
   - Never read the target code whole — only the parts to fix and their adjacent signatures (grep first). For same-**series** items, follow the reference implementation's approach.

2. **Impact check (recommended)** — if target FRs exist, see the peers to examine together via **the SPEC's behavior chains** (operations phase — the joblist is not consulted, lifecycle over):
   ```bash
   python3 .claude/skills/develojt-spec-deriver/scripts/query_chain.py {target FR} spec/SPEC.md
   ```
   Series is checkable only when a deriver increment left sibling notation in the SPEC (full-generation SPECs carry no series notation).
   When the notation exists — fixing a series' *reference implementation* can skew the whole series, so inspect the same spot in those peers together (aligned with pdca S1).

3. **Fix (the five essentials)** —
   - **T1 quality · T5 refactoring**: clean up the structure per `.claude/rules/`. Behavior invariant. Move `@spec` tags with their declarations per the relocation rules above.
   - If `spec/ARCHITECTURE.md` (the structure contract) exists, also comply with its structural decisions (layers, dependency directions, placement — the same contract as builder essentials 3·4; read it in full before fixing). If the fix is possible only by changing the contract, **unilateral revision is forbidden** — get the revision proposal (what → what · reason · application scope) finalized by the human, record one revision-history line, then proceed (the same rule as the builder's 'when a design change is needed' structure paragraph). Without a contract this item does not exist (as before).
   - Never touch anything outside the flags (reinforcement mode).

4. **Self-check (existence & format only)** — re-run the builder's 4 gates plus the 3 machine floor checks. The 4 gates must PASS after relocation/fixes too:
   ```bash
   SKILL=.claude/skills/develojt-code-builder        # global install: ~/.claude/skills/develojt-code-builder
   python3 $SKILL/scripts/verify_refs.py src/
   python3 $SKILL/scripts/verify_todo.py src/
   python3 $SKILL/scripts/verify_spec_coverage.py src/ spec/SPEC.md
   python3 $SKILL/scripts/verify_comments.py src/
   python3 .claude/skills/develojt-code-pdca/scripts/verify_security.py src/ --root-config   # machine floor — security candidate detection (including config-type files, the root .env, etc.; reusing pdca C2's detector; global install: ~/.claude/skills/...)
   python3 .claude/skills/develojt-code-pdca/scripts/verify_enforced_rules.py src/   # machine floor — enforced-rule violation candidate detection (reusing pdca C3's detector; not applicable without .claude/rules/enforced-rules.md)
   python3 .claude/skills/develojt-code-pdca/scripts/verify_architecture.py src/   # machine floor — structure-contract violation candidate detection (reusing pdca C4's detector; not applicable without spec/ARCHITECTURE.md)
   python3 $SKILL/scripts/verify_boot.py spec/run-profile.md   # boot gate — confirming the releasable invariant still holds (reusing the builder's self-check — not applicable without a profile. Even after an operations change, "it builds and it boots" must not break)
   ```
   The lead never judges verify_security candidates — if even one appears, the step 6 pdca re-entry is mandatory (judgment belongs to the checker's C2 procedure — no self-grading). verify_enforced_rules candidates are treated the same (judgment belongs to the checker's C3 procedure). verify_architecture candidates are treated the same (judgment belongs to the checker's C4 procedure — ⚠️ lines are not candidates but contract-grammar maintenance material; carry them in the report only). verify_boot's FAIL and exit 2 are handled exactly by builder workflow 5's boot-gate rules (reinforce only the defects that block booting; if it is an environmental factor, stop and report; for a grammar error, only fix the notation — never alter the profile to pass the gate).

5. **Report (no judgment)** — report what was fixed and where, and if `@spec` relocation happened, which IDs moved where.
   - Behavior-invariant refactoring and quality cleanups are traced by git history (no separate ledger — the minimal design).

6. **Static-completeness recheck (when applicable)** — **mandatory if step 4's machine floor (verify_security·verify_enforced_rules·verify_architecture) produced even one candidate**; otherwise, if the fixes affect bundle completeness (omissions, wiring), re-enter develojt-code-pdca to re-confirm static quiescence (scope: the target FR ID list — C2·C3·C4 scan all of src/ on re-entry).

## Appearance-instruction input — mapping-release integration (requirement-invariant appearance change)

Follow this section when the intake input instructs an **appearance different from the design/ originals** (function invariant — SPEC unchanged). If `design/STORYBOARD.md` is absent, or the target element hits no body mapping row (an appearance-autonomous element), this section doesn't exist — only the existing procedure runs (**side effect 0**).
**The design/ originals are the project's starting baseline and stay frozen — there is no path that edits them.** The human's deviation decision must be recorded as a **release**, or the stale mapping row keeps instructing the next worker to restore the old appearance (an unrecorded deviation = silent deviation, forbidden).

> Flow: list & confirm the release targets (intake) → delegate the mapper remap release → gate → code (per the instruction).

**Only the differences added onto the existing procedure:**

1. **Added to step 1 — list & confirm the release targets** — the lead greps the STORYBOARD (by target FR ID, screen name, element description) and **lists** the body mapping rows (SB IDs) the instruction points at, then states in the intake report: "this instruction departs from the design originals — it will be recorded as a release (from then on that element's appearance baseline is this instruction and the implemented code, not the originals)" (the human confirmation is taken by the intake gate — that confirmation is the release decision). If the instruction could also be read as staying within the originals, ask the human (the failure direction goes to a question, not to silent deviation).

2. **Step inserted before step 3 — delegate the mapper remap release** — reuse the mapper procedure **as a subagent** (not a skill invocation — the same pattern as delegate-mode; the lead never writes the STORYBOARD in its place):
   - Procedure path: `.claude/skills/develojt-design-mapper/references/remap-mode.md` + `common-rules.md` (local first — on global installs, `~/.claude/skills/develojt-design-mapper/references/...`).
   - Target: `design/STORYBOARD.md` only. In the instruction, **explicitly pass the release list (`SB-NN-MM (appearance-release — one-line reason)`)** (no guess-matching — remap step 2-b: row retirement + comment history + `[No UI]` appearance-autonomy transition enrollment).
   - **Gate**: until the mapper verifications (`verify-anchors` · `verify-coverage` · `verify-stale`) PASS. Otherwise re-spawn once with the same instruction; on repeat failure, report to the human and stop (code never starts on an unverified STORYBOARD).

3. **Then steps 3–6 as-is** — fix the code per the instruction (the five essentials — a released element's appearance baseline is the human instruction, not the originals. The completion report's screen-check request also compares against the instruction, not the originals).

> **Forbidden in this branch**: never change a mapped element's appearance away from the originals without the release (silent deviation — the next worker follows the anchor and reverts it). The lead never writes the STORYBOARD directly (mapper procedure only — R&R).

## Structure-instruction input — contract mid-project adoption · revision · migration (requirements invariant — the contract is the target)

When the intake input targets **the structure contract itself**, not code ("set up the structure contract
(architecture)" = mid-project adoption · "change the structure to …" = revision · "run the structure
migration" = executing a finalized `full migration` revision), follow this section. The **single truth of the
procedure is builder `references/architecture-lifecycle.md`** (local first — global install:
`~/.claude/skills/develojt-code-builder/references/architecture-lifecycle.md`) — the lead follows that
document's entry determination and matching procedure **directly, as-is** (no copying, no subagent
delegation: the contract's write rules were always the lead's job — the same grammar as the revision rule in
step 3. Writing happens only ever after human finalization).

**Relation to the existing procedure (closed rules):**

1. **The intake-gate confirmation = the approval to enter the procedure** — it confirms classification and
   target (adoption/revision/migration), not content. The finalization gates inside the lifecycle document
   (human finalization of the adoption draft + mismatch table, the revision proposal, the migration staging plan) are
   **passed as written** (not a double gate — the layers differ).
2. **Adoption and revision change no code** (only the contract document is created/edited) — step 4's gates
   & machine floor and step 6's pdca recheck do not apply, as there is no code change.
3. **Migration moves code** — the lifecycle document's migration procedure includes re-running the gates per
   batch (the builder 4 + the 3 machine-floor detectors), and the existing rule stands unchanged: even one
   machine-floor candidate makes the pdca recheck mandatory (the verdict belongs to the checker — no
   self-grading).
4. **Distinction from T5** — in T5 the code is the target and the contract is a compliance constraint (the
   contract does not change). In a structure instruction the contract is the target, and code moves only in
   the migration procedure. When it is ambiguous whether an instruction is code cleanup or a contract
   change, ask at intake (no silent ruling).

## Forbidden

- **Never change the SPEC** (requirement changes/deletions go through deriver delegation under the 'change/deletion' classification — R1).
- **Never judge behavioral correctness by executing** (essential 5 — behavior judgment is outside the pipeline).
- **Never touch code outside the flags** (reinforcement mode — healthy parts invariant).
- **Never scatter, duplicate, or lose `@spec` tags** (the relocation rules — one ID = only that requirement's implementing declarations).
- **Never lump a structure instruction under T1/T5** — when the instruction changes the contract, it is the 'structure-instruction input' section (the lifecycle procedure · human finalization).
