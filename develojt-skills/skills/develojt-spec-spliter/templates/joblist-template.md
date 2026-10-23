# Job List — {project name}

> Progress ledger (todo) based on SPEC.md. The truth of requirements is the SPEC; this document only points at "how far we got / what's next / what notes exist".
> Checking the status cell is the progress state itself. However, the final truth of "what is finished" is the code's `@spec` tags (this ledger is their quick summary view).

| Base SPEC | Updated |
|---|---|
| spec/SPEC.md | {YYYY-MM-DD} |

---

## Work Unit Definitions

- **Bundle (completion unit)** = a group of tags that physically need each other (calls, data structures, event subscriptions). One bundle runs complete on its own. The coder **picks up one bundle whole**, implements, records, and completes it.
- **Scaffolding (foundation layer)** = the foundation shared by multiple bundles (a code foundation such as config, types, events, boot, build setup + the runtime base — containers/runtime, storage schema and startup, middleware, resident service serving, shared contracts/libraries). It belongs to no feature bundle and is laid **before all bundles**. Scaffolding complete = the walking skeleton (an empty system that builds and boots — the builder's boot gate confirms it).
- **Order** = top to bottom. Scaffolding first, then bundles in dependency order. Work from the first unchecked item.
- **Series** = bundles/tags built the same *way* (method consistency). A different axis from bundles (physical dependency). The series' first item becomes the reference implementation.

---

## 0. Scaffolding (foundation layer — first)

> The foundation every bundle builds on. Made once; later bundles only reference it (never rebuilt).

| Done | SPEC ID | Notes / Hints |
|---|---|---|
| [ ] | NFR-00-000 | |

---

## Work Table (bundle units)

> Each bundle is a unit made complete by physical dependency. The coder finishes one bundle whole, records it, then moves to the next.

### Bundle 1: {bundle name — what completes}

| Done | SPEC ID | Series | Notes / Hints |
|---|---|---|---|
| [ ] | FR-00-000 | — | |

### Bundle 2: {bundle name}

| Done | SPEC ID | Series | Notes / Hints |
|---|---|---|---|
| [ ] | FR-00-000 | — | |

---

> **Series**: the name for bundles that must be built the same way (`—` if none). The series' first item becomes that series' reference implementation.
> **Notes / Hints**: only what the code alone can't tell, or what affects the next work's approach/wiring — one line. Only five kinds:
> - Sibling pointer — `follows FR-11-001 approach` (points at the same series' reference implementation)
> - Intentional deferral — `wire up the calls into the supply code Bundle 3 built, on this row (Bundle 3 deferral handoff)` — a deferral is written on **the resolving bundle's row** (not the leaving side's). The work that picks up the row is the resolution owner
> - Pitfall — `duplicate arrivals of the same input; process only the first`
> - Tech adoption record — `{name} {version} adopted` (left by the builder during implementation)
> - Appearance anchor — `Appearance: SB-02-01·SB-02-05` (recorded by the spliter when design/STORYBOARD.md exists — every UI ID mapped to that FR + the same screen's `[Decorative]` IDs on that screen's first FR row. For multi-FR-mapped UIs and decorations alike, one SB ID rides on exactly one ledger row — the front-most mapped row. The builder checks the row only after every anchor's appearance is reproduced)
> Never write the "what gets built" (in the SPEC) or the "how it works" (in the code).

---

## Parallel Candidates (optional — information layer)

> Groups of bundles with no coupling at all between them, safe to pick up at the same time — only pairs that meet **all** 5 listing conditions (no order dependency · no deferral ties · series independence · screen separation · scaffolding excluded) (SKILL 'joblist structure' 4). It is the basis when the builder proposes a parallel wave; whether to run it is decided by human approval. If no pair qualifies, do not create this section at all.
> It carries no FR/NFR IDs or appearance anchors (bundle numbers only) — an information layer outside the 3 verification scripts' checks.

| Group | Bundles | Basis |
|---|---|---|
| P1 | Bundle {A} · Bundle {B} | no order dependency · no deferral ties · series independence · screen separation |

---

## Past Issues (reference)

> Archive of resolved notes/issues (optional). You need not read it when it is irrelevant to current work.

| SPEC ID | Issue | Status |
|---|---|---|
| | | |
