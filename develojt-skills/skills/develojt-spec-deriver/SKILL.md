---
name: develojt-spec-deriver
description: >
  Design-document automation skill that generates spec/SPEC.md from plan/PRD.md, or incrementally adds new features to an existing SPEC.md.
  [Full generation] Use when the user mentions 'make a SPEC', 'generate the design document', 'design document from the PRD', 'formalize requirements', etc.
  Always trigger when a design-document request appears in a context where plan/PRD.md exists.
  [Incremental] Use when spec/SPEC.md already exists and the user wants to append a new feature — 'add a feature', 'add to the SPEC', 'add a requirement', 'put this feature in', etc. (no negotiation; adds new IDs only after format tagging and dependency assessment).
  [Change] Use change mode when the user wants to modify or remove existing requirements in spec/SPEC.md — 'modify/change this requirement', 'remove/delete this feature', etc. (no negotiation; non-destructive transition via [Removed] + new IDs).
  Deliverable: spec/SPEC.md

disable-model-invocation: true
allowed-tools: Task, Agent, Read, Write, Edit, Bash, Grep, Glob, AskUserQuestion
argument-hint: "[optional: path to plan/PRD.md] | [incremental: description of the feature to add]"
---

# develojt-spec-deriver — agent-negotiation-based SPEC generator

User request: $ARGUMENTS

**[Required] Lead language rule:**
Everything the Lead shows the user (progress reports, escalation questions, completion notices, review requests, …)
must be written in **English**.

**[Required] Human-facing sentences:** Every output shown to a human — reports, explanations, questions, approval requests, and the like — follows `rules/human-language.md`; sentences that ask for a decision follow its §2 (the human-decision sentence rule).

## Position in the pipeline (understand the flow before working)

```
[planner]    plan/PRD.md    — human-led. AI provides hints (seeds)
[this skill] spec/SPEC.md   — infers and expands epic intent into concrete EARS
[spliter]    spec/joblist.md — progress ledger for developing in slices
[builder]    src/           — @spec-traced code, implemented bundle by bundle in ledger order (EP by EP if no joblist)
[pdca]       spec/findings.md — static-completeness loop entered automatically after each implementation. Quiescence defines bundle completion (appearance-comparison target bundles: + screen-review ledger registration & registration confirmation; the comparison itself runs as one batch session after full implementation completion)
```

This skill works in the **opposite direction** from the planner.
Where the planner converged human intent into natural-language seeds (epics),
this skill **exercises intent-reading, analogy, and inference to the fullest** to concretize and expand those seeds into EARS requirements.
SPEC.md is the source of truth for every later stage (spliter, builder) — whatever is missing here is missing from the code too.

## What this skill does

A **domain theory expert (Theorist)** and a **senior hands-on expert (Pragmatist)**
analyze and design from the same PRD.md independently, **exchange reviews and rebuttals via files**, and negotiate SPEC.md into existence.

The Lead (the main session running this skill) only orchestrates rounds, relays user questions, and handles consolidation, verification, and saving.
**The content of design and negotiation is made entirely by the two agents. The Lead never intervenes in content.**

> **Communication method (important):** agents communicate via **file relay**, not real-time messaging.
> Each round's deliverables (drafts, reviews, responses) are saved as files under `spec/`,
> and the next round's agent reads those files. The Lead only guarantees round order.
> This approach depends on no specific harness feature (team messaging), so it behaves identically everywhere.

---

## The three modes — decide before starting

On receiving a request, first decide which mode applies.

- **Full generation mode (default)** — `spec/SPEC.md` does not exist, or the SPEC is being created from the whole PRD for the first time.
  Proceed with STEPs 1–6 below.
- **Incremental mode** — `spec/SPEC.md` already exists and the user wants to add **one new feature (a single, already-decided requirement)**.
  No negotiation. **Read `references/incremental-mode.md` and follow only that procedure.** The existing SPEC is frozen; only new IDs are added.
- **Change mode** — `spec/SPEC.md` already exists and the user (or a develojt-code-changer delegation) requests **modification or deletion of existing requirements**.
  No negotiation. **Read `references/change-mode.md` and follow only that procedure.** Nothing is erased — a non-destructive transition via `[Removed]` + (for modifications) new IDs.

> Decision criteria: with an existing SPEC, "add/append" → incremental; "modify/delete existing requirements" → change; otherwise full generation. When ambiguous, ask the user once.
> (Before change mode existed, the deriver stopped on modify/delete requests — now it accepts them as non-destructive transitions. Changing only the text while the meaning changes is still forbidden: change-mode forces `[Removed]` + new ID, preserving the traceability chain.)

---

## Agent composition

| Role | Expertise | Responsibility |
|---|---|---|
| **Theorist** | Domain theory expert (PhD-level) | Academic grounding, logical rigor, standards/patterns/principles. Complete, with nothing missing. |
| **Pragmatist** | Senior hands-on expert (10+ years) | Field experience, operational incident cases, feasibility checks. Removes over-engineering + adds field-essential items. |
| **Lead** | Round orchestrator | Guarantees round order, relays user ↔ agent questions, consolidates/verifies/saves. Never intervenes in design. |

**Spawn prompt composition (common to all rounds):**
Every time an agent is spawned, concatenate the three parts below in this order. Include file contents **verbatim**.

```
1. Full text of references/common-rules.md   (EARS rules · derivation philosophy · negotiation principles — identical for both sides)
2. Full text of references/{theorist|pragmatist}-prompt.md   (persona)
3. The round's work instruction   (the block specified in the STEP below)
```

The `{role}`/`{counterpart}` placeholders in the work instruction block are substituted by the Lead for the spawn target
(e.g., when spawning Theorist: `{role}`=Theorist, `{counterpart}`=Pragmatist).

Agents are stateless. Specify the file paths needed for each round in the work instruction
so the agent reads them directly.

---

## Deterministic items (non-negotiable)

Items the human explicitly selected (`[x]`) in PRD section 2 (System Setup) are **deterministic constraints**:

| PRD item | Nature | Reflected in |
|---|---|---|
| Runtime environment | Constraint | SPEC Document Info |
| Operating system | Constraint | SPEC Document Info |
| Development type | Constraint | SPEC Document Info |
| Core technologies (language/framework/DB/middleware/model) | Constraint | SPEC Document Info |
| User authentication or not | Constraint | SPEC FR/NFR scope decision |
| External integration or not | Constraint | SPEC FR/NFR scope decision |

These items are not negotiable; both agents accept them as-is (detailed rules in common-rules.md).
Even if "Core Technologies" is empty, agents never decide it on the user's behalf — the deriver is a consumer of constraints, not a producer.
Undecided items are returned to the user at the STEP 1 entry check.

---

## Overall flow (full generation mode)

```
STEP 1  Prepare        — check PRD, create spec/
STEP 2  Independent drafts — spawn both agents in parallel → draft-{role}.md (neither sees the other)
STEP 3  Cross-review   — parallel spawn → review the counterpart's draft → review-{role}-r1.md
STEP 4  Negotiation responses — parallel spawn → accept/rebut/compromise on disagreements → review-{role}-r2.md
STEP 5  Final versions — parallel spawn → apply agreements + unagreed as [Needs review] → spec-{role}.md
STEP 6  Consolidate·verify·approve — Lead: merge → SPEC.md → 3 verifications → user approval → cleanup
```

Between STEPs the Lead confirms the deliverable files exist with their summary lines and reports progress to the user in one line.
**Escalation check:** after STEP 3, `grep -l "\[Escalation\]" spec/review-*-r1.md`;
after STEP 4, `grep -l "\[Escalation\]" spec/review-*-r2.md` (that round's files only — prevents re-detecting already-handled earlier rounds).
If present, read those items, ask the user via AskUserQuestion, and include the answers in the next STEP's work instruction.

### STEP 1: Prepare

```bash
ls plan/PRD.md
mkdir -p ./spec
```

If PRD.md is missing, stop:
> "plan/PRD.md not found. Please generate the PRD first with the develojt-spec-planner skill."

If the PRD's `## 4. Status` is not "Finalized", confirm with the user:
> "The PRD status is not 'Finalized'. Generate the SPEC as-is, or refine the PRD further?"

**[Required] System-setup undecided check:** if any of Language/Framework/DB/Middleware (and Model, if a Model row exists) under the PRD's `### Core Technologies` is blank,
or user authentication / external integration is checked "Don't know yet", do not proceed — confirm with the user
(`None` and "No" are valid decided values):
> "The PRD system setup has undecided items: {list}.
>  Decide them now and I'll update the PRD and proceed. (You may also return to develojt-spec-planner)"

Filling undecided items by agent guess or proposal is forbidden — the human is the decision-maker for system setup.

### STEP 2: Independent drafts (2 parallel spawns)

Spawn both agents **simultaneously**. Work instruction:

```
[Task — independent draft]
Read plan/PRD.md and write a SPEC draft per the common rules' derivation philosophy and 4-stage derivation.
- [Forbidden] Do not read the counterpart expert's files — independent drafting prevents bias.
- Template: .claude/skills/develojt-spec-deriver/templates/SPEC-template.md (global install: ~/.claude/skills/develojt-spec-deriver/templates/SPEC-template.md)
- Keep the order: derive → formalize. Do not start by filling the template.
- Save to: spec/draft-{role}.md
- After saving, repeat the 2 verifications (see common rules) until PASS.
- Final response: one line only — "Draft complete. FR n / NFR n / [Implicit] n"
```

Gate: `ls spec/draft-Theorist.md spec/draft-Pragmatist.md` — both must exist to proceed to STEP 3.
On failure: re-spawn only the side whose deliverable is missing, once, with the same instruction; if it fails again, report to the user and stop.

### STEP 3: Cross-review (2 parallel spawns)

```
[Task — cross-review r1]
Read your own draft (spec/draft-{role}.md) and the counterpart's draft (spec/draft-{counterpart}.md) and write a review.
- Save to: spec/review-{role}-r1.md
- Format (keep this structure):
  # Review r1 — {role}
  Summary: agree N / disagree N / proposals N / escalations N
  ## Agree (only the list of counterpart item IDs you agree with)
  ## Disagree (per item: target | claim | grounds — in your persona's negotiation stance)
  ## Proposals (items the counterpart lacks but needs; items the counterpart has but are excessive)
  ## [Escalation] (PRD interpretation questions the two of you cannot decide — omit the section if none)
- Final response: the summary line only.
```

Gate: both review-*-r1.md exist. On failure: re-spawn only the missing side once with the same instruction; on repeat failure, report to the user and stop.
Escalation check → if any, ask the user.

### STEP 4: Negotiation responses (2 parallel spawns)

```
[Task — negotiation response r2]
Read both drafts and both r1 reviews (spec/draft-*.md, spec/review-*-r1.md).
{If escalation answers exist: include "User answers: ..."}
Answer each disagreement and proposal raised against you:
- Accept (state the reason) / rebut (must bring new grounds — repeating the same claim is forbidden) / propose a compromise
- Save to: spec/review-{role}-r2.md
- Summary line at the head of the format: "Accepted N / Rebutted N / Compromised N / Unresolved N"
- Final response: the summary line only.
```

Gate: both review-*-r2.md exist. On failure: re-spawn only the missing side once with the same instruction; on repeat failure, report to the user and stop.
Escalation check.

### STEP 5: Final versions (2 parallel spawns)

```
[Task — final version]
Read every file so far (2 drafts, 4 reviews{, user answers}) and write the final SPEC.
- Apply every accepted/agreed change.
- Do not force agreement on unresolved items — mark them [Needs review: reason].
- Record the "Negotiation History Summary" table (issue, conclusion, conceding side, rationale).
- Save to: spec/spec-{role}.md
- After saving, repeat the 2 verifications until PASS.
- Final response: one line only — "Final complete. Agreed N / [Needs review] N"
```

Gate: `ls spec/spec-Theorist.md spec/spec-Pragmatist.md` — **both must exist** to proceed to STEP 6.
Never start consolidation with only one side present.
On failure: re-spawn only the missing side once with the same instruction; on repeat failure, report to the user and stop.

### STEP 6: Lead consolidation · verification · approval · cleanup

**[Required] Context-saving consolidation** — Reading both files whole (Read) spikes context consumption.
Check only the differences and consolidate with this procedure:

```bash
# 1. Check only the differences between the two sides with merge-helper
bash .claude/skills/develojt-spec-deriver/scripts/merge-helper.sh spec/spec-Theorist.md spec/spec-Pragmatist.md

# 2. Copy the recommended base file as the final version
cp spec/spec-{base side}.md spec/SPEC.md

# 3. When merge-helper shows IDs present on only one side,
#    grep the base file to check whether it already contains them in different wording.
#    Apply only genuine omissions. (The same requirement often exists under a different ID/wording)
```

If the two files are completely identical, merge-helper recommends "use as-is".
Only when differences exist, apply these consolidation principles:

```
Consolidation principles (apply to differences only):
1. Agreed items — adopt whichever side's wording is more precise EARS
2. Identical wording on both sides — use as-is
3. [Needs review] items — state both sides' opinions and give the user a choice
4. IDs on one side only — grep the base file for the same requirement in different wording.
   Apply if genuinely missing; ignore if already included
5. ID conflicts — prefer Theorist's IDs
```

**[Required] Duplicate requirement detection:**
After consolidation, detect duplicate requirements across epics by these criteria:
- **Same trigger + same behavior**: the same behavior described under the same When/While/If condition in different epics
- **Subsumption**: one FR is a superset of another

For detected duplicates, keep the more specific one or merge into one, listing both sources (e.g., `PRD EP-12, EP-23`).
However, never empty an EP section by merging — if all of an EP's requirements merge into another EP,
leave one representative FR in that EP with both sources listed (avoids conflicting with verify_prd_coverage's empty-epic check).

**[Required] Verification pipeline (right after saving, before requesting approval):**

```bash
bash .claude/skills/develojt-spec-deriver/scripts/verify-sections.sh spec/SPEC.md
bash .claude/skills/develojt-spec-deriver/scripts/verify-sources.sh spec/SPEC.md
python3 .claude/skills/develojt-spec-deriver/scripts/verify_prd_coverage.py plan/PRD.md spec/SPEC.md
```

If any stage has an ERROR, fix and re-verify. The Lead never writes content here —
state the error items (missing epic numbers, …) in a work instruction, re-run the responsible agent, then re-consolidate and re-verify with its output.
Request user approval **only after all PASS**.
(The third script checks that every PRD epic is fully expanded into the SPEC —
 "is anything missing from the human's epics" is this skill's reason to exist, so it must never be skipped.)

**[Required] Negotiation bias check:**
During consolidation, check the **conceding-side distribution** in the "Negotiation History Summary" table.
If one side's concessions are 70% or more of the total, report to the user
(formula: denominator = rows whose conceding side is recorded as Theorist or Pragmatist — compromise rows excluded; numerator = one side's rows among them):
> "In the negotiation, Theorist (or Pragmatist) conceded M of N items.
>  One perspective may be under-represented. Would you like to review?"
This is for **user awareness**, not automatic correction.

**[Required] User approval gate:**

```
Lead → "The SPEC draft is complete.
        - N requirements total (directly derived N / [Implicit] N)
        - [Needs review] items: N (list them)
        - Cross-epic duplicates removed: N
        - Negotiation bias: Theorist conceded N / Pragmatist conceded N / compromises N
        - 3 verifications PASS
        Please review and approve to finish."

User response:
  "approve" / "OK" / "proceed" → cleanup stage
  Change request → fix the items → re-verify → re-review (repeat until this gate passes again)
```

**Cleanup (after approval):** remove intermediate/temporary files.

```bash
cd spec && rm -f draft-*.md review-*.md spec-Theorist.md spec-Pragmatist.md && cd ..
```

After cleanup, the only things left in spec/ must be SPEC.md (and existing artifacts other skills created — joblist.md, findings.md, findings-archive.md, ARCHITECTURE.md, run-profile.md, screen-review.md, etc.).

---

## What not to do

- The Lead never creates design or negotiation content. It handles only round orchestration and simple consolidation per the principles
- Never start designing before understanding the PRD fully
- Never finalize the first draft without negotiation
- Never skip a STEP or proceed without the round's deliverable files
- Never concede without grounds — compromise happens through logic
- Never omit the PRD source from a requirement
- **Never put implementation-level numbers (delta clamp, buffer sizes, …) into the SPEC** — develojt-code-builder's autonomous territory
- **Never use unverifiable phrases ("high quality", "naturally", …) in requirements** — replace with measurable criteria
- **Never leave identical requirements duplicated across epics** — duplicate detection at consolidation is mandatory
- Never skip temporary-file cleanup after the work completes
- Never alter the template's section order or header names on your own
- Never skip running the verification scripts
- **Never treat deterministic items (PRD section 2) as negotiable**
- **Never finish without user approval**
- **Never embed domain-specific examples or content (game terms, product names, …) in the skill** — the skill holds only form and blanks. The domain is filled by the PRD (anti domain-anchoring)
- **Never write requirement responses as unobservable internal phrasing ("processes it", "manages it", …)** — they must be judgeable from outside by behavior alone
- **Never leave a quantitative/enumerable item blank without either a value or the `[Free: reason]` notation** — distinguish omission from intended freedom

---

## Reference files

Paths are relative to the skill install location: `.claude/skills/develojt-spec-deriver/` (local first) or `~/.claude/skills/develojt-spec-deriver/`.

| File | Description | When |
|---|---|---|
| `references/common-rules.md` | Common rules (EARS · derivation philosophy (including runtime-base NFRs) · negotiation principles) — single truth | Part 1 of the prompt at every agent spawn |
| `references/theorist-prompt.md` | Theorist persona | Part 2 of the prompt when spawning Theorist |
| `references/pragmatist-prompt.md` | Pragmatist persona | Part 2 of the prompt when spawning Pragmatist |
| `references/ears-guide.md` | Detailed EARS grammar guide (for the Lead) | When the Lead needs format checks during consolidation |
| `references/incremental-mode.md` | Incremental mode procedure | Incremental mode only |
| `references/change-mode.md` | Change mode procedure (non-destructive transition for modifying/deleting existing requirements) | Change mode only |
| `templates/SPEC-template.md` | SPEC literal skeleton | Basis for agent drafts |
| `scripts/verify-sections.sh` | Section order/omission verification | Right after agent saves + after Lead consolidation |
| `scripts/verify-sources.sh` | Source tag/ID/statistics verification | Right after agent saves + after Lead consolidation |
| `scripts/verify_prd_coverage.py` | PRD epic → SPEC EP full-expansion verification | After Lead consolidation [Required] |
| `scripts/merge-helper.sh` | Diff-based consolidation helper for the two sides | STEP 6 (used instead of whole-file reads) |
| `scripts/query_impact.py` | Impact reverse-query (changed ID → same bundle/series/behavior chain — joblist required) | Change mode step 5 (development phase) |
| `scripts/query_chain.py` | Operations-phase impact query (changed ID → SPEC behavior-chain peers only — joblist not required) | Change mode step 5 (operations phase) |

---

version: 1.0.0
latest: 2026.10.23
Made by develojt
