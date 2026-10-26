# develojt-skill-pipeline

**The human decides what to build; the AI decides how to build it.**

A collection of skills, agents, and rules for Claude Code. It walks a project in order from organizing requirements (PRD) through the requirement specification (SPEC), the work list, implementation, and omission checks.
Requirement IDs stay connected without a break from the PRD to the `@spec` tags in the code, and verification scripts plus human confirmation reduce the cases where the AI reports "all done"
while leaving part of the work out.

`8 skills` · `2 agents` · `15 rules` · `25 verification and helper scripts`

## Contents

1. [What it does](#1-what-it-does)
2. [What you need](#2-what-you-need)
3. [Installation](#3-installation)
4. [Usage](#4-usage)
5. [Skills and agents](#5-skills-and-agents)
6. [How one bundle is processed](#6-how-one-bundle-is-processed)
7. [Changes after development ends](#7-changes-after-development-ends)
8. [Safeguards by risk](#8-safeguards-by-risk)
9. [Steps where the human decides](#9-steps-where-the-human-decides)
10. [Rule files](#10-rule-files)
11. [Design principles](#11-design-principles)
12. [Files created in your project](#12-files-created-in-your-project)
13. [Updating and reinstalling](#13-updating-and-reinstalling)
14. [Repository structure](#14-repository-structure)
15. [License](#15-license)
16. [Versions](#16-versions)

---

## 1. What it does

When you hand development to an AI, similar problems keep recurring. This pipeline puts a safeguard against each one.

| Common problem | Safeguard |
|---|---|
| **Missing requirements**: a feature the human asked for drops out of the SPEC or the code | Requirement IDs are linked from PRD epics → SPEC → work list → code `@spec`, and omissions are checked every time a stage hands over to the next |
| **False completion**: reported as done, but connecting code, failure handling, or part of a screen is missing | The AI that implemented the code does not grade itself. A separate checker that does not know the implementation intent judges with `file:line` evidence, and the human compares screens directly |
| **Guesswork implementation**: API use based on memory, swapping a decided technology on its own, installing without permission | An external technology used for the first time is confirmed against what is actually installed, decided technologies are not reopened, and external resources need approval at every step |
| **Verification piled up at the end**: the first run happens only after everything is built | A basic skeleton that builds and runs even with no features is built first, and "it builds and runs" is checked by script for every bundle |
| **A different structure every session**: the same project is organized differently from session to session | The AI drafts a structure contract (`spec/ARCHITECTURE.md`), the human finalizes it, and it is re-read at the start of every bundle |
| **Different results per model and session**: the same instruction is carried out differently | Output formats are checked by verification scripts instead of prose instructions, and judgment criteria are fixed in rule files |

During development, the human runs the skills in order with slash commands. Each skill creates only its own output files,
and the next skill reads those files to continue the work. Skills exchange information only through files.

| Order | Skill | File it creates | What it does |
|---|---|---|---|
| 1 | `/develojt-spec-planner` | `plan/PRD.md` | Drafts the requirements through conversation. The human decides; the AI proposes candidates |
| 2 | `/develojt-spec-deriver` | `spec/SPEC.md` | Refines the epics into EARS-format requirements. Two agents reconcile their views |
| 3 | `/develojt-design-mapper` *(optional)* | `design/STORYBOARD.md` | Connects the design's UI elements and the SPEC requirements by ID. Runs only when `design/` exists |
| 4 | `/develojt-spec-spliter` | `spec/joblist.md` | Creates the progress list split into a basic skeleton (scaffolding) and work bundles |
| 5 | `/develojt-code-builder` | `src/` | Implements the bundles one at a time. When one finishes, runs pdca automatically |
| 5′ | `develojt-code-pdca` *(automatic)* | `spec/findings.md` | With a separate checker, repeats checking for omissions and fixing them until there are no defects |
| 6 | Screen comparison *(builder)* | `spec/screen-review.md` | The human compares the running screens with the design, one at a time |
| — | `develojt-code-changer` *(after development)* | None | Takes every change request after development ends. It runs even if you just say what you want changed |

When no items remain on the screen-comparison list, it is **development-draft completion**. A project with no screens to compare reaches development-draft completion as soon as all implementation is done.

![Figure 1. Overall flow](docs/img/01-flow.svg)

How requirement IDs connect from the PRD to the code, and the verification scripts that check this at each stage, are shown below.

![Figure 2. The traceability chain](docs/img/02-chain.svg)

## 2. What you need

| Tool | Purpose | Check command |
|---|---|---|
| Claude Code | The tool that runs the pipeline | `claude --version` |
| Python 3.10 or later (the `python3` command) | Running the verification scripts | `python3 --version` |
| `bash`, `perl`, POSIX `sh` | Running the initialization and verification scripts | `bash --version`, `perl -v` |
| `git` | Downloading the repository; part of the security check and the parallel-work check | `git --version` |

What to prepare on each operating system:

| Operating system | What to prepare |
|---|---|
| macOS | The built-in `python3` may be 3.9. If it is below 3.10, install a new one from [python.org](https://www.python.org/downloads/) or with `brew install python`. `bash` and `perl` are built in |
| Linux | Install `python3` (3.10 or later), `perl`, and `git` with your distribution's package manager (e.g., `sudo apt install python3 perl git`) |
| Windows | **[Git for Windows](https://git-scm.com/downloads/win) is required.** The initialization and verification scripts run on `bash` and `perl`, and both come with Git for Windows' Git Bash. Install Python 3.10 or later from [python.org](https://www.python.org/downloads/), and confirm in Git Bash that `python3 --version` shows 3.10 or later |
| Windows (WSL) | If you install and use Claude Code inside WSL, it is the same as Linux. Do installation, initialization, and running Claude Code all inside WSL |

## 3. Installation

Installation is just downloading the repository and running `install.sh` once. `install.sh` first checks that the required tools are present
(if any are missing, it changes nothing, tells you what to install, and stops), then copies to two places.

| Where it is copied | Contents |
|---|---|
| `~/.claude/skills/develojt-init/` | The project initialization skill (`/develojt-init`) |
| `~/.claude/develojt-skills/` | The pipeline originals (skills, agents, rules) |

`~` is your home folder: `/Users/name` or `/home/name` on macOS and Linux, `C:\Users\name` on Windows.

### macOS · Linux · WSL

Run in a terminal.

```sh
git clone https://github.com/develojt-oss/develojt-skill-pipeline.git
cd develojt-skill-pipeline
sh install.sh
```

### Windows

Open **Git Bash** from the Start menu and run it there (it does not run in Command Prompt or PowerShell).

```sh
git clone https://github.com/develojt-oss/develojt-skill-pipeline.git
cd develojt-skill-pipeline
sh install.sh
```

### Confirming the installation

You are done when the last line shows `=== Install complete (N files total, 0 overwritten) ===`.
If Claude Code was already open, you must run `/reload-skills` or restart Claude Code for `/develojt-init` to appear.

When `install.sh` stops:

| Message | What it means and what to do |
|---|---|
| `[ABORT] Required tools are missing` | Install the tools shown, then run it again |
| `[ABORT] CLAUDE_CONFIG_DIR is set` | This pipeline installs only relative to `~/.claude`. Run it without that environment variable in use |
| `[ABORT] Already installed` | Files from a previous installation exist. To reinstall, see [13. Updating and reinstalling](#13-updating-and-reinstalling) |

## 4. Usage

### ① Initialize the project

Open Claude Code in the project folder where you will use the pipeline, and run:

```text
/develojt-init
```

`skills`, `agents`, and `rules` are created under the project's `.claude/`, along with the version record file `.claude/version.md`.
If the project was already initialized, it shows the list of overlapping files (`!` content differs from the original, `=` identical) and asks whether to overwrite.
On a project initialized for the first time, `.claude/skills/` is newly created mid-session, so when initialization finishes, run `/reload-skills` or restart Claude Code.

### ② Getting started

| Situation | Command to run |
|---|---|
| A new project | `/develojt-spec-planner` (you may freely write what you want to build as an argument) |
| `plan/PRD.md` already exists | `/develojt-spec-deriver` |
| Design files (`design/`) exist | `/develojt-design-mapper` after SPEC approval |
| The SPEC is complete | `/develojt-spec-spliter` → `/develojt-code-builder` |
| Changes after development-draft completion | Say the change you want; `develojt-code-changer` runs and reports what it received first |

### ③ Moving implementation forward

By default the builder implements only **the next single bundle not yet checked**, and after each bundle asks whether to proceed to the next.
You can also specify a range, such as `"all"` or `"through FR-07"`. In every case the order **report → approval → implementation** does not change
(just saying "continue" counts as running the skill again, not as an approval).

## 5. Skills and agents

### planner: requirements draft (`plan/PRD.md`)

- Asks one or two questions at a time to gather project information and the **system setup** (runtime environment, OS, development type, core technologies, authentication, external integration).
  For undecided items it shows candidates and lets the human choose. Blanks are never passed to the next stage.
- Proposes epic candidates from four lenses (`[Scene]` usage scenes, `[Rule]` business rules and data, `[Edge]` failures and exceptional situations, `[Quality]` quality and feel),
  4–6 per lens. `[Foundation]` items are generated from a fixed table according to the system-setup combination. Proposals are not decisions;
  adopting, deleting, and editing are the human's.
- Nothing the human provides is discarded. A free-form description gets its handling confirmed phrase by phrase in a table, and for files and folders
  a full list is made first, then each file is read to the end and the extraction results are organized in a table.
- **Technology verification**: after human approval, it researches whether the chosen technologies can handle the requirements, leaving a source for each item.
  If the documents alone leave it unsure, it gets approval and experiments directly with small code in a `spike/` folder (this code is not used in the real implementation).
- Verification script: `validate.py`. The PRD's 'Finalized' check is made by the human directly.

### deriver: EARS requirements (`spec/SPEC.md`)

- Two agents, the **Theorist** (theory expert) and the **Pragmatist** (practice expert), each write a draft, review each other's, answer the objections, and then write the final version.
  Every opinion is exchanged through files. The main session running the process only manages the order, merges, and verifies — it does not write content.
  Items they could not agree on are marked `[Needs review]` and asked of the human.
- Requirements are written in the 5 EARS types (Ubiquitous, Event-Driven, Unwanted, State-Driven, Optional).
  IDs take the forms `FR-epic-seq`, `NFR-00-seq`, and `FR-epic-Eseq`, and with 6 source tags you can tell where in the PRD every requirement came from.
- A requirement's outcome is written in a form that can be confirmed from outside (a screen display, a response, a save, etc.). When one action causes several outcomes together,
  they are organized in a **behavior chain table**. This table becomes the baseline the builder wires code against and the baseline pdca checks against.
  Items whose values are left to the AI are marked `[Free: reason]` to distinguish them from a simple omission.
- It finds features not in the documents but definitely needed (`[Implicit]`), per-feature security behaviors, and even **runtime-base requirements** (what must respond when the system starts).
- It works in three ways: building from scratch (with negotiation), adding features (adding only new IDs), and changing existing requirements (never deleting — marking `[Removed]` and assigning a new ID).
- Verification scripts: `verify-sections.sh`, `verify-sources.sh`, `verify_prd_coverage.py`. The human approves afterwards.

### mapper: connecting design and requirements (`design/STORYBOARD.md`, optional)

- The design is the baseline for how screens look, and the SPEC is the baseline for what features do. The mapper only connects the two by UI ID (`SB-NN-MM`).
  It does not decide new features and does not edit the SPEC.
- Each UI element gets two location markers (which area of the screenshot, an identifier found by searching the screen source) and is connected to its related FRs (several FRs per element and several elements per FR are possible).
- Unpaired items are surfaced, not hidden: `[Candidate]` (a feature in the design but not in the SPEC, collected separately in `spec-candidates.md`),
  `[No UI]` (a feature in the SPEC but not on screen), `[Decorative]` (an element with no feature that must still be implemented on screen as-is),
  and conflicts (the design and the SPEC disagree — collected in `spec-conflicts.md`, and the human decides which side to follow).
- Two agents, DesignTheorist and DesignPractitioner, reconcile their views the same way as in the deriver. For changes after development there are
  promote (adopting candidates, registering new FRs) and remap (reflecting changes, reflecting conflict decisions, reflecting appearance changes) modes.
- Verification scripts: `verify-anchors.sh`, `verify-coverage.sh` (`verify-stale.sh` added in remap). The human approves afterwards.

### spliter: progress list (`spec/joblist.md`)

- The basic code every bundle uses in common (configuration, types, startup code, etc.) and the runtime environment (runtime, data stores, middleware, etc.) are grouped as **scaffolding** and put at the very front.
  When the scaffolding is done, the system builds and runs even with no features (the **walking skeleton**).
- The remaining requirements are made into **bundles** of things that actually call each other or use the same data in the code. Since a finished bundle must let you
  see its result directly, a long processing flow is not split by layer — a bundle that runs thinly from beginning to end is made first, and features are added on top.
- Items that must be built the same way are marked as a **series** (the first item is the reference). It also records reference notes (the location of the same series, work deliberately postponed, cautions,
  technology-use records, screen element IDs) and **parallel candidate** bundles that do not overlap at all and can be built at the same time.
- Verification scripts: `verify_joblist_integrity.py`, `verify_joblist_spec_sync.py` (0 missing IDs, 0 IDs absent from the SPEC), `verify_anchor_sync.py`.

![Figure 5. Cutting bundles](docs/img/05-cut.svg)

### builder: implementation (`src/`)

- **Only five things are strictly enforced.** ① put a `@spec` tag on every implementation ② wire every outcome of the behavior chains into code without omission
  ③ honor the tech stack, structure contract, design, and stated failure handling ④ write only the code that is needed ⑤ never grade your own code.
  Other structure, patterns, and algorithms are freely decided by the AI.
- It always proceeds in the order **assess state → report → stop → approval → implement**. When requirements, technology, structure, or design must change mid-implementation,
  it does not change them on its own; it stops and reports.
- For a new project it puts up a **structure contract** draft in the first report and, when the scaffolding is done, a **run settings (run profile)** draft. The human finalizes both,
  and once the run settings are finalized it also creates the product `README.md`. A project started without a structure contract can adopt one midway with the instruction "set up the structure contract".
- If `design/` exists, screens are built exactly as designed (the design guide README must be followed, and screen sources, screenshots, and related files are each consulted for their own purpose).
  Whether a screen is right is judged finally by the human. Each bundle is put on the screen-comparison list, and once all implementation is done they are compared one by one.
- Verification scripts: `verify_refs.py`, `verify_todo.py`, `verify_spec_coverage.py`, `verify_comments.py`, plus the run check `verify_boot.py`.

### pdca: repeating omission checks and fixes (`spec/findings.md`, automatic)

- Run only by the builder and the changer (if a user runs it directly, it only explains). The main session handles planning (Plan) and fixing (Act),
  and a **separate checker agent** handles checking (Check). The checker receives only the check scope and the defect IDs already recorded, not the implementation intent.
- Verdict criterion: if you can show where the code is actually connected as `file:line`, it is fine; if you cannot, it is a defect.
  There are 10 defect types (M1, W1, W2, W3, F1, C1, C2, C3, C4, S1).
- **Quiescence** (normal end): two consecutive checks with 0 new defects and 0 remaining defects, done in two different ways (way A starting from the code,
  way B starting from the requirement sentences). It does not wait for human approval between checks.
- The first time a project reaches quiescence, a **checker performance measurement** is made once: 3 defects are deliberately planted, the number the checker finds is measured, and the code is restored.
- Records are never deleted. Resolved defects and old check records are moved to `findings-archive.md` with a dedicated script,
  and records judging C2–C4 candidates as not defects are kept in `findings-rejected.md` so the same candidates are not judged again in the next check.

### changer: change intake after development (runs automatically)

- It runs even if you just say what you want changed, like "add a feature", "remove this feature", or "refactor this". Since the other skills run only by slash command,
  this skill prevents fixing the code first, bypassing the SPEC, because someone forgot to run a skill.
- It proceeds in the order **classify → report what was received → human confirmation → execute**. Even when it ran automatically, the human confirmation is never skipped.
- This skill creates no files directly. The SPEC is edited by a subagent following the deriver's procedure, the STORYBOARD by a subagent following the mapper's procedure,
  and the code by the main session following the builder's five principles. Each procedure refers to the original skill's document as-is and never copies it.

### init: initialization

- `/develojt-init`: copies the globally installed originals into the project's `.claude/` and creates the version record file.

### Agents

| Agent | Skill it works with | What it does | What it does not do |
|---|---|---|---|
| `develojt-code-pdca-checker` | pdca's check stage | Reads only SPEC, joblist, findings, and src, and reports defects with evidence in record format | Editing code, adding requirements, flagging `[Free]` items, flagging style |
| `develojt-code-slice-builder` | builder's parallel work | Implements one bundle by creating only new files in its assigned folders, and hands the connections needed in existing files to the main session as a list | Editing existing files, recording the progress list, running pdca, web search |

## 6. How one bundle is processed

1. **Assess state (read only)**: checks the next unchecked bundle, unresolved defects (if any, pdca runs again first), the structure contract, design files, and the number of screen comparisons waiting.
2. **Report → stop → approval**: reports progress, this scope, how the design will be reflected, and structure matters, then waits for the human's approval.
3. **Re-read the rules**: re-reads `design/README.md`, `rules`, and `spec/ARCHITECTURE.md` (to prevent forgetting rules as a long conversation gets its early parts summarized).
4. **Implement**: the main session implements directly, in order. Each time it finishes one module or one processing flow, it immediately leaves a check and a note in the joblist.
5. **Self-check**: runs the 4 verification scripts (`@spec` tags, empty functions, whether requirements are reflected, comment language) and the run check.
6. **pdca runs automatically**: repeats checking and fixing until quiescence. It does not ask in between.
7. **Run check once more**: confirms again that it builds and runs even after pdca fixed the code.
8. **Register on the screen-comparison list**: if the bundle has screens, puts it on the screen-comparison list and gets the human's confirmation (the comparison itself happens after all implementation is done).
9. **Confirm the next bundle**: when the human answers to proceed, that becomes the approval for the next scope.

Once the run settings are finalized, every work scope goes through the run check (`verify_boot.py`) when it finishes.

| Run settings type | Run check pass criterion |
|---|---|
| Resident (servers, apps) | Build succeeds → run → the check URL responds with HTTP 2xx within the time limit |
| One-shot (CLIs, etc.) | Build succeeds → the run command ends with exit code 0 within the time limit |
| Library | The build command ends with exit code 0 within the time limit |

The run check looks only as far as "it builds and runs". Judging whether features work as the requirements say (E2E tests, demos) is outside this pipeline's scope.

**Parallel work (optional)**: when the structure contract and the basic skeleton are in place and 2–3 bundles are registered in the same `## Parallel Candidates` group of the joblist,
several agents can do **only the implementation** at the same time, with the human's approval. Merging results, verification, recording, and pdca are handled by the main session one bundle at a time,
and if even one verification fails, that bundle switches to sequential work.

![Figure 3. How one bundle is processed](docs/img/03-bundle.svg)

![Figure 4. The pdca loop and defect states](docs/img/04-pdca.svg)

![Figure 7. Parallel work](docs/img/07-wave.svg)

## 7. Changes after development ends

Once the development draft is complete, the PRD and the joblist are no longer used, and only the SPEC remains as the baseline document. The changer sorts change requests by kind
and handles them through the relevant skill's procedure, and each stage must pass the previous stage's verification in the order **SPEC → STORYBOARD → code** before moving to the next.

| Category | For requests like | Processing order |
|---|---|---|
| Addition | A new feature, a new requirement | deriver addition mode → (if a STORYBOARD exists) register with mapper promote → code |
| Candidate adoption | Adopting a candidate from `design/spec-candidates.md` | deriver addition mode → reflect into the STORYBOARD with mapper promote → code |
| Change/deletion | Modifying or deleting an existing requirement | deriver change mode (`[Removed]` + a new ID) → (if a STORYBOARD exists) mapper remap → code |
| Conflict resolution | A decision on a conflict in `design/spec-conflicts.md` | A (design baseline): deriver change → remap → code / B (SPEC baseline): tidy up with remap → check the code |
| Code only | Review comments, refactoring, changing a screen's look, instructions about the structure contract | The requirements stay as they are and only the flagged parts are fixed. `@spec` tags move along with their functions |

After the code is fixed, the 4 builder verifications, the 3 minimum-baseline checks (security, duplicate definitions, finding structure-contract violation candidates), and the run check are run.
If even one candidate comes up in the minimum-baseline checks, pdca must check again (the checker judges).

**While development is still in progress** (while the joblist still has unchecked bundles), the changer does not take requirement additions or modifications.
They go into the progress list through `/develojt-spec-deriver` → `/develojt-spec-spliter` addition mode, and then the builder implements them as the next bundle.

![Figure 6. Handling changes in operations](docs/img/06-change.svg)

## 8. Safeguards by risk

| Risk | How it is prevented | Responsible |
|---|---|---|
| PRD epics left out | Checks that the number of epics equals the number of EPs in the SPEC and that every EP has at least 1 requirement | `verify_prd_coverage.py` |
| Items missing from the progress list, references to IDs that do not exist | Cross-checks the SPEC and the joblist in both directions | `verify_joblist_spec_sync.py` |
| Missing tags, tags pointing at IDs that do not exist | Checks that every function and class has `@spec`, that every FR is in the code, and that no ID that does not exist is referenced | `verify_refs.py`, `verify_spec_coverage.py` |
| Functions with only a tag and an empty body | Detects functions whose body is empty or holds only a TODO | `verify_todo.py` |
| Unconnected code | Confirms the actual call path for each outcome of a behavior chain | pdca W1, W3 |
| Missing failure handling | Confirms the handling code for exceptional-situation (If/Unwanted) requirements | pdca F1 |
| Violations of basic security rules | Finds candidates for secrets (S1–S4), dangerous APIs (A1–A9), and SQL string assembly (Q1), and the checker judges them | `verify_security.py` → C2 |
| Duplicate definitions | Detects duplicate definitions with the same name, value, or body (adding a row to the rule table adds a check item) | `verify_enforced_rules.py` → C3 |
| Structure-contract violations | Detects references in directions not allowed and folders not in the structure contract | `verify_architecture.py` → C4 |
| Defects the checker misses | Deliberately plants 3 defects and measures how many it finds | pdca checker performance measurement |
| Sliding back into an unrunnable state | Build → run → response check (criteria fixed per type) | `verify_boot.py` |
| Screens that differ from the design | Puts each bundle on the screen-comparison list, and the human compares directly once implementation is done | `spec/screen-review.md` |
| Mismatches between the design and the SPEC | Marks unpaired items and conflicts, confirms screen-source searches, confirms whether FRs are reflected | the 3 mapper verifications |
| Traces of changed requirements | On modification, changes to `[Removed]` + a new ID, so list rows and tags pointing at the old ID get caught by the checks | deriver change mode |
| "Check complete" on truncated output | Caps output at 16KB and shows a `… N more … not printed` notice | the 3 candidate-detection scripts |
| Judging the same candidates again every time | Carries the records judging them as not defects over to the next check | `spec/findings-rejected.md` |
| Lookups, web searches, and installs without permission | External resources need approval at every step and proceed in order | `rules/resource-acquisition.md` |
| Wavering judgment criteria | 6 principles: respecting what is finalized, confirming grounds, the recommendation criterion, checking everything, handling uncertainty, how to record | `rules/judgment-conduct.md` |
| Records landing in different folders every session, a handoff standing in for the official documents | Fixes a seat table for records; the handoff is for passing on only (it loses effect and is overwritten once the next session takes over); decisions are recorded in the document they belong to | `rules/artifact-seats.md` |
| Reports and questions hard for a human to understand (sentences made of row numbers and status names, questions asking whether you remember what was done in a past session) | Rules for sentences shown to a human: the subject is the product and the human's actions, a target is named by what it is rather than by a number, answerable from what is shown now alone, a check before sending | `rules/human-language.md` |

> A check script passing does not mean "there is no problem"; it means "there are no candidates in the kinds a script can find".
> Judgments outside a script's scope are never replaced by script results.

## 9. Steps where the human decides

There is one principle: **the AI designs; the human finalizes.** The steps that need a human decision are fixed in advance, and progress outside them does not ask.

| Stage | What the human decides |
|---|---|
| planner | Handling of phrases open to different readings, choice of undecided technologies, whether to proceed with technology research and experiments, PRD 'Finalized' |
| deriver | Answers to questions the agents raise, choices on `[Needs review]` items, SPEC approval |
| mapper | Answers to questions the agents raise, STORYBOARD approval, candidate adoption, choosing design or SPEC as the baseline in a conflict |
| builder | The work scope of each bundle, the structure contract, whether to implement design code by translating it to another technology, the run settings, parallel work, screen comparison, design changes (requirements, technology, structure, screens) |
| pdca | Decisions on `Needs review` items, approval of process-improvement proposals (the repetition of checks itself is not asked) |
| changer | Confirming what was received (never skipped, even when it ran automatically) |
| Always | Every action that goes outside the project (system lookups, web research, installs) |

The sentences a skill shows a human (reports, explanations, questions) follow the rules of `rules/human-language.md`. Subjects and objects are the product and the human's actions,
a target is named by what it is rather than by a number or ID, it never asks whether you remember what was done in a past session, and technical terms are briefly explained on first appearance.
When asking for a decision, it ① first states in one sentence what must be decided ② writes one line per option on what changes if you pick it ③ puts only one decision in a sentence.
For hard-to-reverse **structural decisions**, it puts up two or more candidates of different character, with each one's weaknesses, in the same table
(an option the human proposed goes into the same table and is reviewed the same way).

## 10. Rule files

Claude Code automatically loads the files in `rules/` into the session. Files without a `paths` setting load in every session; files with a `paths` setting
load only when working with files on those paths.

| File | When it loads | Contents |
|---|---|---|
| `code-conventions.md` | Always | Language-independent code-quality principles: writing attitude, function design, error handling, design principles, package management, licenses (MIT/BSD/Apache by default, GPL·AGPL·SSPL forbidden, LGPL allowed conditionally), the comment-language setting `comment-language` |
| `security-conventions.md` | Always | 12 items based on the OWASP Top 10, API Security Top 10, and CWE Top 25. When they conflict with other rules, the security rules win |
| `resource-acquisition.md` | Always | The order for obtaining external resources: local check → web research → install, with approval at every step |
| `judgment-conduct.md` | Always | 6 principles for judging (respecting what is finalized, confirming grounds, the recommendation criterion, checking everything, handling uncertainty, how to record) |
| `artifact-seats.md` | Always | Where records are placed (research `research/`, security inspections `security/`, submission documents `deliverables/`, the product README, the handoff `spec/handoff.md`) and their relation to the official documents |
| `human-language.md` | Always | Rules for writing sentences shown to a human (reports, explanations, questions, approval requests) |
| `enforced-rules.md` | When working on `src/**` | A rule table the scripts read and check (no duplicates: R-01 same name, R-02 same value, R-03 same body) |
| 8 per-language rule files | When working on that extension | `cpp`, `csharp`, `java`, `javascript`, `python`, `react`, `typescript`, `vue` |
| `design-philosophy.md` | Not deployed to projects | The judgment criteria for **modifying** the skills ([11. Design principles](#11-design-principles)). Exists only in this repository and the global installation |

The judgment principles in one line:

> Do not change what is finalized lightly, confirm grounds with real files and results, base recommendations on what is technically right, read material all the way through,
> take the safe side when in doubt, and record only facts. The human always makes the decision.

The external-resource rule in one line:

> Every action that goes outside the project (system lookups, web access, installs) happens only after the human's approval. When in doubt, do not run it — ask first.

![Figure 8. The order for obtaining external resources](docs/img/08-ladder.svg)

## 11. Design principles

When **modifying** this pipeline, all 6 criteria below must be met ([`develojt-skills/rules/design-philosophy.md`](develojt-skills/rules/design-philosophy.md) is the original, written in English; this section is an explanation to aid understanding).

| Criterion | Explanation |
|---|---|
| 1. Universality | It must apply equally to all software development. No domain-specific terms or examples go into skills, rules, or samples. Domain content is decided in the PRD and SPEC |
| 2. Same results on weaker models | Write in procedures, tables, and short instructions; keep metaphors and long explanations out of the skill bodies. The baseline minimum model is **fixed** at Claude Opus 4.8/4.7, and raising this baseline is the human's decision |
| 3. Keeping the autonomy of stronger models | Do not make so many rules that they block the autonomy to decide structure, patterns, and algorithms. Enforce only what must be honored (traceability, wiring, the requirements' constraints), and when this conflicts with 2, the stronger model is the baseline |
| 4. Clear division of roles | planner organizes requirements with the human, deriver refines requirements, mapper connects the design and the SPEC, spliter makes the progress list, builder implements, pdca checks for omissions, changer takes changes after development. Each skill creates only its own outputs |
| 5. Simplicity | Use the easiest, most ordinary method with consistent results. Variation in results is managed by verification scripts, not prose instructions |
| 6. Judging actual behavior is out of scope | This pipeline does not judge whether features are right by running them (E2E tests, demos), and pdca also checks only by reading the code. The only exception is the build, run, and response check, which is a check of the same nature as a compile check, not a feature judgment |

**Core principles**

1. **The most important documents are the PRD and the SPEC.** If these two are solid, the later stages (splitting work, writing code) follow well even when the model or technology changes.
2. **planner and deriver must reach the same result whichever model runs them.** Undecided items are resolved by showing candidates and letting the human
   choose, and blanks are never passed to the next stage. The later skills only follow the set conditions and decide nothing new.
3. **The human leads and the AI helps.** The human decides the requirements. The AI proposes candidates generously, and adopting, deleting, and editing are the human's.
4. **Organizing and refining are work in opposite directions.** planner organizes the human's thoughts into short sentences (epics), and deriver, starting from those epics,
   finds the intent and hidden features and refines them into EARS requirements.
5. **Consistent results come from simplicity.** Complex methods that lean on a model's ability break when the model changes. Agents exchange information through files instead of specific tool features.
6. **Split the work, but never break the ID links.** The SPEC is split into bundles implemented one at a time, but the link PRD epic → SPEC ID → joblist row → `@spec`
   must be kept at every stage.

## 12. Files created in your project

```text
your-project/
├── .claude/                  ← files copied by /develojt-init (read-only — never record anything here)
│   ├── skills/  agents/  rules/
│   └── version.md            ← version record
├── README.md                 ← builder · the product README (created when the run settings are finalized)
├── plan/PRD.md               ← planner
├── spec/
│   ├── SPEC.md               ← deriver · the baseline document for every stage
│   ├── joblist.md            ← spliter · the progress list (checks and notes by the builder)
│   ├── ARCHITECTURE.md       ← builder draft · human-finalized (structure contract)
│   ├── run-profile.md        ← builder draft · human-finalized (run settings)
│   ├── findings.md           ← pdca · defect record
│   ├── findings-archive.md   ← pdca · archive of resolved defects
│   ├── findings-rejected.md  ← pdca · record of not-a-defect verdicts
│   ├── screen-review.md      ← builder · screen-comparison list
│   └── handoff.md            ← session handover note (loses effect and is overwritten once the next session takes over)
├── design/                   ← design files the human puts in (the originals are never edited)
│   ├── STORYBOARD.md         ← mapper
│   ├── spec-candidates.md    ← mapper · candidate list
│   └── spec-conflicts.md     ← mapper · list of design-vs-SPEC conflicts
├── research/                 ← raw research material (conclusions go to the PRD and SPEC)
├── security/                 ← external-standard security inspection material and reports (code fixes go to findings)
├── deliverables/             ← submission and delivery documents (only for projects that need them)
├── src/                      ← builder · code always goes in this folder
└── spike/<target>/           ← planner technology experiments · never reused in the real implementation
```

The languages whose code the verification scripts can read are JavaScript, TypeScript, Vue, Python, C#, Java, and C++ (partially supported).
For other languages the scripts cannot check, so the report states that fact and it is confirmed by hand.
Outputs (PRD, SPEC, STORYBOARD) are written in English, and the code comment language follows the `comment-language` setting (english or korean) in `rules/code-conventions.md`.

## 13. Updating and reinstalling

After getting a new version or editing the originals, run two steps again (on Windows, in Git Bash).

```sh
cd develojt-skill-pipeline
git pull
sh install.sh --force     # overwrites the global originals
```

Then run `/develojt-init` again in each project. It shows the list of overlapping files and overwrites after getting confirmation.
A `!` mark in the list means the content differs from the original, so overwriting will lose the changes made in that project.

Reinstalling or re-initializing **only overwrites; it never deletes.** Files removed in a new version stay in `~/.claude/develojt-skills/` and
in the project's `.claude/`, so delete them yourself if needed (in particular, files left in `rules/` keep getting loaded).

The project's `.claude/` is a **read-only copy**. Write project decisions in the project documents (`spec/ARCHITECTURE.md`, `design/README.md`, etc.),
and if you want to change the rules themselves, edit the originals in this repository by the criteria of [11. Design principles](#11-design-principles), then reflect them again in the order above.

![Figure 9. Installation and deployment](docs/img/09-deploy.svg)

## 14. Repository structure

```text
develojt-skill-pipeline/
├── install.sh                    # global installation (~/.claude/)
├── skills/
│   └── develojt-init/            # initialization skill (/develojt-init)
├── develojt-skills/              # pipeline originals
│   ├── version.md                # package version
│   ├── skills/                   # planner · deriver · mapper · spliter · builder · pdca · changer
│   ├── agents/                   # pdca-checker · slice-builder
│   └── rules/                    # 7 common + 8 per-language + design-philosophy (not deployed to projects)
├── docs/img/                     # the 9 figures in this document
└── LICENSE
```

## 15. License

[MIT](LICENSE)

## 16. Versions

| Version | Date | Key addition |
|---|---|---|
| 1.1.0 | 2026-10-26 | The names and shapes of interfaces that outside parties build against (APIs, command arguments, file formats, etc.) are finalized in the SPEC, and the code follows them as-is |
| 1.0.0 | 2026-10-23 | First public release |
