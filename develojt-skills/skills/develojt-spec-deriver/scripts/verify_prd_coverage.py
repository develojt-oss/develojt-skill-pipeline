#!/usr/bin/env python3
"""develojt-spec-deriver PRD coverage gate.

Deterministically checks that every PRD epic is fully expanded into the SPEC.
"Expand the human's requirement items (epics) to the fullest intent" is the deriver's
reason to exist, so a single missing epic stays missing through every later stage (joblist, code).

Checks:
    1. PRD epic count == SPEC EP section count
    2. SPEC EP numbers are consecutive from 01
    3. Every EP has at least 1 requirement row (FR-{ep}- or NFR-{ep}-)

Usage:
    python3 verify_prd_coverage.py <path to PRD.md> <path to SPEC.md>

Exit codes:
    0 — pass
    1 — coverage violation
    3 — file/structure error
"""

import re
import sys
from pathlib import Path

EPIC_ITEM_RE = re.compile(r"^\d+\.\s+\S")
EP_HEADER_RE = re.compile(r"^## EP-(\d+)", re.MULTILINE)


def extract_section(text: str, start: str, end: str) -> str:
    """Cuts from the start header up to just before the end header. Empty string if absent."""
    match = re.search(
        rf"{start}(.*?)(?={end}|\Z)", text, re.MULTILINE | re.DOTALL
    )
    return match.group(0) if match else ""


def count_epics(prd_text: str) -> int:
    """Counts the PRD's epics.

    Numbered items under System-based Epics + Business Epics.
    Guide quotes (>) and empty numbered items (lines with only "1. ") are excluded.
    Additional Considerations become NFRs, so they are not epics.
    """
    ai_section = extract_section(
        prd_text, r"^### System-based Epics", r"^### Business Epics"
    )
    biz_section = extract_section(
        prd_text, r"^### Business Epics", r"^### Additional Considerations|^## 4\."
    )

    count = 0
    for section in (ai_section, biz_section):
        for line in section.splitlines():
            stripped = line.strip()
            if stripped.startswith(">"):
                continue
            if EPIC_ITEM_RE.match(stripped):
                count += 1
    return count


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <PRD.md> <SPEC.md>", file=sys.stderr)
        sys.exit(3)

    prd_path, spec_path = Path(sys.argv[1]), Path(sys.argv[2])
    for path in (prd_path, spec_path):
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(3)

    prd_text = prd_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    spec_text = spec_path.read_text(encoding="utf-8").replace("\r\n", "\n")

    errors = []

    # 1. Epic count comparison
    prd_epics = count_epics(prd_text)
    ep_numbers = [int(n) for n in EP_HEADER_RE.findall(spec_text)]
    if prd_epics == 0:
        print("No epics found in the PRD — check the PRD structure.", file=sys.stderr)
        sys.exit(3)
    if len(ep_numbers) != prd_epics:
        errors.append(
            f"Epic count mismatch: PRD {prd_epics} vs SPEC EP {len(ep_numbers)} — "
            "a missing epic stays missing from the code too"
        )

    # 2. EP number continuity
    expected = list(range(1, len(ep_numbers) + 1))
    if ep_numbers != expected:
        errors.append(
            f"EP numbers discontinuous/out of order: {ep_numbers} (expected: consecutive from 01)"
        )

    # 3. Requirements exist per EP
    for ep in ep_numbers:
        ep_id = f"{ep:02d}"
        row_re = re.compile(rf"^\|\s*(?:FR|NFR)-{ep_id}-", re.MULTILINE)
        if not row_re.search(spec_text):
            errors.append(f"EP-{ep_id}: no requirement rows at all (empty epic)")

    print("=" * 60)
    if errors:
        print("[FAIL] PRD coverage gate violation")
        print("=" * 60)
        for e in errors:
            print(f"  ❌ {e}")
        print()
        print("→ Check that the PRD's epics were expanded without omission, as EP-01 onward in order of appearance.")
        sys.exit(1)

    print("[PASS] PRD coverage gate passed")
    print("=" * 60)
    print(f"  ✅ PRD epics {prd_epics} ↔ SPEC EPs {len(ep_numbers)} match")
    print(f"  ✅ EP numbers consecutive 01–{len(ep_numbers):02d}")
    print(f"  ✅ Every EP has requirements")
    sys.exit(0)


if __name__ == "__main__":
    main()
