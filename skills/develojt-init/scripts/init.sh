#!/bin/sh
set -eu

# develojt-init: copies the global develojt pipeline assets into the current project's .claude/.
#
# Philosophy:
#   - The 'originals' of the user's skill pipeline live only in the global ~/.claude/develojt-skills.
#   - The global skills folder holds no pipeline (only this bootstrap skill).
#   - Every initialization copies the originals into the local project for use there.
#
# Mapping (1:1 structural mirror):
#   ~/.claude/develojt-skills/skills/  → .claude/skills/
#   ~/.claude/develojt-skills/agents/  → .claude/agents/
#   ~/.claude/develojt-skills/rules/   → .claude/rules/
#
# Deployed version stamp (.claude/version.md — generated in refined form, not copied):
#   The original version.md (which carries development history and operating policy) is not deployed — the deployed copy
#   may be used by anyone, so content needed only for development is not carried (the refined-deployment principle). Instead,
#   only the version and baseline date are extracted from the original's 'Current version' table to generate the deployed stamp,
#   and each re-initialization stacks a stamp row on top (a simple deployment history — an identical row is kept only once).
#   This file is an init-owned artifact, so it is not subject to the conflict scan or loss visibility (always regenerated).
#
# Re-initialization (duplicate-run defense):
#   On a default run, if even one target file already exists, report the conflicts
#   'without changing anything' and abort with exit 3. Re-initialization always means
#   overwrite; after user approval, re-run with '--force' (the approval gate lives in
#   the calling skill).
#
# Loss-visibility safety net:
#   The project's .claude/ is a read-only deployed copy (the declaration at the top of
#   code-conventions.md) — so a target file whose content differs from the original means
#   a local recording (edit) or an older version, and overwriting erases that difference.
#   The conflict list marks each file '!' (content differs) / '=' (identical), and --force
#   re-prints the '!' list right before overwriting — it never blocks (the loss judgment
#   belongs to the human).
#
# Excluded: .DS_Store, __pycache__/, *.pyc, design-philosophy.md
#   (design-philosophy is the judgment filter for *modifying* the skills — the file scopes itself
#    to that work ("running follows each SKILL.md"). In projects that only *use* the skills it
#    would just add an always-on context load (a rules file without paths), so it is not deployed.
#    The original stays in the repo/global only.)
#
# Portability: pure POSIX sh. Works on macOS (/bin/sh), mainstream Linux (dash/bash),
#              and Alpine/busybox (ash). No arrays, process substitution, or pipefail.
#              External commands are standard POSIX: find, cp, mkdir, chmod, wc, tr, dirname, pwd, cmp, grep, sed, date.

SRC="$HOME/.claude/develojt-skills"
DEST=".claude"
SUBDIRS="skills agents rules"

FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force|-f) FORCE=1 ;;
    *) echo "[ERROR] Unknown argument: $arg (usage: init.sh [--force])" >&2; exit 2 ;;
  esac
done

echo "=== develojt-init ==="
echo "Source: $SRC"
echo "Target: $(pwd)/$DEST"
[ "$FORCE" -eq 1 ] && echo "Mode: --force (overwrite)"
echo ""

# ── 0. Source validation ──
if [ ! -d "$SRC" ]; then
  echo "[ERROR] Source directory missing: $SRC" >&2
  exit 1
fi
if [ ! -f "$SRC/version.md" ]; then
  echo "[ERROR] Source version file missing: $SRC/version.md (the extraction source of the deployed version stamp — re-check the global install (install.sh))" >&2
  exit 1
fi

# ── 0-b. Deployed version extraction (stamp material — reports a failure before copying starts) ──
# Extracted from the first data row ("| **version** | baseline date |") of the original's 'Current version' table.
PKG_LINE=$(sed -n 's/^| \*\*\([^*][^*]*\)\*\* *| *\([^ |][^ |]*\).*$/\1 \2/p' "$SRC/version.md" | head -n 1)
if [ -z "$PKG_LINE" ]; then
  echo "[ERROR] Could not extract the current version from the original version.md: $SRC/version.md (the '| **version** | baseline date |' table grammar is required)" >&2
  exit 1
fi
PKG_VER=${PKG_LINE%% *}
PKG_DATE=${PKG_LINE#* }

# ── Source file list (exclusion patterns applied) ──
# find is deterministic, so calling it twice yields the same list → atomic pre-check without temp files.
list_src() {
  for sub in $SUBDIRS; do
    [ -d "$SRC/$sub" ] || continue
    find "$SRC/$sub" -type f \
      ! -name '.DS_Store' ! -name '*.pyc' ! -path '*/__pycache__/*' \
      ! -name 'design-philosophy.md' -print
  done
}

# ── 1. Empty-source check ──
total=$(list_src | wc -l | tr -d ' ')
if [ "$total" -eq 0 ]; then
  echo "[ERROR] Nothing to copy (source is empty)." >&2
  exit 1
fi

# ── 2. Conflict pre-scan (full check before any copy → atomic) ──
# Each conflicting file gets a content-comparison mark against the original:
# '!' = content differs (overwriting loses the local change), '=' = identical.
conflicts=$(
  list_src | while IFS= read -r src_file; do
    rel=${src_file#"$SRC"/}
    if [ -e "$DEST/$rel" ]; then
      if cmp -s "$src_file" "$DEST/$rel"; then
        printf '%s\n' "= $DEST/$rel"
      else
        printf '%s\n' "! $DEST/$rel"
      fi
    fi
  done
)

if [ -n "$conflicts" ] && [ "$FORCE" -ne 1 ]; then
  n=$(printf '%s\n' "$conflicts" | wc -l | tr -d ' ')
  echo "[ABORT] ${n} file(s) already exist at the target. Nothing was changed:" >&2
  printf '%s\n' "$conflicts" | while IFS= read -r c; do echo "  $c" >&2; done
  echo "  (! = content differs from the original — overwriting loses the local change / = is identical)" >&2
  echo "" >&2
  echo "Re-initialization always means overwrite. After user approval, re-run with '--force':" >&2
  echo "  sh ~/.claude/skills/develojt-init/scripts/init.sh --force" >&2
  exit 3
fi

# ── 2-b. Loss visibility (--force safety net): print files differing from the originals right before overwriting ──
if [ "$FORCE" -eq 1 ] && [ -n "$conflicts" ]; then
  diffs=$(printf '%s\n' "$conflicts" | grep '^!' || true)
  if [ -n "$diffs" ]; then
    nd=$(printf '%s\n' "$diffs" | wc -l | tr -d ' ')
    echo "[CAUTION] ${nd} existing file(s) differ from the originals — overwriting erases these local changes (recordings):"
    printf '%s\n' "$diffs" | while IFS= read -r d; do echo "  $d"; done
    echo ""
  fi
fi

# Overwrite count = conflict count
if [ -n "$conflicts" ]; then
  overwritten=$(printf '%s\n' "$conflicts" | wc -l | tr -d ' ')
else
  overwritten=0
fi

# ── 3. Copy (filesystem changes persist even from subshells) ──
list_src | while IFS= read -r src_file; do
  rel=${src_file#"$SRC"/}
  dest_file="$DEST/$rel"
  mkdir -p "$(dirname "$dest_file")"
  cp -f "$src_file" "$dest_file"
done

# Preserve script execute permissions
find "$DEST" -type f \( -name '*.sh' -o -name '*.py' \) -exec chmod +x {} + 2>/dev/null || true

# ── 3-b. Deployed version stamp (.claude/version.md — generated in refined form, not a copy of the original) ──
# The deployed copy carries only "what was deployed when" (development history excluded — the refined-deployment principle in the header comment).
# Each re-initialization stacks a new row at the top (if the same row already exists, only once).
TODAY=$(date +%Y-%m-%d)
new_row="| $PKG_VER | $PKG_DATE | $TODAY |"
old_rows=""
if [ -f "$DEST/version.md" ]; then
  old_rows=$(grep '^| ' "$DEST/version.md" | grep -v '^| Deployed version' | grep -v '^|---' || true)
fi
{
  echo "# develojt-skills deployed version"
  echo ""
  echo "> The version record of the develojt pipeline package deployed (initialized) into this project — updated by /develojt-init (latest on top)."
  echo ""
  echo "| Deployed version | Package baseline date | Initialized on |"
  echo "|---|---|---|"
  printf '%s\n' "$new_row"
  if [ -n "$old_rows" ]; then
    printf '%s\n' "$old_rows" | grep -Fxv "$new_row" || true
  fi
} > "$DEST/version.md"

# ── 4. Completion report ──
echo "[COPY] ${total} files (${overwritten} overwritten)"
if [ -f "$DEST/version.md" ]; then
  echo "  $DEST/version.md  ← deployed version stamp (${PKG_VER})"
fi
for sub in $SUBDIRS; do
  [ -d "$DEST/$sub" ] || continue
  n=$(find "$DEST/$sub" -type f ! -name '.DS_Store' | wc -l | tr -d ' ')
  echo "  $DEST/$sub/  ← ${n} files"
done
echo ""
echo "=== Initialization complete ==="
echo "Where to start: /develojt-spec-planner for a new project, /develojt-spec-deriver if a PRD already exists"
