#!/usr/bin/env bash
# verify-anchors.sh — verifies the STORYBOARD's source anchors actually grep in the design/ sources.
# Usage: bash verify-anchors.sh design/STORYBOARD.md design/
# Extracts the key identifier from the table's "Source Anchor" (3rd data cell) and searches the design/ text sources.
# [No source] notation is skipped as normal. Coordinates and volatile indexes are forbidden by the anchor rules to begin with.
set -uo pipefail

SB="${1:?pass the STORYBOARD.md path as an argument}"
DESIGN="${2:?pass the design/ path as an argument}"

[ -f "$SB" ] || { echo "ERROR: STORYBOARD missing: $SB"; exit 1; }
[ -d "$DESIGN" ] || { echo "ERROR: design directory missing: $DESIGN"; exit 1; }

fail=0; checked=0; skipped=0; manual=0

# Table data rows only: rows starting with '| SB-NN'
while IFS= read -r line; do
  # Only 5-column tables are checked (| UI ID | Visual | Source | Description | FR |, 7 fields on pipe split) — the STORYBOARD body and the spec-candidates queue share this structure.
  # Tables with fewer columns (the [No UI] list etc.) have no source-anchor column, so they are skipped.
  nf=$(printf '%s' "$line" | awk -F'|' '{print NF}')
  [ "${nf:-0}" -lt 7 ] && continue
  # Columns: | UI ID | Visual Anchor | Source Anchor | Description | Mapped FR |  → the source anchor is $4
  anchor=$(printf '%s' "$line" | awk -F'|' '{print $4}' | sed 's/^ *//;s/ *$//')
  [ -z "$anchor" ] && continue
  case "$anchor" in
    *"[No source"*) skipped=$((skipped+1)); continue;;
  esac
  checked=$((checked+1))

  # Key token extraction: ① double-quoted text → ② single-quoted text → ③ .classname
  needle=$(printf '%s' "$anchor" | grep -oE '"[^"]+"' | head -1 | tr -d '"')
  [ -z "$needle" ] && needle=$(printf '%s' "$anchor" | grep -oE "'[^']+'" | head -1 | tr -d "'")
  if [ -z "$needle" ]; then
    needle=$(printf '%s' "$anchor" | grep -oE '\.[A-Za-z][A-Za-z0-9_-]+' | head -1)
    needle="${needle#.}"   # strip the class anchor's leading dot (the source carries class="name" form)
  fi

  if [ -z "$needle" ]; then
    echo "WARN  auto-extraction failed (manual check needed): $anchor"
    manual=$((manual+1))
    continue
  fi

  if grep -rqF \
      --include='*.html' --include='*.htm' --include='*.js' --include='*.jsx' \
      --include='*.ts' --include='*.tsx' --include='*.vue' --include='*.css' --include='*.svg' \
      -- "$needle" "$DESIGN" 2>/dev/null; then
    : # found
  else
    echo "FAIL  not found in sources: '$needle'   ← anchor: $anchor"
    fail=$((fail+1))
  fi
done < <(grep -E '^\| *SB-[0-9]' "$SB")

echo "---"
echo "checked $checked / passed $((checked - fail)) / failed $fail / [No source] $skipped / manual $manual"

if [ "$fail" -gt 0 ]; then
  echo "ERROR: ${fail} source anchor(s) do not grep in the design/ sources — correct to more unique identifiers."
  exit 1
fi
echo "PASS: every (auto-extractable) source anchor is confirmed by grep."
