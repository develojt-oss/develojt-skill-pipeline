---
name: develojt-spec-planner
description: "Skill that gathers information interactively and auto-generates a product requirements draft (plan/PRD.md). Use this skill when the user mentions 'make a PRD', 'organize requirements', 'start a project', 'let's figure out what to build', 'planning document', 'write epics', 'requirements draft', 'I want to build X', or when the context shows a new software project is starting. The PRD is a concise draft that humans read and write, not a detailed technical spec. The deliverable is the single file plan/PRD.md. Note: SPEC generation, EARS conversion, and detailed tech stack design are outside this skill's scope — develojt-spec-deriver performs those after the human completes the PRD."

disable-model-invocation: true
argument-hint: "[optional: freely describe what you want to build]"
---

# develojt-spec-planner — interactive requirements draft generator

## Position in the pipeline (understand the flow before working)

```
[this skill] plan/PRD.md    — human-led. AI presents abundant hints (seeds)
[deriver]    spec/SPEC.md   — infers and expands epic intent into concrete EARS
[spliter]    spec/joblist.md — progress ledger for developing in slices
[builder]    src/           — @spec-traced code, implemented bundle by bundle in ledger order (EP by EP if no joblist)
[pdca]       spec/findings.md — static-completeness loop entered automatically after each implementation. Quiescence defines bundle completion (appearance-comparison target bundles: + screen-review ledger registration & registration confirmation; the comparison itself runs as one batch session after full implementation completion)
```

A PRD epic is a **seed** the deriver will unfold through intent-reading, analogy, and inference.
Decomposing or technically refining it here kills the room the deriver needs to unfold.
So an epic stays **one or two natural-language sentences**, with its elements still dissolved in it. Concretization is the deriver's job.

## What this skill does

Converses with the human (AskUserQuestion) to collect project information, then auto-generates a PRD draft from it.

**This skill's only deliverable is the `plan/PRD.md` file.**

**This skill's scope ends at "draft generation". Everything after is not this skill's job.**

```
[this skill]
conversation → collect info → AI hint divergence → generate plan/PRD.md draft → hand to the human (done)

[the human's time]
Carries PRD.md around and fills in the blanks whenever ideas come — for days or for weeks

[next skill — outside this skill's scope]
Human says "it's ready" → develojt-spec-deriver → EARS SPEC generation
```

**Core principles:**
- **The human leads, AI assists.** AI does not complete the document; it builds a good draft so the human can start.
- **AI epics are hints, not decisions.** People can't start from nothing. When AI presents diverse candidates in abundance, the human recalls their own ideas by looking at them. Adopting, deleting, and editing belong to the human.
- **Brevity is life.** A PRD must be skimmable and editable by a human within 5 minutes.
- **Epics are natural-language sentences.** No YAML schema, no priority fields, no dependency mapping.
- **Tech stays shallow, but decisions land here.** Don't ask about details (versions, cache strategies). Record the direction (language/framework/DB/middleware/model) when the user states it; when undecided, present candidates and let the user choose. Never pass blanks to the next stage.
- **Ambiguity is resolved by deterministic questioning.** Whether the starting point is nothing or a parameter description, any undecided system-setup item is asked about — never left blank at model discretion. The decision-maker is always the human.
- **Deliverable language is English.** All PRD prose is written in English (technical terms and proper nouns as-is) — a pipeline-wide rule that continues through the SPEC and code comments.

---

## Preparation

Create the `plan` directory if it doesn't exist:

```bash
mkdir -p ./plan
```

---

## Greeting

When this skill runs, before any other work, print the logo and greeting message below verbatim.

Print the logo first as a code block (read `develojt-logo.md` from the reference file table):

@./references/develojt-logo.md

After preparation completes, print this greeting message:

```
Hello! Welcome to the PRD Planner skill.

I'm a specialist AI that organizes the requirements of the system/software you want to build into a document draft (PRD.md).

What this skill does:
- Derives a diverse set of predictable requirements (epics) from your input (AI hints)
- Writes/provides guidance so you can comfortably add your own requirements
- Auto-generates the organized draft PRD.md document

Tell me your project idea freely.
It can be concrete, or as vague as "I want to build something like this…".
I'll organize it with you, step by step!
```

> The greeting is printed once, on the skill's first run only. Do not repeat it later in the conversation.

---

## Input analysis

$ARGUMENTS

After printing the greeting, do not wait for the user's response — start STEP 0 immediately within the same response.

---

## Interactive information-gathering procedure

When the user requests a PRD, **first analyze the input ($ARGUMENTS)**, then proceed with the conversation.

### STEP 0: Input analysis

First analyze what can be extracted from $ARGUMENTS.

```
Input example:
  "Make a PRD. It's an in-house supply request management system. Web-based client-server
   architecture, Linux server, FastAPI + Vue.js, MariaDB for the DB. Login is required and
   it must integrate with the company messenger for notifications."
```

**Analysis procedure:**

1. Extract the following items from the input text:
   - Project info (name, description)
   - System setup (runtime environment, OS, development type, tech stack, authentication, external integration)
   - Business epics (when features are mentioned)
   - Additional considerations (when performance, constraints, etc. are mentioned)

2. Decide how to proceed based on the extraction result:

| Extraction state | How to proceed |
|-----------|-----------|
| **Sufficient** — project info + system setup mostly filled | Present the organized extraction, fill missing system-setup items with confirmation questions, then go to STEP 3 |
| **Partial** — only some info present | Skip already-extracted items and continue from the missing STEP |
| **None** — only "make a PRD" | Proceed from STEP 1 from the beginning |

**Cautions:**
- Always get the extraction confirmed by the user: "Here's what I understood from your input. Is this right?"
- Never guess. System-setup items not stated in the input are never filled arbitrarily — collect them with that STEP's questions. Never move on leaving them blank.
- If the user says "right", collect only what's missing; if "no", fix the item in question.
- **Never discard the user's free-form text.** It is the most important raw material for the domain hint divergence in STEP 3.

**[Required] Full confirmation of free-form text (no loss):**

Not a single phrase of the user's free-form text (original input + free descriptions during conversation) is discarded at model discretion.
Judging a phrase unsuitable or ambiguous is a reason to ask, not to delete. Confirm every phrase through human decisions with the procedure below.

1. Split the free-form text into meaning-unit phrases and show the user the 3-column table below.
   **Every phrase of the original must appear as a row** — the less a phrase fits this system or the harder it is to interpret, the more it must be raised as a row rather than dropped.

```
| Original phrase (verbatim quote) | Model's interpretation (translated into this system's language) | Disposition |
|---|---|---|
| (input phrase as-is) | (one-line interpretation) | reflect in epics / reflect in system setup / needs question |
```

2. For phrases marked "needs question" (interpretation splits or can't apply as-is), present 2–3 interpretation candidates
   and let the user choose (AskUserQuestion). The model never decides on the user's behalf.
3. Only user-confirmed interpretations go into the PRD. Excluding a phrase is possible only when the user chose it.

**[Required] Full analysis of file/folder materials (no skimming):**

When the user presents folders or files as material and asks for analysis and feature extraction — at STEP 0 or mid-conversation —
follow the procedure below. Extracting after reading only part of the presented material is the same loss as discarding a free-form phrase.

1. **Exhaustive listing** — if a folder is presented, produce the file list with a command (never enumerate from
   model memory or guesses — the command output is the baseline). If individual files are named, that list is the baseline.

```bash
find <presented folder> -type f | sort
```

   Show the user the list and the file count. Exclusion proposals (hidden files, binaries, etc.) are never dropped
   silently — they appear in the list as `exclusion proposed: reason`. An exclusion is also a decision the human sees.

2. **Read every file in full** — read each file on the confirmed list in its entirety. Substituting a read of only the beginning
   or a grep excerpt is forbidden; if a file is long, keep reading to the end. Formats that cannot be read
   (encrypted, unsupported binaries) are honestly marked `unreadable` in the ledger and their disposition is asked of the human.

3. **Per-file extraction ledger** — the file edition of the free-form full-confirmation table. **Every file on the list must
   appear as a row** — the less a file seems to offer, the more it must be raised as a row rather than dropped.

```
| File | Extracted feature candidates | Disposition |
|---|---|---|
| (path) | (one per line — if none, `nothing to extract: reason`) | reflect in epics / reflect in system setup / needs question / nothing to extract |
```

4. **Check, then reflect** — write `check: N files listed = N ledger rows` under the ledger. If the numbers differ,
   do not move on to reflection. Rows marked "needs question" are decided by the human the same way as item 2 of the
   free-form full confirmation (AskUserQuestion). Confirmed extraction results are raw material of equal standing
   with free-form text — epic reflection uses the existing path (STEP 3) as-is.

---

STEPs 1–5 below are the procedure for **collecting the missing information** after input analysis.
Skip items already filled in STEP 0.
**Ask only 1–2 questions at a time.**

**[Required]** Questions to the user must be conversational (AskUserQuestion) so choosing is convenient for them.

### STEP 1: Understand the project

| Item | Question example |
|-----------|-----------|
| Name | "Does the project have a name? It's fine to decide later" |
| One-liner | "How would you describe this project in one sentence?" |

**Caution:** never re-ask items already established in STEP 0.

---

### STEP 2: System setup

Present choices to the user. Multiple selection is allowed, and anything not listed can be entered directly as "Other".

**Runtime environment** → "Where does this system run?"
- Standalone (one server or one PC) / client-server architecture / cloud deployment / edge-embedded / other

**Operating system** → "Which OS does it run on?"
- Windows / Linux / macOS / iOS-Android / web browser (OS-independent) / other

**Development type** → "How will it be built?"
- Web (frontend + backend) / web (backend/API only) / native-desktop app / mobile app / CLI-batch program / library-SDK / other

**Core technologies** → "Are any languages or frameworks already decided?"
- Language / framework / DB / middleware / model / other
- Record the user's stated values as-is.
- **Undecided items are never left blank** — based on the setup collected so far and the user's free-form text,
  present 2–3 candidates with one-line rationales and let the user choose (AskUserQuestion, direct input allowed).
  Items that don't apply (DB, middleware, model, …) are recorded as `None`.
- **Model** = when AI/ML models perform the epics' core behaviors, the model for each role (inference, embedding, reranking, etc. —
  the very "models" of technology-verification target ①). Even if the design registers and swaps models during operation, **the default
  model used for initial startup and verification is a decision made here** — the abstraction "it's a runtime setting" is no reason to defer the decision
  (only once the model is decided do the derived decisions (values that fossilize into the storage structure, such as the embedding dimension) go through verification).
  A project with no AI/ML role: `None`.

**User authentication** → "Is user authentication like login needed?"
- Yes / no / don't know yet

**External integration** → "Is there anything to integrate with other systems?"
- Yes (→ follow-up question for targets) / no / don't know yet

**Important:** do not go deep into tech stack details here (DB engine, framework versions, cache strategy, …) — details belong to the stages after the SPEC. But **the direction (language/framework/DB/middleware/model) must reach a decided state at this stage.** The system setup is handed to the deriver as non-negotiable constraints — a blank is not "delegated to AI" but a "missing decision", and validate.py catches it as FAIL.

#### Technology verification — confirming the decided technologies sustain the requirements (research via human approval)

Once the core technologies' direction is decided (user-stated and candidate-chosen alike), confirm their
capabilities before finalizing. **AI memory is not research** — fast-moving open-source projects and models
in particular differ in reality from the training-time snapshot, and a memory-only decision surfaces "unsupported
feature" only at implementation time. The procedure is four steps, order fixed:

1. **Propose the verification-target list** — one line per decided technology: `name | role it plays |
   capabilities to verify (what this technology must pull off, derived from the epics and free-form text)`.
   Two classes always go on the list: ① role technologies that directly perform the epics' core behaviors
   (inference engines, models, DBs, middleware, core libraries) ② active open-source projects/models whose
   features vary by version. Others (general-purpose languages, …) default to a proposed exclusion but still
   appear on the list — an exclusion is also a decision the human sees.
2. **Human confirmation (AskUserQuestion)** — show the list and get the research decision (items can be
   added/removed). **"Proceed without research" is a valid decision** — it is recorded in the PRD as
   `Not researched (user decision)`, distinguishing it from silent omission. **Web research happens only
   after this confirmation** (exploration outside the project requires prior approval — the list above is
   exactly what would be checked out there).
   This confirmation doubles as the approval for rung 2 (web research) of the resource-acquisition ladder, **so attach the result of rung 1 (local reality check)
   to the request** (protocol §2 "a lower rung's result is the premise of an upper rung's request") — when the reality of the runtime environment and already-held resources
   shapes the list's scope or the capabilities to verify (technologies that depend on models or hardware being on the list is the typical case), the reality check comes
   before the list proposal. A list made without the reality creates an update round-trip every time the reality surfaces.
3. **Run the research (approved items only)** — confirm each capability against official/repository docs
   and **leave a source on every row** (`capability | verdict | source (doc URL · checked version) |
   constraints/cautions`). **No support claims without a source** — items not confirmed by documentation
   are marked `memory-based (unverified)` (pretending to have verified is the worst outcome; the honest
   unverified mark is a state the human can see and judge). If unfitness surfaces, return to the
   core-technology candidate proposal (the decision is the human's).
   If a capability to verify presupposes the reality of the runtime environment (hardware acceleration, already-installed tools, available resources), **settle that
   reality before web research** — this is rung 1 of the resource-acquisition protocol (`rules/resource-acquisition.md`) ladder (local reality check —
   system checks go through named-lookup approval), and verifying a capability without knowing the reality is only half done (e.g., without knowing whether
   an acceleration device exists, the model size cannot be decided). If step 2 already attached the rung 1 result, that is this settlement
   — this sentence is the safety net for when it was omitted.

   **Measured confirmation (spike) — not mandatory, only when the documents leave you unsure**: if, even after the research, you are not sure whether that row's capability
   holds (conflicts between documents, missing documents, and environment dependence are typical), instead of repeating the document search
   you may propose measuring it — build minimal code in `spike/<target>/` (several targets side by side at the same level) and run it
   to confirm. It proceeds only after human approval (the proposal = the capability row you are unsure of and one line on how to confirm it — if an install
   comes with it, add the acquisition-ladder rung 3 request alongside). The confirmation target is exactly step 1's "capabilities to verify" row — the aim is not a rehearsal
   for building it well but gaining certainty, so once there is an answer (yes and no are both answers) stop immediately and return to this
   procedure (any further implementation or tidying is out of scope). Record the result in step 4 with the source `measured (spike/<target>/)`.
   **spike/ code is discarded code** — quality is irrelevant (conventions, the structure contract, @spec, and tests do not apply) and reuse is forbidden
   (src/ never brings it in by import, copy, or reference — the real implementation starts fresh from the SPEC). But the standing controls
   apply to spikes as-is (the acquisition ladder, the ban on hardcoded credentials).

4. **Record in the PRD** — enter the results in the PRD's `### Technology Verification` section (template).
   **[Required] When the research finalizes or changes a means of implementation, reflect that decision in
   the `### Core Technologies` fields as well** — three targets: ① a finalized package/wrapper
   (e.g., the B of "A can't play this role → wrap it with package B") ② a replacement technology adopted
   on an unfitness verdict ③ a finalized version constraint. The Technology Verification section is the
   evidence record; what the deriver deterministically carries into the SPEC tech stack (document info) is
   the `### Core Technologies` fields — a means of implementation not landed there never reaches the
   builder, who reads only the SPEC (a record is memory only where its consumer's eyes land). This record
   propagates to the deriver automatically (its agents read the full PRD — material for the
   capability premises during requirement formalization).

Boundary: this verification goes as far as "does the choice sustain the requirements" (capabilities and
constraints) — design details like version pinning and cache strategies are still out of scope here (the
**Important** paragraph's principle above, unchanged).

---

### STEP 3: AI epic hint divergence + user epic collection

Once system-setup collection completes, proceed in this order.

#### 3-1. System-based epics (deterministic rule table)

Generate epics exactly per the "epic inference rules" table (section below) according to the chosen system-setup combination.
Apply the rule table as-is — no creativity. The results go into the `[Foundation]` block.

#### 3-2. Domain epic divergence (hints — the heart of this skill)

Using the user's free-form text (STEP 0 input + mentions during conversation) as raw material,
sweep **the four views below in fixed order, diverging 4–6 epic candidates per view**.

| View | Label | Question it asks |
|------|------|-----------|
| 1 | `[Scene]` core usage scenes | Who uses this system, and how? What scenes unfold? |
| 2 | `[Rule]` domain rules & data | What information does it handle? What business rules exist? |
| 3 | `[Edge]` failure & edge situations | What does the scene look like when something goes wrong? What are the limit conditions? |
| 4 | `[Quality]` quality & experience | What speed, feel, and mood does the user expect? |

Why sweep all four views without exception: to block bias toward one category (per-view allocation),
to prevent shortage (per-view minimums), and to give hints even in areas the user struggles to imagine (especially `[Edge]`).

**Epic writing principles:**
- **One or two natural-language sentences.** A "when someone/something does X, Y happens" narrative or "a Y capability is needed" form.
- **Hint line format is `N. [AI] sentence`.** (e.g., `1. [AI] A staff member views the list on screen`) — without the `[AI]` marker, the verification gate does not count the line as a hint.
- **Write only the core concern.** No implementation methods (JWT, Redis, REST, state machines, …).
- **Do not decompose elements.** It's fine for functional and non-functional elements to stay dissolved in one epic — the deriver unfolds them.
- Use business language a human understands on first read.

#### 3-3. Present + collect user epics

Show the diverged epics to the user with this guidance:

```
"Based on your system setup and what you've told me, here are some epic candidates.
 These are hints, not decisions.
 - Tell me which ones you don't need and I'll remove them
 - If they spark any features in your mind, say them freely
 Now, tell me the core things this system actually has to do."
```

If the user states business epics right away, record them; if they say "I'll write them later", leave the blanks.
The writing guide and examples are included inside PRD.md so the human can fill it in later.
If the user asks to delete hints, delete them — but if deletion breaks a view's minimum (4), diverge new candidates in the same view to replenish.

#### Good epics vs bad epics

```
✅ Good epics (core concern, natural language, instantly understood by a human)
  "User login/logout and authentication handling is needed"
  "A staff member browses today's submitted requests on a web screen"
  "When an external integration drops, it shows on screen and the staff member is notified"
  "The list screen must appear fast enough that waiting is barely felt"

❌ Bad epics 1 — implementation detail, technical terms (trespassing into SPEC level)
  "Implement JWT-token-based auth and apply refresh token rotation"
  "Send notifications asynchronously via a Redis queue with latency under 500ms"

❌ Bad epics 2 — too vague to carry information
  "A viewing feature"  (who, what, how?)
  "The system should run well"  (a truism)
```

---

### STEP 4: Additional considerations (optional)

"Any additional requirements like performance, security, schedule, or constraints? If not, we'll move on."

---

### STEP 5: Generate PRD.md + verify

1. Read `references/sample.md` to check tone, level, and volume.
2. Fill `references/template.md` with the collected information to generate `plan/PRD.md`.
   - Number the epics **continuously from 1**, from `[Foundation]` through `[Quality]`.
   - Write AI hint lines in the `N. [AI] sentence` format (e.g., `1. [AI] System logs must be recorded so problems can be traced`).
   - If user epics were collected during conversation, enter them at the `{user_epics}` spot numbered from 1 and remove the empty scaffold lines below (`1. `–`3. `). If none, leave the empty scaffold as-is.
   - Leave the free-form areas (`_(add ... here)_`) empty — they are the human's to fill.
   - **[Required]** In the status section (`## 4. Status`), check `[x]` **only on 'Drafting'** — leave the other two unchecked. 'Finalized' is an approval gate the human checks personally.
3. **[Required] Run the verification gate:**

```bash
python3 <skill folder>/scripts/validate.py plan/PRD.md
```

On FAIL, fix the flagged items and re-run. Hand over to the user **only after PASS**.

4. After generation, guide the user:

> "I've generated the PRD draft.
> The checkboxes and AI hint epics are already filled in.
> Please add the core things this system must do to the 'Business Epics' area, freely.
> Feel free to delete any AI hints you don't need.
> There's no rush. Fill in a line whenever it comes to mind.
> Once it's complete, you can hand it to develojt-spec-deriver to generate the detailed SPEC."

---

## Epic inference rules (the `[Foundation]` block — deterministic)

AI auto-generates epics according to the chosen system-setup combination.

**Condition criteria**: 'DB present' = the DB item under Core Technologies has an entry /
'middleware present' = the middleware item under Core Technologies has an entry / 'multiple OS' = 2 or more selected under Operating System.

| Condition (system setup) | Auto-generated epic |
|---|---|
| [Required]**always** | When an error occurs, the user must be given appropriate guidance |
| [Required]**always** | System logs must be recorded so problems can be traced |
| Client-server or cloud | Client-server communication over the network is needed |
| Client-server or cloud | An API contract (protocol) for the communication must be designed |
| Web (frontend + backend) | The screens users access need a basic layout and page navigation structure |
| Web (frontend + backend) | Basic on-screen entry/viewing/editing/deletion of data is needed |
| Web (backend/API only) | API endpoints callable from outside must be designed |
| Auth=yes | User login/logout and authentication handling is needed |
| Auth=yes | Accessible features must be restricted by user permission |
| DB present | Storing/viewing/editing/deleting data is needed |
| DB present | The database structure must be designed and initial data set up |
| External integration=yes | Integration for exchanging data with external systems is needed |
| External integration=yes | Handling for external integration failures is needed |
| Middleware present | Inter-system communication via asynchronous messages is needed |
| Mobile app | The app install/update/distribution method must be decided |
| Mobile app | Whether the app works offline during network loss must be decided |
| CLI-batch program | Command arguments/options and execution results (exit status, output format) must be designed |
| CLI-batch program | Execution must be safe against interruption and re-running the same job |
| Library-SDK | The public interface (API) for external developers must be designed |
| Library-SDK | A compatibility policy so existing user code survives version changes is needed |
| Native-desktop app | The install/update/distribution method must be decided |
| Edge-embedded | Operating conditions under constrained resources (memory, storage, network) must be defined |
| Cloud deployment | Deployment environments (dev/staging/production) must be set up |
| Multiple OS | Identical behavior across multiple operating systems must be verified |

---

## Reference files

| File | Description | When to read |
|------|------|-------------|
| `references/develojt-logo.md` | Logo | At greeting |
| `references/sample.md` | Completed PRD.md sample (CCTV system) | Right before generating PRD.md — the benchmark for tone, level, volume |
| `references/template.md` | PRD.md template (with placeholders) | When generating PRD.md — fill this template in |
| `scripts/validate.py` | PRD verification gate (structure, completeness, per-view counts, ambiguity) | Right after saving PRD.md [Required] |

Paths are relative to the skill install location: `.claude/skills/develojt-spec-planner/` (local first) or `~/.claude/skills/develojt-spec-planner/`. If neither exists, ask the user to confirm the installation. Never assume cwd-relative paths.

---

## What not to do

### 1. Don't shape the PRD like a SPEC
- No YAML schema, no priority/dependency/acceptance_criteria fields, no 7–10-section subdivision
- Checkboxes + natural-language sentences, 4 sections (project/system setup/epics/status), skimmable by a human in 5 minutes

### 2. Don't dig deep into the tech stack — but do finish deciding the direction
Don't ask about details (DB engine, versions, cache strategy, …).
For the direction (language/framework/DB/middleware/model), when the user doesn't know, present candidates and get a choice;
when not applicable, record `None`. What's forbidden is handing the PRD to the deriver with blanks —
the deriver is a consumer of constraints, not a producer.
Technology verification (the STEP 2 subsection) is not "depth" but the decision's input — it stops at
capability/constraint confirmation and never crosses into design details.

### 3. Don't treat hints as decisions
AI epics are raw material for the human to look at and recall their own thinking.
No blanket-approval nudges like "shall we finalize these as-is?".
This skill's purpose is guiding the human to write the business epics themselves.

### 4. Don't decompose or refine epics
No concrete numbers, libraries, or implementation methods in epics. That belongs to the deriver's EARS unfolding.

### 5. Don't alter view labels or the template structure
The `[Foundation]` `[Scene]` `[Rule]` `[Edge]` `[Quality]` labels and the section structure are the compatibility baseline for the verification script and the deriver.

### 6. Don't dump questions all at once
In interactive collection, proceed naturally with 1–2 questions at a time.

### 7. Don't assume AI knows the user's whole domain
Ask about unfamiliar business terms, but never judge them wrong.

### 8. Don't verify epics at this stage
Requirement-level verification — detecting vague epics, proposing missing areas — happens at the SPEC generation stage.
This skill's validate.py checks only document form/completeness and surface-level vague expressions (forbidden phrases like 'as appropriate', 'TBD').

### 9. Don't lose free-form phrases at model discretion
Judging an input phrase unsuitable or ambiguous for this system is a reason to ask, not to delete.
Raise it in STEP 0's full-confirmation table so the human decides its disposition (reflect, convert, exclude).
Any phrase missing from the PRD without passing through the table is a violation.

### 10. Don't skim presented files and folders for extraction
File/folder materials are exhaustively listed by command, every file is read in full, and every file becomes a row of the extraction ledger.
An extraction missed because a file never passed through the ledger is the same violation as #9's phrase loss.

---

## Deliverable

This skill has exactly one deliverable: **`plan/PRD.md`**

---

version: 1.0.0
latest: 2026.10.23
Made by develojt
