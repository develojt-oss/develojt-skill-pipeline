# Artifact Seats Protocol (Artifact Seats)

This file sets **where the records produced while a project progresses are placed, and in which direction they connect to the official documents**.
The content, format, and procedures of each artifact are set by its owning skill — this file sets only the seats and the directions.

- **Covered**: records such as documents, reports, research, inspections, and handovers.
- **Not covered**: product files such as code, tests, configuration, and assets (their seats are set by the tech stack's conventions and the structure contract `spec/ARCHITECTURE.md`),
  and the internal structure of official artifacts whose seats the owning skill has already set.
- **A seat goes down to the top-level folder** — the substructure below it is autonomous and not covered by this protocol.

**In one sentence: seats exactly as in the table below, conclusions into the official documents, the handoff for transfer only, decisions into the document they
govern — for a kind not in the table, ask the human before creating a new folder.**

## 1. Seat table

| Kind | Seat | Direction relative to the official documents |
|---|---|---|
| Official artifacts | `plan/PRD.md` · `spec/` (SPEC, ARCHITECTURE, joblist, findings (+archive, rejected), run-profile, screen-review) · `design/` (STORYBOARD, spec-candidates, spec-conflicts — the README and screen sources are design originals) | Written only through each owning skill's procedure — this row is a pointer |
| Spike (measurement) | `spike/<target>/` | Exactly the planner's technology-verification procedure — the result goes into the PRD's `### Technology Verification` with the source `measured (spike/…)`, and the code is discarded code (no bringing it in). The product's test code is not a spike — it goes in the tech stack's conventional seat (`tests/`, etc.) |
| Research | `research/` — research work-in-progress, source excerpts, comparison tables, full reports | **Conclusions go into the official documents** — in the planning phase, the PRD's `### Technology Verification` and `### Core Technologies`; after that, the procedure of the relevant phase (requirements via a deriver transition, structure via an ARCHITECTURE revision). The folder keeps only the grounds, never the decisions. Web access and downloads follow the resource-acquisition ladder as-is |
| Security inspection (external standards) | `security/` — the standard documents referenced (originals, checklists) and inspection result reports | **Code fix items** from an inspection **go to `spec/findings.md`** (there is one defect ledger) — a report is a record of the inspection's facts, not a defect ledger. Code-writing norms are `security-conventions.md` as-is |
| Submission/delivery documents | `deliverables/` — may or may not exist depending on the project | **One-way**: the PRD, SPEC, ARCHITECTURE, joblist, and findings are the sources, and submission documents are derivatives — changes of content are made at the source (that skill's procedure) and the document is regenerated. Never edit a submission document directly and leave it out of step with its sources |
| Product README | Root `README.md` (**required**) — the frame is the builder's `templates/README-template.md` (7 required sections: Overview, Requirements, Installation, Configuration, Running and usage, Operations, License and third-party notices + optional sections after them) | Derived sections **point to their sources instead of copying values** (PRD, SPEC, run-profile, joblist install records, manifests, LICENSE) — the only copies are install and run commands. The operations and optional sections have the README as their source. A section that does not apply says `Not applicable — reason`. No credential values. **When installation, configuration, or running changes, align the relevant section in that work** (whether during development or operations). An existing README is not overwritten — only its required sections are filled in. The first generation is the builder's (when the run profile is finalized) |
| Session handoff | One file, `spec/handoff.md` | §2 |
| Human decisions and agreements | **No separate ledger** — a decision is recorded in place in the document it governs | §3 |

- Names are exactly as in the table — never make synonyms, translations, or a different name per session. If a kind not in the table is needed, **ask the human for its seat before
  creating a new folder or file** (the failure direction goes to a question, not to arbitrary naming).
- No seat is inside `.claude/` — it is a deployed copy, read-only (the top of `code-conventions.md`).

## 2. Session handoff — a transfer-only envelope, not a ledger

- **Role**: letting the next session, which knows nothing, take over work that cannot finish in one session because of the context limit —
  that is all. It holds four things: ① **Position** — which phase, how far into which skill (ledger pointers: the joblist's
  current row, findings' active rows, the last commit) ② **Context** — the work that was stopped midway and why ③ **Next step**
  ④ **Items not yet reflected in the official documents** — decisions and changes made during the session that have not yet gone into their official seats (being empty is normal).
- **What it does not hold**: history (it is in git, `spec/findings-archive.md`, and the ARCHITECTURE revision history), to-do lists (they are in the joblist and
  findings' active rows), and the body of decisions (it is in the seats of §3) — the handoff holds only pointers to them.
- **Lifespan**: the transfer ends and the handoff loses effect when the next session has read it and landed ④ in the official seats (or reported to the human that it could not land them).
  The next handoff **overwrites** it (no accumulation — history is in git). Carrying ④ into the next envelope as-is without landing it
  is the path by which a handoff turns into a ledger — do not carry it over; land it or report it.
- **When to read**: at session start, if this file exists, read it first. If the handoff and the official documents disagree, trust neither side
  arbitrarily — report before proceeding and let the human judge (the official documents may be stale, or the handoff may be unlanded).
- **When to write**: on a session-end request, or when the context limit is near. The format is free-form text with the four items above as headings.

## 3. Human decisions and agreements — recorded in place in the governing document (a separate decision ledger is forbidden)

| Kind of decision | Seat |
|---|---|
| Requirements, scope, technology (planning phase) | `plan/PRD.md` — `### Core Technologies`, `### Technology Verification`, `### Additional Considerations` |
| Requirement negotiation and transitions | `spec/SPEC.md` Negotiation History Summary — requirement changes during development go deriver incremental/change → spliter incremental |
| Structure | `spec/ARCHITECTURE.md` §4 revision history (no row deletions) |
| Defect handling, Needs review | `spec/findings.md` Action Log |
| Rejection of detection candidates | `spec/findings-rejected.md` |
| Design↔SPEC conflicts, appearance releases | `design/spec-conflicts.md` verdicts → mapper remap |
| Boot and runtime environment | `spec/run-profile.md` |
| Adoption and installation | The Notes of the relevant row in `spec/joblist.md` (`name version adopted/confirmed/installed`) |

The same decision in two places will inevitably diverge — this is the document version of `code-conventions.md`'s 'The single home of definitions'. A decision that fits
no row is written in handoff ④ as "not yet reflected", and the human is asked for its seat — never create a separate `decisions/`-style ledger.
If a decision log is required as a deliverable, generate it into `deliverables/` with the seats above as its sources (one-way).
