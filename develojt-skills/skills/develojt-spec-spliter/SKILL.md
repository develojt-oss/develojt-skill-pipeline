---
name: develojt-spec-spliter
description: Skill that unfolds the requirement items (FR/NFR) of spec/SPEC.md into the progress ledger spec/joblist.md. It groups tags into "complete bundles" connected by physical dependency (code actually calling/referencing each other), separates the foundation shared by all bundles into a "scaffolding" layer, and orders them. Use this skill when SPEC.md exists and work is split across multiple sessions, when creating spec/joblist.md fresh, or when incrementally reflecting added features as new rows. Use when the user mentions "joblist", "work list", "progress status", "continue working", "split the work", etc. This skill creates no requirements — it only points at SPEC IDs, groups them, and records progress. It does not verify code behavior.
disable-model-invocation: true
argument-hint: "[new | incremental]"
---

# develojt-spec-spliter — SPEC-based progress ledger generator

User request: $ARGUMENTS

## Position in the pipeline (understand the flow before working)

```
[planner]    plan/PRD.md    — human-led. AI provides hints (seeds)
[deriver]    spec/SPEC.md   — infers and expands epic intent into concrete EARS
[this skill] spec/joblist.md — progress ledger for developing in slices
[builder]    src/           — @spec-traced code, implemented bundle by bundle in ledger order (EP by EP if no joblist)
[pdca]       spec/findings.md — static-completeness loop entered automatically after each implementation. Quiescence defines bundle completion (appearance-comparison target bundles: + screen-review ledger registration & registration confirmation; the comparison itself runs as one batch session after full implementation completion)
```

Projects never finish in one sitting. This skill cuts the SPEC into **units developable across multiple sessions**,
so the coder (builder) never guesses "how far did we get, and what do I pick up next".

The SPEC is *what* gets built (the invariant truth). The `spec/joblist.md` this skill makes is the *progress view* on top — how far we got, what continues next, what notes exist. The joblist never creates or replaces requirements. **It only points at SPEC IDs, groups them, and orders them.**

## The core — what gets bundled

This skill's job is cutting the joblist into **units the coder can pick up and complete in one go**. Cut wrong, and the coder guesses "how far should I go" every time.

There are two cutting criteria.

1. **Scaffolding (foundation layer)** — the foundation shared by multiple bundles. The **code foundation** — config, types, event bus, boot/initialization, build setup — and the **runtime base** — execution containers/runtime, data-store schema and startup, middleware, resident services/model serving, shared protocol/API contracts, shared library initialization (the SPEC's runtime-base NFRs are the requirement source): things belonging to no specific feature that **everyone builds on**. It comes **before** the bundles. Separated as its own layer. **Completing the scaffolding is itself the walking skeleton (an empty system with no features that still builds and boots)** — confirming that it holds and stays held belongs to the builder's run profile and boot gate (the spliter handles structure only).

2. **Bundle (completion unit)** — a group of tags connected by **physical dependency**. **Definition of completion: "One bundle runs complete on its own"** (the joblist convention — that sentence in the template's 'Work Unit Definitions'): once work reaches the end of that bundle in ledger order, **that bundle's behavior is confirmed by an observable result** (a screen, a response, an output). The builder's agile releasable increments presuppose this convention — if the cut cannot produce the convention, the downstream gates have nothing to guard.
   - Physical dependency = one tag's code **actually needs** another tag's code (function calls, shared data structures, event subscriptions). *Code-level* dependency, not *logical/conceptual* affinity.
   - If a tag **compiles and runs by itself** without any other tag → it is a bundle of one.
   - If tag A's code only stands with tag B's code (ordering/subordination) → **gather** A and B into one bundle.
   - The group gathered by following all physical-dependency links is the bundle boundary (a connected component).
   - **Bundles must not bloat.** Gather only what is *actually* depended on. "Nice to have" items and things that can join later stay out.
   - **Cutting tiebreaker** — read-only reuse (merely consuming another bundle's deliverable) can be split across the boundary. Merge only on **mutual calls or co-modification of the same data structure**. But the **direction** of a split is set by the cutting direction below — "can be split" is no license to create a bundle with no observation.
   - **Cutting direction (through-slice first)** — when a long production→consumption chain bloats the connected component, **do not cut by layer (production layer / coordination layer / presentation layer)**; cut into a **minimal through-slice bundle** that passes thinly through the whole chain **+ increment bundles stacked on top of it** (an increment bundle's observation = the result that changes on top of the through-slice). A cut that leaves a producer with no consumer violates the completion convention — that bundle shows zero visible change even when finished, and completion confirmation gets pushed to later bundles.
   - **Shared-producer exception** — a producer whose deliverable has **two or more** consumer bundles may stand as its own bundle (merging it into any one consumer tangles the order with the other consumers — the same shared-foundation logic as scaffolding). This is the completion convention's only observation deferral, and it is never silent — write it in the deferral grammar in the Notes of the first consumer bundle's row where the observation happens (a deferral goes on the row of the bundle that resolves it — exactly the Notes rule).

> With no code yet, physical dependency is a **prediction** from the SPEC. The SPEC's **behavior chain tables** are the signal — a chain written as "A's outcome is B" means "A's code needs B", so they share a bundle. For items with no chain table, use the deliverables the requirement sentences mention (whose outcome/data/event does it use) as the dependency-verdict basis.

Cut this way, the coder **lays the scaffolding first → then implements, records, and completes bundles one at a time, whole**. The bundle boundary is the "unit done at once", so guessing disappears.

---

## Input · Output

- **Input: `spec/SPEC.md`** — FR/NFR requirement items + behavior chain tables. The basis for reading dependencies.
- **Auxiliary input: `design/STORYBOARD.md`** (if present) — the original source of the appearance anchors (`SB-` IDs) written into UI FR rows' Notes. Grep it by FR ID only (no full reads).
- **Output: `spec/joblist.md`** — placed in the same `spec/` as the SPEC. Scaffolding layer + bundles + (per row) status/notes.

---

## joblist structure

Follows `templates/joblist-template.md`. Three parts.

1. **`## 0. Scaffolding`** — 3 columns (Done / SPEC ID / Notes). The foundation of all bundles. First.
2. **`## Work Table (bundle units)`** — under it, per `### Bundle N: name` header, a 4-column table (Done / SPEC ID / Series / Notes). Bundles in dependency order.
3. **`## Past Issues`** — (optional) archive of resolved issues.
4. **`## Parallel Candidates`** — (optional — an information layer) a group table of bundles with no coupling at all between them, safe to pick up at the same time. 3 columns (Group / Bundles / Basis). It is the basis when the builder proposes a parallel wave (`references/parallel-wave.md`); if absent or empty, no parallel proposal (sequential as-is). It carries no FR/NFR IDs or appearance anchors (bundle numbers only) — outside the 3 verification scripts' checks.

   **Parallel-candidate listing conditions (a bundle pair must meet every one to share a group — if even one is not clearly met, do not list them. Fixed toward misses: a missed parallel merely goes sequential, but a wrong parallel is a conflict):**
   - **No order dependency** — neither uses the other's deliverable (the same basis as the dependency verdict that set the bundle order — behavior chains, requirement sentences).
   - **No deferral ties** — neither side's row Notes hold an intentional deferral aimed at, or received from, the other bundle.
   - **Series independence** — they share no series, or the reference implementation (the series' first item) of a shared series sits in an **earlier** bundle outside the group (if the reference is inside the group, reference-first ordering breaks).
   - **Screen separation** — (when appearance anchors exist) they do not split anchors of the same screen (SB-NN) between them (a possible co-edit of the same screen source or shell).
   - **Scaffolding excluded** — scaffolding goes into no group (everyone's prerequisite foundation).

   The table is a record of structural fact — whether and how to run in parallel is decided by the builder's parallel-wave procedure and human approval (the spliter only records).

Column meanings:
- **Done** — `[ ]`/`[x]`. Checked once a SPEC ID is implemented and tagged.
- **SPEC ID** — the requirement item pointed at. Must exist in the SPEC (no ghosts). Each SPEC ID appears in **exactly one row** across the whole ledger (no duplicates).
- **Series** — things built the same *way* (method consistency). A **different axis** from bundles (physical dependency) — items in different bundles can share a series. The series' first item is the reference implementation.
- **Notes** — one pointer line only (sibling pointer / intentional deferral / pitfall / tech adoption record / appearance anchor). An empty cell means "as the SPEC says". Never write the "what" (in the SPEC) or the "how" (in the code). The tech adoption record (`{name} {version} adopted`) is left by the builder during implementation — the spliter never creates it, and preserves it when present.
  **Appearance anchors** (`Appearance: SB-02-01·SB-02-05`) are recorded by the spliter when `design/STORYBOARD.md` exists — every UI ID mapped to that FR (**but a UI ID mapped to multiple FRs rides only on the front-most of those FRs' rows in the ledger** — under N:M mapping, "every" means once each across the whole ledger, not repeated per row), plus the same screen's (SB-NN) `[Decorative]` IDs riding along on the front-most row in the ledger among that screen's mapped FR rows (decorations must enter the row-completion definition, or they get silently omitted. If the screen has no mapped FR row, there is no row to carry them — the builder's human screen comparison is the last line of defense). **Never as rows — as Notes pointers only** (the SPEC ID column holds FR/NFR only: no ghosts, verification scripts unchanged). The builder checks the row only after the appearance of every one of these anchors is reproduced (part of the row's completion condition).
  **An intentional deferral is written on the row of the bundle that resolves it** — not the row that left it. The work that picks up the row must be the resolution owner, or the deferral gets orphaned (a deferral written on the leaving side's row is never read again once that row is checked).

---

## Workflow — new (when `spec/joblist.md` doesn't exist)

1. **Read the SPEC** — collect FR/NFR IDs: `grep -oE "\b(FR|NFR)-[0-9]{2}-([0-9]{3}|E[0-9]{2})\b" spec/SPEC.md | sort -u`. Read the behavior chain tables too (the dependency basis). Rows whose source cell is `[Removed]` (strikethrough IDs) are history-preservation rows — exclude them from the work set.

2. **Extract scaffolding** — pick out the foundation items multiple bundles share. The code foundation — config, types, events, runtime initialization, boot, build — and the runtime base (execution containers/runtime, data-store schema and startup, middleware, resident services/model serving, shared protocol/API contracts, shared library initialization — what the runtime-base NFRs point to): what belongs to no specific feature and everyone depends on. Collect them under `## 0. Scaffolding`.
   Even an ID that looks feature-epic-owned gets pulled up into scaffolding if it demands a **global decision** (global output format, global settings, build flags — anything whose satisfaction requires touching several bundles or the whole existing code). Left inside a feature bundle, the coder ends up making broad edits to existing code at that point.
   Among NFRs, only **foundational** ones (a code foundation such as config, types, boot + the runtime base — NFRs that demand startup, connection, or residency) go into scaffolding; behavioral/quality NFRs attach to the bundle that produces that behavior.

3. **Form bundles** — group the remaining tags by physical dependency. Follow "A's outcome is B" relations in the behavior chains, and relations where one tag must use another tag's deliverable (function, data structure, event), gathering connected items into one bundle. Unconnected tags are bundles of one. **No bloat** — only real dependencies, narrowly. Cut a long production→consumption chain not by layer but by through-slice + increments (core 2's cutting direction). **Cut check** — after cutting, ask of each bundle "once work reaches the end of this bundle, what becomes visible?". A bundle with no answer (zero observation) means the cut is wrong unless it is the shared-producer exception — re-cut in the through-slice direction.

4. **Set the order** — scaffolding at the top. Then bundles, sorted by inter-bundle dependency (a bundle that uses another's deliverable comes after it). Within a bundle, dependency order too.

5. **Mark series** — tag groups built the same way (multiple kinds of the same sort, repeated patterns) get a series name, and a reference item is chosen. A series may cross bundles.

6. **Write the table** — fill `templates/joblist-template.md`. Every row unchecked (`[ ]`). Each bundle gets a `### Bundle N: {name of what completes}` header. Notes only on rows with a series/dependency (sibling pointer, deferral). If bundle pairs that meet all 5 listing conditions (joblist structure 4) actually exist, add the `## Parallel Candidates` table — if none, do not create the section at all (no empty section). If `design/STORYBOARD.md` exists, **record the appearance anchors** — grep the STORYBOARD by each FR ID (no full reads) and write the mapped `SB-` IDs into that row's Notes as `Appearance: SB-…`, with the same screen's `[Decorative]` IDs riding on that screen's first FR row. One SB ID rides on exactly one row across the whole ledger (a UI ID mapped to multiple FRs rides on the front-most of those FRs' rows — the same placement rule as `[Decorative]`).

7. **Verify** (below)

---

## Workflow — incremental (when `spec/joblist.md` already exists)

When new IDs were added to the SPEC (a deriver incremental result), preserve the existing state and add only new rows.
When a requirement was **`[Removed]`** in the SPEC (deriver change-mode deletion — T4), **move** that ID's work row to `## Past Issues` to resolve the ghost (deletion propagation — non-destructive history preservation, not outright deletion).
However, if the SPEC was **fully regenerated** and the existing joblist is stale (the consistency check finds **massive** omissions/ghosts), do not force an increment — stop and get user confirmation. On approval, back up the existing joblist and re-split fresh. (A few `[Removed]` ghosts are resolved by Past Issues moves, not regeneration — distinguished by incremental-update's deletion-propagation procedure.)
**Read and follow `references/incremental-update.md`.** The core: existing checks, notes, order, and bundle composition stay invariant. A new ID — joins an existing bundle when it has physical dependency on that bundle's tags; otherwise becomes a new bundle. Scaffolding-grade (shared foundation) goes to scaffolding. Series is judged **for the new ID only**, against the existing joblist's series definitions (re-judging existing rows is forbidden). If `design/STORYBOARD.md` exists, record appearance anchors (`Appearance: SB-…`) **on new rows only**, by the same rule as the fresh flow (no backfilling existing rows' Notes). `[Removed]` ghosts move to Past Issues via deletion propagation. If `## Parallel Candidates` exists, **the existing groups stay invariant** — judge only whether the new bundles are listed, by the same 5 conditions (add to an existing group / a new group / not listed. Never re-judge existing bundles against each other — the same principle as no series re-judgment).

> **Progress records (row checks, notes) belong to the coder, not the spliter** — made right after implementation, when context is freshest. The spliter handles structure only (scaffolding/bundle composition, order, series).

---

## Verification

After creating or updating the joblist, run both checks. On FAIL, fix and re-run.

```bash
python3 .claude/skills/develojt-spec-spliter/scripts/verify_joblist_integrity.py spec/joblist.md              # format (scaffolding/bundle table structure, checkboxes, IDs)
python3 .claude/skills/develojt-spec-spliter/scripts/verify_joblist_spec_sync.py spec/joblist.md spec/SPEC.md  # SPEC↔joblist bidirectional consistency
python3 .claude/skills/develojt-spec-spliter/scripts/verify_anchor_sync.py spec/joblist.md design/STORYBOARD.md # appearance-anchor consistency (auto-SKIP when no STORYBOARD)
```

(When the skill is installed globally, use the `~/.claude/skills/develojt-spec-spliter/scripts/...` path. Never assume a cwd-relative `scripts/` path.)

- **Consistency "omissions" (in SPEC, not in joblist) = 0** — otherwise work has dropped out of the ledger (the most dangerous).
- **"Ghosts" (in joblist, not in SPEC) = 0** — otherwise the ledger points at a requirement that doesn't exist.
- **Anchor consistency (when a STORYBOARD exists) = 0 ghost anchors · 0 duplicate placements · 0 uncarried mapped UIs** — the appearance-anchor rules (every mapped UI carried, one SB ID on one row, decorations riding along) are enforced by script, not prose. Only `[Decorative]` IDs on screens without a mapped FR row pass as INFO (the builder's human screen comparison is the line of defense).

IDs in both the scaffolding and bundle tables are consistency targets. This check sees only "has the ledger diverged from the SPEC" (never "does the code run"). `## Parallel Candidates` is not a check target — it is an information layer carrying no FR/NFR IDs or anchors, so all three scripts ignore this section (the basis for zero script changes).

---

## What not to do

- Never create or change requirements — only point at the SPEC.
- **Never bundle by logical affinity instead of physical dependency** — even one conceptual flow stays separate if the code isn't entangled.
- **Never cut bundles by logical layer either** — a horizontal cut such as production layer / coordination layer / presentation layer produces producer bundles with no observation (a completion-convention violation). Long chains go through-slice + increments; the only exception is the shared producer (core 2).
- **Never bloat bundles** — only real dependencies, narrowly. Shared foundations go to scaffolding, not a bundle.
- Never add IDs absent from the SPEC (ghost rows).
- Never touch existing checks, notes, order, or bundle composition during an increment.
- Never verify code behavior/reachability.
- Never put a pair that fails the listing conditions, or whose verdict is ambiguous, into the parallel candidates — ambiguous means not listed (a missed parallel merely goes sequential; a wrong parallel is a conflict).

---

## Reference files

| File | Description |
|---|---|
| spec/SPEC.md | Input — requirement items + behavior chains (dependency basis) |
| design/STORYBOARD.md | (if present) auxiliary input — the original source of UI FR rows' Notes appearance anchors (`Appearance: SB-…`) (FR ID grep only) |
| spec/joblist.md | Output — scaffolding + bundle progress ledger |
| templates/joblist-template.md | joblist format (2-layer structure) |
| references/incremental-update.md | Procedure for feature increments + deletion propagation (`[Removed]`→Past Issues move) |
| scripts/verify_joblist_integrity.py | Integrity (format) check |
| scripts/verify_joblist_spec_sync.py | SPEC↔joblist consistency check |
| scripts/verify_anchor_sync.py | STORYBOARD↔joblist appearance-anchor consistency check (SKIP when no STORYBOARD) |

---

version: 1.0.0
latest: 2026.10.23
Made by develojt
