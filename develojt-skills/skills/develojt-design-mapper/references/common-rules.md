# common-rules — design mapping common rules (single truth)

This document holds the rules **both** DesignTheorist and DesignPractitioner follow identically.
Personas (perspectives) differ, but the rules, formats, and verdict criteria below bind both equally.

---

## 0. Mapping philosophy (why this work exists)

- **Design = source of truth for appearance (how it looks)** — layout, color, fonts, animation, placement.
- **SPEC = source of truth for function (what it does)** — what gets implemented.
- This work only **links the two via UI IDs**. **It creates no new features.**
- **Never modify the SPEC.** The SPEC is frozen input. Features present only in the design are **surfaced** as `[Candidate]`,
  and the human decides adoption later (this skill never decides).
- So the builder can follow without inference, **point instead of describing** (dual anchors).

---

## 1. UI element identification

### Design-asset reading priority (required)
Identification and mapping are grounded in the design/ assets. Read them in this priority (top-down; whatever exists is the baseline):
1. **If a README (design guide) exists, always read it in full** — the normative original for the screen list, global layout, states, interactions, and tokens.
   The "no whole-file Reads" rule applies to large screen sources (`.dc.html` etc.); **the README is the exception** (a small normative document).
   The 4-axis **states and transitions** in particular are hard to see in still screenshots and greps — identify them by cross-checking the README's behavior descriptions (Interactions/Behavior etc.).
2. Without a README → identify from the design files present (screen sources etc.) as the baseline (anchor checks still by Grep).
3. Screenshots only → identify from the screenshots as far as they go (source anchors: `[No source: screenshots only]`).

If **companion assets** the screen source loads or references exist (runtime/helper `support.js` etc., stylesheets, fonts, icons, images, mock data): record their existence **in the STORYBOARD Document Info shared-technical-assets row, as it is** (never write "absent" for a file that exists — confirm via `ls` and the source's load/reference declarations (`<script src>`, `<link href>`, `@import`, `url()`, fetch, etc.); if none: "none (ls-confirmed)"), and when the states/transitions reading needs them, consult them partially by grep (no whole-file Reads). Even when the README labels them "viewer-only / not production", never skip the record or the consult (that label only excludes the file from the builder's as-is use — it is not no-record, not no-consult — builder essential 3) — unlike the inventory (deleted after approval), this row persists into the final version, forming the 2nd safety net on top of the builder's direct check of the load/reference declarations (1st).

### What counts as a "UI element"
A meaning unit the user **sees or interacts with**. Buttons, inputs, toggles, cards, list rows, tabs, panels, badges,
charts, avatars, empty-state notices, loading indicators, and so on. Layout-only empty `<div>`s and pure wrappers are not elements.

### The 4 decomposition axes — sweep each screen through these four lenses to prevent identification omissions
Sweep one screen along these 4 axes. **What each axis finds is never turned into a new feature** — map it to an existing FR
(or `[Candidate]` if none) per §3·§4. The 4 axes are only "lenses for finding everything"; the output is always a mapping or an orphan.
1. **Affordances**: buttons, inputs, toggles, links, and other interactive elements — each implies one or more behaviors.
2. **States**: empty/loading/error/success variants — see "state variants" below (an error banner = failure-handling behavior).
3. **Transitions**: does an element's action move to another screen/state — check the FR for that movement (flow).
   A transition is not a separate element — **attach it to the trigger element** (button etc.), with a note ("→ transitions to {target}").
4. **Displayed data**: data values visible on screen (numbers, lists, sources, metrics, …) imply the **read/render behavior**
   producing them — check for a matching FR (or `[Candidate]` if none).

### Granularity — neither too fine nor too coarse
- Never elementize every pixel/div of a screen (excess).
- Never collapse one big screen into a single row (deficit).
- Criterion: **the unit the builder would ask "how do I build this" about**, or **a unit that could link to one FR**.

### Never miss state variants
When the design expresses **default / hover / active / disabled / loading / error / empty** for the same element, don't miss them.
- Variants of one element are grouped in one row's note (`SB-02-02 · variants: default/loading`), or a separate row when the meaning differs greatly.

### Motion (time-axis behavior) is notated `[Dynamic]`
An element with **time-axis behavior** that a still screen cannot capture (animation, transition effects, particles, auto-refresh — motion) gets
**`[Dynamic]` prefixed at the very front of its Description cell**. Example: `[Dynamic] background knowledge-graph animation`.
- Judge only by observable grounds: the source greps a time-axis declaration (`animation`, `transition`, `requestAnimationFrame`, `setInterval`, …),
  or the README describes that element's motion.
- This notation is the trigger for the **"cannot be judged by still comparison — check the motion on the running screen"** guidance
  in the builder's human screen comparison (builder workflow 7), because screenshots cannot in principle reveal missing or deviating motion.
- **Never add a column** — the in-cell prefix in the Description cell only (table shape and downstream verification scripts unchanged).

### ID scheme
- Screen level: `SB-NN` (NN = screen order, 2 digits per the inventory)
- Element level: `SB-NN-MM` (MM = element order within the screen, 2 digits)
- Once assigned, IDs stay stable (builder and reviews reference them by ID).

---

## 2. Dual anchor rules (the heart of this work)

Each UI element is identified by **two anchors**.

### Visual anchor (confirmed by eye)
`{screenshot file} · {region within the screen}` form. e.g., `02-search.png · bottom input bar`, `08-...png · top-right summary card`.
- Written so a human can instantly point at which screenshot, where.

### Source anchor (confirmed by grep)
A **stable identifier actually findable** in the screen source (`.dc.html` etc.). Priority:
1. **Unique text / placeholder** — e.g., `placeholder^="Search"`, `text "Export"`
2. **Unique class / component name** — e.g., `.result-card`, a `<sc-...>` component
3. **Structural path** (only when neither exists) — e.g., `left rail > 3rd nav item`

**Forbidden:**
- **Coordinates/pixel positions** (`x:120,y:400`) — break under responsive layouts and re-renders.
- **Volatile indexes** (`data-dc-tpl="37"`, auto-generated sequence numbers) — values change when the source regenerates.

### Self-verification (required)
After writing a source anchor, **actually grep it in the screen source** and confirm at least 1 hit.
- If it doesn't hit, or hits too many (>1 obvious spot per screen), switch to a more unique identifier.
- When the source truly has nothing (pure `<canvas>` graphics, dynamic generation, …): visual anchor only + `[No source: reason]`.

---

## 3. FR mapping rules

### Reading FRs from the SPEC
Requirement IDs in `spec/SPEC.md` have the `FR-NN-NNN` form (number NNN of EP-NN). Write these IDs in the mapping column.
**A row whose source cell (column 2) is `[Removed]` is not a live FR** (a requirement removed by negotiation or change mode — the same goes for an old SPEC's `~~FR~~` strikethrough-ID row):
it is a target of none of mapping, `[No UI]` classification, or coverage, and its ID is never written in the body, tables, or headers (history goes in HTML comments — the remap-mode convention.
`verify-coverage` does not require that ID, and `verify-stale` catches that ID in the body as a dead reference).

### FR IDs in full form — abbreviation forbidden
In mappings, `[No UI]`, and **every notation, FR IDs are written in full form** (`FR-19-002`). Even when grouping several FRs
in one cell, **never abbreviate** like `FR-19-001 / -002 / -003` — write **all full IDs**: `FR-19-001, FR-19-002, FR-19-003`.
Reason: the builder and verification trace specific FR IDs by grep; abbreviation makes `FR-19-002` invisible to grep and breaks traceability.

### N:M allowed (not 1:1)
- One UI may show/enable several FRs → list multiple FRs.
- One FR may appear on several screens/elements → that FR appears in multiple UI rows.

### Mapping verdict criterion
> **"If this UI disappeared, which FR's behavior could the user no longer observe or perform?"**

If such an FR exists, map it. Whether display (visibility) or manipulation (input/click), the criterion is an **observable connection**.
Never map by guessing internals ("this button probably calls an API") — judge only by visible behavior.

---

## 4. Orphan verdicts

| Notation | Definition | Verdict criterion |
|---|---|---|
| `[Candidate]` | The UI **implies a feature** but no matching FR exists in the SPEC | There is a "behavior lost if this disappears", and that behavior is not in the SPEC |
| `[Decorative]` | A purely visual element, unrelated to function | Its disappearance makes no FR unobservable (backgrounds, gradients, particles, …) |
| `[No UI]` | In the FRs but not visible on any screen | A non-UI feature (backend, policy, data rules) or a design omission |

**When in doubt, mark `[Candidate]`, not `[Decorative]`.** Surfacing for human verdict is safer than hiding.
For `[No UI]`, add a one-line guess: "normal (non-UI)" or "design omission".

### `[Decorative]` is excluded from requirement-ization only — it is not exempt from reproduction
- `[Decorative]` = "no matching FR needs to be created", not "it need not be implemented". As part of the design it is
  **the builder's appearance-reproduction target**, and downstream its reproduction is enforced by joblist appearance anchors and
  row completion conditions (the spliter co-loads it onto the same screen's first FR row — the builder must not check the row
  off until every anchor is reproduced).
- Therefore `[Decorative]` too is **always a row of the body table (with an SB ID)** — never placed in the orphan list or a separate section.
- **Global decorations** (backgrounds, frame effects, etc. shared by several screens) attach to the **common frame (shell) screen** on which
  they always appear, or, if no shell screen exists, to the **front-most screen where they appear**, taking that screen's SB ID.
  Notations without an SB ID such as `(global)` are forbidden — downstream (spliter anchor loading, verify_anchor_sync) **tallies
  by SB ID**, so without an SB ID it is caught by no gate and silently omitted.

### `[Candidate]` goes in the queue file, not the STORYBOARD
`[Candidate]` entries are never placed in the STORYBOARD body — record them **with their anchors in the separate queue file `design/spec-candidates.md`**
(when the human later adopts them into the SPEC, the UI ID and anchors are reused as-is — "filling the empty FR cell"). Therefore:
- Never write `[Candidate]` in the body table's Mapped FR cell — the body keeps **only mapped FRs and `[Decorative]`**.
- `[Decorative]` and `[No UI]` are not queue items (not SPEC-adoption targets, so they stay in the STORYBOARD).

### Conflicts — when the design and the SPEC contradict irreconcilably
Different from orphans (present on one side only). This is **the design and the SPEC violating each other over the same target**
(e.g., the design provides a dark-mode toggle; the SPEC fixes the theme and forbids changing it). Handle as `[Needs review]`:
- Record it **in the separate file `design/spec-conflicts.md`, not the STORYBOARD body**, in human language + options (A design wins / B SPEC wins).
- **The conflicting element's FR is still classified in the STORYBOARD body (mapping or `[No UI]`)** — that FR is alive in the SPEC and must not drop out of coverage. The conflict file additionally surfaces only that FR's **"violation case"**.
- The direction (fix the design vs revise the SPEC) is **never decided here** — the human decides.

---

## 5. Completeness (self-check before submitting)

- [ ] If a README (design guide) exists, **read it in full** and cross-checked against its screen/behavior descriptions (§1 priority).
- [ ] Recorded the companion assets' existence (runtime/helper, stylesheets, fonts, assets, data) **as it is** (no file that exists written as "absent" — §1).
- [ ] Swept **every screen** in the inventory (0 screens missed).
- [ ] Identified each screen's **interactive/display elements** as meaning units.
- [ ] **Confirmed every source anchor by grep** (or marked `[No source]`).
- [ ] Every SPEC **FR** is mapped to some UI or classified `[No UI]` (0 FRs missed).
- [ ] No orphans hidden — all surfaced as `[Candidate]`/`[Decorative]`/`[No UI]`.
- [ ] Every `[Decorative]` is a **body-table row with an SB ID** (0 orphan-list placements or SB-ID-less notations like `(global)` — §4) · elements with motion notated `[Dynamic]` (§1).

---

## 6. Review (cross) stance

Priorities when reviewing the counterpart's mapping:
1. **Anchor validity** — do the counterpart's source anchors actually grep? If not, that's the top flag.
2. **Omissions** — screens/elements/state variants the counterpart missed.
3. **Verdict disagreements** — `[Candidate]` vs part-of-FR-X, `[Decorative]` vs `[Candidate]`, and other judgment differences. Argue with grounds.

**SPEC interpretation questions** the two of you cannot decide (is this UI within FR-X's scope, or an outright omission?) are raised as `[Escalation]` for the human.

---

## 7. Output format

Follow the structure, headers, and table columns of `templates/STORYBOARD-template.md` exactly. Never alter columns unilaterally.
`[Candidate]` entries are written to `design/spec-candidates.md` in the `templates/spec-candidates-template.md` structure (same columns as the body table + empty FR cell).
`[Needs review]` (conflicts) are written to `design/spec-conflicts.md` in the `templates/spec-conflicts-template.md` structure (anchor table + human-language options).
All prose is written in English (code identifiers and technical terms as-is).

---

## 8. What not to do (summary)

- Never finalize a design-only feature into the SPEC/code — surface it as `[Candidate]`.
- Never modify the SPEC.
- Never use coordinates or volatile indexes in source anchors.
- Never describe UI in words alone — attach pointable dual anchors.
- Never hide orphans.
- Never map by guessing internals — observable behavior only.
- Never generalize product/domain-specific terms into rules — the domain is filled by design/.
