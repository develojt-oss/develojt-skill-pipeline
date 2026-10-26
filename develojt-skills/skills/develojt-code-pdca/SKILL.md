---
name: develojt-code-pdca
description: >
  The inspect-and-reinforce loop (PDCA) that is the body of the development cycle. It auto-enters
  whenever develojt-code-builder finishes implementing a bundle, and finds and completes
  "things that should have been done but weren't" (missing requirements, missing wiring, missing comments, empty implementations).
  It also detects machine-detectable violations of the global security rules (C2).
  Machine-detectable violations of the enforced-rules table (rules/enforced-rules.md — if present) are detected the same way (C3).
  Machine-detectable violations of the structure contract (spec/ARCHITECTURE.md — if present) are detected the same way (C4).
  It is not runtime behavioral integrity verification (E2E, execution tests) — inspection is static.
  It auto-repeats cycles until quiescence (2 consecutive defect-free cycles) is reached (no approvals between cycles).
  Standalone execution forbidden — invoked only from develojt-code-builder's workflow (right after bundle
  implementation, or re-entry on unresolved defects) and develojt-code-changer's operations-change rechecks.
  If the user invokes this skill directly, do no work and guide: "proceed via develojt-code-builder (develojt-code-changer for operations changes)".
  The Lead runs Plan and Act; the isolated checker agent (develojt-code-pdca-checker) runs Check.
  Deliverables: spec/findings.md (defect ledger — resolved rows and past cycle-log rows are archived to and preserved in spec/findings-archive.md) + reinforced src/.
argument-hint: "[passed by builder/develojt-code-changer: inspection scope — Bundle N | FR-XX | re-entry (only these three forms; EPs are converted to FR IDs by the builder)]"
---

# develojt-code-pdca — static-completeness loop (the body of the dev cycle · builder/develojt-code-changer transit only)

Inspection scope passed by the invoking skill (builder/develojt-code-changer): $ARGUMENTS

**[Required] Human-facing sentences:** Every output shown to a human — reports, explanations, questions, approval requests, and the like — follows `rules/human-language.md`; sentences that ask for a decision follow its §2 (the human-decision sentence rule).

## Position in the pipeline

```
[planner]    plan/PRD.md      — human-led. AI provides hints (seeds)
[deriver]    spec/SPEC.md     — epics concretized into EARS (source of truth = this skill's scoresheet)
[spliter]    spec/joblist.md  — progress ledger
[builder]    src/             — implementation (Do). The single front door for all code work
[this skill] spec/findings.md — the static-completeness loop (Check·Act) auto-entered after each implementation. Quiescence defines bundle completion (appearance-comparison target bundles: the builder finalizes completion with screen-review ledger registration & the human's registration confirmation on top — the comparison itself runs in builder's screen-comparison session after full implementation completion)
```

**This loop is the body of the development cycle.** The builder's implementation (Do) is this loop's input,
and a bundle meets its completion criterion only when quiescence (2 consecutive defect-free cycles) is reached
(for appearance-comparison target bundles, the builder finalizes completion only after also receiving screen-review ledger registration and the human's registration confirmation; the comparison itself runs in builder's screen-comparison session after full implementation completion — appearance is not an inspection axis of this loop, and this loop never reads the ledger (spec/screen-review.md)).
What this skill completes is **"things that should have been done but weren't"** — missing requirements, missing wiring, missing comments, empty implementations.
On top of that, it detects machine-detectable violations of the global security rules (C2 — "things that should not have been done").
General convention compliance remains the builder's (at generation) and develojt-code-changer's (review application) responsibility (R&R) — C2 is only the security subset that has substance (a script + a procedure).
Machine-detectable violations of the **enforced rules** (the enforced-rules table in `.claude/rules/enforced-rules.md` — if present) are **C3**, a subset admitted through the same door as C2 —
candidates come from verify_enforced_rules.py, judgment belongs to the checker. Only what the table declares as scan/pattern is covered (conventions outside the table remain the builder's responsibility),
and a project without the rules file has no C3 at all (behavior unchanged).
Machine-detectable violations of the **structure contract** (`spec/ARCHITECTURE.md` — if present; the human-finalized layer/direction baseline) are **C4**, a subset admitted through the same door —
**the contract itself is the rules table**, so there is no separate rules file; candidates come from verify_architecture.py (only cross-layer references in directions not allowed and folders absent
from the layer map), judgment belongs to the checker. The contract's §3 placement prose and interface quality are out of scope (no design nitpicking — freedom inside the contract stays the
builder's autonomy), and a project without the contract file has no C4 at all (behavior unchanged).
Runtime behavior judgment (E2E, execution tests, live demos) is not done — that is outside the pipeline.

## Invocation rules (forced)

- **This skill is invoked only from develojt-code-builder's or develojt-code-changer's flow.** On direct user invocation, do no work and guide:
  "This skill runs via develojt-code-builder (develojt-code-changer for operations-change rechecks)."
- The absence of `disable-model-invocation` in the frontmatter is **intentional (not an omission)** — builder/develojt-code-changer
  must enter via model invocation mid-flow. Defense against direct user requests is handled by the guidance rule above.
- The checker agent (`develojt-code-pdca-checker`) is also spawned only in this skill's Check stage.
- Stop if `spec/SPEC.md` or `src/` is missing — earlier stages come first. `spec/joblist.md` is an **input used when present** (the basis for bundle/series/deferral judgments) —
  when absent (builder EP-unit development), the scope arrives as an FR ID list, and every joblist-reading point (Plan 4·5 / S1 / checker calibration) follows its own 'no joblist' branch.
- **The received scope format is only these three: `Bundle N | FR-XX | re-entry`.** EP-unit work is converted by the builder
  to that EP's FR ID list before passing (the same contract is stated on the builder side).
- **There are no approvals between cycles.** On builder/develojt-code-changer transit invocation, print the plan and result reports but proceed
  immediately without waiting for approval (reports are records for visibility). The only points needing human decisions are
  `Needs review` questions, escalations, and process-improvement approvals — and even those ride in the reports and await the answer without stopping the loop.

## The three rules (this skill's essence)

1. **State lives in the file.** Every bit of loop state is written to `spec/findings.md`. The next session reads only this file and continues. Never rely on memory.
   Resolved rows and the cycle log's rows beyond the latest 5 are archived at the Record stage into `spec/findings-archive.md` (the resolved-history ledger) — the ledger keeps only active rows (unresolved, Needs review, Rejected) and the latest cycle log, so per-cycle reading never grows with progress.
   Rejection verdicts on C2, C3, C4 **candidates** are written to `spec/findings-rejected.md` (the candidate-rejection ledger) — not a ledger the loop reads, but one the 3 detectors read so they never print the same candidate again (only recorded verdicts are inherited — unrecorded verdicts are not).
2. **The ledger comes first.** Verdicts on findings and fixes may be wrong (the next cycle catches them again). Ledger records must not be wrong. Run the verification script every time you record.
3. **The same mistake three times proposes a rule.** When 3 defects of the same type accumulate, write one line in "Process Improvement Proposals" for a rule that would block that class. Propose only — skill modifications are approved by a human (directly editing the project's `.claude/` copies — skills, rules, the enforced-rules table — is also a skill modification: they are deployed copies, and re-initialization overwrites them with the originals, losing the edit. The human applies changes to the originals in the pipeline repository — the declaration at the top of `code-conventions.md`).

## Roles (never mix them)

| Role | Does | Must not do |
|---|---|---|
| **Lead** (the executor of this skill) | Plan (set scope) · Act (fix code) · ledger recording | Judging defects itself (the checker's job) |
| **Checker** (`develojt-code-pdca-checker`) | Check (finding defects, re-verification) only | Fixing code, inventing requirements |
| **Human** | [Needs review] decisions · escalation responses · process-improvement approvals | Approving cycle progression (the loop is automatic) |

The checker receives **only the scope and the existing defect ID list**. The Lead's implementation intent and conversation are never given.
(Reason: a checker that knows the intent reads the code as intended, and the inspection loses its value.)

---

## Cycle procedure (one cycle = 1→5. Auto-repeat until quiescence — never stop between cycles)

### 0. Ledger check

- If `spec/findings.md` doesn't exist → create it by copying `templates/findings-template.md` (cycle 0).
  For projects without a joblist, after copying, change the header's 'Base joblist' cell to `—`.
- If it exists → read it. The cycle number and unresolved defects are the current position.
- `spec/findings-archive.md` (the resolved-history ledger) is **never read** — archival is a context-saving device. All active state lives
  in findings.md; numbering is covered by the header's 'Last F-number', and type tallies by the verification script's output.

### 1. Plan — set the scope (in this order, first applicable item)

1. If `Awaiting recheck` defects exist → those rows (re-verification always comes first)
2. If `New`/`Fixing` defects exist → skip Check and go to Act (step 3)
3. The scope passed by the invoking skill (builder/develojt-code-changer) (Bundle N / FR-XX)
4. Bundles whose code changed since the last cycle — the judgment basis is the ledger record only: bundles containing
   `src/` files updated later than the latest cycle-log row's date. If there is no joblist or this comparison can't decide, skip 4 and go to 5
5. Bundles never inspected (joblist order, 1–2 bundles per cycle. Without a joblist this doesn't apply — the scope is only step 3's passed FR list)

- When 1 and 2 both apply → do re-verification (1) first, then continue Acting on `New`/`Fixing` in the same cycle.
- If an unimplemented (`[ ]`) bundle is caught from the joblist → stop and report: "Bundle N is unimplemented — builder implementation comes first."
- With nothing to inspect and nothing to reinforce → go to step 5's quiescence verdict.

**Proceed immediately after reporting**: print the following and go straight to step 2 (Check) without waiting for approval. Reports are records for visibility.

```
## PDCA cycle {N} plan

| Item | Content |
|---|---|
| Unresolved defects | {list or none} |
| This scope | {…} |
```

### 2. Check — spawn the checker

Spawn the `develojt-code-pdca-checker` agent. Put only this in the prompt:

```
1. This scope (recheck row list / target bundle·FR IDs)
2. The ledger's existing defect ID + symptom list (to prevent duplicate reports)
3. The inspection lens — one line, "Lens A" or "Lens B"
4. "Read .claude/skills/develojt-code-pdca/references/checker-rules.md first and inspect by that procedure"
```

**Lens selection (deterministic):** if the cycle log's latest row for this same scope has 0 new
(a recheck for the quiescence verdict) → **Lens B**; otherwise (first inspection, post-fix inspection) → **Lens A**.
Recheck rows (`Awaiting recheck`) are judged by checker-rules' re-verification procedure regardless of lens.
(Reason: rechecking by reading with the same lens twice repeats the same trial, so it can't be quiescence's second basis —
Lens B reads in reverse, starting from SPEC sentences and arriving at the code, making the two cycles independent trials.)
If the same scope's previous row has been archived out of the ledger, that is 'otherwise' — start with Lens A, the same as a
first inspection (the safe direction: quiescence is only ever established from the latest 2 rows left in the ledger).

Record the checker's returned results in the ledger as-is:
- New defects → add rows with the next F-numbers, status `New`, one line `found in cycle N` in the Action Log (the escalation-count basis)
- Recheck resolved → status `Resolved`, the checker's confirmation evidence in the Action Log
- Recheck unresolved → status back to `New`, reason appended to the Action Log
- Checker notes marked **"SPEC-specified usage"** (a C2/C3/C4 candidate that is a usage/definition/reference the SPEC specifies) → add a row
  with the next F-number: type `that candidate's type (C2/C3/C4)`, status `Needs review`, the note's site and SPEC ID quoted as Evidence, and
  one line in the Action Log with the question for the human (a global rule or the contract colliding with an explicit human
  decision — the human resolves it).
- Checker notes marked **"candidate rejected"** (`Note: candidate rejected | key | basis` — a C2, C3, C4 candidate that is not a defect) → not a defect row but
  a row added to the **candidate-rejection ledger** `spec/findings-rejected.md` (if absent, copy `templates/findings-rejected-template.md`): key, basis, recorded cycle.
  The 3 detectors read this ledger and never print the same candidate again (inheriting the recorded verdict — when the code changes and the key no longer matches, it is printed and judged again).
  All other notes (deferral confirmations, …) create no rows — they are informational reports only.

**F-number assignment**: the next F-number = the header's 'Last F-number' + 1 (update the header by as many as you assign). Never count
from the ledger's maximum ID — resolved rows may have been archived out of the ledger (ID uniqueness and continuity are gated by the verification script, archive included).

After recording, run: `python3 .claude/skills/develojt-code-pdca/scripts/verify_findings_integrity.py spec/findings.md spec/SPEC.md` → fix the ledger until PASS.

### 3. Act — the Lead reinforces

Handle `New`/`Fixing` defects one by one, in one of three ways.
(`Fixing` rows are what a previous session started and left off — read the start line in the Action Log and continue.)

| Action | Condition | Afterwards |
|---|---|---|
| **Fix** | The finding is right | On start: status → `Fixing` + one start line in the Action Log. Fix only what was flagged, keeping the builder's five essentials (@spec, wiring, constraints, leanness). Builder's 4 verifications + compile check. On completion: add one line on what was fixed (file:line) to the Action Log, status → `Awaiting recheck` |
| **Reject** | The finding is wrong | Rejection is possible **only with counter-evidence (the actual wiring's file:line) written in the Action Log**. Status → `Rejected` |
| **Needs review** | SPEC interpretation splits, or a decision absent from the SPEC is needed | Write the question for the human in the Action Log — when the question comes with options, write **the options, a recommendation, and one line of grounds too** (the recommendation axis is `rules/judgment-conduct.md` §3 — the standard practice by default, costs stated alongside). Status → `Needs review`. The loop leaves this row untouched until the human decides |

**`Needs review` exit (after the human decides)**: write the decision in one Action Log line, then —
fix instruction → back to `New` / rejection decision → `Rejected` / SPEC addition needed → `Resolved` after a deriver increment.
If the decision comes with an **appearance release** (finalizing a specific element's appearance differently from the design original — requirements invariant, SPEC unchanged), record the
release first, before any exit — if the calling flow is develojt-code-builder (development phase), via that skill's 'when a design change is needed' appearance paragraph (the mapper remap
release delegation + joblist anchor cleanup); if develojt-code-changer (operations phase), via that skill's revise 'Appearance-instruction input' section. Each calling skill is the
single truth for the procedure, and this skill is the same lead inside that flow (no duplication).
**A `Needs review` row is a handover** — the options and recommendation written on the row are an earlier session's analysis, not the human's decision,
and a later session inherits that row: restructuring it, inventing new options, or changing the recommendation happens **only when there is a newly measured fact**, with that
fact stated in the row and in the report (`rules/judgment-conduct.md` §1 · §6). The "human decision" of an exit is an explicit utterance only —
a question or a counter-question is not a decision (§6).

When 3 defects of the same type accumulate → add one line to the "Process Improvement Proposals" section (what rule added where would prevent recurrence).
The tally is counted not from memory or by reading the archive ledger but **from the verification script's PASS output 'Type tally'** (archived resolved rows included, Rejected excluded — the script prints the combined count).

### 4. Record

1. Add one row to the cycle log (the template's 7 cells): Cycle / Date / Scope / New N / Resolved N / Rejected N / Notes
   — write the unresolved (carryover) N at cycle end in Notes (the quiescence verdict reads this cell)
   — mark the lens used in the Scope cell (e.g., `Bundle 3 recheck (Lens B)`) — the quiescence verdict reads this notation too
2. Update the header's "Current cycle" number
3. **Archive**: run `scripts/archive_resolved_findings.py spec/findings.md` — ① every ledger row with status `Resolved`
   moves to the end of the `spec/findings-archive.md` (resolved-history ledger) Resolved History table, and ② the cycle log's
   rows beyond the latest 5 move to the end of the same file's Cycle Log History table, each as its raw line (the sole exception to the
   no-row-deletion rule — relocation, not destruction. If the archive ledger doesn't exist, the script creates it from the template;
   a legacy archive gets the Cycle Log History section inserted template-identically).
   Confirm the printed archived IDs, cycles, and remaining counts.
   **Archival is done with this script only — never move rows with ad-hoc code or hand edits** (archival is the only operation that
   rewrites the active ledger file, so one full-file rewrite mistake destroys the entire active ledger — on any anomaly the script
   writes nothing and FAILs).
   `Rejected` and `Needs review` are not archival targets (the script won't move them either) — Rejected rows are the memory that
   prevents duplicate checker reports (the existing-defect list in Check spawn instruction 2 comes from the ledger — archive them
   and the same false positive gets re-reported, resetting quiescence), and Needs-review rows are active rows awaiting a human decision.
   The cycle log's latest 5 rows are the verdicts' reading window, so they stay in the ledger (quiescence = the latest 2 rows ·
   lens selection = the same scope's previous row · changed-bundle judgment = the latest row's date — all read within the rows
   that remain. The retention window's single source is the verification script's CYCLE_KEEP).
4. Re-run `verify_findings_integrity.py` → confirm PASS (when the archive ledger exists in the same folder, the script also verifies ID uniqueness/continuity and the archival discipline)

### 5. Verdict → report → auto-repeat until quiescence

- **Quiescence (the loop's only normal exit)**: 0 new + 0 unresolved for 2 consecutive cycles, **and those 2 rows' scope
  notations carry Lens A and Lens B once each** — the verdict basis is read from the ledger, not memory (rule 1 —
  the verification output at Record step 4 prints the latest 2 rows' new/carryover/lens parse as the 'Quiescence aid';
  a row it cannot read for missing notation is flagged with ⚠️):
  if the cycle log's latest 2 rows have 0 new, 0 unresolved (carryover in Notes), and Lens A·B once each, it is quiescence
  (the same lens twice repeats the same trial — even with both rows defect-free, a single-sided lens means one more cycle with the missing lens) →
  "2 defect-free cycles (Lens A+B) — quiescence. Returning to the invoking skill (builder / develojt-code-changer)."
  (Declaring bundle completion belongs to the invoking skill — for appearance-comparison target bundles, the builder finalizes completion after screen-review ledger registration and the human's registration confirmation.)
  **Right after the project's first quiescence, perform 'checker calibration' (section below) once before returning.**
  If `Needs review` rows remain, the quiescence report **must state "N items awaiting review + the question list"**
  (Needs review doesn't block quiescence, but it is never silenced).
- **Escalation**: the same defect unresolved for 3 cycles (counted from the ledger too: current cycle − the Action Log's discovery cycle ≥ 3)
  → change status to `Needs review` and put the question in the result report. The loop continues with the rest of the work.
- **Continue**: otherwise → print the report below and **enter the next cycle's step 1 immediately, without waiting for approval.**
  Never ask the user between cycles — the only stops are quiescence (return) and unimplemented scope (Plan's stop branch).

```
## PDCA cycle {N} results

| Item | Content |
|---|---|
| Inspection scope | {…} |
| New defects | {N — ID · one-line symptom} |
| Resolved / rejected | {N / N} |
| Unresolved (carryover) | {N} |
| Awaiting review | {N — one line per question, — if none} |
| Process improvement proposals | {one line if any, — if none} |

→ auto-entering cycle {N+1}
```

---

## Checker calibration — mutation injection (once per project)

Quiescence (0 defects) cannot distinguish "the code was complete" from "the checker couldn't see".
Calibration measures the checker's detection power with **3 planted defects whose answers are known**, making this
project's quiescence reports an interpretable number. It is **measurement**, not inspection — the code is restored afterwards.

**Timing (deterministic):** right after quiescence first holds in this project, run once if the findings.md
"Checker Calibration" table is empty. Afterwards, re-run only on human request.

**Procedure:**

1. **Backup**: `cp -R src .pdca-calib-backup` — mutations happen in place in src/
   (an inspection environment that differs from usual tips the checker off that it's calibration).
2. **Plant 3 mutations**: sweep the SPEC IDs of the bundle that just reached quiescence in joblist table order
   (without a joblist, sweep this quiescence scope's FR IDs in SPEC appearance order),
   applying the catalog's type order (M1→W1→W3→F1) to the first applicable ID, one per type, 3 total.

   | Type | Mutation operation (tags and declarations stay) |
   |---|---|
   | M1 | Remove from the body the output/recording call that produces the EARS response |
   | W1 | Remove 1 line of a call reaching one of the chain table's required outcomes |
   | W3 | Keep the provider declaration but remove only its call site |
   | F1 | Remove an If/Unwanted guard branch |

3. **Record the answer key**: in `.pdca-calib-key.md` (project root — outside src/), one line per mutation:
   type / SPEC ID / file:line / what was removed.
4. **Spawn the checker**: with the same instruction as a usual first inspection (same scope, Lens A).
   **Don't announce it's calibration. Don't give the answer key.**
5. **Score**: compare the report to the answer key and count detections n/3. Note any new reports unrelated
   to the mutations separately, and after restoration judge their genuineness in a regular cycle (they may be real defects).
6. **Restore + gate**: after `rm -rf src && cp -R .pdca-calib-backup src`,
   only once `diff -r src .pdca-calib-backup` shows no differences may
   `.pdca-calib-backup` and `.pdca-calib-key.md` be deleted. If differences remain, do no other work until restoration completes.
7. **Record**: one row in the findings.md "Checker Calibration" table (Date / Scope / planted mutations / detected n‧3 / Notes).
   **Synthetic defects the checker reported during calibration are never written to the defect ledger** — this table is the only record.
   If detection is below 3/3, note in "Process Improvement Proposals" the missed types and the need to reinforce
   checker rules, and carry it into the next report as-is. Calibration never reverts quiescence (the code is the original) —
   what to do with the measurement is the human's decision.

---

## What not to do

- Never work in response to direct user invocation — guide to builder (develojt-code-changer for operations changes).
- The checker never fixes code. The Lead never judges defects itself.
- Never give the checker the Lead's intent or conversation.
- Never invent requirements absent from the SPEC — if one seems needed, `Needs review` to the human (additions belong to deriver increments).
- Never write a defect row without evidence, or a rejection without counter-evidence.
- Never delete ledger rows — only change status. The sole exception is the Record stage's archival (`Resolved` rows · the cycle log's rows beyond the latest 5), and even that is done only with the dedicated script (archive_resolved_findings.py) (the rows are preserved as-is in the archive ledger — relocation, not destruction).
- The archive ledger (findings-archive.md) is append-at-table-ends only — never modify or delete existing lines, and never read it mid-cycle (the tallies you need are printed by the verification script).
- Never delete rows of the candidate-rejection ledger (findings-rejected.md) by hand — when the code changes, the key stops matching and the row becomes void on its own (a mismatched row left in place is harmless). If a full re-check is needed, give the detectors `--all` (on human instruction / checker calibration).
- Never modify the skill or checker rules directly — proposals only.
- Never contort the code or the ledger to pass verification.
- Never flag choices delegated via `[Free: reason]` as defects.
- Never try to finish everything in one cycle — keep cycles small, record as you go.
- **Never wait for approval between cycles** — the loop is automatic until quiescence. Only Needs-review questions, escalations, and process improvements call the human, and even those ride in reports without stopping the loop.
- Never inspect runtime behavior — what this loop completes is "what wasn't done" (omissions), not "I ran it and it works".
- Never announce a calibration run to the checker. Never write calibration-time reports to the defect ledger — records go only to the 'Checker Calibration' table.
- Never move on to other work with calibration mutations unrestored — the no-difference restoration diff is the gate.

---

## Reference files

Paths: `.claude/skills/develojt-code-pdca/` (local first) or `~/.claude/skills/develojt-code-pdca/`.

| File | Description | When |
|---|---|---|
| spec/SPEC.md | The judgment baseline (EARS + behavior chains = the scoresheet) | Every cycle |
| spec/joblist.md | (if present) scope units (bundles, series, reference implementations) — absent, the scope is the passed FR list | Plan |
| spec/findings.md | The defect ledger — all of the loop's active state | Every cycle |
| spec/findings-archive.md | (if present) the resolved-history ledger — the Record stage archives and preserves Resolved rows and past cycle-log rows in it. The loop never reads it | Record (written by the archival script) — append only |
| .claude/agents/develojt-code-pdca-checker.md | The Check-dedicated agent (this skill's exclusive pair) | Check spawn |
| references/checker-rules.md | Per-type inspection procedures — the checker reads it as its first action | Check |
| templates/findings-template.md | Ledger format | New ledger creation |
| templates/findings-archive-template.md | Resolved-history ledger format | New archive ledger creation (copied by the archival script on first archival) |
| spec/findings-rejected.md | (if present) the candidate-rejection ledger — rejection verdicts on C2, C3, C4 candidates (key, basis, cycle). The Lead writes it in the Check record and the 3 detectors read it (the loop and the checker do not). No row deletions | Check record (write) · detector runs (read) |
| templates/findings-rejected-template.md | Candidate-rejection ledger format | New ledger creation (copied by the Lead on the first candidate rejection) |
| scripts/verify_findings_integrity.py | Ledger format gate | Right after writing to the ledger [required] |
| scripts/archive_resolved_findings.py | Archival executor for Resolved rows and cycle-log rows beyond the latest 5 (archival goes through this only — no ad-hoc code, no hand edits; on failure it writes nothing and FAILs) | Record 3 [required] |
| scripts/verify_security.py | Security rule violation candidate detection — config-type files included, and with `--root-config` the config files directly under the root (.env, etc.) too. Matches with the candidate-rejection ledger are not printed (`--all` for everything). Secret values are printed as `<masked>` + an end-of-line tag (the key too) (judgment via the checker's C2 procedure) | Check (run by the checker) |
| scripts/verify_enforced_rules.py | Enforced-rule (the `.claude/rules/enforced-rules.md` table) violation candidate detection (judgment via the checker's C3 procedure — not applicable without the rules file; `--inventory` prints the builder's symbol sight — over the cap, per-folder tallies and `--inventory=<keyword>` lookups. Matches with the candidate-rejection ledger are not printed (`--all` for everything)) | Check (run by the checker) |
| scripts/verify_architecture.py | Structure-contract (`spec/ARCHITECTURE.md`) violation candidate detection — cross-layer references in directions not allowed, unlisted folders (judgment via the checker's C4 procedure — not applicable without the contract. When a table cannot be read, that class holds its verdict with a `[CAUTION]` tally (false-positive-storm prevention — holds and ⚠️ are grammar-maintenance notes); passing only the contract .md runs grammar-check mode, which the builder uses right after recording the contract; `--metrics` prints structure metrics — collect-and-print only, judgment belongs to the human. Matches with the candidate-rejection ledger are not printed (`--all` for everything)) | Check (run by the checker) |

> This skill's gate sees only "ledger format". "Is the finding right" is seen by the next cycle's re-verification.

---

version: 1.1.0
latest: 2026.10.26
Made by develojt
