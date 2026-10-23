#!/bin/bash
# verify-sources.sh — requirement source tag verification
# Usage: bash scripts/verify-sources.sh <path to SPEC file>
# Verifies: every FR/NFR row carries a valid source tag
# Requirement-row criterion: only rows starting with "| FR-"/"| NFR-" — the behavior chain table's 'Related IDs' cells are not counted
# Exit codes: 0=pass, 1=errors found

set -euo pipefail

FILE="${1:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "ERROR: specify the SPEC file path: bash scripts/verify-sources.sh <SPEC.md>"
    exit 1
fi

BASENAME=$(basename "$FILE")
ERRORS=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

error() { echo -e "${RED}ERROR${NC} $1"; ERRORS=$((ERRORS + 1)); }
ok()    { echo -e "${GREEN}OK${NC}    $1"; }
warn()  { echo -e "${YELLOW}WARN${NC}  $1"; }

echo "═══════════════════════════════════════"
echo " Source tag verification: $BASENAME"
echo "═══════════════════════════════════════"
echo ""

# ─── 1. Extract FR/NFR rows ───
# Verify only requirement table rows (excluding non-requirement tables like negotiation history / summary statistics)
# Sections after "## Summary Statistics" may show FR/NFR IDs without sources, so they are excluded
# Anchored to row start (^) — never mistakes the behavior chain table's 'Related IDs' cell (column 3) for a requirement row
CUTOFF_LINE=$(grep -n "^## Summary Statistics" "$FILE" | head -1 | cut -d: -f1 || true)
if [ -n "$CUTOFF_LINE" ]; then
    FR_LINES=$(head -n "$((CUTOFF_LINE - 1))" "$FILE" | grep -nE "^\| *(FR-|NFR-)" || true)
else
    FR_LINES=$(grep -nE "^\| *(FR-|NFR-)" "$FILE" || true)
fi

if [ -z "$FR_LINES" ]; then
    error "No FR/NFR rows found at all"
    exit 1
fi

TOTAL=$(echo "$FR_LINES" | wc -l | tr -d ' ')
ok "Found ${TOTAL} FR/NFR row(s)"
echo ""

# ─── 2. Valid source tag patterns ───
# Allowed: PRD EP-XX, PRD Considerations, [Implicit], [Requested], [Removed], [Needs review: ...]
VALID_SOURCE='PRD EP-|PRD Considerations|\[Implicit\]|\[Requested\]|\[Removed\]|\[Needs review'

# ─── 3. Verify each row ───
MISSING=0
INVALID=0

while IFS= read -r line; do
    LINE_NUM=$(echo "$line" | cut -d: -f1)
    CONTENT=$(echo "$line" | cut -d: -f2-)

    # Extract the ID (first column) — pipe-delimited field extraction via awk (macOS BSD sed compatible)
    ID=$(echo "$CONTENT" | awk -F'|' '{gsub(/^ +| +$/, "", $2); print $2}')

    # Extract the source (second column)
    SOURCE=$(echo "$CONTENT" | awk -F'|' '{gsub(/^ +| +$/, "", $3); print $3}')

    if [ -z "$SOURCE" ]; then
        error "line ${LINE_NUM}: ${ID} — source column is empty"
        MISSING=$((MISSING + 1))
    elif echo "$SOURCE" | grep -qE "$VALID_SOURCE"; then
        : # valid — pass silently
    else
        error "line ${LINE_NUM}: ${ID} — invalid source tag: '${SOURCE}'"
        warn "  allowed tags: PRD EP-XX | PRD Considerations | [Implicit] | [Requested] | [Removed] | [Needs review: reason]"
        INVALID=$((INVALID + 1))
    fi
done <<< "$FR_LINES"

# ─── 4. Check that [Needs review] tags carry a reason ───
# Searched only in FR/NFR rows (avoids false positives on the [Needs review] label in the summary table)
REVIEW_LINES=$(grep -nE "^\| *(FR-|NFR-)" "$FILE" | grep "Needs review" || true)
if [ -n "$REVIEW_LINES" ]; then
    REVIEW_COUNT=$(echo "$REVIEW_LINES" | wc -l | tr -d ' ')
    echo ""
    warn "Found ${REVIEW_COUNT} [Needs review] item(s) — user review required:"
    echo "$REVIEW_LINES" | while IFS= read -r rline; do
        echo "  $rline"
    done

    # Check for [Needs review] with an empty reason (FR/NFR rows only)
    EMPTY_REASON=$(echo "$REVIEW_LINES" | grep "\[Needs review\]" | grep -v "Needs review:" || true)
    if [ -n "$EMPTY_REASON" ]; then
        while IFS= read -r eline; do
            error "$(echo "$eline" | cut -d: -f1): [Needs review] tag has no reason (format: [Needs review: reason])"
        done <<< "$EMPTY_REASON"
    fi
fi

# ─── 5. Check that [Removed] tags carry strikethrough ───
# Searched only in FR/NFR rows
REMOVED_LINES=$(grep -nE "^\| *(FR-|NFR-)" "$FILE" | grep "\[Removed\]" || true)
if [ -n "$REMOVED_LINES" ]; then
    while IFS= read -r rline; do
        LINE_NUM=$(echo "$rline" | cut -d: -f1)
        if ! echo "$rline" | grep -q "~~"; then
            warn "line ${LINE_NUM}: [Removed] tag present but no strikethrough (~~)"
        fi
    done <<< "$REMOVED_LINES"
fi

# ─── 6. ID scheme verification ───
echo ""
echo "--- ID scheme verification ---"

# Extract only the requirement table region (avoids false positives on FR/NFR text after Summary Statistics)
if [ -n "$CUTOFF_LINE" ]; then
    SPEC_BODY=$(head -n "$((CUTOFF_LINE - 1))" "$FILE")
else
    SPEC_BODY=$(cat "$FILE")
fi

# Count only first-column IDs of requirement rows (rows starting with | FR-/| NFR-) — excludes the behavior chain table's 'Related IDs' cells
ROW_IDS=$(echo "$SPEC_BODY" | grep -E "^\| *(FR-|NFR-)" | awk -F'|' '{gsub(/^ +| +$/, "", $2); print $2}' || true)

# FR-epic#-seq format check — same digit-count criterion as the statistics count (section 7)
BAD_IDS=$(echo "$ROW_IDS" | sort -u | grep -vE "^(FR|NFR)-[0-9]{2}-([0-9]{3}|E[0-9]{2})$" || true)
if [ -n "$BAD_IDS" ]; then
    error "Non-standard ID format found (only FR-XX-XXX / NFR-XX-XXX / FR-XX-EXX allowed — 2-digit epic, 3-digit seq / E+2 digits):"
    echo "$BAD_IDS" | head -5
fi

# Duplicate ID check
DUPLICATE_IDS=$(echo "$ROW_IDS" | sort | uniq -d || true)
if [ -n "$DUPLICATE_IDS" ]; then
    error "Duplicate IDs found:"
    echo "$DUPLICATE_IDS" | while IFS= read -r did; do
        echo "  $did"
    done
fi

# ─── 7. Summary statistics cross-check ───
echo ""
echo "--- Summary statistics cross-check ---"

# Actual row counts (requirement table region only, anchored to row start)
ACTUAL_FR=$(echo "$SPEC_BODY" | grep -E "^\| *FR-[0-9]+-[0-9][0-9]" | grep -vE "^\| *FR-[0-9]+-E" | wc -l | tr -d ' ' || true)
ACTUAL_EDGE=$(echo "$SPEC_BODY" | grep -E "^\| *FR-[0-9]+-E" | wc -l | tr -d ' ' || true)
ACTUAL_NFR=$(echo "$SPEC_BODY" | grep -E "^\| *NFR-" | wc -l | tr -d ' ' || true)
ACTUAL_TOTAL=$((ACTUAL_FR + ACTUAL_EDGE + ACTUAL_NFR))

# Extract the numbers from the document's summary statistics
SUMMARY_SECTION=$(sed -n '/^## Summary Statistics/,/^## /p' "$FILE" || true)

SUMMARY_FR=$(echo "$SUMMARY_SECTION" | grep "Functional requirements" | grep -oE "[0-9]+" | head -1 || true)
SUMMARY_NFR=$(echo "$SUMMARY_SECTION" | grep "Non-functional requirements" | grep -oE "[0-9]+" | head -1 || true)
SUMMARY_EDGE=$(echo "$SUMMARY_SECTION" | grep "Edge cases" | grep -oE "[0-9]+" | head -1 || true)
SUMMARY_TOTAL=$(echo "$SUMMARY_SECTION" | grep "Total" | grep -oE "[0-9]+" | head -1 || true)

if [ -z "$SUMMARY_TOTAL" ]; then
    warn "Cannot parse the Summary Statistics section"
else
    echo "  Actual counts:   FR=${ACTUAL_FR} + Edge=${ACTUAL_EDGE} + NFR=${ACTUAL_NFR} = ${ACTUAL_TOTAL}"
    echo "  Document stats:  FR=${SUMMARY_FR:-?} + Edge=${SUMMARY_EDGE:-?} + NFR=${SUMMARY_NFR:-?} = ${SUMMARY_TOTAL:-?}"

    # Total cross-check
    if [ "$ACTUAL_TOTAL" != "$SUMMARY_TOTAL" ]; then
        error "Summary statistics total mismatch: actual ${ACTUAL_TOTAL} vs document ${SUMMARY_TOTAL}"
    else
        ok "Summary statistics total matches: ${ACTUAL_TOTAL}"
    fi

    # Internal sum cross-check (FR + Edge + NFR = total?)
    if [ -n "$SUMMARY_FR" ] && [ -n "$SUMMARY_EDGE" ] && [ -n "$SUMMARY_NFR" ]; then
        INTERNAL_SUM=$((SUMMARY_FR + SUMMARY_EDGE + SUMMARY_NFR))
        if [ "$INTERNAL_SUM" != "$SUMMARY_TOTAL" ]; then
            error "Summary statistics internal sum mismatch: ${SUMMARY_FR}+${SUMMARY_EDGE}+${SUMMARY_NFR}=${INTERNAL_SUM} vs total ${SUMMARY_TOTAL}"
        fi
    fi

    # Per-item cross-check
    if [ -n "$SUMMARY_FR" ] && [ "$ACTUAL_FR" != "$SUMMARY_FR" ]; then
        error "FR count mismatch: actual ${ACTUAL_FR} vs document ${SUMMARY_FR}"
    fi
    if [ -n "$SUMMARY_EDGE" ] && [ "$ACTUAL_EDGE" != "$SUMMARY_EDGE" ]; then
        error "Edge case count mismatch: actual ${ACTUAL_EDGE} vs document ${SUMMARY_EDGE}"
    fi
    if [ -n "$SUMMARY_NFR" ] && [ "$ACTUAL_NFR" != "$SUMMARY_NFR" ]; then
        error "NFR count mismatch: actual ${ACTUAL_NFR} vs document ${SUMMARY_NFR}"
    fi
fi

# ─── Result summary ───
echo ""
echo "═══════════════════════════════════════"
VALID=$((TOTAL - MISSING - INVALID))
echo "Total: ${TOTAL} | valid: ${VALID} | missing: ${MISSING} | invalid: ${INVALID}"

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}FAIL${NC}: ${ERRORS} ERROR(s)"
    echo "→ Fix the source tags and re-verify."
    exit 1
else
    echo -e "${GREEN}PASS${NC}: all source tags are valid"
    exit 0
fi
