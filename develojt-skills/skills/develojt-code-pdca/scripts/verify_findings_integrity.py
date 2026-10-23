#!/usr/bin/env python3
"""develojt-code-pdca findings.md ledger integrity gate.

Judgment (is the finding right) is not checked — that belongs to the next cycle's re-verification.
This script sees only the ledger record: for the next session to read this file alone and continue
the loop, the format/status/evidence discipline must not be broken.

Checks:
  1. Required sections exist (Defect Ledger / Process Improvement Proposals / Cycle Log)
  2. Defect ID format (F-NNN), no duplicates (unique across ledger ∪ archive when the archive exists)
  3. Status/type values are within the defined sets
  4. Every defect row has evidence (empty evidence forbidden)
  5. Every status other than New requires an Action Log (without "what was done", re-entry is impossible)
  6. FR/NFR IDs in the Target cell actually exist in the SPEC's ID set (no ghosts) — only when a SPEC path is given
  7. The cycle log is not empty, and the header's current cycle number matches the log maximum
  8. (when the header has a 'Last F-number' cell) its value = the maximum ID across ledger ∪ archive,
     and 1..max has no gaps (a gap = a lost row — every row must live in the ledger or the archive)
  9. (when the archive ledger exists) the same row checks apply + status must be `Resolved` only
     (Rejected/Needs review must never be archived) — if the archive ledger exists but the findings.md header has no 'Last F-number'
     cell, it FAILs (the numbering baseline is missing)
 10. (when the archive ledger has a '## Cycle Log History' section) cycle numbers are unique
     across ledger ∪ archive and 0..max has no gaps (a gap = a lost row — every row must live
     in the ledger or the archive ledger)

Table parsing: `\\|` escapes count as cell content, and defect rows exceeding 7 cells get the excess
re-joined into the evidence cell — so `|` in in-cell code quotes (e.g., `a || b`) neither
false-FAILs a healthy ledger nor truncates evidence.

Usage:
    python3 verify_findings_integrity.py spec/findings.md [spec/SPEC.md]
    (when spec/findings-archive.md exists in the same folder, it is verified alongside automatically)

Exit codes: 0 — PASS / 1 — FAIL
"""

import re
import sys
from pathlib import Path

VALID_STATUS = {"New", "Fixing", "Awaiting recheck", "Resolved", "Rejected", "Needs review"}
VALID_TYPES = {"M1", "W1", "W2", "W3", "F1", "C1", "C2", "C3", "C4", "S1"}
# Type tally print order (checker-rules catalog order)
TYPE_ORDER = ("M1", "W1", "W2", "W3", "F1", "C1", "C2", "C3", "C4", "S1")
# Statuses counted in the type tally — Rejected (a wrong finding) is not a defect, so it's excluded
TALLY_STATUS = {"New", "Fixing", "Awaiting recheck", "Resolved"}
# Statuses whose Action Log may be empty (right after the checker's report)
RECORD_OPTIONAL_STATUS = {"New"}
# The Notes cell's carryover (unresolved) notation — read by the quiescence-aid print
# (e.g., "carryover 0", "unresolved (carryover) 2")
CARRY_RE = re.compile(r"(?:carryover|unresolved)\D*(\d+)", re.IGNORECASE)
# The resolved-history ledger — verified alongside automatically when present in findings.md's folder
ARCHIVE_FILENAME = "findings-archive.md"
ARCHIVE_SECTION = "## Resolved History"
ARCHIVE_ONLY_STATUS = {"Resolved"}
# Cycle Log History — the archive ledger's section preserving past cycle-log rows (absent in legacy archives)
CYCLE_SECTION = "## Cycle Log History"
# The ledger cycle log's retention window — rows beyond it are due for archival (the single source
# imported by the archival script. The widest window any verdict reads: quiescence 2 rows ·
# Plan 4 the latest 1 row · lens selection 'the previous row of the same scope' — 5 rows keeps that
# within the window even in real loops with interleaved re-verifications, and beyond it the
# Lens A fallback is the safe direction)
CYCLE_KEEP = 5

FINDING_ID_RE = re.compile(r"^F-\d{3,}$")
SPEC_ID_RE = re.compile(r"(?:FR|NFR)-\d+-[0-9E]\w*")
REQUIRED_SECTIONS = ["## Defect Ledger", "## Process Improvement Proposals", "## Cycle Log"]
# The header table's 'Last F-number' cell (the cell right before Current cycle — findings-template format)
LAST_ID_RE = re.compile(
    r"^\|[^\n]*Last F-number\s*\|\s*Current cycle\s*\|[ \t]*\n"
    r"\|[\s:|-]+\|[ \t]*\n"
    r"\|[^\n]*\|\s*([^|\n]*?)\s*\|\s*\d+\s*\|[ \t]*$",
    re.MULTILINE,
)
# Defect ledger column count (ID, Status, Type, Target, Symptom, Evidence, Action Log)
FINDING_COLUMN_COUNT = 7
# Temporary character protecting `\|` escapes (a value that can't appear in md text)
_ESCAPED_PIPE = "\x00"


def split_cells(line: str) -> list[str]:
    """Splits one table line into a list of cells. `\\|` escapes count as cell content."""
    protected = line.strip().replace("\\|", _ESCAPED_PIPE)
    return [
        c.strip().replace(_ESCAPED_PIPE, "|")
        for c in protected.strip("|").split("|")
    ]


def split_table_rows(text: str, section: str) -> list[list[str]]:
    """Returns the data rows (headers/dividers excluded) of the section's table as cell lists.

    The section ends at the next `## ` heading — a missing middle section never swallows another section.
    """
    match = re.search(
        rf"{re.escape(section)}(.*?)(?=^## |\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if not match:
        return []
    rows = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = split_cells(line)
        # Exclude headers/dividers
        if not cells or all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue
        if cells[0] in ("ID", "Cycle", "Proposal"):
            continue
        rows.append(cells)
    return rows


def normalize_finding_cells(cells: list[str]) -> list[str]:
    """Defect rows exceeding 7 cells get the excess re-joined into the evidence cell.

    Unescaped `|` shows up in the evidence/Action Log cells where code quotes are mandatory —
    pin the first 5 cells (ID, Status, Type, Target, Symptom) and the last cell (Action Log)
    and merge everything in between into the evidence cell, blocking cell-shift false positives
    and evidence truncation.
    """
    if len(cells) <= FINDING_COLUMN_COUNT:
        return cells
    head = cells[: FINDING_COLUMN_COUNT - 2]
    evidence = "|".join(cells[FINDING_COLUMN_COUNT - 2 : -1])
    return head + [evidence, cells[-1]]


def check_findings(
    rows: list[list[str]],
    spec_ids: set[str] | None,
    seen_ids: set[str],
    allowed_status: set[str] = VALID_STATUS,
    where: str = "",
) -> list[str]:
    """Checks defect rows. The caller shares seen_ids so ID uniqueness spans ledger ∪ archive.

    Archive rows get the same checks with allowed_status={Resolved} and a where prefix
    (the SPEC ghost check is skipped via spec_ids=None — frozen history already passed it at archival time).
    """
    errors = []
    for cells in rows:
        cells = normalize_finding_cells(cells)
        if len(cells) < FINDING_COLUMN_COUNT:
            errors.append(f"{where}Defect row has too few cells (7 required): {' | '.join(cells)}")
            continue
        fid, status, ftype, target, _symptom, evidence, record = cells

        if not FINDING_ID_RE.match(fid):
            errors.append(f"{where}{fid}: ID format violation (F-NNN required)")
        if fid in seen_ids:
            errors.append(f"{where}{fid}: duplicate ID (each ID must live in exactly one place across ledger and archive)")
        seen_ids.add(fid)

        if status not in allowed_status:
            errors.append(f"{where}{fid}: status '{status}' not allowed here ({'/'.join(sorted(allowed_status))} only)")
        if ftype not in VALID_TYPES:
            errors.append(f"{where}{fid}: type '{ftype}' not in the definition ({'/'.join(sorted(VALID_TYPES))})")

        if not evidence:
            errors.append(f"{where}{fid}: evidence empty — defect rows without evidence forbidden")

        if status not in RECORD_OPTIONAL_STATUS and not record:
            errors.append(f"{where}{fid}: status '{status}' with an empty Action Log — re-entry impossible")

        if spec_ids is not None and target:
            for sid in SPEC_ID_RE.findall(target):
                if sid not in spec_ids:
                    errors.append(f"{where}{fid}: target {sid} not in the SPEC (ghost)")
    return errors


def fmt_id(num: int) -> str:
    """Renders an assigned number (0 = none yet → '—')."""
    return "—" if num == 0 else f"F-{num:03d}"


def parse_last_id(text: str) -> tuple[bool, int, str | None]:
    """Reads the header table's 'Last F-number' cell → (cell present, last number (none=0), format error).

    A missing cell means a legacy ledger — the caller branches the checks.
    """
    match = LAST_ID_RE.search(text)
    if not match:
        return False, 0, None
    cell = match.group(1).strip()
    if cell in ("—", "-", ""):
        return True, 0, None
    if FINDING_ID_RE.match(cell):
        return True, int(cell[2:]), None
    return True, 0, f"Header 'Last F-number' cell format violation: '{cell}' (F-NNN or — only)"


def id_numbers(rows: list[list[str]]) -> list[int]:
    """The numbers of format-valid defect IDs (format violations are caught separately by check_findings)."""
    nums = []
    for cells in rows:
        cells = normalize_finding_cells(cells)
        if cells and FINDING_ID_RE.match(cells[0]):
            nums.append(int(cells[0][2:]))
    return nums


def type_tally(rows_lists: list[list[list[str]]]) -> dict[str, int]:
    """Per-type tally across ledger ∪ archive (Rejected/Needs review excluded — the counting basis of the 'same type 3 times' rule)."""
    tally: dict[str, int] = {}
    for rows in rows_lists:
        for cells in rows:
            cells = normalize_finding_cells(cells)
            if len(cells) >= 3 and cells[1] in TALLY_STATUS and cells[2] in VALID_TYPES:
                tally[cells[2]] = tally.get(cells[2], 0) + 1
    return tally


def check_cycle_log(text: str, rows: list[list[str]]) -> list[str]:
    errors = []
    if not rows:
        errors.append("The cycle log is empty — at least the cycle 0 (ledger created) row is required")
        return errors

    cycle_numbers = []
    for cells in rows:
        if not cells or not cells[0].isdigit():
            errors.append(f"A cycle log row's cycle number is not a number: {' | '.join(cells)}")
            continue
        cycle_numbers.append(int(cells[0]))

    # Find the 'Current cycle' cell in the header table — no dependence on the SPEC path string
    header_match = re.search(
        r"^\|[^\n]*Current cycle\s*\|[ \t]*\n"  # header row (Current cycle = last cell)
        r"\|[\s:|-]+\|[ \t]*\n"                 # divider
        r"\|[^\n]*\|\s*(\d+)\s*\|[ \t]*$",      # data row (last cell = cycle number)
        text,
        re.MULTILINE,
    )
    if not header_match:
        errors.append("Cannot find the header table's 'Current cycle' number")
    elif cycle_numbers and int(header_match.group(1)) != max(cycle_numbers):
        errors.append(
            f"Header current cycle ({header_match.group(1)}) and "
            f"log maximum cycle ({max(cycle_numbers)}) mismatch"
        )
    return errors


def hiatus_summary(rows: list[list[str]]) -> tuple[list[str], list[str]]:
    """Parses the latest 2 cycle-log rows' quiescence-verdict inputs (new/carryover/lens) → (row summaries, warnings).

    Makes no verdict (the quiescence rule belongs to SKILL step 5) — it replaces the model's
    eye-parsing of the prose notations (lens in Scope, carryover in Notes) with a print,
    so a missing notation never stays silent.
    Cycle 0 (ledger created) is not an inspection cycle and is exempt from warnings.
    """
    recent = [c for c in rows if c and c[0].isdigit()][-2:]
    parts, warns = [], []
    for cells in recent:
        cycle = cells[0]
        scope = cells[2] if len(cells) > 2 else ""
        new_count = cells[3].strip() if len(cells) > 3 else ""
        note = cells[6] if len(cells) > 6 else ""
        lenses = [name for name in ("A", "B") if f"Lens {name}" in scope]
        carry = CARRY_RE.search(note)
        parts.append(
            f"cycle {cycle} — new {new_count or '?'} · "
            f"carryover {carry.group(1) if carry else 'no notation'} · "
            f"lens {'·'.join(lenses) if lenses else 'no notation'}"
        )
        missing = [name for name, found in (("lens", lenses), ("carryover", carry)) if not found]
        if int(cycle) >= 1 and new_count == "0" and missing:
            warns.append(
                f"Cycle {cycle} row: 0 new but no {'/'.join(missing)} notation — "
                "the quiescence verdict cannot read this row ('Lens A/B' in Scope · 'carryover N' in Notes — Record step 1)"
            )
    return parts, warns


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print(f"Usage: {sys.argv[0]} <findings.md> [SPEC.md]", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    text = path.read_text(encoding="utf-8")

    spec_ids: set[str] | None = None
    if len(sys.argv) == 3:
        spec_path = Path(sys.argv[2])
        if not spec_path.exists():
            print(f"SPEC file not found: {spec_path}", file=sys.stderr)
            sys.exit(1)
        spec_text = spec_path.read_text(encoding="utf-8")
        # Compared against the SPEC ID set, not substring checks — blocks prefix-match false passes of other IDs
        spec_ids = set(SPEC_ID_RE.findall(spec_text))

    errors = []
    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"Required section missing: {section}")

    finding_rows = split_table_rows(text, "## Defect Ledger")
    cycle_rows = split_table_rows(text, "## Cycle Log")

    # The resolved-history ledger — the loop never reads it, but the gate verifies it alongside
    # (archival discipline, ID uniqueness/continuity)
    archive_path = path.parent / ARCHIVE_FILENAME
    archive_rows: list[list[str]] = []
    archive_cycle_rows: list[list[str]] = []
    archive_has_cycle_section = False
    if archive_path.exists():
        archive_text = archive_path.read_text(encoding="utf-8")
        if ARCHIVE_SECTION not in archive_text:
            errors.append(f"Archive ledger ({archive_path.name}) missing required section: {ARCHIVE_SECTION}")
        archive_rows = split_table_rows(archive_text, ARCHIVE_SECTION)
        # Cycle Log History — verified only when the section exists (legacy archives stay as before)
        archive_has_cycle_section = any(
            l.strip() == CYCLE_SECTION for l in archive_text.splitlines()
        )
        if archive_has_cycle_section:
            archive_cycle_rows = split_table_rows(archive_text, CYCLE_SECTION)

    seen_ids: set[str] = set()
    errors += check_findings(finding_rows, spec_ids, seen_ids)
    errors += check_findings(
        archive_rows, None, seen_ids, allowed_status=ARCHIVE_ONLY_STATUS, where="archive ledger "
    )
    errors += check_cycle_log(text, cycle_rows)

    # Cycle uniqueness/continuity gate — only when the archive has the cycle section (same shape as the F-number gap gate)
    if archive_has_cycle_section:
        union_cycles: list[int] = []
        for cells in archive_cycle_rows:
            if not cells or not cells[0].isdigit():
                errors.append(
                    f"An archive Cycle Log History row's cycle number is not a number: {' | '.join(cells)}"
                )
                continue
            union_cycles.append(int(cells[0]))
        union_cycles += [int(c[0]) for c in cycle_rows if c and c[0].isdigit()]
        dup_cycles = sorted({n for n in union_cycles if union_cycles.count(n) > 1})
        if dup_cycles:
            errors.append(
                "Duplicate cycle numbers (each must live in exactly one place across ledger and archive): "
                + ", ".join(str(n) for n in dup_cycles)
            )
        if union_cycles:
            missing_cycles = sorted(set(range(0, max(union_cycles) + 1)) - set(union_cycles))
            if missing_cycles:
                errors.append(
                    "Cycle log row gap (a lost row — every row must live in the ledger or the archive ledger): "
                    + ", ".join(str(n) for n in missing_cycles)
                )

    # Numbering gate — the header's 'Last F-number' (new-form ledgers) = max ID across ledger ∪ archive, no gaps in 1..max
    last_present, last_num, last_err = parse_last_id(text)
    all_nums = id_numbers(finding_rows) + id_numbers(archive_rows)
    max_num = max(all_nums, default=0)
    if last_err:
        errors.append(last_err)
    elif last_present:
        if last_num != max_num:
            errors.append(
                f"Header Last F-number ({fmt_id(last_num)}) and the ledger∪archive maximum ID ({fmt_id(max_num)}) mismatch"
            )
        missing = sorted(set(range(1, max_num + 1)) - set(all_nums))
        if missing:
            errors.append(
                "Defect ID gap (a lost row — every row must live in the ledger or the archive ledger): "
                + ", ".join(fmt_id(n) for n in missing)
            )
    elif archive_path.exists():
        errors.append(
            "An archive ledger exists but the findings.md header has no 'Last F-number' cell — the numbering baseline is missing. "
            "Add the cell to the header table and fill it with the maximum defect ID across ledger and archive"
        )

    print("=" * 60)
    if errors:
        print("[FAIL] Ledger integrity violation — loop re-entry not guaranteed")
        print("=" * 60)
        for e in errors:
            print(f"  ❌ {e}")
        print()
        print("→ Fix the ledger first. Bookkeeping comes before judgment.")
        sys.exit(1)

    open_count = sum(
        1 for c in finding_rows if len(c) >= 2 and c[1] in ("New", "Fixing", "Awaiting recheck")
    )
    resolved_in_ledger = sum(1 for c in finding_rows if len(c) >= 2 and c[1] == "Resolved")
    print("[PASS] Ledger integrity passed")
    print("=" * 60)
    print(f"  ✅ {len(finding_rows)} defect row(s) ({open_count} unresolved) — format/status/evidence discipline OK")
    if archive_path.exists():
        print(f"  ✅ Resolved history {len(archive_rows)} row(s) — archival discipline, ID uniqueness/continuity OK (ledger∪archive max {fmt_id(max_num)})")
    if archive_has_cycle_section:
        print(f"  ✅ Cycle history {len(archive_cycle_rows)} row(s) — cycle uniqueness/continuity OK (ledger∪archive)")
    print(f"  ✅ Cycle log {len(cycle_rows)} row(s) — re-entry possible")
    cycle_overflow = len(cycle_rows) - CYCLE_KEEP
    if cycle_overflow > 0:
        print(
            f"  ℹ️  Cycle log exceeds the latest {CYCLE_KEEP} rows by {cycle_overflow} — "
            f"due for archival to {ARCHIVE_FILENAME} (Cycle Log History) at the Record stage"
        )
    tally = type_tally([finding_rows, archive_rows])
    if tally:
        counted = " · ".join(f"{t} {tally[t]}" for t in TYPE_ORDER if t in tally)
        print(f"  ℹ️  Type tally (archive included · Rejected excluded): {counted}")
        for t in TYPE_ORDER:
            if tally.get(t, 0) >= 3:
                print(f"  ⚠️  Type {t} tally {tally[t]} — same type 3 times: consider a Process Improvement Proposal (rule 3 of the three rules)")
    hiatus_parts, hiatus_warns = hiatus_summary(cycle_rows)
    if hiatus_parts:
        print(f"  ℹ️  Quiescence aid (latest {len(hiatus_parts)} row(s)): {' / '.join(hiatus_parts)}")
    for warn in hiatus_warns:
        print(f"  ⚠️  {warn}")
    if resolved_in_ledger:
        print(
            f"  ℹ️  {resolved_in_ledger} Resolved row(s) in the ledger — due for archival to {ARCHIVE_FILENAME} (the resolved-history ledger) at the Record stage"
        )
    if not last_present and not archive_path.exists():
        print(
            "  ℹ️  No 'Last F-number' cell in the header (legacy ledger) — to use resolved-row archival, add the cell"
            f" (value: the maximum defect ID {fmt_id(max_num)})"
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
