#!/usr/bin/env bash
# merge-helper.sh — shows only the differences between the two sides' finals, aiding STEP 6 consolidation (instead of whole-file Reads).
# Usage: bash merge-helper.sh design/storyboard-DesignTheorist.md design/storyboard-DesignPractitioner.md
#        (spec-candidates-* / spec-conflicts-* pairs work the same way — comparison is SB-ID-based, so one script handles them all)
set -uo pipefail

A="${1:?mapping file A}"; B="${2:?mapping file B}"
[ -f "$A" ] && [ -f "$B" ] || { echo "ERROR: input file missing: $A / $B"; exit 1; }

ids_a=$(grep -oE 'SB-[0-9]+-[0-9]+' "$A" | sort -u)
ids_b=$(grep -oE 'SB-[0-9]+-[0-9]+' "$B" | sort -u)

echo "=== UI ID comparison ==="
only_a=$(comm -23 <(printf '%s\n' "$ids_a") <(printf '%s\n' "$ids_b"))
only_b=$(comm -13 <(printf '%s\n' "$ids_a") <(printf '%s\n' "$ids_b"))
both=$(comm -12 <(printf '%s\n' "$ids_a") <(printf '%s\n' "$ids_b") | grep -c .)
echo "common: ${both}"
[ -n "$only_a" ] && { echo "[only in $A]"; printf '%s\n' "$only_a" | sed 's/^/  /'; }
[ -n "$only_b" ] && { echo "[only in $B]"; printf '%s\n' "$only_b" | sed 's/^/  /'; }
[ -z "$only_a$only_b" ] && echo "UI ID sets identical."

echo ""
echo "=== Orphan count comparison ==="
for f in "$A" "$B"; do
  de=$(grep -c '\[Decorative\]' "$f"); nu=$(grep -c '\[No UI\]' "$f")
  echo "  $f : [Decorative] $de / [No UI] $nu"
done

echo ""
echo "=== Recommendation ==="
if [ -z "$only_a$only_b" ]; then
  echo "UI ID sets are identical. Copy one side as the base, then check only mapping/anchor differences."
else
  echo "Some IDs exist on one side only. Confirm whether the list above is a genuine omission (grep whether it already exists under other wording) before applying."
fi
