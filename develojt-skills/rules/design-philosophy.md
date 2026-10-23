# Design Philosophy — develojt Skill Pipeline

> This file is the canonical judgment filter for AI sessions, kept in the pipeline repository for
> skill-editing sessions (deployment-excluded — running projects load each SKILL.md and the
> deployed rules instead).
> Every modification, improvement, or extension of the skills under `.claude/skills/` must pass
> the six axes below — whatever session or model is doing the work.
> The bilingual narrative in `README.md` is the human-facing detail; when one changes, sync the other.
>
> **Scope**: this file governs *judging and modifying* the skills.
> *Running* the pipeline follows each SKILL.md procedure — this file never overrides them.

## Six Axes of Judgment

| Axis | Meaning |
|---|---|
| **1. Universality** | Applies uniformly to all software development. No domain-specific terms or examples baked into skill bodies, rules, or samples (anti domain-anchoring). The domain is supplied by the artifacts (PRD, SPEC) |
| **2. Consistency on weaker models** | Written as procedures, tables, and short imperatives. A weaker model must produce the same result. No metaphors or long philosophical passages in skill bodies |
| **3. No degradation of stronger models** | Over-regulation must not suppress a strong model's autonomy over the How (structure, patterns, algorithms). Only the essentials (tracing, wiring, constraints of the What) are enforced |
| **4. Clear R&R** | planner = human-led convergence / deriver = divergence & elaboration / mapper = design↔SPEC bridge (STORYBOARD) / spliter = progress ledger / builder = implementation (Do) / pdca = static completion loop (the core of the development cycle) / changer = operational intake & routing (no artifact of its own — reuses the owning skills' procedures by path). No role trespassing — each skill produces only its own artifact |
| **5. Simplicity** | The easiest, most ordinary, most deterministic way. Variability is controlled by verification script gates, not by prose instructions |
| **6. E2E is out of scope** | Runtime **behavior** judgment (e2e tests, live demos, whether features behave as specified) is a separate stage outside this pipeline. Even pdca inspects statically only (tracing, wiring, guards, constraints). One human-decided exception: the **boot invariant** — build + launch + observable liveness checked deterministically against the human-confirmed run profile (`verify_boot.py`) — is a releasable-state mirror of the same family as compile checks (builder self-check), NOT behavior judgment |

> **"Weaker models" in Axis 2**: the floor is a **fixed minimum — Claude Opus 4.8 / 4.7**
> (deliberately pinned as the guaranteed support line). Models below that tier are not a
> consistency target. The floor does NOT rise automatically as newer models ship — raising it
> is an explicit human decision, like dropping support for a version; AI sessions never move it.
> The floor exists to protect stronger models: accommodating models below it adds regulation
> that degrades a strong model's performance and autonomy.
> When Axis 2 and Axis 3 conflict, **the stronger model always wins** —
> calibrate every judgment to the strong model, never below the floor.

## Core Principles

1. **Two documents are the constitution — PRD and SPEC.** If these two are solid, every
   downstream stage (work splitting, code generation) follows, regardless of model or
   technology changes. If they are weak, no downstream improvement is guaranteed.

2. **planner and deriver are a harness, not mere skills.** Harness means: whatever model
   executes them must arrive at the same decided state of PRD and SPEC.
   - Two entry points exist: start from nothing and choose among AI proposals, or start by
     describing what you know as arguments to the skill invocation.
   - Either way the user's input keeps some ambiguity ("a game on the web" is raw material,
     not a decision).
   - Rule: resolve every undecided item by deterministic questioning — present candidate
     hints, the human chooses. Never fill it by model discretion.
   - Rule: a blank (the absence of a decision) is never carried to the next stage.
     Downstream skills are consumers of constraints, never producers.

3. **The human leads, AI assists.** Requirements belong to the human. AI presents candidate
   hints as richly as possible; the human, looking at them, recalls their own ideas.
   A hint is not a decision — adopting, deleting, and editing belong to the human.

4. **Convergence and divergence — engines in two directions.** planner converges: it guides the
   human to settle the system configuration and gathers intent into natural-language epics
   (seeds — undecomposed one-or-two-sentence narratives). deriver diverges: it expands the
   epics into EARS requirements, exercising intent-reading, analogy, and inference to the fullest.

5. **Determinism comes from simplicity.** Clever machinery that leans on a model's intelligence
   breaks when the model changes. Skill instructions stay short, plain, and concrete.
   Variability is controlled by **verification script gates**, not instructions.
   Agents communicate via **file relay**, not harness-specific features.

6. **Develop in slices; never break the traceability chain.** The SPEC is cut into
   physically-dependent bundles in a progress ledger (joblist); the coder picks up one bundle
   at a time. The chain — human epic (PRD) → SPEC ID → joblist row → `@spec` tag in code —
   must survive every stage; coverage gates exist to prevent a dropped epic.

## Quick Check Before Any Skill Edit

Answer all six questions. Any "yes" = stop and redesign the change.

| # | Question | Violates |
|---|---|---|
| 1 | Does the edit put domain-specific words or examples into a skill body, rule, or sample? | Axis 1 |
| 2 | Could two models **at or above the Axis-2 floor** read the new instruction and act differently? (watch for discretion words: "if needed", "optionally", "A or B" — do NOT add regulation for models below the floor) | Axis 2 / harness |
| 3 | Does it dictate code structure, patterns, or algorithms to the implementing model? | Axis 3 |
| 4 | Does one skill now decide, produce, or modify another skill's artifact or constraint? | Axis 4 |
| 5 | Does it control variability with prose instructions instead of a script gate or a user question? | Axis 5 |
| 6 | Does it make the pipeline judge runtime behavior (run the app to judge feature correctness, e2e, demo)? — the boot invariant (deterministic build/launch/liveness via `verify_boot.py` against the human-confirmed run profile) is the sanctioned exception, not behavior judgment | Axis 6 |
| 7 | Does the edit add another per-situation paragraph for a judgment principle that has already fired in 2+ other situations? (3rd occurrence = reinforce the principle in `rules/judgment-conduct.md` + a one-line situational pointer — not another paragraph) | Axis 5 / saturation |
