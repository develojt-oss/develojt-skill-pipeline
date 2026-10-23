# {project name} — SPEC

> Requirements formalization document based on the PRD.
> Every requirement is written in EARS (Easy Approach to Requirements Syntax) grammar.
> Each entry states its PRD source to guarantee traceability.

<!-- Two writing conventions:
     1) Write responses as externally observable results ("processes it" forbidden → what is shown/heard/stored/returned).
     2) Mark quantitative/enumerable items left to AI autonomy as [Free: reason] inside the requirement sentence (never leave blank). -->

---

## Document Info

| Item | Content |
|---|---|
| Project name | {project name or "Untitled"} |
| PRD version | {PRD version/date} |
| Tech stack | {tech stack stated in the PRD} |
| Runtime environment | {environment stated in the PRD} |
| Negotiation participants | Theorist, Pragmatist |
| Agreement status | {Full agreement / Partial agreement ([Needs review] N)} |

---

## EP-01: {epic name}

| ID | Source | EARS Type | Requirement |
|---|---|---|---|
| FR-01-001 | PRD EP-01 | {type} | {requirement} |
| FR-01-002 | PRD EP-01 | {type} | {requirement} |
| FR-01-E01 | [Implicit] | Unwanted | If {abnormal situation}, the system shall {response} |

<!-- If fan-out exists (one trigger causing multiple outcomes simultaneously), add the table below at the end of the EP. Omit if none.
     Write only observable results (What). Never write which code calls what (How). -->

**Observable Behavior Chain** _(only when fan-out exists)_

| Trigger (observable event) | Required simultaneous outcomes (observable) | Related IDs |
|---|---|---|
| {event} | {outcome 1}, {outcome 2}, … | FR-01-xxx, … |

<!-- Repeat the EP-XX section for as many epics as exist. Below is the repetition example: -->

## EP-02: {epic name}

| ID | Source | EARS Type | Requirement |
|---|---|---|---|
| FR-02-001 | PRD EP-02 | {type} | {requirement} |

<!-- End of per-epic section repetition -->

---

## Non-functional Requirements (Common)

> Cross-cutting concerns belonging to no specific epic.

| ID | Source | EARS Type | Requirement |
|---|---|---|---|
| NFR-00-001 | {source} | {type} | {requirement} |
| NFR-00-002 | {source} | {type} | {requirement} |

---

## Summary Statistics

| Category | Count |
|---|---|
| Functional requirements (FR) | {N} |
| Non-functional requirements (NFR) | {N} |
| Edge cases (FR-XX-EXX) | {N} |
| **Total** | **{N}** |

**Distribution by source:**

| Source | Count |
|---|---|
| PRD EP-XX (directly derived) | {N} |
| PRD Considerations (derived from Additional Considerations) | {N} |
| [Implicit] (scenario/completeness derivation) | {N} |
| [Needs review] (unagreed) | {N} |

---

## Negotiation History Summary

| Stage | Content |
|---|---|
| r1 cross-review | agree {N} / disagree {N} / proposals {N} / escalations {N} |
| r2 negotiation responses | accepted {N} / rebutted {N} / compromised {N} / unresolved {N} |
| Final | agreed {N}, [Needs review] {N} |

**Key negotiation outcomes:**

<!-- [Caution] This table is not a requirements table.
     Writing FR/NFR IDs directly here makes verify-sources.sh misfire.
     Reference as "EP-01 E03". -->

| Item | Conclusion | Conceding side | Rationale |
|---|---|---|---|
| {contested item} | {agreed content} | {Theorist/Pragmatist/compromise} | {why it was decided this way} |

---

## [Future Extensions]

> Features outside the current PRD scope but worth considering later.

<!-- [Caution] This section is also outside the requirements tables. Never write FR/NFR IDs directly. -->

- {extensible feature 1}
- {extensible feature 2}

<!-- If project characteristics require additional sections, place them here (at the end).
     Never change the order or names of the 6 required sections above. -->
