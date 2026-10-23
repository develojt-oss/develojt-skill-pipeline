#!/usr/bin/env bash
# verify-coverage.sh — verifies every SPEC FR is mapped in the STORYBOARD or classified [No UI].
# Usage: bash verify-coverage.sh design/STORYBOARD.md spec/SPEC.md
# Enforces "no UI missing from the human's features" — a missing FR is an ERROR.
# HTML comments (<!-- -->) are excluded from counting — they are the record space for transition/verdict
# history (remap-mode convention), so an FR mention inside a comment is not a mapping. FRs that exist
# only in comments are not counted as covered — they surface as unmapped ERRORs.
set -uo pipefail

SB="${1:?pass the STORYBOARD.md path as an argument}"
SPEC="${2:?pass the SPEC.md path as an argument}"

[ -f "$SB" ] || { echo "ERROR: STORYBOARD missing: $SB"; exit 1; }
[ -f "$SPEC" ] || { echo "ERROR: SPEC missing: $SPEC"; exit 1; }

# FR ID format: FR-NN-NNN, implicit variants FR-NN-E01 etc. (uppercase+digit tails allowed)
# Only live FRs are counted:
#  - SPEC: after first filtering out rows whose source cell (column 2) is [Removed] (the single verdict key for removal — the same rule
#    as the spliter and builder gates. The ID cell is unchanged, so the row-head anchor alone cannot tell them apart from active rows),
#    count only FRs in a table row's first cell (^| FR-).
#    Strikethrough-ID rows (| ~~FR~~ — an old SPEC's preservation notation) and NFR- (| NFR-) are automatically excluded by the row-first-cell anchor.
#  - STORYBOARD: extracted after removing HTML comments (same pipeline as verify-stale — appearances
#    inside comments never count as coverage). To block NFR- partial matches (NFR-00-008 → FR-00-008),
#    extract with N?FR then keep only FR-.
spec_frs=$(awk -F'|' 'index($3,"[Removed]")==0' "$SPEC" | grep -oE '^\| *FR-[0-9]+-[A-Z0-9]+' | grep -oE 'FR-[0-9]+-[A-Z0-9]+' | sort -u)
sb_frs=$(perl -0pe 's/<!--.*?-->//gs' "$SB" | grep -oE 'N?FR-[0-9]+-[A-Z0-9]+' | grep '^FR-' | sort -u)

total=$(printf '%s\n' "$spec_frs" | grep -c .)
covered=$(printf '%s\n' "$sb_frs" | grep -c .)
missing=$(comm -23 <(printf '%s\n' "$spec_frs") <(printf '%s\n' "$sb_frs"))

echo "SPEC FRs: ${total} total / appearing in STORYBOARD: ${covered} (HTML comments excluded)"

if [ -n "$missing" ]; then
  echo "ERROR: the following FRs are not mapped/classified in the STORYBOARD — map them or classify as [No UI]:"
  printf '%s\n' "$missing" | sed 's/^/  - /'
  exit 1
fi
echo "PASS: every SPEC FR is mapped or classified in the STORYBOARD."
