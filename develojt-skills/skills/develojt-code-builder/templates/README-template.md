# {project name}

> **Writing guide — delete this entire guide block when generating the README.** The protocol for the seat and direction is `rules/artifact-seats.md`
> (the product README row), and the generation point is develojt-code-builder workflow 7 (when the run profile is finalized).
>
> - **The 7 required sections always keep their headings, and their order never changes.** A section that does not apply is not deleted — write one line, `Not applicable — {reason}`,
>   in its body (to tell what was left out apart from what does not apply).
> - **Values are not copied; point to their sources** — values that change, such as versions, ports, and paths, point to the file where the value lives (manifests, configuration
>   files, `spec/run-profile.md`). The only things that may be copied are **install and run commands** (the user runs them as-is).
> - **Credential values are written in no section** — write only the item names and meanings, and point to `.env.example` or the like.
> - Optional sections are added only after the 7 required sections. Use the same language as `plan/PRD.md` (section headings in the same language too).
> - If a README already exists, do not overwrite it — fill in only the missing required sections.
> - In work that changes installation, configuration, or running (whether during development or operations), align the relevant section within that same work.
>
> | Section | What it holds | Source (the baseline of fact) | Not-applicable condition |
> |---|---|---|---|
> | 1. Overview | What the software does · who it is for · list of core features | `plan/PRD.md` §1 Project, `spec/SPEC.md` epic titles | None |
> | 2. Requirements | Runtime environment, OS, runtime versions, required external systems, hardware | PRD §2 System Setup and Technology Verification, SPEC runtime-base NFRs, `spec/joblist.md` install records, manifests | None |
> | 3. Installation | ① Components and downloads (packages, models, data, external tools) ② Procedure (install dependencies → build → confirm installation) | The manifests' install commands, `spec/run-profile.md` build command, PRD Core Technologies and joblist install records | None |
> | 4. Configuration | Names, meanings, whether required, and defaults of environment variables and configuration-file items (items, not values) | `.env.example` and configuration files, `rules/security-conventions.md` (secrets) | When there are no configuration items |
> | 5. Running and usage | Boot command → confirming a normal boot → basic usage examples (server: connecting and calling / CLI: command examples / library: import examples) | `spec/run-profile.md` boot, observation-check, and stop commands, the observable behaviors of the SPEC's core epics | None |
> | 6. Operations | Log locations · backup/recovery · monitoring · what to do on failure · upgrades/migrations · shutdown procedure | **This README is the source** (only the stop command comes from run-profile) | When the `spec/run-profile.md` type is not resident |
> | 7. License and third-party notices | This software's license, license notices for the third-party components it includes | `LICENSE`, the `rules/code-conventions.md` §4 policy, dependency audit results (the place where the notice duty of the LGPL conditional acceptance lands) | None (if private, "internal, not public") |
>
> Optional sections (examples — not a closed list): project structure (→ `spec/ARCHITECTURE.md`) · development and testing · deployment · troubleshooting ·
> change history (→ CHANGELOG) · screenshots/demos · how to contribute · support/contact · reporting security vulnerabilities, etc.

{One-sentence introduction — what the software does}

## 1. Overview

{Who it is for · what problem it solves — one paragraph}

Core features:
- {Feature 1 — based on the SPEC epic titles}
- {Feature 2}

## 2. Requirements

| Item | Requirement | Where to check |
|---|---|---|
| Runtime environment, OS | {e.g., Linux/macOS} | {PRD §2} |
| Runtime | {name — see the manifest for the version} | {e.g., package.json engines} |
| External systems | {DB, services — None if none} | {PRD §2 External System Integration} |
| Hardware | {acceleration devices, memory — None if none} | {PRD Technology Verification} |

## 3. Installation

### 3.1 Components and downloads

- {Packages, models, data, external tools — what to get and from where. For versions, see the manifest and joblist install records}

### 3.2 Procedure

```sh
{dependency install command}
{build command — the same as the spec/run-profile.md build command}
```

Confirming installation: {command or method}

## 4. Configuration

| Item | Meaning | Required | Default |
|---|---|---|---|
| {environment variable name} | {what it sets} | {Yes/No} | {value or None — secret values are never written} |

Example file: {path of `.env.example`}

## 5. Running and usage

```sh
{boot command — the same as the spec/run-profile.md boot command}
```

Confirming a normal boot: {the run-profile observation check — URL response / exit code / build success}
Stopping: {stop command or None}

Basic usage examples:

{server: connecting and calling examples / CLI: command and option examples / library: import and call examples — 1–2 core flows}

## 6. Operations

- Logs: {location, format}
- Backup and recovery: {method}
- Monitoring: {what to watch and how}
- What to do on failure: {symptom → action}
- Upgrades and migrations: {procedure}
- Shutdown procedure: {the run-profile stop command}

## 7. License and third-party notices

- This software: {license name — see `LICENSE` / internal, not public}
- Third-party component notices: {name — license — notice text, or see the NOTICE file. None if none}
