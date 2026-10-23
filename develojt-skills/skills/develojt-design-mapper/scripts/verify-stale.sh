#!/usr/bin/env bash
# verify-stale.sh — verifies every FR the STORYBOARD points at is an active (live) FR in the SPEC (reverse direction).
# Usage: bash verify-stale.sh design/STORYBOARD.md spec/SPEC.md
# The counterpart of verify-coverage (SPEC→STORYBOARD omission check) — catches stale mappings in the
# STORYBOARD→SPEC direction (mappings still pointing at [Removed]/absent FRs). Used in the remap gate after deriver change transitions.
# HTML comments (<!-- -->) are excluded from the check — they are the record space for transition/verdict history (remap-mode convention).
set -uo pipefail

SB="${1:?pass the STORYBOARD.md path as an argument}"
SPEC="${2:?pass the SPEC.md path as an argument}"

[ -f "$SB" ] || { echo "ERROR: STORYBOARD missing: $SB"; exit 1; }
[ -f "$SPEC" ] || { echo "ERROR: SPEC missing: $SPEC"; exit 1; }

# SPEC active FRs: same extraction as verify-coverage.sh — after first filtering out rows whose source cell (column 2) is [Removed]
# (the single verdict key for removal — the same rule as the spliter and builder gates), only table-row first cells (^| FR-).
# Strikethrough-ID rows (| ~~FR~~ — an old SPEC's preservation notation) and NFR- (| NFR-) are automatically excluded by the row-first-cell anchor.
spec_frs=$(awk -F'|' 'index($3,"[Removed]")==0' "$SPEC" | grep -oE '^\| *FR-[0-9]+-[A-Z0-9]+' | grep -oE 'FR-[0-9]+-[A-Z0-9]+' | sort -u)
# STORYBOARD-appearing FRs: extracted from the whole file after removing HTML comments (tables, [No UI], headers — every real reference must be active).
# To block NFR- partial matches (NFR-00-008 → FR-00-008), extract with N?FR then keep only FR- (same as coverage).
sb_frs=$(perl -0pe 's/<!--.*?-->//gs' "$SB" | grep -oE 'N?FR-[0-9]+-[A-Z0-9]+' | grep '^FR-' | sort -u)

total=$(printf '%s\n' "$sb_frs" | grep -c .)
stale=$(comm -13 <(printf '%s\n' "$spec_frs") <(printf '%s\n' "$sb_frs"))

echo "FRs appearing in the STORYBOARD: ${total} (HTML comments excluded)"

if [ -n "$stale" ]; then
  echo "ERROR: the following FRs are not active in the SPEC ([Removed] or absent) — the STORYBOARD points at dead IDs (remap needed):"
  printf '%s\n' "$stale" | sed 's/^/  - /'
  exit 1
fi
echo "PASS: every STORYBOARD FR is an active SPEC FR (stale 0)."
