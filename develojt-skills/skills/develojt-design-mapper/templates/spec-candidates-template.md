# {project name} — SPEC adoption candidate queue (spec-candidates)

> A queue collecting features present in the design but not yet in the SPEC (`[Candidate]`), **with their anchors**.
> They live in this file, not the STORYBOARD — once the human decides SPEC adoption, the UI IDs and anchors are reused as-is:
> the deriver creates the new FRs and design-mapper promotes those FRs into the STORYBOARD ("filling the empty FR cell").
> This document never decides — it only surfaces.

## Queue Items

The table columns are **identical** to the STORYBOARD body (so adopted rows move over as-is). "Target FR" stays `(not adopted)` until adoption.

| UI ID | Visual Anchor | Source Anchor (grep) | Description (what behavior it implies) | Target FR |
|---|---|---|---|---|
| {SB-NN-MM} | {screenshot file · region} | {grep-able stable identifier} | {functional behavior with no matching FR} | (not adopted) |

<!-- Anchor rules are the same as the STORYBOARD: unique text/placeholder > class > structural path. Coordinates and volatile indexes forbidden. -->
<!-- To group by screen, subdivide with ## SB-NN subheadings (table columns stay the same). -->

---

> **Why keep anchors attached:** when adopted, the row is promoted into the STORYBOARD body as-is (fill the Target FR cell and move).
> That's why source anchors must be as stable as the STORYBOARD's (reuse — re-identification 0).
> `[Needs review]` (design conflicting with the SPEC) is a different beast and never enters this queue — it lives in the separate file `design/spec-conflicts.md`.
