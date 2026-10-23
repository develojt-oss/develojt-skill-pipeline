---
name: develojt-design-mapper
description: >
  Skill that analyzes the design/ package and spec/SPEC.md, assigns IDs to UI elements,
  and generates the traceability document design/STORYBOARD.md mapping them to SPEC requirements (FRs).
  Use when the user mentions 'design mapping', 'generate a storyboard', 'apply the design', 'UI tracing',
  'link screens to the SPEC', 'analyze the design folder', 'design-spec consistency', and the like, or when a design
  package exists in design/ and UI↔SPEC consistency/tracing is needed before builder implementation.
  Design = source of truth for appearance, SPEC = source of truth for function — this creates the bridge
  document linking the two via UI IDs.
  It defines no new features (features present only in the design are merely surfaced as [Candidate]).
  Deliverables: design/STORYBOARD.md (UI ID ↔ FR mapping + dual anchors + orphan detection) ·
  design/spec-candidates.md (SPEC adoption candidate queue) · design/spec-conflicts.md (design↔SPEC conflicts, awaiting human verdict)

disable-model-invocation: true
allowed-tools: Task, Agent, Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion
argument-hint: "[optional: design/ path] (default: ./design)"
---

# develojt-design-mapper — design↔SPEC traceability mapping generator

User request: $ARGUMENTS

**[Required] Lead language rule:**
Everything the Lead shows the user (progress reports, escalation questions, completion notices, approval requests, …)
must be written in **English**. All prose in the deliverable (STORYBOARD.md) is also written in English (technical terms and code identifiers as-is).

**[Required] Human-facing sentences:** Every output shown to a human — reports, explanations, questions, approval requests, and the like — follows `rules/human-language.md`; sentences that ask for a decision follow its §2 (the human-decision sentence rule).

## Position in the pipeline (understand the flow before working)

```
[planner]    plan/PRD.md         — human-led. Epic seeds
[deriver]    spec/SPEC.md        — source of truth for function (EARS)
[this skill] design/STORYBOARD.md — bridge linking design (appearance) and SPEC (function) via UI IDs. Only when design/ exists.
[spliter]    spec/joblist.md      — progress ledger
[builder]    src/                — SPEC=what / design/=how it looks / STORYBOARD=which FR is which UI
[pdca]       spec/findings.md     — static-completeness loop
```

This skill is **optional preprocessing** that runs **after the deriver finishes the SPEC and before the builder implements**.
It works only when a design package exists in `design/`. Without one, no STORYBOARD is made and the builder develops with appearance autonomy by default.

> **Why it's needed:** the builder implements against `@spec` IDs. If the design is given as "reference only", the door opens
> for false completion — the builder silently drops some screens and reports "done". Assigning IDs to UI and binding them to FRs
> (a traceability matrix, RTM) guarantees the consistency of "what's visible" and "the SPEC" by ID, and whatever is missing shows.

## What this skill does

Two design experts independently analyze and cross-review the `design/` package and `spec/SPEC.md` to:

1. Assign a **unique ID** (`SB-NN-MM`) to each screen's UI elements.
2. Attach **dual anchors** (visual + source) to each UI — **pointing at the real target** instead of describing in words.
3. **Map** each UI to SPEC **FRs** (not 1:1 — N:M).
4. **Detect orphans** — in UI but no FR (SPEC omission candidates) / in FRs but no UI.

The Lead (the main session running this skill) handles only round orchestration, inventory, consolidation, verification, and user relay.
**The mapping content is made by the two agents. The Lead never intervenes in content.**
Communication is **file relay**, not real-time messaging (same as the deriver — harness-independent).

The deliverables are three files — `design/STORYBOARD.md` (the mapping body) · `design/spec-candidates.md` (candidate queue) · `design/spec-conflicts.md` (design↔SPEC conflicts, awaiting human verdict). When implementing an FR, the builder uses the STORYBOARD table to find the exact UI appearance.

---

## Core principles (boundaries — non-negotiable)

- **Design = source of truth for appearance (how it looks).** It decides layout, color, fonts, animation, placement. (The originals are the project's **starting baseline — frozen**: when the human later decides a specific element's appearance departs from them, the originals are not edited; only that element's mapping is retired via remap appearance release — `references/remap-mode.md`.)
- **SPEC = source of truth for function (what it does).** It decides what gets implemented.
- This skill only **links** the two. **It defines no new features.**
  Features present only in the design are **surfaced** as `[Candidate]` (in the separate queue `design/spec-candidates.md`); whether to implement is the human's decision via deriver incremental mode.
- **Never modifies the SPEC.** The SPEC is frozen. The STORYBOARD is only a bridge — it never overwrites a source of truth.

---

## Dual anchor rules (the heart of this skill)

Each UI element is identified by **anchors that can be pointed at, not text descriptions**. Writing "the message input bar" in prose
forces the builder to infer again — the goal is to reduce inference to zero.

- **Visual anchor**: `screenshots/{file}` + region within the screen. e.g., `02-search.png · bottom input bar`
- **Source anchor**: a **grep-able stable identifier** in the screen source (`.dc.html` etc.).
  - Priority: ① unique text/placeholder → ② unique class name → ③ structural path
  - **Forbidden**: coordinates (break under responsive layouts), and **volatile regeneration-sensitive indexes** like `data-dc-tpl`
- **Attaching both is the rule.** When the source has nothing to find (pure `<canvas>` graphics etc.): visual anchor + `[No source: reason]`.

→ The builder greps the source anchor to find the actual element in the screen source and reads the appearance (color, spacing, animation) **directly**.

---

## Orphan handling

| Situation | Notation | Handling |
|---|---|---|
| UI exists, mapped FR exists | (normal) | Record the mapping row |
| UI exists but no FR (functional) | `[Candidate]` | Collected with anchors into the separate queue `design/spec-candidates.md` → human reviews via deriver incremental |
| UI exists but needs no mapping (decorative) | `[Decorative]` | Normal — recorded as a body-table row with an SB ID (background particles etc. **Excluded from requirement-ization only — not exempt from reproduction**; global decorations attach to the shell screen: common-rules §4) |
| FR exists but no UI | `[No UI]` | Non-UI feature (normal) or design omission — human verdict |

**Never hide orphans. Surfacing them is this skill's consistency-verification value.**

---

## Agent composition

| Role | Expertise | Responsibility |
|---|---|---|
| **DesignTheorist** (design theory expert) | UX principles, design systems, information architecture, accessibility, heuristics | Identify UI elements exhaustively, state-variant completeness (loading/error/empty), mapping-logic rigor |
| **DesignPractitioner** (senior hands-on designer) | 10+ years design→code implementation | Anchor feasibility; responsive/performance/dark-mode reality; supplementing **"what the design didn't say"**; removing over-identification |
| **Lead** | Round orchestrator | Round order, inventory extraction, consolidation, verification, user relay. **Never intervenes in mapping content** |

**Spawn prompt composition (common to all rounds)** — concatenate the three parts below in this order (same pattern as the deriver):
```
1. Full text of references/common-rules.md   (dual anchors · orphan verdicts · mapping philosophy — identical for both sides)
2. Full text of references/{theorist|practitioner}-prompt.md   (persona)
3. The round's work instruction   (the block in the STEP below)
```
Agents are stateless. Specify the file paths needed for each round in the work instruction so they read them directly.

---

## Overall flow (negotiation-based — the Lead never intervenes in content)

The same negotiation structure as the deriver. **The mapping content is made entirely by the two agents.**
The Lead does only round order, inventory, verification, consolidation (differences only), and user relay — **it never writes STORYBOARD content itself.**

```
STEP 1  Prepare · inventory — entry checks + screen inventory (Lead)
STEP 2  Independent mapping — both agents in parallel → map-{role}.md
STEP 3  Cross-review r1    — both agents in parallel → review-{role}-r1.md  [escalation check]
STEP 4  Negotiation r2     — both agents in parallel → review-{role}-r2.md  (accept/rebut/compromise on disagreements)
STEP 5  Final versions     — both agents in parallel → storyboard·spec-candidates·spec-conflicts-{role}.md  (body + candidate queue + conflicts)
STEP 6  Consolidate·verify·approve — Lead: merge differences only → STORYBOARD·spec-candidates·spec-conflicts.md → verify → approval → cleanup
```

### Weaker-model support (design-philosophy Axis 2 — [Required])
This skill **never assumes the best model at the highest effort.** It makes models **at or above** the design-philosophy Axis 2 floor
(a fixed minimum — that document owns the value and definition) produce the same result.
Models **below** the floor are not a consistency target — regulation to accommodate them harms Axis 3 (strong-model autonomy), so it is not added.
The means of guaranteeing identical results at or above the floor is not model intelligence but **strict formats · verification gates · clear R&R**:
- **Keep inputs small**: never make an agent Read a large source (`.dc.html` etc.) whole — anchor checks are **Grep only**. The SPEC too is checked partially by grepping relevant FRs (whole-file Read forbidden). (In practice an agent stalled on ~245KB of combined input → input reduction is mandatory.) **The README (design guide) is the exception — always read it in full** (a small normative document, the original source of appearance norms — common-rules §1 priority).
- **Keep formats strict**: each round's deliverable follows the template/required header format, and the final response is one summary line only.
- **Block with gates**: after each STEP the Lead checks file existence and format, and re-spawns on deficiency (procedure enforces quality even when the model is weak).
- **Limit scope**: never make one agent synthesize all screens + the whole SPEC at once (overload stalls). Final versions are written by each agent from its own map, and the Lead merges.

### STEP 1: Prepare · inventory (Lead)

```bash
DESIGN_DIR="./design"       # if the user request ($ARGUMENTS) specifies a different design/ path, use that
                            # caution: the pipeline-convention path is ./design — downstream (spliter, builder) is fixed to ./design,
                            # so deliverables at a non-standard path are never consumed. In that case state this fact in the approval report.
ls "$DESIGN_DIR"            # confirm the design package exists
ls spec/SPEC.md             # confirm the source of truth for function
# Intermediate files (inventory, map, review) live directly in design/ — same as the deriver using spec/ (no separate folder).
```

**Entry mode decision:**
- **Promotion delegation (promote mode)** — when develojt-code-changer (operations change intake) delegates in with `candidate UI ID ↔ new FR ID` pairs (adoption promotion) or a `new FR ID (no candidate)` list (new-FR enrollment — base 'addition', a `[No UI]` classification only) (after a deriver increment recorded the FRs in the SPEC) → follow `references/promote-mode.md` (instead of the 3 modes below — applies SPEC increments to the STORYBOARD). Entry precondition: target FRs exist in the SPEC + for adoption promotion, matching candidates in spec-candidates / for new-FR enrollment, no matching candidate. If a human runs `/develojt-design-mapper` directly, decide among the 3 modes below (not promote).
- **Mapping-update delegation (remap mode)** — when develojt-code-changer delegates in with conflict verdicts (A/B) and transition pairs ('conflict resolution' — A: after a deriver change transitioned the SPEC / B only: without transitions), or with pure transition pairs alone (base 'change/deletion' — modification `old FR → new FR` / deletion `old FR → (deleted)`, no conflict lists), or with a **release list alone** (appearance release — retiring the mapping rows of elements whose appearance the human decided departs from the design originals, `SB-NN-MM (appearance-release — reason)`. SPEC unchanged — delegated by develojt-code-changer or develojt-code-builder (a human instruction mid-development)) → follow `references/remap-mode.md` (instead of the 3 modes below — syncs transitions into the existing mapping + applies verdicts + releases). Entry precondition: STORYBOARD exists (spec-conflicts too when conflict lists are delegated) + (on transition) the transition results actually in the SPEC (modification: new FR active, old FR `[Removed]` / deletion: old FR `[Removed]`) + (on release) the target rows exist in the body and their mapped FRs remain active in the SPEC.
- **No design** — `design/` absent, or no screen assets (README/source/screenshots) → exit without making a STORYBOARD:
  > "No design package in design/. Skipping design mapping — the builder develops with appearance autonomy."
- **No SPEC + design exists** — proceed in **candidate extraction mode** (do not stop). With no FRs to compare,
  **no mapping, `[No UI]`, conflicts, or coverage are produced** — identify every functional UI, attach anchors, and
  extract to `spec-candidates.md` (every Target FR `(not adopted)`, pure decoration only `[Decorative]`). In this mode the flow simplifies:
  > - STEPs 2–5: agents write only `spec-candidates-{role}.md` (no STORYBOARD, no spec-conflicts). Negotiation (r1, r2) focuses on anchor validity, identification completeness, and decorative verdicts (no mapping disagreements).
  > - STEP 6: gate = the 2 `spec-candidates` files / merge·cp = `spec-candidates` only / verification = verify-anchors only (**verify-coverage skipped** — no SPEC).
  > - Lead notice: "spec/SPEC.md is missing — extracting feature candidates from the design into spec-candidates.md (mapping comes after SPEC generation)."
- **Both exist** — proceed to STEP 2 in **mapping mode** (the full flow below. Behavior when the SPEC exists is unchanged).

**Inventory extraction (deterministic):** identify the screen list and assets from the design package and save as `design/inventory.md`.
- Screen list: if a README (design guide) exists, **its screen sections are the baseline** (the Lead reads the README), supplemented by `screenshots/` file names. Without one, from screen-source and screenshot file names.
- Per-screen assets: visual (screenshot path) / source (`.dc.html` etc. existence).
- **Shared technical assets**: record **the existence and file names, as they are**, of the companion assets the screen source loads or references (runtime/helper `support.js` etc., stylesheets, fonts, icons, images, mock data — confirmed via the source's load/reference declarations (`<script src>`, `<link href>`, `@import`, `url()`, fetch, etc.) and `ls`). No speculative statements — write "absent" only when `ls` confirmed it (a README's "viewer-only" label never excludes the record).
- This inventory is the **screen map** both agents read in STEP 2 (the baseline that makes agents sweep exhaustively).

### STEP 2: Independent mapping drafts (2 parallel spawns)

Work instruction:
```
[Task — independent mapping draft]
Read design/inventory.md, spec/SPEC.md, and the design guide (README — if present, **always in full**) in design/ (common-rules §1 priority).
- [Weaker-model support / required] Never Read screen sources (.dc.html etc.) whole — confirm anchors with Grep.
  Check the SPEC too by grepping relevant FRs (whole-file Reads cause overload and stalls). The README is the exception to this limit — always read it in full.
- [Forbidden] Do not read the counterpart expert's files — independent drafting prevents bias.
- Sweep every screen in the inventory exhaustively **along 4 axes (affordances, states, transitions, displayed data)**, assigning IDs (SB-NN-MM) to each screen's UI elements
  (transitions attach to their trigger element; displayed data implies read/render behavior — common-rules §1).
- Attach dual anchors (visual + source) to each UI. Source anchors use only grep-able stable identifiers
  from the screen source (no coordinates or volatile indexes). If none can be found: [No source: reason].
- Map each UI to SPEC FRs (N:M allowed). If no mapping applies, judge [Candidate] or [Decorative].
- [Mapping mode only] Check that every SPEC FR is mapped somewhere or classified [No UI] (no FRs left out). (Candidate mode has no SPEC — skip; everything is a candidate)
- Template: templates/STORYBOARD-template.md
- Save to: design/map-{role}.md
- Final response: one line only — "Mapping complete. Screens N / UI N / mapped N / [Candidate] N / [Decorative] N / [No UI] N"
```
Gate: `ls design/map-DesignTheorist.md design/map-DesignPractitioner.md` — both must exist for STEP 3.
On failure: re-spawn only the missing side once with the same instruction; on repeat failure, report to the user and stop.

### STEP 3: Cross-review r1 (2 parallel spawns)

Work instruction:
```
[Task — cross-review r1]
Read your own mapping (map-{role}.md) and the counterpart's (map-{counterpart}.md) and write a review.
If a README (design guide) exists, read it alongside as the cross-check original — it is the baseline that catches screens/behaviors both sides missed.
- Anchor validity: confirm the counterpart's source anchors in the screen source with Grep (flag what can't be found). [No whole-file Reads — grep only. The README is the exception]
- Missing UI: screens/elements/state variants the counterpart missed (cross-checked against the README's screen/behavior descriptions).
- Verdict disagreements: items where decorative/functional/candidate judgments split (especially [Candidate] vs part-of-FR-X) — give grounds.
- [Escalation]: SPEC interpretation questions the two of you cannot decide — omit the section if none.
- Save to: design/review-{role}-r1.md
- Final response: one line only — "Review complete. agree N / disagree N / omissions flagged N / escalations N"
```
Gate: both review-*-r1.md exist. On failure re-spawn only the missing side once.
**Escalation check:** `grep -l "\[Escalation\]" design/review-*-r1.md` → if present, ask the user via AskUserQuestion and pass the answers into STEP 4.

### STEP 4: Negotiation responses r2 (2 parallel spawns)

Work instruction:
```
[Task — negotiation response r2]
Read both mappings (map-*.md) and both r1 reviews (review-*-r1.md).
{If escalation user answers exist: include "User answers: …"}
Answer each disagreement and omission flag raised against you:
- Accept (state the reason) / rebut (must bring new grounds — repeating the same claim is forbidden) / propose a compromise
- For anchor-validity flags from the counterpart, re-confirm with Grep before accepting/rebutting.
- Save to: design/review-{role}-r2.md (summary at the head: "Accepted N / Rebutted N / Compromised N / Unresolved N")
- Final response: the summary line only.
```
Gate: both review-*-r2.md exist. On failure re-spawn only the missing side once.
**Escalation check:** `grep -l "\[Escalation\]" design/review-*-r2.md` → if present, ask the user and pass the answers into STEP 5.

### STEP 5: Final versions (2 parallel spawns — the agents write the STORYBOARD)

Work instruction:
```
[Task — final version]
Read every file so far (both maps, both r1/r2 reviews{, user answers}) plus the README (design guide — mandatory if present) and write the final STORYBOARD and the candidate queue.
- Apply every accepted/agreed change from the negotiation. Mark unresolved items [Needs review: reason].
- [Weaker-model support / required] Never Read screen sources (.dc.html etc.) whole — confirm anchors with Grep. Check the SPEC with grep too.
- [Mapping mode only] Self-check that every SPEC FR is mapped or classified [No UI] (0 FRs left out). **Write FR IDs in full form (abbreviation `FR-19-001 / -002` forbidden — common-rules §3).** Instead of self-reporting, **run `scripts/verify-coverage.sh <body storyboard> spec/SPEC.md` yourself and confirm PASS**. (Candidate mode writes only spec-candidates without STORYBOARD/spec-conflicts — skip this check)
- **Never put `[Candidate]` in the STORYBOARD body** — write it separately to `design/spec-candidates-{role}.md`
  (spec-candidates-template.md structure = same columns as the body table; the Target FR cell is `(not adopted)`). The body keeps only mapped FRs and `[Decorative]`.
- **Never put `[Needs review]` (design↔SPEC conflicts) in the STORYBOARD body** — write it separately to `design/spec-conflicts-{role}.md`
  (spec-conflicts-template.md structure = anchor table + human-language options A/B). **However, the conflicting element's FR is also classified in the body (mapping/[No UI])** (coverage maintained — that FR is alive in the SPEC).
- In the Document Info **shared technical assets** row, record the companion assets' existence (runtime/helper `support.js` etc., stylesheets, fonts, assets, data) as it is — confirmed via `ls` and the screen source's load/reference declarations (`<script src>`, `<link href>`, etc.). Never write "absent" for a file that exists. If none: "none (ls-confirmed)" (common-rules §1 — the persistent record of the builder's double net).
- Templates: STORYBOARD-template.md (body) · spec-candidates-template.md (queue) · spec-conflicts-template.md (conflicts) — keep structure/columns; all prose in English.
- Save to: design/storyboard-{role}.md · design/spec-candidates-{role}.md · design/spec-conflicts-{role}.md (create at least the headers even with 0 candidates/conflicts).
- Final response: one line only — "Final complete. Screens N / UI N / mapped N / [Candidate] N / [No UI] N / [Needs review] N"
```
Gate: confirm all 6 files from both sides exist — `ls design/storyboard-DesignTheorist.md design/storyboard-DesignPractitioner.md design/spec-candidates-DesignTheorist.md design/spec-candidates-DesignPractitioner.md design/spec-conflicts-DesignTheorist.md design/spec-conflicts-DesignPractitioner.md` — **all must exist** for STEP 6 (headers alone are fine with 0 candidates/conflicts). Consolidating from one side only is forbidden.
On failure: re-spawn only the missing side once with the same instruction; on repeat failure, report to the user and stop.

### STEP 6: Consolidate · verify · approve · cleanup (Lead — never writes content itself)

**[Required] The Lead never writes or edits STORYBOARD content.** Check only differences with merge-helper and copy the base file.
```bash
bash <skill path>/scripts/merge-helper.sh design/storyboard-DesignTheorist.md design/storyboard-DesignPractitioner.md
bash <skill path>/scripts/merge-helper.sh design/spec-candidates-DesignTheorist.md design/spec-candidates-DesignPractitioner.md  # queue differences via the same script
bash <skill path>/scripts/merge-helper.sh design/spec-conflicts-DesignTheorist.md design/spec-conflicts-DesignPractitioner.md  # conflict differences via the same script
cp design/storyboard-{base side}.md design/STORYBOARD.md
cp design/spec-candidates-{base side}.md design/spec-candidates.md   # copy the queue from the same base side (paired with the body)
cp design/spec-conflicts-{base side}.md design/spec-conflicts.md     # copy the conflicts from the same base side too
# For UI IDs on one side only, grep the base file for the same thing in different wording.
# On a genuine omission the Lead never fills it in — re-run that side's agent with the STEP 5 instruction (naming the missing items).
```

**[Required] Verification pipeline:**
```bash
bash <skill path>/scripts/verify-anchors.sh design/STORYBOARD.md design/         # do the body's source anchors actually grep?
bash <skill path>/scripts/verify-anchors.sh design/spec-candidates.md design/    # same verification for queue anchors (same columns as the body → same script reused)
bash <skill path>/scripts/verify-anchors.sh design/spec-conflicts.md design/     # conflict anchors too (same-column anchor table)
# [Mapping mode only] candidate mode skips verify-coverage (no SPEC)
bash <skill path>/scripts/verify-coverage.sh design/STORYBOARD.md spec/SPEC.md   # live FR coverage (queue/conflict FRs are also classified in the body, so covered here)
```
On ERROR (missing FRs, anchor grep failures) **the Lead never fixes it directly** — state the error items in a work instruction, re-run that side's agent (STEP 5), then re-consolidate and re-verify with its output.
`Manual check N` in the verify-anchors output (WARN — structural-path anchors that defy automatic extraction) is an unverified remainder not included in PASS — the Lead greps those anchors in the design/ sources directly, and if one cannot be confirmed, follow the same agent re-run path as an ERROR.

**[Required] User approval gate:**
```
Lead → "The STORYBOARD is complete.
        - Screens N / UI elements N / FR coverage N/N
        - [Candidate] N (spec-candidates.md queue — in the design but not the SPEC; deriver incremental review): {list}
        - [Needs review] N (spec-conflicts.md — design↔SPEC conflicts; human decides design-wins/SPEC-wins): {list}
        - [No UI] N / anchor & coverage verification PASS
        Please approve to finish."

Approve → cleanup / change request → re-run that side's agent → re-verify → repeat until it passes again
```

**Cleanup (after approval):** remove intermediate files only (preserve the original design package). What stays in `design/` is STORYBOARD.md · spec-candidates.md · spec-conflicts.md (plus the original design package).
```bash
rm -f design/inventory.md design/map-*.md design/review-*.md design/storyboard-*.md design/spec-candidates-*.md design/spec-conflicts-*.md
# The final deliverables design/STORYBOARD.md, design/spec-candidates.md, design/spec-conflicts.md remain
#   (the spec-candidates-*.md/spec-conflicts-*.md globs match only the intermediate {…}-{role}.md files — the finals without a role suffix after the hyphen are excluded).
```

---

## Deliverable shapes (three files)

### design/STORYBOARD.md (mapping + orphans [No UI · Decorative])

```
## SB-02: Search results screen        ← README "2. Search" / screenshots/02-search.png

| UI ID    | Visual Anchor          | Source Anchor (grep)             | Description       | Mapped FR |
|----------|------------------------|----------------------------------|-------------------|-----------|
| SB-02-01 | 02-search.png top      | input[placeholder^="Search"]     | search input      | FR-02-003 |
| SB-02-02 | 02-search.png list     | .result-card                     | result card       | FR-02-005 |
| SB-02-03 | 02-search.png empty    | text "No results"                | empty-state notice | FR-02-007 |
| SB-02-05 | 02-search.png background | [No source: canvas particles]  | background decoration | [Decorative] |

## Orphan List
> [Candidate] → see the design/spec-candidates.md queue (1) · [Needs review] (conflicts) → see design/spec-conflicts.md
### [No UI] (in FRs but not in the design → presumed non-UI feature / design omission needs verdict)
- FR-05-002 access permission policy — backend feature (presumed normal)
```

### design/spec-candidates.md (candidate queue — promoted into the body above when adopted)

```
| UI ID    | Visual Anchor           | Source Anchor (grep) | Description (implied behavior) | Target FR |
|----------|-------------------------|----------------------|-------------------------------|-----------|
| SB-02-04 | 02-search.png top-right | text "Export"        | export button (no FR)         | (not adopted) |
```

### design/spec-conflicts.md (design↔SPEC conflicts — awaiting human verdict)

```
## Conflict 1 — theme switching on the settings screen

| UI ID    | Visual Anchor            | Source Anchor (grep)        | Design Behavior       | Violated SPEC |
|----------|--------------------------|-----------------------------|-----------------------|---------------|
| SB-10-03 | 10-settings theme section | onClick="{{ toggleTheme }}" | provides dark-mode toggle | FR-06-005 |

- The design: draws dark/light theme switchable via a toggle
- The SPEC (FR-06-005): fixed to light theme, no theme-change control provided
- Option A · Design wins → revise the SPEC (develojt-code-changer change/deletion)  /  B · SPEC wins → drop the toggle, keep light fixed
- Decision: ☐ A  ☐ B
```

---

## What not to do

- **Never unilaterally finalize a design-only feature into the SPEC/code** — surface it as `[Candidate]` (in the spec-candidates.md queue) and let the human decide
- **Never modify the SPEC** — the SPEC is frozen; the STORYBOARD is only a bridge
- **Never use coordinates or volatile indexes (`data-dc-tpl` etc.) in source anchors** — they break under regeneration and responsive layouts
- **Never describe UI in words alone** — always attach pointable dual anchors
- **Never hide orphans** — surfacing them is this skill's purpose
- **[Required] The Lead never writes or edits STORYBOARD content** — orchestration, consolidation (differences only), verification, relay only. Even if an agent stalls, the Lead never writes in its place — reduce the input and re-delegate (false-completion prevention)
- **[Required] Never skip the negotiation response (r2) or the agents' final versions (STEP 5)** — cross-review alone with the Lead consolidating leaves disagreements unresolved between agents, inviting Lead intervention
- **[Weaker-model support] Never make agents Read large sources (.dc.html etc.) whole** — anchor checks by Grep only (prevents overload stalls). The README (design guide) is the exception — full read required (common-rules §1)
- **Never force a STORYBOARD when there is no design** — skip, and leave the builder to default development
- **Never embed domain-specific examples or content (RAG, game terms, …) in the skill** — form and blanks only. The domain is filled by design/
- Never skip running the verification scripts
- **Never finish without user approval**

---

## Reference files

Paths are relative to the skill install location: `.claude/skills/develojt-design-mapper/` (local first) or `~/.claude/skills/develojt-design-mapper/`.

| File | Description | When |
|---|---|---|
| `references/common-rules.md` | Dual anchors · orphan verdicts · mapping philosophy (single truth) | Part 1 of the prompt at every agent spawn |
| `references/theorist-prompt.md` | DesignTheorist persona | Part 2 when spawning Theorist |
| `references/practitioner-prompt.md` | DesignPractitioner persona | Part 2 when spawning Practitioner |
| `references/promote-mode.md` | Procedure applying SPEC increments to the STORYBOARD — adoption promotion + new-FR `[No UI]` enrollment (develojt-code-changer delegation — the mapper counterpart of deriver incremental, no negotiation) | Stage 2 of develojt-code-changer candidate-adoption/base-addition delegation |
| `references/remap-mode.md` | Procedure syncing SPEC transitions (change·deletion) into the existing mapping + applying conflict verdicts (A/B) + appearance release (human-decided — mapping-row retirement + `[No UI]` appearance-autonomy transition) (develojt-code-changer delegation — the mapper counterpart of deriver change, promote's counterpart, no negotiation) | Stage 2 of develojt-code-changer conflict-resolution/base-change-deletion delegation · appearance-release delegation (changer/builder) |
| `templates/STORYBOARD-template.md` | Storyboard literal skeleton | Basis for agent drafts |
| `templates/spec-candidates-template.md` | Candidate-queue literal skeleton (same columns as the body table) | Basis for agent finals (STEP 5) |
| `templates/spec-conflicts-template.md` | Conflict-document literal skeleton (anchor table + A/B choices) | Basis for agent finals (STEP 5) |
| `scripts/verify-anchors.sh` | Verifies source anchors actually grep in the screen sources (body tables only) | STEP 6 |
| `scripts/verify-coverage.sh` | Live FR coverage verification (excludes source-cell `[Removed]` rows, strikethrough-ID rows, NFRs, and HTML comments) | STEP 6 |
| `scripts/verify-stale.sh` | Verifies every STORYBOARD FR is active in the SPEC (reverse direction — HTML comments excluded) | remap gate |
| `scripts/merge-helper.sh` | Diff-based consolidation helper for the two sides' finals | STEP 6 |

---

## Consumption & integration (implemented — notes)

**(1) Read — the builder (develojt-code-builder), when implementing an FR:**
> The builder follows every file inside design/, each in its own role (not a closed list — but this skill's own deliverables, the candidate
> queue and the conflicts file, are not appearance norms and are never followed). Compliance priority (builder essential 3): if
> `design/README.md` exists, **compliance is mandatory** (full read) → without it, consult design files such as screen sources →
> screenshots only, follow the screenshots as far as they go. Companion assets the screen source loads or references (runtime/helper
> `support.js` etc., stylesheets, fonts, assets, data) must be consulted when reproducing behaviors/effects (static assets are used
> as-is) — the entry is a double net: the builder confirms directly via the screen source's load/reference declarations (1st, builder
> workflow 1) + greps the shared-technical-assets row in the STORYBOARD Document Info (2nd, the persistent record — wired into builder
> essential 3 and workflow 1; the inventory is deleted after approval, so it is not an entry point). If
> `design/STORYBOARD.md` exists, grep it by the FR ID to find the mapped UI (when the joblist row carries an `Appearance: SB-…`
> anchor, that is the row's reproduction scope and check condition), locate the position in the screen source via the source anchor,
> and **actually Read that element's source region** and follow its appearance (the consumption mode is decided by whether the
> stacks match: when the design source's language/format is valid as-is in the tech stack, **using the source as-is is the
> default**; on a mismatch, translated reproduction — and reproduction is subject to approval. The grep is for locating only —
> builder essential 3). The README is re-read at the start of every UI FR bundle, and
> bundle completion = pdca quiescence + **screen-review ledger registration & the human's registration confirmation** (the comparison itself runs in builder's screen-comparison session after full implementation completion).
> If `design/` itself is absent, develop with appearance autonomy.

**(1-b) Read — the spliter (develojt-spec-spliter), when creating/incrementing the joblist:**
> To record appearance anchors (`Appearance: SB-…`) in UI FR rows' Notes, it greps the STORYBOARD by FR ID (no full reads).
> The same screen's `[Decorative]` IDs ride along on that screen's first FR row, so decorations enter the row-completion definition too.

**(2) Delegation — candidate adoption (develojt-code-changer, operations change intake):**
> Features in `design/spec-candidates.md` are not in the SPEC, so they are never implemented unilaterally. When the human decides to adopt, develojt-code-changer delegates in 2 stages:
>  ① run deriver incremental mode as a subagent to record the new FRs in the SPEC (verification PASS) →
>  ② run the mapper's `references/promote-mode.md` as a subagent to promote/create those candidates into the STORYBOARD (verification PASS) →
>  ③ implement the new FRs in code.
>  **The order is forced** — ② reads the FRs ① recorded from the SPEC file, so deriver verification PASS is the mapper's entry precondition (the mapper never modifies the SPEC — R&R).
>  **Base 'addition'** (pure new FRs unrelated to candidates) uses the same 2-stage delegation — in ②, promote enrolls the new FRs as `[No UI]`
>  (delegate-mode step 3-b, only when a STORYBOARD exists — no anchor/mapping creation, keeping the coverage contract).

**(3) Delegation — mapping update (develojt-code-changer, conflict resolution):**
> When the human gives verdicts A (design wins)/B (SPEC wins) on the conflicts in `design/spec-conflicts.md`, develojt-code-changer
> receives them. When a deriver change transitions the violated FR to `[Removed]`+new ID under A, the STORYBOARD mapping points at a dead ID
> (stale — `verify-coverage` catches only missing new FRs, not lingering old ones). The changer passes the transition pairs and conflict verdicts
> explicitly and runs `references/remap-mode.md` as a subagent — full replacement of old FRs + conflict-A incorporation,
> B header refresh, resolved-section cleanup, with `verify-stale` (reverse direction) in the gate.
> **The order is forced** — deriver verification PASS is remap's entry precondition (the mapper never modifies the SPEC — R&R).
> **Base 'change/deletion'** (pure transitions unrelated to conflicts) uses the same remap delegation — transition pairs only (no conflict
> lists — modification `old FR → new FR` / deletion `old FR → (deleted)`, deletions cleaned up occurrence-by-occurrence with comment history)
> (delegate-mode step 3-b, only when a STORYBOARD exists).
> **Appearance release** (requirement invariant — SPEC unchanged, no deriver stage) uses the same remap delegation too — when the
> human decides a specific element's appearance departs from the design originals, develojt-code-changer (operations — revise's
> 'appearance-instruction input' section · delegate step 3-b) or develojt-code-builder (mid-development — its 'when a design change
> is needed' section) passes a **release list** (`SB-NN-MM (appearance-release — reason)`) alone and runs remap: mapping-row
> retirement (removal + comment history) + coverage-preserving enrollment (`[No UI]` **appearance-autonomy transition (human-decided
> release)**). The design originals (design/) are the starting baseline — frozen, never edited. From then on that element's
> appearance baseline is not the originals but the human instruction and the implemented code.

---

version: 1.0.0
latest: 2026.10.23
Made by develojt
