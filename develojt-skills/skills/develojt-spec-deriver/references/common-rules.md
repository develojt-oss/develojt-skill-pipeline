# Common Rules — applied identically to both Theorist · Pragmatist

> This file is the single truth included **in common** in both expert agents' spawn prompts.
> Persona differences (role, negotiation stance, judgment criteria) live only in each persona's prompt file.
> The per-round work instruction is appended by the Lead at spawn time.

---

## The essence of this work

A PRD epic is a natural-language seed written by a human.
Your job is to **exercise intent-reading, analogy, and inference to the fullest** to concretize and expand that seed into EARS requirements.
This is semantic analysis, not mere translation — only by finding the features hidden behind the surface sentences does it become a real SPEC.

Deliverable rules:
- Requirements and document prose are written in English (technical terms and EARS keywords as-is).
- Save every deliverable to the instructed file path. The file name must be exact for the Lead to consolidate.
- Never delete files created during the work — the Lead cleans up at the end.
- The final response (returned text) is only the instructed one-line summary — never dump deliverable content into the response.

---

## EARS core rules (every requirement is formalized with these)

**The 5 types:**

```
Ubiquitous:            The system shall [requirement]
Event-Driven:          When [trigger], the system shall [response]
Unwanted:              If [abnormal situation], the system shall [response]
State-Driven:          While [state], the system shall [behavior]
Optional:              Where [feature/condition], the system shall [requirement]
```

Compound patterns: While + When and Where + If combinations are allowed.

**ID scheme:**

```
FR-epic#-seq   : functional requirement       e.g., FR-01-001
NFR-epic#-seq  : non-functional requirement   e.g., NFR-00-001
FR-epic#-Eseq  : edge case                    e.g., FR-03-E01
```

**Source tags (only these 6 — arbitrary tags forbidden):**

| Tag | Meaning |
|---|---|
| `PRD EP-XX` | Directly derived from a PRD epic |
| `PRD Considerations` | Directly derived from the PRD "Additional Considerations" section |
| `[Implicit]` | Not in the PRD but required for scenario/completeness |
| `[Requested]` | Added/changed by user request after the PRD |
| `[Removed]` | Removed after agreement (history preserved — the ID cell stays as-is, strikethrough ~~ on the requirement sentence. This tag is the verdict key for "inactive" — see the ears-guide example) |
| `[Needs review: reason]` | Agreement not reached or confidence insufficient |

**Good requirement principles:**
- State only the **What** — the **How** is decided at the implementation stage (develojt-code-builder)
- Must be measurable/verifiable
- One requirement per sentence

**[Required] The What/How boundary — never include in the SPEC:**
- Implementation numbers: delta clamp values, buffer sizes, timeout values, thread counts, …
- Algorithm choices: A*, BFS, FSM, behavior trees, or any concrete algorithm name
- Internal structure: class names, function signatures, design pattern names
- Optimization strategies: object pool sizes, LOD level counts, cache strategy details
Boundary test: "does changing this value change the requirement's intent?" → Yes = What, No = How.
Exception: numbers the user explicitly specified in the PRD (deterministic items) are recorded as-is.

**[Required] Verifiability — forbidden phrasing:**
Subjective phrases like "high quality", "photorealistic", "naturally", "adequately", "imposing" are forbidden.
Always replace them with measurable criteria.
e.g., "high-quality result screen" → "display name, status, and update time as separate columns"
Test: "can an automated test be written from this requirement?" → if not, it is vague.

---

## Deterministic items (non-negotiable)

Items the human explicitly selected (`[x]`) in PRD section 2 (System Setup) are **deterministic constraints**:
runtime environment, operating system, development type, core technologies (language/framework/DB/middleware/model), authentication or not, external integration or not.

**Rules:**
- These items are **not negotiable** — both agents accept them as-is
- They are **unrelated** to the EARS "What/How" distinction — a human's explicit technology choice is a "constraint", not an "implementation method (How)"
- Record them verbatim in the SPEC `Document Info`
- Even if "Core Technologies" is empty in the PRD, agents never fill or propose it — undecided items are returned to the user by the Lead at the STEP 1 entry check. Agents accept only values written in the PRD as constraints (`None` is a valid decided value)

---

## PRD reading rules

**[Required] Epic number mapping:**
PRD epics receive serial numbers EP-01 onward in document order.
Only the sequence applies — no distinction between "System-based Epics" and "Business Epics".
The PRD's `[Foundation]` `[Scene]` `[Rule]` `[Edge]` `[Quality]` labels are merely the planner's hint-divergence views —
they are not epic categories or priorities, so ignore them and treat every remaining epic as an equal requirement seed.
(The PRD has passed human review, so remaining `[AI]` hints are adopted requirements too.)

**[Required] Project name and document title rule:**

Check the `Name` field under `## 1. Project` in PRD.md.

```
When a name exists (e.g., "OrderHub"):
  - Document title:  "OrderHub — SPEC"

When there is no name (undecided, blank, _(TBD)_ …):
  - Document title:  "Untitled — SPEC"
```

Never invent a name that is not in the PRD.

---

## Requirement derivation philosophy (important)

The core of SPEC writing is **deep requirement derivation**. The template is merely the vessel holding the results.

**Derivation philosophy**
  - Break down every natural-language requirement in PRD.md, grasp its meaning, and derive the hidden required features.
    This is **semantic analysis**, not mere translation — only by finding the features hidden behind the surface sentences does it become a real SPEC.
  - Understand the **epic scenarios** written in natural language and derive the inferable features.
    An epic is a story carrying the user's intent, so following its flow reveals features never stated.
  - Find insights, infer, and organize feasible, reasonable requirements in EARS grammar

**4-stage derivation (must be applied to every epic):**

  1. Intent grasp — "why is this feature needed?"
     First grasp the purpose/value hidden behind the surface feature.

  2. Scenario tracing — "what do you find if you follow the flow in which this feature actually runs?"
     Follow start → middle → end and derive the features that must exist.
     (Domain-agnostic form — following one epic's flow start→middle→end reveals hidden steps.
      e.g., an auth epic: input validation → credential check → session issuance → lockout on failure → expiry handling.
      e.g., an upload epic: format validation → storage → progress display → duplicate handling → failure rollback.
      Don't fixate on any domain — internalize only the form: "follow the flow to find hidden steps".)

  3. Hidden feature derivation — "never stated, but the system doesn't work without it"
     Error handling, boundary conditions, exception cases, links to other features.
     If an epic yielded no [Implicit] requirements, check it once more.
     If there genuinely are none, none is correct — never force them.

  4. Predictive derivation — "going this direction, this will surely become necessary"
     Only with reasonable grounds. Over-prediction forbidden.

**[Required] Observable behavior chains — the core of verification:**

A requirement's response is always written as an **externally observable result**.
Internal phrasing like "processes it", "manages it", "reflects it adequately" is forbidden. Write what is shown/heard/stored/returned.
Test: "can compliance be judged from behavior alone, without looking inside the code?" → if not, rewrite.

**Fan-out (one trigger → multiple outcomes):**
When one observable trigger must cause multiple outcomes simultaneously, group those outcomes in one place explicitly.
This is not a code call graph — write only "what must happen together" (What); never "what calls what" (How).
Domain-agnostic examples (internalize the form only; don't fixate on a domain):
- Web API: valid order created → order stored + 201 response + confirmation event published
- CLI:     --export runs → file created + summary printed + exit code 0
- Embedded: button interrupt → debounce + state toggle + output refresh
Notation: when fan-out exists, group by trigger in a table at the end of that EP (omit if none). Format: see templates/SPEC-template.md.

**Fan-out completeness — the chain table is the builder's wiring contract and the verification scoresheet (an occurrence point missing from the table is never wired, all the way through):**
- When the same trigger class occurs on **different target classes** (one event applying to two or more kinds of objects),
  write one row per target class — never collapse them into a single row for one representative class.
- **A cross-cutting requirement enumerating multiple events** ("when A, B, or C occurs, do X") gets one row per enumerated event,
  with the event-producing requirement ID and the cross-cutting requirement ID written **together** in the Related IDs cell — even when the event belongs to another epic.
  (This is what pulls the cross-cutting obligation into scope when the event-producing side is implemented and inspected.)

**[Required] Ambiguity removal — written requirements must be deterministic:**

Writing in EARS does not remove ambiguity by itself. Check every requirement along these axes:
- Boundary/edge: does it also apply to already-finished/empty/invalid targets?
- Subject scope: all subjects, or specific ones only?
- Target/location: applied where/to what?
- Timing/order: when, and in what order?
Test: "would two different people read this sentence and imagine the same behavior?" → if not, it is ambiguous; rewrite.
(No need to supply every number. It only must not be ambiguous — concrete numbers/implementation detail are code-builder's autonomous territory.)

**[Required] Blank notation — intended freedom is stated explicitly:**

A quantitative/enumerable item left to AI autonomy (count, threshold, multiplier, time, limit, …)
is marked inside the requirement sentence as `[Free: reason]`. Left blank, omission and intended freedom become indistinguishable.
e.g., "The system shall provide two or more sort criteria [Free: kinds and count decided at implementation]"
(`[Free: ...]` is an inline notation inside the requirement text, not a source tag.)

**[Required] [Implicit] derivation quality bar:**
- **Include**: edge cases users struggle to predict, system stability, platform-specific constraints
- **Exclude**: items any developer in the domain would implement as a matter of course (e.g., "a mute feature")
  Test: "if this item is absent from the SPEC, is there a chance code-builder omits it?" → if low, don't add it.

**[Important] PRD "Additional Considerations" → NFR derivation:**
The PRD's additional considerations (performance, security, schedule, constraints, …) are cross-cutting concerns belonging to no epic.
Derive them as `NFR-00-xxx` into the "Non-functional Requirements (Common)" section.
Mark the source as `PRD Considerations` — the human wrote them personally, so `[Implicit]` is not used.

**[Required] Systematic NFR derivation checklist:**
After FR derivation completes, check for NFR omissions by category (skip inapplicable ones):
performance (response time, throughput) / memory (allocation, cache, leak prevention) / resource limits (concurrency, buffers) /
compatibility (runtime, OS, resolution/standards) / startup & loading (init time, readiness) / accessibility / security / scalability / maintainability (logging, observability)
(The categories above are a domain-agnostic list. Apply only those fitting the project.)
If the "Non-functional Requirements (Common)" section has fewer than 5, re-check the checklist.

**[Required] Runtime-base NFR derivation — turning the releasable state into requirements:**
Derive each **runtime-base component** the system must stand up first in order to "come up" before any feature as its own `NFR-00-xxx`.
The grounds are only what the PRD has already finalized — the targets are the components that actually exist among those listed in the system setup
(runtime environment, core technologies) and the `### Technology Verification` section (if present) (execution containers/runtime, data-store schema and startup,
middleware, resident services and model serving, shared protocol/API contracts, shared library initialization), and **no base absent there is invented**
(a project without such components has no such derivation either — never force one).
Write the response as an observable result at startup — what responds, is established, or stays resident.
Example (learn the form only): "When the system starts, the system shall [respond to health-check requests / establish the storage connection]."
This NFR's response becomes **the observation criterion of the run profile (the builder's boot gate)** — when the scaffolding is complete, that criterion
machine-confirms "it builds and it boots" (the releasable invariant). Mark the source as `[Implicit] derived from system setup` or
`[Implicit] derived from technology verification` (the same grammar as the security checklist's derived notation — verify-sources PASSes on an `[Implicit]` substring match).

**[Required] Security requirement derivation checklist:**
(The 'security' category of the NFR checklist above is performed via this checklist.)
After FR derivation completes, check each epic for the surfaces below, and for every surface it has,
derive **that feature's own observable security behavior** as FRs (epic-owned) or NFR-00 (cross-cutting) (skip absent surfaces):

| Surface (if the epic includes this) | Security requirements to derive (as observable behavior) |
|---|---|
| Authentication (login, signup, password reset, sessions, tokens) | Behavior when attempt limits are exceeded (lockout/delay), behavior on session/token expiry, invalidation on logout, whether authentication-failure/duplicate-signup/reset responses disclose account existence (derived as non-disclosure — uniform responses — unless the PRD requires disclosure; disclosure only on an explicit human decision, under its source tag) |
| Authorization (roles, permissions, owned resources) | Denial response to unauthorized requests, denial when accessing another's resource identifier |
| Sensitive data & PII handling | Fields protected at rest (encrypt/hash), masking scope on display, fields excluded from responses |
| External input intake (forms, APIs, files, messages) | Rejection behavior on invalid input (If ...), size/count caps and behavior when exceeded |
| File upload/download | Allowed formats and size caps with rejection behavior on violation, access scope of stored files |
| Server requests to user-supplied addresses (webhooks, previews, …) | Allowed target scope, denial of out-of-scope requests |

Boundary rules (preventing SPEC bloat):
- Global security principles (parameter binding, output escaping, cipher algorithm choice, …) are enforced
  globally at the implementation stage by `.claude/rules/security-conventions.md` — never restate them in the SPEC.
  What goes into the SPEC is only **observable behavior requiring a policy decision specific to that feature**
  (lockout criteria, expiry policy, masking scope, permission boundaries, caps).
  Test: "is this behavior a policy decision of this feature, or a general principle applying to all code?" → if a general principle, leave it out.
- Security requirements follow every rule in this document equally (What/How boundary, observability,
  ambiguity removal, blank notation, source tags). If the PRD gives no basis for a policy value
  (counts, durations, caps), mark it `[Free: reason]` — agents never fix it arbitrarily.
- Source: the matching tag if grounded in the PRD, otherwise `[Implicit] derived from {grounding FR ID}` (e.g., `[Implicit] derived from FR-01-003`; multiple grounds joined with `·` — a back-tracing link pointing at the feature FR that created the surface. When that FR is later modified/deleted, change mode finds the derived security requirements deterministically via `grep "derived from {that ID}"`. verify-sources matches `[Implicit]` as a substring, so it still PASSes). The "matter-of-course items excluded"
  clause of the [Implicit] quality bar applies only to general principles — the feature-specific security
  behaviors in the table above are derived, because absent from the SPEC they drop out of wiring and verification.

**After derivation completes**, fill the results into the skill's `templates/SPEC-template.md`.
Never alter section order, table formats, or header names on your own.
The template is a tool guaranteeing form — it never limits the depth of derivation.

**[Caution] Never start a row with an ID like `| FR-...` outside the requirement tables.**
verify-sources.sh counts only rows starting with `| FR-`/`| NFR-` as requirement rows.
In the behavior chain table's 'Related IDs' cell (column 3), write FR/NFR IDs as-is — the row starts with a trigger, so no false positive.
In narrative text (negotiation history table, future extensions, …), reference as "EP-01 E03".

---

## Common negotiation principles (round-independent)

- Argue your perspective exclusively and stubbornly — don't concede easily
- Accept the counterpart's claim when it is logically sound — compromise happens through logic
- Never reopen already-agreed items
- Never repeat the same claim without new grounds
- Never force agreement — if agreement never comes, handing it to the user as `[Needs review: reason]` is better
- **Record the "why" for agreed/compromised key design decisions** — a decision without grounds leaves code-builder no criterion to adjust by
- PRD interpretation questions the two of you cannot decide go in the review's `[Escalation]` section — the Lead asks the user

---

## Verification (required when saving deliverables)

Every time you save a SPEC-format file (draft or final), run the following; on ERROR, fix and re-run.
**Repeat until PASS** — only then consider it complete.

```bash
bash .claude/skills/develojt-spec-deriver/scripts/verify-sections.sh <file>
bash .claude/skills/develojt-spec-deriver/scripts/verify-sources.sh <file>
```

(When the skill is installed globally, use the `~/.claude/skills/develojt-spec-deriver/scripts/...` path.)
