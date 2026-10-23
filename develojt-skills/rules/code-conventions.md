# Universal Code Quality Principles (Code Conventions)

This file holds universal code-writing principles independent of any language or framework.
Where the per-project implementation guides (traceability, commit format, tech stack compliance, …)
cover "implementing without omissions",
this file covers "is the code being written good code in itself".

Concrete per-language rules — naming, formatting, error-handling patterns, function length,
parameter counts — are defined in `{language}.md` in this same folder.
When a principle here conflicts with a per-language rule, the per-language rule wins.

> **Scope of this document**: code quality and design principles only.
> Git workflow (branch strategy, commit message format) and CI/CD pipeline setup are managed
> by per-project implementation guides and are not covered here.

> **`.claude/` is a deployed copy — read-only**: this file, and all of `.claude/` (skills · agents ·
> rules), is a deployed copy of the global originals (`~/.claude/develojt-skills`). **No session records
> anything here** (no additions, no edits) — re-initialization (`/develojt-init`) overwrites everything
> with the originals, and the recording is lost. Decisions and rules that arise in the project go into
> project-owned documents (structural decisions via the `spec/ARCHITECTURE.md` revision procedure,
> appearance norms via `design/README.md`, and so on — through each owning skill's procedure). When the
> norms themselves (the files in this folder) need improving, raise it to the human via a report or a
> process-improvement proposal — the human applies it to the originals in the pipeline repository, and
> re-initialization propagates it.

---

## 0. Language Setting

Specifies the language code comments are written in. The builder (develojt-code-builder) and the comment verification gate (verify_comments) follow this value.

comment-language: english

- `english` (default for this package) — write comments in English. Verification: presence of a substantive English description in the comment block (a block with only @tags/symbols/non-English text does not count).
- `korean` — write comments in Korean (technical terms and proper nouns stay in English). Verification: presence of Korean text in the comment block.
- When this item or this file is absent, `english` is assumed.

---

## 1. Coding Mindset

These principles are a way of thinking that applies to every moment of writing code.

- **Handle the essentials, simply**: implement only the core functionality in the simplest way. Complex code has a higher bug rate, and its maintenance cost grows exponentially.
- **Prevent over-engineering**: add no unnecessary abstraction or design-for-the-future. When the need actually arrives, the requirements will differ from the prediction, so adding it then is both more accurate and more efficient (YAGNI).
- **One change at a time**: perform exactly one clear change at a time. Mixing multiple changes makes root-cause tracing hard when problems appear, and complicates code review and rollback.
- **Respect existing code**: identify and follow the project's existing patterns, naming rules, and structure first. If a linter/formatter is configured, comply with it. An inconsistent codebase drags down the whole team's productivity.
- **Prevent side effects**: in every add/modify/change/delete operation, leave unrelated existing code, features, structures, schemas, data, settings, and so on untouched. Unintended changes cause unpredictable bugs.
- **Immutability first**: declare variables immutable by default (`const`, `final`, `readonly`, `val`, …) and switch to mutable only when change is genuinely required. Immutable values prevent concurrency bugs, unintended state changes, and debugging pain at the source.
- **Minimal scope**: declare variables as close to their use as possible, accessible in the narrowest possible range. Default access control to private, widening only when needed. The wider the scope, the harder it is to trace the impact range.

---

## 2. Code Quality

The principles below apply identically to every language.
Concrete numbers and code examples — function length, parameter counts, error-handling patterns —
are defined per language in `{language}.md` in this same folder, so they are not repeated here.

### Function design

- **Single responsibility**: a function does one thing. A function that does several things is hard to test, and a change to one part affects the others.
- Keep functions short. When one grows, split it along units of meaning.
- Keep parameters few. When they multiply, group them into an object. Follow `{language}.md` in this folder for concrete thresholds.
- If a function has side effects, state that in its name.
- **Design for testability**: consider "how would I test this function?" as you write it. Abstract external dependencies, prefer pure functions, avoid depending on global state.

### Error handling

- Use exceptions only for exceptional situations. Controlling normal flow with exceptions obscures the code's intent.
- State the possibility of failure in the return type. Idiomatic patterns differ per language (Optional, Result, error returns, …), so follow `{language}.md` in this folder.
- Error messages include what went wrong and how to fix it.
- **Fail fast**: the moment bad input or state is detected, fail immediately. If the error only surfaces after bad data has passed through several layers, root-cause tracing becomes very hard.

### Boundary validation and external dependencies

Validate data at system boundaries (API input, file reads, user input, external service responses),
and trust data that has passed the boundary once inside.
Validating everywhere bloats the code defensively;
validating nowhere lets bugs burrow deep.

- **Master external APIs completely**: when using an external library or API, check the official docs or source directly to pin down the exact spec — parameter purposes, return values, error codes, call order. Functions with similar names but completely different purposes exist, so guess-based API usage is forbidden. The procedure that performs this check is builder essential 3's "first-use confirmation of external technologies" — a first-used external technology is always confirmed against the installed reality (type definitions, bundled docs) with `name version confirmed` recorded in the joblist, and web checks go through human approval.

### Code cleanup

- **Delete dead code immediately**: unused code is deleted on the spot. Version control preserves the history.
- **TODO comments**: state the concrete content and the owner. A vague TODO stays abandoned forever.
- **No magic numbers**: extract numeric literals into constants with meaningful names. `if retries > MAX_RETRIES` conveys intent more clearly than `if retries > 3`.
- **Avoid hard-coded strings**: separate configuration values, URLs, and paths into config files or environment variables.

### Readability

- **Use early returns / guard clauses**: minimize nesting. Deep nesting raises cognitive load.
- **Apply DRY on AHA timing**: don't repeat the same logic, but don't abstract prematurely either. Abstract once the common pattern is confirmed after 2–3 repetitions. A little duplication beats an unconvinced abstraction.

---

## 3. Design Principles

### Separation of concerns

Each module has one clear role. When roles blend, the impact range of a change becomes unpredictable.
For a web backend, separate into presentation/business/data-access layers; for a frontend, UI/state/service layers;
for a CLI tool, I/O and core logic. Decide the concrete layering to fit the project.

- No business logic in the presentation layer.
- Isolate data-access logic in a dedicated module.

### The single home of definitions

Enumerations of states, codes, and classifications (enums), named constants, and data structures (structs, data classes, types) are definitions — not business logic.

- A definition is declared and changed in exactly one shared home (if a structure contract exists, the definition home that contract sets). Everything else — screens, services, storage, and so on — only imports and uses it.
- A defined value is never restated as a literal at the point of use (state strings and code values are not written directly into screens or queries).
- Groupings derived from the same definition (a set of several states, etc.) are also named in that home — the set is not reassembled at each point of use.
- A definition is changed only in its home. A change of meaning requires a SPEC transition first.

### Composition over Inheritance

Prefer composition (assembly) over inheritance. Inheritance creates tight parent-child coupling,
and as the hierarchy deepens, changes propagate across the whole tree.
Composition assembles small independent units, so replacement and testing stay easy.
Use inheritance only for a true "is-a" relationship with a shallow hierarchy (2 levels or fewer).
Concrete inheritance-depth limits are defined per language in `{language}.md` in this folder.

### Dependency direction

Only upper layers reference lower layers. Reverse references cause circular dependencies.

### Dependency Injection

A module does not create its own dependencies; they are handed in from outside.
Constructor injection in OOP, Props/Context/provide on the frontend —
the patterns differ but the core principle is the same.
Injecting dependencies from outside makes mock substitution easy in tests,
and lowers coupling between modules so they can change independently.

### Backward compatibility

When changing a public API, interface, or data schema, verify compatibility with existing call sites.
Changing internal implementation and changing external interfaces have fundamentally different impact ranges.

### Configuration management

- Manage configuration centrally (environment variables or config files).
- Use a structure that supports per-environment configuration (dev/staging/production).
- Never put sensitive information (API keys, passwords) in code.

### Exception hierarchy design

> Where §2 Error handling gives function-level principles (return types, fail-fast),
> this section covers the project-architecture-level exception structure.

- Use layered custom exceptions. Define domain-specific exceptions inheriting from a project base exception class.
- Handle exceptions at the nearest appropriate layer to where they occur.

### Logging

- Use a centralized logger pattern.
- Distinguish log levels properly (DEBUG / INFO / WARNING / ERROR / CRITICAL).
- Never include sensitive information in logs.

---

## 4. Tools & Environment

> **Scope of this section**: package managers and licenses only.
> Linter/formatter settings follow the project's existing configuration (§1 "Respect existing code");
> if separate rules are needed, define them in `{language}.md` in this folder.

### Package manager

| Principle | Reason |
|------|------|
| Use the package manager the project already has | Mixing tools causes dependency conflicts and build failures |
| Always commit the lock file | Guarantees identical dependency versions across environments |
| Pin exact versions where possible | Range specifiers can break the build via unexpected updates |
| Add only strictly necessary dependencies | Pulling a large library for a small feature widens the security vulnerability surface |

**"Only strictly necessary dependencies" is a principle for the places where the AI chooses dependencies at its own discretion** —
the tech stack the SPEC has finalized is not subject to reduction or reconsideration under this clause (the upstream
decision has already answered whether it is necessary). Changing a finalized technology goes through the SPEC transition procedure, and is not an implementer's
alternative proposal (builder 'when a design change is needed').

### Licenses

Use **MIT / BSD / Apache-2.0** licensed external libraries by default.
Strong copyleft (GPL, AGPL, SSPL) is never used — its disclosure obligations reach the whole application.

**LGPL is conditionally accepted** — as weak copyleft, its disclosure obligations reach only
the library itself, so it can be used even in commercial projects when all three conditions
below hold. When an equivalent permissively licensed alternative (MIT/BSD/Apache) exists,
prefer that instead:
① **No modification** — do not touch the library's source (modifications fall under the LGPL
   disclosure obligation).
② **Replaceable linkage** — use it only in forms where the user can replace the
   library — dynamic linking, a separate file, a separate process. Static linking and
   single-artifact embedding (single binaries, merged bundles) create an obligation to provide
   relink means, so they are not used.
③ **Notice** — ship the LGPL notice, the full license text, and the library's origin (where it comes from)
   with the distribution.
However, on distribution channels where the user cannot replace the library (iOS App Store-like
channels, locked firmware), ② cannot be satisfied, so LGPL is not used there. Server-side code
that is never distributed does not trigger the obligations, so its burden is the lightest. When
adopting an LGPL library, state the linkage form (condition ② compliance) in the approval
request (the resource-acquisition protocol `resource-acquisition.md`, rung 3)
(note: LGPL conflicts with terms (EULA, license terms) that forbid reverse engineering of the combined work —
drafting those terms is the human's domain).

Always check the license when adding a new dependency.
