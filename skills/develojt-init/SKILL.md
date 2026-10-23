---
name: develojt-init
description: |
  develojt pipeline initialization skill.
  Copies the original assets (skills/agents/rules) from the global ~/.claude/develojt-skills into the current project's .claude/.
  Run with /develojt-init.
---

# develojt-init

## Philosophy

- The develojt pipeline's **originals live only in the global `~/.claude/develojt-skills`**.
- The global `~/.claude/skills/` holds no pipeline — only this bootstrap skill (`develojt-init`).
- **Every initialization copies the originals into the current project's `.claude/`** for use there.

## What gets copied (1:1 mirror)

| Source | → Target |
|---|---|
| `~/.claude/develojt-skills/skills/` | `.claude/skills/` |
| `~/.claude/develojt-skills/agents/` | `.claude/agents/` |
| `~/.claude/develojt-skills/rules/`  | `.claude/rules/` |

- Target folders are created automatically if missing.
- `.DS_Store`, `__pycache__/`, and `*.pyc` are excluded.
- `rules/design-philosophy.md` is excluded too — it is the judgment filter for **modifying** the skills (the file scopes itself: "running follows each SKILL.md"), so deploying it to projects that only **use** the skills would only add the cost of loading it in every session. The original stays in the repo/global only.
- `.sh`/`.py` scripts get execute permission.
- Separately from the copy, it generates the **deployed version stamp** `.claude/version.md` — the original `version.md` (a developer document holding the development history and operating policy) is not deployed; only the version and baseline date are extracted from its 'Current version' table into a `Deployed version | Package baseline date | Initialized on` table. Each re-initialization stacks a new row on top, and an identical row is kept only once. It is an init-owned artifact, so it is not subject to the conflict scan or loss visibility (always regenerated).

## Re-initialization policy (duplicate runs)

**Re-initializing always overwrites — but user approval is required before overwriting.**

- Default `init.sh` run: if even one file of the same name already exists at the target, it **changes nothing**, prints the conflict list, and aborts with `exit 3` (preventing partial copies).
- Once the user approves the overwrite, re-run with `--force` to refresh everything to the latest global originals.
- **Loss-visibility safety net**: the project's `.claude/` is a read-only deployed copy (the declaration at the top of `rules/code-conventions.md`), so a file whose content differs from the original means it was written to locally or is an older version. Each file in the conflict list is marked `!` (content differs from the original — overwriting loses the local change) or `=` (identical), and `--force` re-prints the `!` list as `[CAUTION]` right before overwriting. The script never blocks — when `!` files exist, show that list to the user as-is while asking for the overwrite approval, and let them judge whether anything needs preserving (the loss judgment belongs to the human).

## Execution Procedure

The script must be run from **the project root being initialized** (`.claude/` is created relative to the current working directory).

`init.sh` is written in pure POSIX sh and works on macOS, mainstream Linux, and Alpine/busybox alike (no bash dependency).

### 1) Default run

```sh
sh ~/.claude/skills/develojt-init/scripts/init.sh
```

- **exit 0** → fresh copy complete. Done.
- **exit 3** → conflicts with existing files (an already-initialized project). Go to 2) below.

### 2) On conflict — overwrite after approval

On `exit 3`, show the user the conflict list exactly as the script printed it, and **get explicit approval to overwrite** (AskUserQuestion). If approved:

```sh
sh ~/.claude/skills/develojt-init/scripts/init.sh --force
```

If not approved, exit without any changes.

## After copying — starting the pipeline

The develojt pipeline installed into `.claude/skills/`:

- `develojt-spec-planner` — write `plan/PRD.md` interactively
- `develojt-spec-deriver` — PRD → `spec/SPEC.md` (EARS)
- `develojt-design-mapper` — (if design/ exists) SPEC↔design mapping → `design/STORYBOARD.md`
- `develojt-spec-spliter` — SPEC → progress ledger `spec/joblist.md`
- `develojt-code-builder` — SPEC/joblist-based code implementation (harness, every design/ asset in its own role — README mandatory → screen sources → screenshots as the fallback. When a parallel wave is approved, paired with the slice agent `develojt-code-slice-builder`)
- `develojt-code-pdca` — post-implementation inspect-and-reinforce loop (paired with the checker agent `develojt-code-pdca-checker`)
- `develojt-code-changer` — (operations phase) change intake front door — auto-enters on stated change intent, human confirmation before any write

Where to start: for a new project, `/develojt-spec-planner`; with an existing `plan/PRD.md`, `/develojt-spec-deriver`.

---

version: 1.0.0
latest: 2026.10.23
Made by develojt
