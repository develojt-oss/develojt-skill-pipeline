#!/usr/bin/env python3
"""develojt-spec-planner PRD.md verification gate.

Deterministically checks the generated plan/PRD.md for structure, completeness,
per-view hint counts, and ambiguity.
The purpose is guaranteeing the deliverable's form even when LLM instructions
drift under context compaction or model changes.

Usage:
    python3 validate.py <path to PRD.md>

Exit codes:
    0 — all gates passed
    1 — completeness gate violation (required fields, undecided Core Technologies, per-view count shortfall, status check error)
    2 — ambiguity gate violation
    3 — structure violation (validate/deriver compatibility broken) or input error
"""

import re
import sys
from pathlib import Path

# Required sections — must exist exactly as in the template (deriver compatibility)
REQUIRED_SECTIONS = [
    r"^# PRD",
    r"^## 1\. Project",
    r"^## 2\. System Setup",
    r"^### Runtime Environment",
    r"^### Operating System",
    r"^### Development Type",
    r"^### Core Technologies",
    r"^### User Authentication",
    r"^### External System Integration",
    r"^## 3\. Epics",
    r"^### System-based Epics",
    r"^### Business Epics",
    r"^## 4\. Status",
]

# Required project fields and placeholder values treated as unfilled
PROJECT_FIELDS = ["Name", "One-liner"]
PLACEHOLDER_VALUES = {"{project_name}", "{one_liner}"}

# Core Technologies fields — must be in a decided state: a value or "None" (blank = missing decision, harness principle)
TECH_FIELDS = ["Language", "Framework", "DB", "Middleware"]
TECH_PLACEHOLDERS = {"{languages}", "{frameworks}", "{database}", "{middleware}"}

# AI hint view blocks — labels and minimum counts (synced with SKILL.md STEP 3)
VIEW_BLOCKS = [
    ("[Foundation]", 2),
    ("[Scene]", 4),
    ("[Rule]", 4),
    ("[Edge]", 4),
    ("[Quality]", 4),
]

# Vague expressions — rejected in epic bodies (guide quotes and free-form areas excluded)
VAGUE_PATTERNS = [
    r"(?i)\b(?:decide|determine|figure\s+out|fill\s+in)\s+(?:this\s+|it\s+)?later\b",
    r"(?i)\bappropriately\b|\bas\s+appropriate\b",
    r"(?i)\bas\s+(?:needed|necessary)\b",
    r"(?i)\b(?:works?|runs?)\s+(?:well|fine|properly)\b",
    r"(?i)\bat\s+(?:its|their)\s+discretion\b|\bas\s+(?:it|they)\s+sees?\s+fit\b",
    r"\bTBD\b",
    r"\bTODO\b",
]

VIEW_LABEL_RE = re.compile(
    r"^\*\*(\[(?:Foundation|Scene|Rule|Edge|Quality)\])[^*]*\*\*\s*$"
)
NUMBERED_AI_RE = re.compile(r"^\d+\.\s+\[AI\]\s+\S+")


def check_structure(text: str) -> list[str]:
    """Deriver-compatibility structure check."""
    errors = []
    for pattern in REQUIRED_SECTIONS:
        if not re.search(pattern, text, re.MULTILINE):
            errors.append(f"Required section missing: {pattern}")
    return errors


def extract_section(text: str, start: str, end: str) -> str:
    """Cuts the region from the start header up to just before the end header."""
    match = re.search(
        rf"{start}(.*?)(?={end}|\Z)", text, re.MULTILINE | re.DOTALL
    )
    return match.group(0) if match else ""


def check_completeness(text: str) -> list[str]:
    """Completeness gate — required fields filled + per-view hint counts."""
    errors = []

    # Project fields — whitespace limited to within the line ([ \t]) so values never swallow past a newline
    project = extract_section(text, r"^## 1\. Project", r"^## 2\.")
    for field in PROJECT_FIELDS:
        field_match = re.search(
            rf"\*\*{field}\*\*[ \t]*[:：][ \t]*(.*)", project
        )
        if not field_match:
            errors.append(f"Project field missing: {field}")
            continue
        value = field_match.group(1).strip()
        if not value or value in PLACEHOLDER_VALUES:
            errors.append(f"Project field unfilled: {field}")

    # Core Technologies — reject undecided (blank/placeholder). 'None' is a valid decided value
    tech = extract_section(text, r"^### Core Technologies", r"^### User Authentication")
    for field in TECH_FIELDS:
        field_match = re.search(rf"\*\*{field}\*\*[ \t]*[:：][ \t]*(.*)", tech)
        if not field_match:
            errors.append(f"Core Technologies field missing: {field}")
            continue
        value = field_match.group(1).strip()
        if not value or value in TECH_PLACEHOLDERS:
            errors.append(
                f"Core Technologies undecided: {field} — decide a value via candidates → user choice, "
                "or record 'None' if not applicable"
            )

    # [AI] hint count per view block
    ai_section = extract_section(
        text, r"^### System-based Epics", r"^### Business Epics"
    )
    if ai_section:
        blocks = split_view_blocks(ai_section)
        for label, min_count in VIEW_BLOCKS:
            if label not in blocks:
                errors.append(f"View block missing: no **{label} ...** label")
                continue
            count = sum(
                1 for line in blocks[label] if NUMBERED_AI_RE.match(line)
            )
            if count < min_count:
                errors.append(
                    f"View {label} hints short: {count} (minimum {min_count}) — "
                    "only lines in the `N. [AI] sentence` format are counted"
                )

    # Status section — exactly one checkbox must be checked
    # (checking 'Finalized' itself is not blocked — re-validation compatibility for a human-completed PRD)
    status = extract_section(text, r"^## 4\. Status", r"^---")
    checked = re.findall(r"^- \[x\]", status, re.MULTILINE)
    if len(checked) != 1:
        errors.append(
            f"Status check error: {len(checked)} boxes checked — exactly 1 must be checked "
            "(right after draft generation, [x] only on 'Drafting')"
        )

    return errors


def split_view_blocks(ai_section: str) -> dict[str, list[str]]:
    """Splits the AI epic area into blocks by view label."""
    blocks: dict[str, list[str]] = {}
    current = None
    for line in ai_section.splitlines():
        label_match = VIEW_LABEL_RE.match(line.strip())
        if label_match:
            current = label_match.group(1)
            blocks[current] = []
        elif current is not None:
            blocks[current].append(line.strip())
    return blocks


def check_ambiguity(text: str) -> list[str]:
    """Ambiguity gate — detect vague expressions in the epic area.

    Guide quotes (>) and free-form area notes (_(...)_) are not detection targets.
    """
    epic_section = extract_section(text, r"^## 3\. Epics", r"^## 4\.")
    target = epic_section if epic_section else text

    cleaned = re.sub(r"^>.*$", "", target, flags=re.MULTILINE)
    cleaned = re.sub(r"_\(.*?\)_", "", cleaned, flags=re.DOTALL)

    errors = []
    for pattern in VAGUE_PATTERNS:
        matches = re.findall(pattern, cleaned)
        if matches:
            errors.append(
                f"Vague expression detected: '{pattern}' {len(matches)} time(s) — replace with concrete wording"
            )
    return errors


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path to PRD.md>", file=sys.stderr)
        sys.exit(3)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(3)
    if not path.is_file():
        print(
            f"Not a file: {path} — specify the path to a PRD.md file.",
            file=sys.stderr,
        )
        sys.exit(3)

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        print(
            f"Cannot read file: {path} — check that it is a UTF-8 text file. ({e})",
            file=sys.stderr,
        )
        sys.exit(3)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    structure_errors = check_structure(text)
    if structure_errors:
        print("=" * 60)
        print("[FAIL] Structure violation (deriver compatibility broken)")
        print("=" * 60)
        for e in structure_errors:
            print(f"  ❌ {e}")
        sys.exit(3)

    completeness_errors = check_completeness(text)
    if completeness_errors:
        print("=" * 60)
        print("[FAIL] Completeness gate violation")
        print("=" * 60)
        for e in completeness_errors:
            print(f"  ❌ {e}")
        print()
        print("→ Fill the empty fields, and diverge additional hints for short views")
        print("  in the `N. [AI] sentence` format. (e.g., `1. [AI] A staff member views the list on screen`)")
        print("→ For undecided Core Technologies items, present candidates to the user and get a choice.")
        print("  (Record 'None' for items that don't apply — never hand blanks to the deriver)")
        sys.exit(1)

    ambiguity_errors = check_ambiguity(text)
    if ambiguity_errors:
        print("=" * 60)
        print("[FAIL] Ambiguity gate violation")
        print("=" * 60)
        for e in ambiguity_errors:
            print(f"  ❌ {e}")
        print()
        print("→ Replace expressions like 'later' or 'as appropriate' with concrete wording.")
        sys.exit(2)

    print("=" * 60)
    print("[PASS] All gates passed")
    print("=" * 60)
    print("  ✅ Structure — deriver compatibility OK")
    print("  ✅ Completeness — required fields & Core Technologies decided, per-view hint counts met, 1 status check")
    print("  ✅ Ambiguity — no vague expressions detected")
    print()
    print("→ Once the human completes the business epics, the PRD can be handed to spec-deriver.")
    sys.exit(0)


if __name__ == "__main__":
    main()
