# Parallel wave — parallel implementation of independent bundles by slice agents (only via proposal and approval)

> **This document is loaded only when a parallel-wave proposal has been approved** (the same conditional-load grammar as architecture-lifecycle).
> Parallel is not the default — the default is workflow 4's sequential, lead-direct work, and if any gate of this procedure does not pass cleanly,
> **the failure direction is a fallback to sequential** (a missed parallel merely goes sequential, but a wrong parallel is a conflict).
> **Only Do (slice implementation) is parallelized** — integration, gates, ledger records, and pdca are done by the lead, serially per bundle.
> It is not a parallelization of verification or recording, and the false-completion defense (gate PASS + the lead's wiring and cross-checks are the grounds for completion — agent
> self-reports are not trusted) stands as-is.

## Prerequisite gates (all met — if even one is not, sequential)

1. A finalized `spec/ARCHITECTURE.md` exists — the baseline that unifies the slices' structure, and the grounds for the write boundary (assigned folders).
2. A finalized `spec/run-profile.md` exists + the most recent boot gate PASSed — parallelism happens only on top of the walking skeleton (the releasable invariant).
3. Every bundle in this wave is listed in the **same group** of the joblist's `## Parallel Candidates` — an unlisted bundle is not a proposal target
   (the verdict on the 5 listing conditions is the spliter's record — the builder does not re-judge it. If the record seems doubtful, do not go parallel).
4. Wave size of 2–3 bundles — the default cap is 3 (widening it is a human instruction).
5. Human approval of the **parallel-wave proposal** in the scope report (group, bundles, and assigned folders stated) — without approval, sequential.

## Procedure

1. **Assign the write boundaries** — for each bundle, set a **folder for new creation only** per structure contract §3 (the place for new features)
   (e.g., if the contract says "a new feature = one feature folder", that bundle's feature folder). If two bundles' assignments overlap, that pair cannot go parallel —
   fall back to sequential. The assignment is stated in the scope report's proposal line (it is part of what gets approved).

2. **Spawn (file relay — one `develojt-code-slice-builder` per bundle, simultaneously)** — the spawn prompt carries the following eight as
   a closed composition. Never include the lead's implementation intent or conversation summaries (file paths and facts only — the same principle as checker isolation):
   ① the bundle number + that bundle's SPEC ID list + the `spec/SPEC.md` path (the agent reads those ID rows and the relevant behavior-chain rows itself)
   ② the assigned folders (for new creation only — state that editing existing files is forbidden)
   ③ the list of first-action norm paths (the builder SKILL's five essentials, rules, `spec/ARCHITECTURE.md`, (for UI FRs) the design norms — real local/global paths)
   ④ the Notes of that bundle's joblist rows (if there is a series, including the @spec location of the reference implementation)
   ⑤ the existing symbol inventory output (`verify_enforced_rules.py --inventory` — the duplication-prevention sight, the same as workflow 1 — in summary mode, give the lookup command `--inventory=<keyword>` and the real path instead of the output)
   ⑥ the manifest save path: `spec/wave-merge-{bundleN}.md`
   ⑦ (for UI FRs) the appearance anchors (`SB-…`) and the design/ screen-source paths
   ⑧ one line re-confirming the prohibitions (follow the write-boundary and forbidden sections of the agent definition)

3. **Lead integration (serial per bundle — after every slice returns, in joblist order)** — for each bundle, complete a–e before moving to the next:
   a. **Manifest check** — compare paths to confirm that every created file is under the assigned folders. If even one is outside, that slice is **rejected**:
      delete its output files and re-spawn once with narrowed input; on repeated failure, that bundle falls back to sequential (the lead never writes it instead —
      Lead non-intervention). In a git repository, cross-check exhaustively with `git status` that there are no changes outside the manifest; without git,
      state one line in the wave report, "write boundary could not be cross-checked exhaustively (non-git)" (honest disclosure — the indirect defenses are the 4 gates, C3, C4, and boot).
   b. **Do the wiring** — the lead performs the manifest's wiring instructions (contact points in existing files) directly, by the builder's essentials
      (since the slices never touched existing files, this is the only contact point in shared files — lateral links are the lead's original part).
   c. **Gates** — the builder's 4 self-checks + the boot gate (exactly workflow 5 — FAIL handling the same too).
   d. **Record** — the lead checks the joblist rows and reflects the Notes (reviewing the manifest's technology-record and notes candidates —
      never trusting the agent's self-report as-is: **gate PASS + wiring confirmation are the grounds for the check**). Once reflected, delete the
      manifest file (the same convention as cleaning up deriver intermediate artifacts — no remnants).
   e. **Enter pdca** — with the scope `Bundle N`, under the existing contract as-is (auto-repeating until quiescence). Completion handling after quiescence is exactly workflow 7
      (including the post-quiescence boot-gate re-check and, for screen-comparison targets, registration and registration confirmation — **the definition of bundle completion is unchanged even in parallel**).

4. **Wave report** — one line per slice (gate result · number of rejections/re-spawns · whether it fell back to sequential) + whether the git exhaustive cross-check was done.
   This record is the evidence of parallelism's benefit and defect rate — **widening, narrowing, or stopping the wave is decided by the human on this evidence** (the pilot gate —
   if evidence accumulates that parallel is worse than sequential, simply don't use it. The procedure is a proposal grammar, so it does not change the default behavior).

## Manifest format (agent output — `spec/wave-merge-{bundleN}.md`)

| Section | Content |
|---|---|
| Created files | Every created file path (one per line — an omission is grounds for rejection in the manifest check) |
| Wiring instructions | Changes needed in existing files: `{file}:{location anchor (function / block name)} — {one line on what to insert}` (no direct edits by the agent — the lead performs them) |
| Technology-record candidates | `{name} {version} adopted/confirmed` — reflecting them into joblist Notes is done by the lead after review |
| Notes candidates | Deferrals, pitfalls, no place in the contract, need for shared code — for the lead's review (including things that look like they need a requirement addition — intake and routing belong to the lead and the human) |

## What not to do

- No parallel without approval, no parallel for bundles outside a `## Parallel Candidates` group, no parallel for scaffolding or dependent bundles.
- **No changes to the foundation, structure contract, or run profile during a wave** — if one becomes necessary, stop and recall every slice (discard or
  hold the unintegrated output), then start from the revision procedure (human approval) (the stop line — never continue parallel work while the foundation is shaking).
- The lead never writes a slice's code instead (a stalled or rejected slice is re-spawned with narrowed input or falls back to sequential —
  the same false-completion-prevention principle as the changer's Lead non-intervention). Doing the integration wiring is not an exception but the lead's original part
  (only the contact points in shared files that the manifest instructs).
- Never use an agent's returned summary as grounds for completion — the grounds are gate PASS + the lead's wiring and cross-checks.
- Never let slices of the same wave reference each other's output (the group listing conditions already exclude it, but the spawn instruction also does not
  tell a slice that other slices exist — not knowing each other is the proof of independence).
