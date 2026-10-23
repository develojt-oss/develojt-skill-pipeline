# External Resource Acquisition Protocol (Resource Acquisition)

This file is the conduct protocol for the moment work needs "something not here yet" — a system
tool, a package/library, web information or files. Whatever the phase (planning, derivation,
implementation, verification, change) and whatever the reason (implementation, environment
setup, error resolution, research), the same ladder applies.

**One-sentence summary: every act that leaves the project — system queries, web access,
installation — happens only after human approval. When in doubt, the default is a question,
not execution.**

## 0. Scope

- **Covered**: every act that inspects or brings in resources from **outside** the project
  directory and the pipeline's deployed asset paths (`.claude/`, and the skills · agents ·
  rules under `~/.claude/`).
- **Not covered**: ① reading/searching files inside the project (that is everyday work)
  ② running the pipeline's own scripts and templates ③ using dependencies already installed
  in the project (pre-use confirmation belongs to builder essential 3, "first-use confirmation
  of external technologies").
- **Instruction = approval**: when the human's instruction names the target (e.g. "install X
  and proceed"), that instruction is the approval — but only for that named target and scope.

## 1. The acquisition ladder — order fixed, approval at every rung

When a need arises, climb in this order only. When a lower rung resolves it, stop there
(use what exists).

**Rung 1. Local reality check — "is it already here?"**
- **What to check is set by derivation from the documents, not by listing from memory** — the technologies relevant to this need
  are all to be checked if they appear in the project documents (all that exist: the PRD's core technologies and external integrations, the SPEC tech stack, the joblist's adoption and install
  records). Dropping a target written in the documents without checking it is a silent omission — to drop one, show it in the list as excluded.
- The project first: the dependency ledger (package.json, requirements, …), lock files,
  existing code, project configuration. No approval is needed here (it is project reading)
  and it is **not skippable** — do not move to rungs 2–3 without this check.
- When a system check (outside the project) is needed, **name the target and the command and
  get approval**. The only allowed form is **named lookups**: `which X` · `X --version` ·
  the package manager's query commands. **Directory walks, broad scans, and home-folder
  exploration are exploration, not checking — forbidden.**
- **An absence verdict comes only after checking the designated location** — a resource's actual location can be changed by environment variables and settings (cache paths,
  service settings). Do not judge "absent" because the default path is empty — first check the clues that designate the location (environment-variable and
  setting lookups — within the named-lookup category).

**Rung 2. Web research — "what are you going out to learn?"**
- Only when rung 1 is not enough. Present **the list of things to find out**, get approval,
  and research only the approved items.
- Source obligation: a source per row (doc URL, confirmed version). What could not be
  confirmed by documents is honestly marked `memory-based (unverified)` (pretending it was
  confirmed is the worst outcome).
- **Error-resolution searches are web research too** — "it was urgent" is not an exemption.

**Rung 3. Install/download — "what are you bringing in?"**
- Before executing, state **the name, version, install location, and exact command** and get
  approval.
- The install location defaults to **project-local**. Global installs (`-g`, brew, system
  packages) require a separately stated reason and are never proposed by default.
- File downloads, repository clones, and running install scripts belong to this rung too.
- After executing: record it (in the build phase, one line `name version installed` in that
  joblist row's Notes) + run the dependency audit (security-conventions §11 — audit tools,
  name-accuracy check).

## 2. The grammar of approval

- An approval request carries **three elements: target, reason, command (or question list)** —
  without all three it is not an approval request.
- **A request for an already-finalized target asks only whether to proceed** — if the project documents (the SPEC tech stack, etc.)
  have already finalized the target, the request's question is not "what should we use" but "may we bring in what has been decided".
  Listing or recommending alternatives outside the contract reopens what was finalized, so it is not done (listing cost facts such as size and burden
  is reporting — never used as grounds for presenting alternatives). Changing a technology decision is, as in §3, outside this protocol
  (on meeting a measured impossibility, stop and report without alternatives — through that phase's procedure).
- **A lower rung's result is the premise of an upper rung's request** — rung 2 and 3 approval requests carry the lower rung's result (for rung 1:
  what already exists and what does not). A rung 2 request without a rung 1 result is premature — rung 2 is
  "only when rung 1 is not enough", and only the rung 1 result tells whether it is not enough. Even when several rungs are bundled into one approval,
  **execution follows the ladder order**, and when a lower rung's result changes the need or the list of an upper rung
  (already present, a changed premise), get reconfirmation with the updated list before proceeding.
- Approval covers **only the enumerated targets**. A new target means a new approval. Multiple
  items born of the same need may be approved together as one list (with per-item exclusion).
- **Blanket delegation is neither requested nor accepted** ("just install whatever you need
  from now on" and the like) — on receiving such an instruction, state that this protocol
  presumes per-item approval and get confirmation.
- Nothing executes before approval — report and wait.

## 3. Relation to existing norms

- planner's "technology verification" (research via human approval) is this ladder's rung 2
  specialized for the planning phase — that procedure stands as-is.
- builder's "first-use confirmation of external technologies" is the confirmation duty
  **after** acquisition and **before** use — this protocol covers the moment before it:
  acquisition.
- Changing the tech-stack decision itself (adopting/replacing a technology) is not this
  protocol's job — follow each phase's procedure (planner technology verification; requirement/
  technology-change intake is the changer classification table's routing — mid-development,
  deriver incremental → spliter incremental). Whatever the decision, this protocol governs
  only its **execution acts** (queries, research, installation).
