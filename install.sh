#!/bin/sh
set -eu

# develojt-skill-pipeline install script.
#
# Copies this repo's assets into the global ~/.claude/.
#
# Mapping (1:1 structural mirror):
#   <repo>/skills/          → ~/.claude/skills/          (bootstrap skill develojt-init)
#   <repo>/develojt-skills/ → ~/.claude/develojt-skills/ (pipeline originals: skills/agents/rules)
#
# Once installed, pull the pipeline into any project root with /develojt-init.
#
# Re-install (duplicate-run defense):
#   On a default run, if even one target file already exists, report the conflicts
#   'without changing anything' and abort with exit 3. Re-install always means overwrite;
#   after user approval, re-run with '--force' (the approval gate lives on the caller side).
#
# Excluded: .DS_Store, __pycache__/, *.pyc
#
# Pre-checks (before copying — if even one is missing, nothing is changed and it exits 4):
#   python3 3.10 or later · bash · perl — the tools the pipeline's verification scripts use at run time.
#   If CLAUDE_CONFIG_DIR is set to somewhere other than ~/.claude, it aborts
#   (because /develojt-init reads ~/.claude/develojt-skills as the originals).
#   On Windows, run it in Git Bash from Git for Windows (on WSL, run it inside WSL).
#
# Exit codes: 0 installed / 1 source error / 2 argument error / 3 already installed (--force needed) / 4 pre-check failed
#
# Portability: pure POSIX sh. Works on macOS (/bin/sh), mainstream Linux (dash/bash),
#              and Alpine/busybox (ash). No arrays, process substitution, or pipefail.
#              External commands are standard POSIX: find, cp, mkdir, chmod, wc, tr, dirname, cd, pwd.

# ── Script location = repo root (works from any directory) ──
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEST_ROOT="$HOME/.claude"

# Copy units: "<repo subpath>:<target subpath>"
MAPPINGS="skills:skills develojt-skills:develojt-skills"

FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force|-f) FORCE=1 ;;
    *) echo "[ERROR] Unknown argument: $arg (usage: install.sh [--force])" >&2; exit 2 ;;
  esac
done

echo "=== develojt-skill-pipeline install ==="
echo "Source: $SCRIPT_DIR"
echo "Target: $DEST_ROOT"
[ "$FORCE" -eq 1 ] && echo "Mode: --force (overwrite)"
echo ""

# ── Pre-checks (before copying — on failure nothing is changed) ──
case "$(uname -s 2>/dev/null || echo unknown)" in
  MINGW*|MSYS*|CYGWIN*) OS_KIND="windows" ;;
  Darwin*)              OS_KIND="macos" ;;
  *)                    OS_KIND="linux" ;;
esac
missing=""
if command -v python3 >/dev/null 2>&1; then
  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    missing="$missing python3(3.10 or later — currently $(python3 -c 'import platform; print(platform.python_version())' 2>/dev/null || echo 'unknown'))"
  fi
else
  missing="$missing python3(3.10 or later)"
fi
command -v bash >/dev/null 2>&1 || missing="$missing bash"
command -v perl >/dev/null 2>&1 || missing="$missing perl"
if [ -n "$missing" ]; then
  echo "[ABORT] Required tools are missing:$missing" >&2
  echo "Nothing was changed. Install them and run again:" >&2
  case "$OS_KIND" in
    macos)   echo "  - Python 3.10 or later: https://www.python.org/downloads/ or 'brew install python'" >&2 ;;
    windows) echo "  - Python 3.10 or later: https://www.python.org/downloads/ (after installing, check 'python3 --version' in Git Bash)" >&2
             echo "  - bash, perl: included in Git for Windows (https://git-scm.com/downloads/win) — run this in Git Bash" >&2 ;;
    *)       echo "  - Install with your distribution's package manager (e.g., 'sudo apt install python3 perl')" >&2 ;;
  esac
  exit 4
fi
if [ -n "${CLAUDE_CONFIG_DIR:-}" ] && [ "${CLAUDE_CONFIG_DIR%/}" != "$DEST_ROOT" ]; then
  echo "[ABORT] CLAUDE_CONFIG_DIR is set: $CLAUDE_CONFIG_DIR" >&2
  echo "This pipeline installs and initializes relative to ~/.claude. Nothing was changed." >&2
  exit 4
fi
echo "[CHECK] python3 $(python3 -c 'import platform; print(platform.python_version())') · bash · perl — OK ($OS_KIND)"
echo ""

# ── Source file list (exclusion patterns applied) ──
# find is deterministic, so calling it twice yields the same list → atomic pre-check without temp files.
list_src() {
  # $1 = source directory
  find "$1" -type f \
    ! -name '.DS_Store' ! -name '*.pyc' ! -path '*/__pycache__/*' -print
}

# ── 0. Source validation + empty-source check ──
grand_total=0
for map in $MAPPINGS; do
  src_sub=${map%%:*}
  src_dir="$SCRIPT_DIR/$src_sub"
  if [ ! -d "$src_dir" ]; then
    echo "[ERROR] Source directory missing: $src_dir" >&2
    exit 1
  fi
  count=$(list_src "$src_dir" | wc -l | tr -d ' ')
  if [ "$count" -eq 0 ]; then
    echo "[ERROR] Nothing to copy (source is empty): $src_dir" >&2
    exit 1
  fi
  grand_total=$((grand_total + count))
done

# ── 1. Conflict pre-scan (full check before any copy → atomic) ──
conflicts=$(
  for map in $MAPPINGS; do
    src_sub=${map%%:*}
    dest_sub=${map##*:}
    src_dir="$SCRIPT_DIR/$src_sub"
    dest_dir="$DEST_ROOT/$dest_sub"
    list_src "$src_dir" | while IFS= read -r src_file; do
      rel=${src_file#"$src_dir"/}
      if [ -e "$dest_dir/$rel" ]; then
        printf '%s\n' "$dest_dir/$rel"
      fi
    done
  done
)

if [ -n "$conflicts" ] && [ "$FORCE" -ne 1 ]; then
  n=$(printf '%s\n' "$conflicts" | wc -l | tr -d ' ')
  echo "[ABORT] Already installed. ${n} file(s) exist at the target. Nothing was changed:" >&2
  printf '%s\n' "$conflicts" | while IFS= read -r c; do echo "  - $c" >&2; done
  echo "" >&2
  echo "Re-install always means overwrite. After user approval, re-run with '--force':" >&2
  echo "  sh \"$SCRIPT_DIR/install.sh\" --force" >&2
  exit 3
fi

if [ -n "$conflicts" ]; then
  overwritten=$(printf '%s\n' "$conflicts" | wc -l | tr -d ' ')
else
  overwritten=0
fi

# ── 2. Copy (filesystem changes persist even from subshells) ──
mkdir -p "$DEST_ROOT"
for map in $MAPPINGS; do
  src_sub=${map%%:*}
  dest_sub=${map##*:}
  src_dir="$SCRIPT_DIR/$src_sub"
  dest_dir="$DEST_ROOT/$dest_sub"

  count=$(list_src "$src_dir" | wc -l | tr -d ' ')
  list_src "$src_dir" | while IFS= read -r src_file; do
    rel=${src_file#"$src_dir"/}
    dest_file="$dest_dir/$rel"
    mkdir -p "$(dirname "$dest_file")"
    cp -f "$src_file" "$dest_file"
  done
  echo "[COPY] $src_sub/ → $dest_dir/  (${count} files)"
done

# ── 3. Preserve script execute permissions ──
for map in $MAPPINGS; do
  dest_sub=${map##*:}
  find "$DEST_ROOT/$dest_sub" -type f \( -name '*.sh' -o -name '*.py' \) \
    -exec chmod +x {} + 2>/dev/null || true
done

echo ""
echo "=== Install complete (${grand_total} files total, ${overwritten} overwritten) ==="
echo "Next step: move to the project root you want to initialize, then run /develojt-init in Claude Code"
