# {project name} — STORYBOARD (design↔SPEC traceability mapping)

> The **bridge document** linking the design/ package and spec/SPEC.md.
> Design = source of truth for appearance, SPEC = source of truth for function — this document only **links the two via UI IDs**.
> Each UI is identified by **dual anchors** (visual + source), so the builder finds appearance without inference.
> Features present only in the design are never built — they are surfaced as `[Candidate]`. The SPEC is never modified.

## Document Info

| Item | Content |
|---|---|
| Project name | {project name or "Untitled"} |
| Design package | {design/ path · key files (README, sources, screenshots)} |
| Shared technical assets | {file names of the companion assets the screen source loads or references (runtime/helper `support.js` etc., stylesheets, fonts, assets, data) — confirmed via `ls` and the source's load/reference declarations (`<script src>`, `<link href>`, etc.), as they are. If none: "none (ls-confirmed)"} |
| SPEC baseline | {spec/SPEC.md version/date} |
| Screen count | {N} |
| UI element count | {N} |
| FR coverage | {mapped + No-UI classified / total FRs} (missing FRs: {0}) |

## Anchor Notation Rules

- **Visual anchor**: `{screenshot file} · {region within the screen}`
- **Source anchor**: a stable identifier grep-able in the screen source (unique text/placeholder > class > structural path).
  Coordinates and volatile indexes forbidden. If nothing can be found: `[No source: reason]`.
- **Mapped FR**: `FR-NN-NNN` (N:M allowed) · `[Decorative]` (excluded from requirement-ization only — a reproduction target. Global decorations too, as body rows of the shell/common screen — SB-ID-less notations forbidden, common-rules §4). **`[Candidate]` is never written in this body** —
  it is separated into the queue file `design/spec-candidates.md`.

---

## SB-01: {screen name}     ← {README screen source} / {screenshot file}

| UI ID | Visual Anchor | Source Anchor (grep) | Description | Mapped FR |
|---|---|---|---|---|
| SB-01-01 | {file · region} | {identifier} | {element} | {FR-... / [Decorative]} |
| SB-01-02 | {file · region} | {identifier} | {element} | {FR-...} |

<!-- State variants go in a note: "SB-01-02 · variants: default/loading/error" -->
<!-- An element with motion (animation, transition effects, …) gets [Dynamic] at the very front of its Description cell — e.g. "[Dynamic] background particle animation" (common-rules §1) -->
<!-- Repeat SB-NN sections for as many screens as exist. -->

## SB-02: {screen name}     ← {source} / {screenshot}

| UI ID | Visual Anchor | Source Anchor (grep) | Description | Mapped FR |
|---|---|---|---|---|
| SB-02-01 | {file · region} | {identifier} | {element} | {FR-...} |

---

## Orphan List

> **`[Decorative]` never goes in the orphan list** — it is a body-table row (SB ID). Global decorations attach to the shell/common screen (common-rules §4).
> **`[Candidate]`** (in the design but not the SPEC) lives not in this document but in the separate queue file **`design/spec-candidates.md`** ({N} items).
> The human decides SPEC adoption via develojt-spec-deriver incremental mode (this document never decides).

### [No UI] — in FRs but not in the design
> To be judged: a non-UI feature (normal) or a design omission.

| FR ID | Requirement gist | Guess |
|---|---|---|
| {FR-..-...} | {gist} | {backend/policy (normal) or design omission} |

---

## Design↔SPEC Conflicts

> **`[Needs review]` (conflicts) live not in this document but in the separate file `design/spec-conflicts.md`** ({N} items).
> The human decides "design wins / SPEC wins" and routes it to the builder.
> The conflicting elements' FRs are also classified in the body above (mapping/`[No UI]`) — coverage maintained.
