#!/bin/bash
# merge-helper.sh — extracts only the differences between the two sides' files, minimizing the Lead's context consumption
# Usage: bash scripts/merge-helper.sh <file A> <file B>
#
# The two agents have finished agreeing, so most of the content is identical.
# Instead of the Lead reading both files whole, this script surfaces only the differences for consolidation.
#
# Output:
#   1. Basic statistics (line counts, requirement counts)
#   2. Difference list (diff)
#   3. Consolidation base file recommendation
#
# Exit codes: 0=differences found (normal), 1=file error

set -euo pipefail

FILE_A="${1:-}"
FILE_B="${2:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ -z "$FILE_A" ] || [ -z "$FILE_B" ]; then
    echo "Usage: bash scripts/merge-helper.sh <Theorist file> <Pragmatist file>"
    exit 1
fi

if [ ! -f "$FILE_A" ] || [ ! -f "$FILE_B" ]; then
    echo "ERROR: file does not exist."
    [ ! -f "$FILE_A" ] && echo "  missing: $FILE_A"
    [ ! -f "$FILE_B" ] && echo "  missing: $FILE_B"
    exit 1
fi

NAME_A=$(basename "$FILE_A")
NAME_B=$(basename "$FILE_B")

echo "═══════════════════════════════════════"
echo " Comparing both sides: $NAME_A vs $NAME_B"
echo "═══════════════════════════════════════"
echo ""

# ─── 1. Basic statistics ───
echo -e "${CYAN}--- Basic statistics ---${NC}"
echo ""

LINES_A=$(wc -l < "$FILE_A" | tr -d ' ')
LINES_B=$(wc -l < "$FILE_B" | tr -d ' ')
printf "  %-30s %4d lines\n" "$NAME_A" "$LINES_A"
printf "  %-30s %4d lines\n" "$NAME_B" "$LINES_B"

# Anchored to row start — never counts the behavior chain table's 'Related IDs' cells as requirement rows
FR_A=$(grep -Ec "^\| *(FR-|NFR-)" "$FILE_A" || true)
FR_B=$(grep -Ec "^\| *(FR-|NFR-)" "$FILE_B" || true)
printf "  %-30s %4d requirements\n" "$NAME_A" "$FR_A"
printf "  %-30s %4d requirements\n" "$NAME_B" "$FR_B"

echo ""

# ─── 2. Identity check ───
if diff -q "$FILE_A" "$FILE_B" > /dev/null 2>&1; then
    echo -e "${GREEN}The two files are completely identical.${NC}"
    echo "→ Use either one as-is."
    exit 0
fi

# ─── 3. Difference extraction ───
echo -e "${CYAN}--- Differences ---${NC}"
echo ""

# Line-level diff (2 context lines only)
DIFF_OUTPUT=$(diff -u --label="$NAME_A" --label="$NAME_B" "$FILE_A" "$FILE_B" 2>/dev/null || true)
DIFF_LINES=$(echo "$DIFF_OUTPUT" | grep "^[+-]" | grep -v "^[+-][+-][+-]" | wc -l | tr -d ' ' || true)

# Zero-denominator defense — a single-line file without a newline is 0 lines by wc -l
TOTAL_LINES=$((LINES_A + LINES_B))
if [ "$TOTAL_LINES" -gt 0 ]; then
    echo "Differing lines: ${DIFF_LINES} ($((DIFF_LINES * 100 / TOTAL_LINES))% of total)"
else
    echo "Differing lines: ${DIFF_LINES}"
fi
echo ""

if [ "$DIFF_LINES" -le 50 ]; then
    # Few differences — print the full diff
    echo "$DIFF_OUTPUT" | head -100
else
    # Many differences — skip the diff and show only the ID comparison below
    echo -e "${YELLOW}Differences are large (${DIFF_LINES} lines). Showing the ID comparison only:${NC}"
fi
echo ""

# ─── FR/NFR IDs present on one side only — always printed regardless of diff size ───
IDS_A=$(grep -oE "FR-[0-9]+-[0-9E][0-9]*|NFR-[0-9]+-[0-9][0-9]*" "$FILE_A" | sort -u || true)
IDS_B=$(grep -oE "FR-[0-9]+-[0-9E][0-9]*|NFR-[0-9]+-[0-9][0-9]*" "$FILE_B" | sort -u || true)

ONLY_A=$(comm -23 <(echo "$IDS_A") <(echo "$IDS_B") || true)
ONLY_B=$(comm -13 <(echo "$IDS_A") <(echo "$IDS_B") || true)

if [ -n "$ONLY_A" ]; then
    echo -e "${YELLOW}IDs only in $NAME_A:${NC}"
    echo "$ONLY_A" | while read id; do
        echo "  $id"
    done
    echo ""
fi

if [ -n "$ONLY_B" ]; then
    echo -e "${YELLOW}IDs only in $NAME_B:${NC}"
    echo "$ONLY_B" | while read id; do
        echo "  $id"
    done
    echo ""
fi

if [ -z "$ONLY_A" ] && [ -z "$ONLY_B" ]; then
    echo "IDs on one side only: none"
fi

COMMON=$(comm -12 <(echo "$IDS_A") <(echo "$IDS_B") | grep -c . || true)
echo "Common IDs: ${COMMON}"

echo ""

# ─── 4. Consolidation recommendation ───
echo -e "${CYAN}--- Consolidation recommendation ---${NC}"
echo ""

if [ "$FR_A" -ge "$FR_B" ]; then
    echo "→ Recommended: use $NAME_A as the base file and apply the differences from $NAME_B."
    echo "  (requirement counts: $FR_A ≥ $FR_B)"
else
    echo "→ Recommended: use $NAME_B as the base file and apply the differences from $NAME_A."
    echo "  (requirement counts: $FR_B > $FR_A)"
fi

echo ""
echo -e "${CYAN}Consolidation procedure:${NC}"
echo "  1. Copy the base file to spec/{document name}.md"
echo "  2. Check and apply only the differences above"
echo "  3. Run the verification scripts"
echo ""
echo "═══════════════════════════════════════"
