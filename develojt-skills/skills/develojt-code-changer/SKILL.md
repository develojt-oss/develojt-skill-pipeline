---
name: develojt-code-changer
description: >
  Operations-phase (post-SPEC-finalization, post-implementation) change intake skill — in pipeline projects
  (spec/SPEC.md exists), it receives, classifies, and confirms requirement/code change requests, then syncs
  SPEC→STORYBOARD→code through ordered gates by reusing the deriver/design-mapper/code-builder procedures.
  When change intent appears — "add a feature", "remove this feature", "change this requirement",
  "adopt a candidate", "apply the conflict verdicts (design/SPEC-wins decisions)", "apply the review comments",
  "refactor this", "set up/change the structure contract (architecture)", "run the structure migration", and the like — use this skill even when the human never names it (the front door of operations changes —
  even if a skill invocation is forgotten, it stops a bare session from bypassing the SPEC and editing code directly).
  However, advancing new development (joblist bundle/EP implementation) is develojt-code-builder's territory,
  first-time SPEC generation is develojt-spec-deriver's, and PRD writing is develojt-spec-planner's — never use this skill for those requests.
argument-hint: "[change request description | candidate adoption: design/spec-candidates.md | conflict resolution: design/spec-conflicts.md] (old builder flags --add/--change/--review are also accepted as classification signals)"
allowed-tools: Task, Agent, Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion
---

# develojt-code-changer — operations change intake (the pipeline's front door)

User request: $ARGUMENTS

**[Required] Lead language rule:**
Everything the Lead shows the user (intake reports, confirmation questions, completion notices, …) must be written in **English**.

**[Required] Human-facing sentences:** Every output shown to a human — reports, explanations, questions, approval requests, and the like — follows `rules/human-language.md`; sentences that ask for a decision follow its §2 (the human-decision sentence rule).

## Position in the pipeline (understand the flow before working)

```
[Development phase — the human invokes skills in order (slash-only)]
planner → deriver → (mapper) → spliter → builder ⇄ pdca
 PRD       SPEC     STORYBOARD   joblist    src/    findings

[Operations phase — after development completes, this skill is the single front door]
change request → [this skill] intake·classify·confirm → delegate deriver/mapper procedures + code via builder essentials
                                        (SPEC → STORYBOARD → src/ ordered-gate sync)
```

**Why it's needed:** every other user-entry skill in the pipeline is slash-invocation-only (`disable-model-invocation`),
so when a skill invocation is forgotten on an operations change request, a bare session bypasses the SPEC and edits code
directly — **severing the traceability chain**. For user requests, only this skill allows auto-invocation (the model enters
on its own upon seeing change intent), closing that hole — in exchange, every path requires **human confirmation before any write**.
(develojt-code-pdca also lacks `disable-model-invocation`, but it is transit-only, invoked mid-flow by builder and this skill —
the front door for user requests is this skill alone.)

## Intake gate (forced — honor this before anything else)

The order is always this: **classify (read-only) → intake report → stop → user confirmation → run the path.**

- Before printing the intake report, and before the user's confirmation arrives, **write tools (Edit, Write, file creation) are forbidden.**
  Only reads (ls, grep, Read) are allowed.
- **On auto-invoked entry, confirmation can never be skipped** — this confirmation is the only defense against misfires
  (wrong trigger, wrong classification). Even when the user named the skill directly and the request is clear,
  report the classification and target and get confirmation.

Print the intake report by filling this template verbatim:

```
## Change intake

- **Classification**: addition | candidate adoption | change/deletion | conflict resolution | code-only
- **Target**: {whichever applies: requirement description · target FR/NFR IDs · candidate UI IDs · conflict N (violated FR · A/B decision)}
- **Path**: {exactly as in the classification table below}
- **Impact**: {for change/deletion and conflict resolution (A) — the target (violated) ID's behavior-chain peers confirmed via query_chain.py. Omit otherwise}

Proceed as-is?
```

End the turn on that final question and wait for the user's confirmation. (For conflict resolution with undecided A/B conflicts,
ask the per-conflict A/B in this same report — the verdict belongs to the human.)

## Classification (deterministic — the fork is "does the requirement (SPEC) change". Only conflict resolution takes that answer from the human's A/B verdict)

| Classification | Signal | Path |
|---|---|---|
| **Mid-development requirement** | An addition or change/deletion signal while `spec/joblist.md`'s scaffolding and bundle tables still have unchecked rows (Done cell `[ ]`) (development in progress — the verdict is that existence check alone) | Not this skill — guide and exit: "For mid-development requirement additions/changes, please proceed in this order: /develojt-spec-deriver (addition = incremental · modification/deletion = change mode) → /develojt-spec-spliter incremental (ledger enrollment). /develojt-code-builder then picks it up as the next bundle for implementation" — this skill is the operations-phase front door and never reads the joblist; received mid-development, a new requirement is never assigned in the ledger (candidate adoption, conflict resolution, and code-only are unaffected by this row — their existing routes hold even mid-development) |
| **Addition** | A new feature / new requirement description (`--add`) — if development is in progress, the 'Mid-development requirement' row above comes first | `references/delegate-mode.md` — deriver incremental delegation → (STORYBOARD sync 3-b) → code |
| **Candidate adoption** | The input is `design/spec-candidates.md` or names its candidates (UI IDs) | `references/delegate-mode.md` 'candidate-file input' section — deriver incremental → mapper promote → code |
| **Change/deletion** | Modification/deletion of existing requirements (FR/NFR IDs, existing features) (`--change`) — if development is in progress, the 'Mid-development requirement' row above comes first | `references/delegate-mode.md` — deriver change delegation → (STORYBOARD sync 3-b) → code |
| **Conflict resolution** | The input is `design/spec-conflicts.md` or names its conflicts (conflict N, UI IDs) | `references/delegate-mode.md` 'conflict-file input' section — per-conflict A/B fixed at intake (A=SPEC revision → remap → code / B=SPEC invariant → remap cleanup + code check) |
| **Code-only** | Requirements invariant — review comments, code quality, refactoring, appearance change (an instruction for an appearance different from the design originals), **structure-contract instructions** (mid-project adoption · revision · migration of spec/ARCHITECTURE.md) (`--review`) | `references/revise-mode.md` — when an appearance instruction hits a STORYBOARD mapping row, its 'appearance-instruction input' section (mapping release first — the originals are frozen, never edited). On a structure-contract instruction, its 'structure-instruction input' section (the single truth of the procedure is builder `references/architecture-lifecycle.md`) |
| **New development advance** | Next bundle/EP implementation, joblist progress | Not this skill — guide "please proceed with /develojt-code-builder for new implementation" and exit |
| **Ambiguous** | Undecidable above, multiple requirements mixed | Do not proceed — ask the user to split/finalize |

## Core principles (boundaries — non-negotiable)

- **Procedure reuse — single truth, no copying.** Each logic's original exists exactly once in its R&R owner skill, and this skill points by path:
  SPEC transitions = deriver `references/{incremental,change}-mode.md` · STORYBOARD application (promotion/enrollment) = design-mapper
  `references/promote-mode.md` · mapping transition sync = design-mapper `references/remap-mode.md` ·
  code implementation & self-check = code-builder SKILL.md's five essentials + `scripts/verify_*.py` ·
  structure-contract lifecycle (mid-project adoption · revision · migration) = code-builder `references/architecture-lifecycle.md`.
  No logic is ever copied into this skill's document — when an original changes, this skill automatically follows the latest.
- **No deliverable of its own (R&R).** This skill creates no files — intake, classification, confirmation, delegation, and gates only.
  The SPEC comes via deriver procedures (subagents), the STORYBOARD/candidate queue via mapper procedures (subagents), and the code is written by the lead following the builder essentials
  (the structure contract `spec/ARCHITECTURE.md` is the one exception — the lead follows the builder's lifecycle/revision rules, and writing happens only ever after human finalization).
- **File relay + verification gates.** Delegated outputs are exchanged as files, and each stage's entry precondition is the owning
  skill's verification script PASS (ordered gates — code never starts on an unverified SPEC/STORYBOARD).
- **Lead non-intervention (false-completion prevention).** When a subagent stalls, re-delegate with reduced input — the lead never writes the SPEC/STORYBOARD in its place.
- **Operations phase = SPEC only.** The PRD and joblist are not consulted (their lifecycles ended with development — the only exceptions are candidate adoption's design/ deliverables and `spec/ARCHITECTURE.md` (the structure contract — when present, the code stage's structural baseline; like the SPEC, it lives through operations)).

## Procedure

1. **Entry check** — `ls spec/SPEC.md`. If absent, don't take the intake:
   > "spec/SPEC.md is missing — the pipeline hasn't started.
   >  Please begin with develojt-spec-planner (PRD) → develojt-spec-deriver (SPEC)."
2. **Classify** — judge by the table above (read-only — the SPEC, candidate queue, and conflict file are checked by grep). **Before ruling 'addition', cross-check the candidate queue** — if `design/spec-candidates.md` (when it exists) holds a candidate (UI ID) implying the same behavior as the request, the classification is 'candidate adoption' even when the input never named it (prevents reinventing a feature already drawn in the design and losing its anchors). If ambiguous, don't proceed — ask.
   **Absence visibility**: when `src/` exists but `spec/ARCHITECTURE.md` doesn't (a project started on older skills), regardless of classification carry one line in the intake report — "No structure contract — to adopt one, intake 'set up the structure contract' (a structural baseline for the code, so later changes follow the same baseline)". No blocking, no auto-creation (visibility only — the same principle as the builder's one-line absence notice).
3. **Intake report → wait for confirmation** — fill the intake gate template verbatim, print it, and end the turn.
4. **Run the path** — after confirmation, follow the classified references procedure as-is. Never skip a gate (verification PASS, plus the in-procedure human approval — delegate-mode step 4's appearance-consumption gate).
5. **Completion report** — summarize the transitioned IDs (new IDs added / old IDs `[Removed]` / new IDs on modification), the STORYBOARD changes (when applicable),
   the code files modified, and verification PASS. If the structure contract (`spec/ARCHITECTURE.md`) was revised, state the revision too (on a structure instruction, also its result — adoption: contract finalized + mismatch treatment; migration: per-batch gate PASS + zero remnants). If the change created or altered `design/`-baseline appearance, **also state the appearance-consumption verdict** (use as-is / translated reproduction (pre-approved) — delegate-mode step 4's consumption gate). If the machine floor (verify_security·verify_enforced_rules·verify_architecture) produced candidates or the code changes affected static completeness, include the develojt-code-pdca recheck results too. If the change created or altered `design/`-baseline appearance, include a screen-comparison table (running screen ↔ design baseline ↔ reproduced anchors) and request the human eye comparison — **until the confirmation answer arrives, the change is not treated as complete** (the appearance gate of delegate-mode step 4).

## What not to do

- **Never write before confirmation** — it is the only defense against auto-invocation misfires.
- **Never write the SPEC, STORYBOARD, or joblist directly** — the SPEC only via deriver procedures, the STORYBOARD/candidate queue only via mapper procedures.
  The joblist doesn't exist in the operations phase (the spliter's territory).
- **Never copy logic into this skill's document** — path references only (single truth).
- **Never intercept new-development advances** — joblist bundle/EP implementation is develojt-code-builder's territory.
- **Never delegate an ambiguous requirement** — subagents can't converse with the user (stateless). The lead resolves it at intake.
- **Never write under `.claude/`** (skills · agents · rules) — it is a deployed copy of the global originals, and re-initialization (`/develojt-init`) overwrites it, losing the recording. A need to improve the norms goes to the human via a report — the human applies it to the originals in the pipeline repository (the declaration at the top of `code-conventions.md`).
- **Never try to invoke the deriver/design-mapper skills** — they carry `disable-model-invocation`, so they can't be called.
  Perform via subagents that follow the procedure documents (procedure reuse). The code stage too is not a skill invocation —
  the lead follows code-builder SKILL.md's essentials.
- **Never move to the next stage or the completion report without verification PASS** — the deliverable guarantee comes first.
- **Never embed domain-specific examples or content in the skill** — form and classification only. The domain is filled by the SPEC/design deliverables.

## Reference files

Paths are relative to the skill install location: `.claude/skills/develojt-code-changer/` (local first) or `~/.claude/skills/develojt-code-changer/`.

| File | Description | When |
|---|---|---|
| `references/delegate-mode.md` | Delegation procedures (addition, candidate adoption, change/deletion, conflict resolution — deriver/mapper procedure reuse + gates) | Classifications: addition, candidate adoption, change/deletion, conflict resolution |
| `references/revise-mode.md` | Code-only edit procedure (requirements invariant — T1 quality, T5 refactoring, appearance change (mapping-release integration), structure instructions (lifecycle integration) + @spec relocation) | Classification: code-only |
| `../develojt-code-builder/references/architecture-lifecycle.md` | The single truth of the structure-contract lifecycle logic (mid-project adoption · top-down revision · full-migration execution) — the lead follows it directly (writes only ever after human finalization) | Classification: code-only — the 'structure-instruction input' section |
| `../develojt-spec-deriver/references/{incremental,change}-mode.md` | The single truth of SPEC transition logic | The delegation procedures instruct subagents with these |
| `../develojt-design-mapper/references/promote-mode.md` | The single truth of STORYBOARD application logic (adoption promotion · new-FR enrollment) | Candidate adoption, stage 2 · base addition's 3-b |
| `../develojt-design-mapper/references/remap-mode.md` | The single truth of STORYBOARD mapping-update logic (transition sync, conflict-verdict application, appearance release) | Conflict resolution, stage 2 · base change/deletion's 3-b · the appearance-instruction release stage |
| `../develojt-code-builder/SKILL.md` + `scripts/verify_*.py` | The single truth of the code five essentials & self-check | The code stage of path execution |
| `spec/ARCHITECTURE.md` | (if present) the structure contract — the code stage's layer/dependency-direction/placement baseline (the same contract as the builder's essentials 3·4); revisions only through human approval (the builder's 'when a design change is needed' structure rule) | The code stage of path execution |
| `../develojt-code-pdca/` (+ `scripts/verify_security.py`·`scripts/verify_enforced_rules.py`·`scripts/verify_architecture.py`) | Static-completeness recheck (scope: the target FR ID list) — the 3 machine-floor detectors always run after code changes (each is not applicable when its rules file/contract is absent) | Recheck mandatory when the machine floor produces candidates; otherwise when code changes affect static completeness |

---

version: 1.0.0
latest: 2026.10.23
Made by develojt
