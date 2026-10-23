# Structure-Contract Lifecycle — mid-project adoption · top-down revision · full migration (via human instruction)

The **single truth** for the procedures that establish (adoption), change (revision), and physically migrate
existing code under (`migration`) the structure contract `spec/ARCHITECTURE.md` **on a human instruction**. A new
project's contract creation (builder workflow 1 — the first-report draft) and mid-work encounter revisions
(builder 'when a design change is needed' · the structure rules in changer revise/delegate — bottom-up) stay
exactly as they are; this document does not change them — it only adds the survey/report/execution procedures
for the cases **whose entrance is an instruction** (top-down).

- **Performed by the lead directly** (no subagent delegation — the contract's write rules were always the
  lead's job: identical to the existing builder/changer revision rules). In the development phase (joblist in
  progress) the **develojt-code-builder** lead follows this document (the routing in the report & approval
  gate); in the operations phase (after development completes) the **develojt-code-changer** lead does
  (intake classification 'code-only' → the 'structure-instruction input' section).
- **When to load**: only when a lifecycle instruction arrives (the screen-review-session.md convention).
- Never copy these procedures outside this document (single truth — when the original changes, both skills
  automatically follow the latest).

## Common principles (closed — non-negotiable)

- **AI designs; the human finalizes.** Before human finalization, never write `spec/ARCHITECTURE.md`
  (neither creation nor modification).
- **After finalization, record the finalized content verbatim** — no unilateral rewriting, embellishment, or
  summarizing. Revision-history rows are never deleted.
- **Make things visible, but never act automatically.** Printing the contract's absence or a revision need
  goes only as far as one line in a report — execution goes only through a human instruction.
- **The failure direction goes to a question.** When the instruction is ambiguous or the entry determination
  could go either way, don't proceed — ask (no silent interpretation).
- **[Weaker-model support / required] Survey by machine sight only.** The command list stated in each
  procedure is the entire survey net — never read `src/` whole (folder tree, symbol inventory, and sample
  greps only; never try to grasp the full picture by Reading file contents).
- Contract sentences follow the template shape (`templates/ARCHITECTURE-template.md`) — machine-checkable
  invariants with concrete paths and directions only. A wish sentence like "keep coupling low" is not a
  contract.

## Entry determination (deterministic)

| Entrance | Entry condition (machine check) | Instruction signals (examples) |
|---|---|---|
| **Adoption** | `ls spec/ARCHITECTURE.md` absent + `ls src/` present | "set up the structure contract (architecture)" |
| **Revision** | `spec/ARCHITECTURE.md` present + an instruction changing a structural decision itself | "change layer X to Y", "let's improve the structure" |
| **Migration** | A revision-history row with application scope `full migration` exists (grep) + an instruction to run the migration | "run the structure migration" |

- An adoption instruction when a contract already exists → point to revision and ask what to change. A
  revision instruction with no contract → explain adoption comes first and ask whether to enter the adoption
  procedure. A migration instruction with no `full migration` history row → don't proceed; explain (revision
  finalization comes first). A new project's (no src/) "set it up" is not this document — builder workflow 1
  (the first-report draft) is that place.
- Code cleanup/refactoring instructions (the contract is only a compliance constraint and does not change)
  are not this document — that is changer T1/T5 (revise). The fork is whether the contract changes; when
  ambiguous, ask.

## Adoption procedure (establishing the contract on an existing project — src/ present, no contract)

1. **As-is survey (SPEC in full + machine sight — this list is the whole net)**:
   First read `spec/SPEC.md` **in full** (same baseline as new-project drafting — builder workflow 1: the
   contract is a one-time deliverable setting the whole-life structural baseline, so its input is the full
   body of requirements. While reading, extract the material — Document Info's tech stack & runtime
   environment · EP composition & summary statistics · the NFR section (cross-cutting concerns) · external
   integration/storage FRs (system boundaries) · the behavior chain tables. **The common principles'
   no-whole-reads rule targets `src/` — the full SPEC read is part of the survey named in this procedure**).
   Then:
   ```bash
   find src -type d | sort                            # the real folder tree = current layer candidates
   python3 .claude/skills/develojt-code-pdca/scripts/verify_enforced_rules.py src/ --inventory   # per-file top-level symbols (global install: ~/.claude/skills/...)
   ```
   If `spec/joblist.md` exists, also check its checked/unchecked state (development-phase status and
   implemented scale). Confirm dependency directions by sample grep — import/require/using declaration lines
   only (e.g., `grep -rn "^import\|require(" src/{folder} | head -20`); never read files whole.
2. **Compose the draft** — in the exact 4-section shape of `templates/ARCHITECTURE-template.md` (layer map ·
   dependency directions · placement rules · revision history). **The draft's default is the current
   majority structure** (start from as-is — turn the real folders and directions visible in the survey
   output into rule sentences. Never make an idealized redesign the default). Fill §3 placement rules'
   cross-cutting-concern and external-integration rows from the step-1 SPEC material (NFRs · integration
   FRs) — the places of requirements not yet in the current code (unchecked bundles) are also material the
   contract settles first. Putting a rule that differs
   from the current code (to-be) is allowed but cannot be hidden — existing code will violate it, so it
   necessarily surfaces in the mismatch table of step 3, and adoption of it is the human's decision.
3. **Build the mismatch table** — for each draft rule, list where the current code deviates, out of the
   step-1 survey output (file/folder/symbol granularity — no guessing beyond the survey). Propose exactly one
   treatment per row — **a closed three-way choice; inventing outside it is forbidden**:
   - `accept as-is` — fix the contract side to match reality (reality becomes the baseline)
   - `from new code onward` — the contract keeps the rule; existing code coexists under the old structure
     (it stays in the revision history, so it is **recorded coexistence** — unrecorded coexistence is the rot)
   - `full migration` — move the existing code to match the contract (the migration work itself is separate —
     the migration procedure below; not this scope)
   If there is no mismatch, state "no mismatches" explicitly.
4. **Report → human finalization** — fixed format (the human-decision sentence rules apply):
   ```
   ## Structure-contract adoption report (project started on older skills — mid-project adoption)
   [full contract draft — the template's 4 sections]
   ### Draft grounds (report-only — never recorded into the contract file)
   | Draft row (layer/rule) | Grounds (requiring SPEC ID group · current folder) |
   |---|---|
   ### Mismatch table
   | # | Draft rule | Current code (file/symbol) | Proposed treatment |
   |---|---|---|---|
   To decide: ① whether to finalize the contract draft (edit instructions welcome) ② the treatment of each
   mismatch row (as proposed, or changed).
   Once finalized it is recorded as spec/ARCHITECTURE.md and every later code work follows this baseline.
   ```
   No writes before finalization. If edit instructions arrive, apply and re-report (until finalized).
5. **Record after finalization** — create `spec/ARCHITECTURE.md` with the finalized content verbatim.
   Fold `accept as-is` rows into the contract body, and leave the adoption in the first revision-history row
   (the mismatch-treatment summary in the application-scope cell — the `from new code onward` items are
   themselves the record of the recorded coexistence):
   ```
   | {date} | Mid-project adoption — contract established | Project started on older skills (human instruction) | from new code onward: {rules}… · full migration: {rules}… (separate intake) — or "no mismatches" | {approval} |
   ```
   The places/directions of code coexisting under `from new code onward` are **also enrolled in the
   contract tables as they actually exist** — annotate the layer-map/Allowed rows with `(coexistence — revision history, adoption
   row)` (recorded coexistence becomes a record the machine check C4 also reads — unenrolled coexistence
   keeps printing as violation candidates; template §1·§2 grammar).
   Immediately re-confirm by grep (write-application check — one history row), then run the violation
   candidate detector once and confirm its candidate list corresponds to the mismatch table —
   `python3 .claude/skills/develojt-code-pdca/scripts/verify_architecture.py src/`
   (global installs: `~/.claude/skills/...`). A candidate outside the table means a survey omission —
   report it to the human (0 code changes stays invariant — this run is a machine cross-check of the
   mismatch table, not judgment or repair). If ⚠️ rows print, those contract sentences are notation the
   machine cannot read — keep the finalized content verbatim and fix **only the notation** into the
   template's machine-readable grammar (§1·§2), re-running until ⚠️ 0 (if resolution would require a
   content change, re-report to the human).
6. **Afterwards** — this invocation's scope ends here (0 code changes — no pdca entry. Bundle implementation
   is a separate scope with the normal gates). From the next bundle on, the existing compliance mechanisms
   (bundle-start ritual re-reads · essentials 3·4) operate automatically. Executing the `full migration`
   items is a separate human instruction (the migration procedure below).

## Revision procedure (top-down — the human instructs a structural change itself)

1. **Absorb the instruction** — what → what. Read the contract in full (a small norm document) and confirm by
   grep that the target rule actually exists in it. If ambiguous, or several decisions are mixed, don't
   proceed — ask (split to one decision per sentence).
2. **Impact survey (machine sight only)** — list the current code that the changing rule touches. The
   commands are the same as adoption step 1 (`--inventory`, folder tree, sample greps — scoped to the target
   rule).
3. **Revision proposal → human finalization** — fixed format: **what → what · reason (quoting the human
   instruction) · proposed application scope (`from new code onward` / `full migration` — a closed two-way
   choice, inventing outside it is forbidden) · impact summary (the N touched code sites, listed)**. No
   writes before finalization.
4. **Record after finalization** — add one row to the revision history + edit the body (history rows are
   never deleted — the existing revision rules as-is). Immediately re-confirm by grep, and run one grammar
   check — `python3 .claude/skills/develojt-code-pdca/scripts/verify_architecture.py spec/ARCHITECTURE.md`
   (contract parsing only — if ⚠️ prints, keep the finalized content and fix only the notation into the
   machine-readable grammar until ⚠️ 0; re-report if a content change would be required). 0 code changes (no
   pdca). If the application scope is `full migration`, running the migration is a separate instruction (the
   procedure below — not this scope). If the application scope is `from new code onward`, enroll the old
   code's places/directions as coexistence rows in the contract tables — annotated `(coexistence — revision
   history #N)` (the same grammar as adoption step 5 — recorded coexistence becomes a record the machine
   check C4 also reads).

> A mid-work encounter (discovering during implementation/fixes that code has no place in the contract) is
> not this procedure — it stays under the existing rules of builder 'when a design change is needed' and
> changer revise/delegate (the same revision rules, the same record format — this document only adds the
> survey/report stages for the top-down entrance).

## Migration procedure (executing a finalized `full migration` revision — the only procedure where code moves)

**Precondition (machine check)**: a revision-history row with application scope `full migration` exists
(grep), and the human instructed the migration run. Otherwise don't proceed (revision finalization comes
first). Migration is a **behavior-invariant code move** — never touch the SPEC, `design/`, or the STORYBOARD
(if requirement or appearance changes are mixed in, split them out to their own paths as separate intakes).

1. **List the targets (machine — this list is the work scope)** — enumerate all code still under the old
   structure. Derive the commands from the revision row's "what → what" (e.g., for a `src/utils/ →
   src/core/` revision: `find src/utils -type f` · `grep -rln "utils/" src/`). **Never touch code outside
   the list** (the same principle as reinforcement mode — no opportunistic cleanup along the way).
2. **Staging plan report → human confirmation** — split the list into batches (folder/layer granularity —
   one batch is one verification cycle; a cut that severs no chain). Report the batch order and each batch's
   target list and get confirmation (the same grammar as the scope-approval gate). The report **states the
   regression-net status in one line** — if an executable regression check exists (the project's tests or
   run scripts), name it; if none exists, state that "this migration's behavioral regressions are outside
   the static gates" (no blocking — approving with that knowledge is the gate; behavior judgment itself
   stays outside the pipeline, invariant). No writes before confirmation.
3. **Per batch** — move and rewire → `@spec` tags travel with their declarations (the '@spec relocation
   rules' in changer `references/revise-mode.md` are the single truth — no loss, duplication, or orphans) →
   re-run the gates:
   ```bash
   SKILL=.claude/skills/develojt-code-builder        # global install: ~/.claude/skills/develojt-code-builder
   python3 $SKILL/scripts/verify_refs.py src/
   python3 $SKILL/scripts/verify_todo.py src/
   python3 $SKILL/scripts/verify_spec_coverage.py src/ spec/SPEC.md
   python3 $SKILL/scripts/verify_comments.py src/
   python3 .claude/skills/develojt-code-pdca/scripts/verify_security.py src/ --root-config
   python3 .claude/skills/develojt-code-pdca/scripts/verify_enforced_rules.py src/
   python3 .claude/skills/develojt-code-pdca/scripts/verify_architecture.py src/   # is the migration result free of new-contract violations — the C4 candidate detector
   ```
   **No next batch before PASS.** On FAIL, fix and re-run; if it won't resolve within the batch, stop and
   report to the human (no silent workarounds, no gaming edits — verification is a mirror, not a burden).
4. **Zero-remnant check** — re-run the step-1 commands and print that the old locations/directions return 0
   hits, and print verify_architecture.py's 0 candidates alongside (migration completion = the machine proof
   of zero new-contract violations). If anything remains, report why and wait for the human decision (no
   silent remnants).
5. **Completion report** — the move list (from → to), per-batch gate PASS, and the zero-remnant result. If
   the machine floor (verify_security · verify_enforced_rules · verify_architecture) produced even one candidate, a
   develojt-code-pdca recheck is mandatory (the verdict belongs to the checker — no self-grading by the
   lead; the same rule as changer revise-mode). Never judge behavior (essential 5 — outside the pipeline).

## Forbidden (closed list)

- **Never adopt or revise automatically without an instruction** — visibility of absence/need goes only as
  far as one report line.
- **Never write `spec/ARCHITECTURE.md` before human finalization** (neither creation nor modification).
  **Never delete revision-history rows.**
- **Never invent mismatch treatments outside the three choices, or application scopes outside the two.**
- **In migration, never touch code outside the target list. Never change the SPEC, `design/`, or the
  STORYBOARD during migration.**
- **[Weaker-model support / required] Never read `src/` whole** — the survey net is exactly the commands
  stated in each procedure.
- **Never write wish sentences into the contract** — machine-checkable sentences with concrete paths and
  directions only (the template shape).
