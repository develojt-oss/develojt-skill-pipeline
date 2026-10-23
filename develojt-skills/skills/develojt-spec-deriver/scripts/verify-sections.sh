#!/bin/bash
# verify-sections.sh — SPEC document section order/omission verification
# Usage: bash scripts/verify-sections.sh <file path>
# Exit codes: 0=pass, 1=errors found

set -euo pipefail

FILE="${1:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "ERROR: specify a file path: bash scripts/verify-sections.sh <file>"
    exit 1
fi

BASENAME=$(basename "$FILE")
ERRORS=0
WARNINGS=0

# ─── Colors ───
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

error() { echo -e "${RED}ERROR${NC} [$BASENAME] $1"; ERRORS=$((ERRORS + 1)); }
warn()  { echo -e "${YELLOW}WARN${NC}  [$BASENAME] $1"; WARNINGS=$((WARNINGS + 1)); }
ok()    { echo -e "${GREEN}OK${NC}    [$BASENAME] $1"; }

# ─── Header order verification function ───
verify_order() {
    local -a patterns=("$@")
    local last_line=0
    local all_found=true

    for pattern in "${patterns[@]}"; do
        local line_num
        # || true so a no-match doesn't die silently under set -e + pipefail — lets the omission diagnosis (error below) run
        line_num=$(grep -n "^## " "$FILE" | grep -iE "$pattern" | head -1 | cut -d: -f1 || true)

        if [ -z "$line_num" ]; then
            error "Required section missing: '## ${pattern}'"
            all_found=false
            continue
        fi

        if [ "$line_num" -le "$last_line" ]; then
            error "Section order violation: '## ${pattern}' (line $line_num) precedes the previous section (line $last_line)"
        else
            ok "Section found: '## ${pattern}' (line $line_num)"
        fi

        last_line=$line_num
    done

    if [ "$all_found" = true ] && [ "$ERRORS" -eq 0 ]; then
        ok "All required sections exist in the correct order"
    fi
}

# ─── SPEC.md verification ───
echo ""
echo "═══════════════════════════════════════"
echo " Section order verification: $BASENAME"
echo "═══════════════════════════════════════"
echo ""

verify_order \
    "Document Info" \
    "EP-" \
    "Non-functional Requirements" \
    "Summary Statistics" \
    "Negotiation History" \
    "Future Extension"

# EP section order check
ep_lines=$(grep -n "^## EP-" "$FILE" | cut -d: -f1 || true)
prev=0
for line in $ep_lines; do
    if [ "$line" -le "$prev" ]; then
        error "EP section out of order: line $line"
    fi
    prev=$line
done

ep_count=$(grep -c "^## EP-" "$FILE" || true)
if [ "$ep_count" -eq 0 ]; then
    error "No EP-XX sections at all"
else
    ok "Found ${ep_count} EP section(s)"
fi

# ─── Result summary ───
echo ""
echo "═══════════════════════════════════════"
if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}FAIL${NC}: ${ERRORS} ERROR(s), ${WARNINGS} WARN(s)"
    echo "→ Fix the section order/omissions and re-verify."
    exit 1
else
    echo -e "${GREEN}PASS${NC}: 0 ERRORs, ${WARNINGS} WARN(s)"
    exit 0
fi
