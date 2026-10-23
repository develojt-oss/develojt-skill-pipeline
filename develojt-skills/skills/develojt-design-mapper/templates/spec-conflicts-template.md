# {project name} — design↔SPEC conflicts (awaiting human verdict)

> Points where the design and the SPEC **contradict each other over the same target** (both exist, yet can't coexist).
> If the builder carried the design over as-is it would violate the SPEC, so the human must decide **"design wins / SPEC wins"**.
> This document never decides — it only **surfaces the conflict in human language and presents the options**.
> The conflicting elements' FRs are also classified in the STORYBOARD body (coverage maintained) — this file collects **only the "violation cases"**.

## Conflict 1 — {one-line title: what conflicts, where}

| UI ID | Visual Anchor | Source Anchor (grep) | Design Behavior | Violated SPEC |
|---|---|---|---|---|
| {SB-NN-MM} | {screenshot · region} | {grep-able stable identifier} | {what the design enables} | {FR-NN-NNN} |

- **The design**: {human language — what the design was drawn to allow}
- **The SPEC ({FR-NN-NNN})**: {human language — what the SPEC requires/forbids}
- **Option A · Design wins** → revise the SPEC to allow the design (develojt-code-changer 'conflict resolution' intake — the deriver modifies that FR)
- **Option B · SPEC wins** → drop that design element and implement per the SPEC
- **Recommendation**: {neutral reference — security/consistency grounds etc. Omit if none}
- **Decision**: ☐ A   ☐ B   _(the human fills this)_

<!-- Repeat ## Conflict N sections for as many conflicts as exist. The table serves verify-anchors (source anchor grep); the description and options serve the human verdict. -->
<!-- Anchor rules are the same as the STORYBOARD: unique text/placeholder > class > structural path. Coordinates and volatile indexes forbidden. -->

---

> **Flow after decision**: whichever of A/B, **after the human decides**, it is received by develojt-code-changer **'conflict resolution'**
> (with this file or the conflict numbers as input). A → deriver change (SPEC revision) → mapper remap (mapping update + cleaning this file's
> resolved sections) → code. B → SPEC and mapping invariant — remap (header refresh + resolved-section cleanup) + code check/correction.
> Resolved conflicts are removed from this file (consumed).
