#!/usr/bin/env python3
"""develojt-code-pdca resolved-row & cycle-log archival executor script (Record step 3 only).

Archival is done with this script only — no ad-hoc code, no hand edits (SKILL Record step 3).
Rationale: archival is the only operation that rewrites findings.md (all of the loop's active
state), and performing it each cycle with freshly written ad-hoc code means one full-file
rewrite mistake destroys the active ledger (confirmed by 1 field incident). The execution is
made deterministic while verification stays untouched — executor/verifier separation: this
script moves the rows, and the verify re-run at Record step 4 gates the result.

Behavior (zero judgment — a purely mechanical move):
  ① Every `Resolved` row of '## Defect Ledger' moves to the end of the '## Resolved History'
     table of findings-archive.md in the same folder, and ② the '## Cycle Log' rows beyond the
     latest CYCLE_KEEP (imported from verify — the retention window's single source) move to the
     end of the same file's '## Cycle Log History' table — each as its raw line (byte-unmodified —
     parsing is used only to identify rows; the move itself is the raw line), then exactly those
     lines are removed from the ledger.
  If the archive ledger doesn't exist, it is created from templates/findings-archive-template.md;
  a legacy archive (no cycle section) gets a template-identical section inserted before
  '## Resolved History'. `Rejected`/`Needs review`/unresolved rows, the header
  ('Last F-number' · 'Current cycle'), and the Process Improvement Proposals are never touched
  (numbering and cycle numbers invariant).

Safety properties (the failure direction = no changes, not loss):
  - Both new file contents are composed in memory first and every invariant is verified before
    any write — if even one fails, nothing is written and the script FAILs: removed lines =
    moved lines (the removed lines are re-inserted at their original positions and compared
    against the original in full — proving "zero changes to other lines") · removing the
    inserted lines from the new archive restores the old exactly (proving inserts/appends only) ·
    after archival the ledger has Resolved 0 and the cycle log at the retention window.
  - Write order: archive first → ledger second. Even if interrupted in between, the worst case
    is duplication (made visible by verify's duplicate ID/cycle FAIL), not loss.
  - Resumption: if a target row already exists in the archive (the previous run was interrupted
    before the ledger write), the move is skipped and only the ledger removal happens — and
    only when the contents are identical; otherwise FAIL (a human must check).

Table parsing is imported from verify_findings_integrity.py (a single source of parsing
semantics — the same `\\|` escape, >7-cell evidence recombination, and CYCLE_KEEP window).

Usage:
    python3 archive_resolved_findings.py spec/findings.md
    (the archive ledger lives in the ledger's folder; the template resolves relative to this
    script's location at ../templates — both automatic)

Exit codes: 0 — archived, or nothing to archive (no changes) / 1 — FAIL (nothing written)
"""

import re
import sys
from pathlib import Path

from verify_findings_integrity import (
    ARCHIVE_FILENAME,
    ARCHIVE_ONLY_STATUS,
    ARCHIVE_SECTION,
    CYCLE_KEEP,
    CYCLE_SECTION,
    FINDING_COLUMN_COUNT,
    FINDING_ID_RE,
    normalize_finding_cells,
    split_cells,
)

LEDGER_SECTION = "## Defect Ledger"
LEDGER_CYCLE_SECTION = "## Cycle Log"
TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "findings-archive-template.md"
# Extracts the project name from the findings.md title (to fill {project name} on archive creation)
TITLE_RE = re.compile(r"^# Findings — (.+?) \(PDCA ledger\)", re.MULTILINE)


def fail(errors: list[str]) -> None:
    print("=" * 60)
    print("[FAIL] Archival aborted — nothing was written")
    print("=" * 60)
    for e in errors:
        print(f"  ❌ {e}")
    print()
    print("→ Fix the ledger first. Bookkeeping comes before judgment.")
    sys.exit(1)


def section_line_range(lines: list[str], heading: str) -> tuple[int, int] | None:
    """The [start, end) line indexes from right after the heading line to the next '## ' heading (or EOF)."""
    start = None
    for i, line in enumerate(lines):
        s = line.strip()
        if start is None:
            if s == heading:
                start = i + 1
        elif s.startswith("## "):
            return start, i
    return (start, len(lines)) if start is not None else None


def row_cells(line: str) -> list[str] | None:
    """Normalized cell list if the line is a table line, else None (same parser as verify)."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    return normalize_finding_cells(split_cells(stripped))


def data_row_ids(lines: list[str], span: tuple[int, int]) -> list[str]:
    """IDs of rows with a valid defect ID (F-NNN) inside the span (headers/separators fall out naturally)."""
    ids = []
    for i in range(span[0], span[1]):
        cells = row_cells(lines[i])
        if cells and FINDING_ID_RE.match(cells[0]):
            ids.append(cells[0])
    return ids


def resolved_rows(lines: list[str], span: tuple[int, int]) -> tuple[list[tuple[int, str, str]], list[str]]:
    """Archival-target rows in the span (status in the archive-allowed set = `Resolved`) →
    [(line index, raw line, ID)], format errors.

    Target judgment reuses verify's ARCHIVE_ONLY_STATUS — a single source for "what may enter
    the archive" and "what gets moved".
    """
    rows, errors = [], []
    for i in range(span[0], span[1]):
        cells = row_cells(lines[i])
        if not cells or len(cells) < 2 or cells[1] not in ARCHIVE_ONLY_STATUS:
            continue
        if len(cells) < FINDING_COLUMN_COUNT:
            errors.append(f"{cells[0]}: Resolved row with too few cells (7 required) — cannot archive")
            continue
        if not FINDING_ID_RE.match(cells[0]):
            errors.append(f"Resolved row with an invalid ID format: '{cells[0]}' (F-NNN required) — cannot archive")
            continue
        rows.append((i, lines[i], cells[0]))
    return rows, errors


def cycle_data_rows(lines: list[str], span: tuple[int, int]) -> list[tuple[int, str, int]]:
    """Cycle data rows of the table inside the span → [(line index, raw line, cycle number)]
    (headers/separators fall out naturally via the digit check)."""
    rows = []
    for i in range(span[0], span[1]):
        cells = row_cells(lines[i])
        if cells and cells[0].isdigit():
            rows.append((i, lines[i], int(cells[0])))
    return rows


def template_cycle_block() -> list[str] | None:
    """The template's Cycle Log History section block (heading included, up to the next heading) —
    for migrating legacy archive ledgers."""
    if not TEMPLATE_PATH.exists():
        return None
    tlines = TEMPLATE_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    start = None
    for i, line in enumerate(tlines):
        s = line.strip()
        if start is None:
            if s == CYCLE_SECTION:
                start = i
        elif s.startswith("## "):
            return tlines[start:i]
    return tlines[start:] if start is not None else None


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <findings.md>", file=sys.stderr)
        sys.exit(1)

    ledger_path = Path(sys.argv[1])
    if not ledger_path.exists():
        print(f"File not found: {ledger_path}", file=sys.stderr)
        sys.exit(1)
    ledger_text = ledger_path.read_text(encoding="utf-8")
    ledger_lines = ledger_text.splitlines(keepends=True)

    span = section_line_range(ledger_lines, LEDGER_SECTION)
    if span is None:
        fail([f"Required section missing from the ledger: {LEDGER_SECTION}"])
    cyc_span = section_line_range(ledger_lines, LEDGER_CYCLE_SECTION)
    if cyc_span is None:
        fail([f"Required section missing from the ledger: {LEDGER_CYCLE_SECTION}"])

    # 1. Select the targets — parsing identifies, the raw line moves
    moved, errors = resolved_rows(ledger_lines, span)
    if errors:
        fail(errors)
    moved_ids = [fid for _, _, fid in moved]
    dup = sorted({x for x in moved_ids if moved_ids.count(x) > 1})
    if dup:
        fail([f"Duplicate Resolved-row ID inside the ledger: {' · '.join(dup)}"])

    ledger_cycles = cycle_data_rows(ledger_lines, cyc_span)
    all_cycle_nums = [n for _, _, n in ledger_cycles]
    dup_cycles = sorted({n for n in all_cycle_nums if all_cycle_nums.count(n) > 1})
    if dup_cycles:
        fail([f"Duplicate cycle numbers inside the ledger's cycle log: {' · '.join(str(n) for n in dup_cycles)}"])
    cycle_moved = ledger_cycles[:-CYCLE_KEEP] if len(ledger_cycles) > CYCLE_KEEP else []
    cycle_moved_nums = [n for _, _, n in cycle_moved]

    if not moved and not cycle_moved:
        print(
            f"Nothing to archive — the ledger has no `Resolved` rows and the cycle log is within the latest {CYCLE_KEEP} rows (no changes)."
        )
        sys.exit(0)

    # 2. Load the archive ledger (create from the template if absent — {project name} from the ledger title)
    archive_path = ledger_path.parent / ARCHIVE_FILENAME
    created = False
    warns: list[str] = []
    if archive_path.exists():
        archive_text = archive_path.read_text(encoding="utf-8")
    else:
        if not TEMPLATE_PATH.exists():
            fail([f"Neither the archive ledger nor the template exists: {TEMPLATE_PATH}"])
        archive_text = TEMPLATE_PATH.read_text(encoding="utf-8")
        title = TITLE_RE.search(ledger_text)
        if title:
            archive_text = archive_text.replace("{project name}", title.group(1), 1)
        else:
            warns.append("Could not read the project name from the findings.md title — left {project name} as-is")
        created = True

    if ARCHIVE_SECTION not in archive_text:
        fail([f"Required section missing from the archive ledger ({archive_path.name}): {ARCHIVE_SECTION}"])
    archive_lines = archive_text.splitlines(keepends=True)
    arch_span = section_line_range(archive_lines, ARCHIVE_SECTION)

    # The Resolved History table's end must be the file end — prevents appending outside the
    # table / into another table
    pipe_idx = [i for i, l in enumerate(archive_lines) if l.strip().startswith("|")]
    if not pipe_idx:
        fail([f"The archive ledger has no table — a table header and separator are required under {ARCHIVE_SECTION}"])
    if pipe_idx[-1] < arch_span[0]:
        fail([f"The archive ledger's last table sits outside the {ARCHIVE_SECTION} section — appending at the table end cannot hold"])
    trailing = [l.strip() for l in archive_lines[pipe_idx[-1] + 1 :] if l.strip()]
    if trailing:
        fail([f"Content found after the archive ledger's table — appending at the table end cannot hold: {trailing[0][:60]}"])

    # 3. Resolved resumption branch — targets already in the archive skip the append (ledger removal only) when identical
    existing: dict[str, list[str]] = {}
    for i in range(arch_span[0], arch_span[1]):
        cells = row_cells(archive_lines[i])
        if cells and FINDING_ID_RE.match(cells[0]):
            existing.setdefault(cells[0], []).append(archive_lines[i].strip())
    to_append: list[str] = []
    resumed: list[str] = []
    for _, raw, fid in moved:
        if fid in existing:
            if len(existing[fid]) > 1:
                fail([f"{fid} duplicated inside the archive ledger — fix the archive ledger first"])
            if existing[fid][0] != raw.strip():
                fail([f"{fid}: the ledger row and the existing archive row differ — a human must determine which is the original"])
            resumed.append(fid)
        else:
            to_append.append(raw if raw.endswith("\n") else raw + "\n")

    # 4. Compose the new archive in memory — (line, inserted) marks make "inserts/appends only" machine-provable
    marked: list[tuple[str, bool]] = [(l, False) for l in archive_lines]
    section_added = False
    existing_cycles: dict[int, list[str]] = {}
    cycle_to_insert: list[str] = []
    cycle_resumed: list[int] = []
    if cycle_moved:
        # Legacy archive (no cycle section): insert the template-identical section before the '## Resolved History' heading
        lines_now = [l for l, _ in marked]
        if not any(l.strip() == CYCLE_SECTION for l in lines_now):
            block = template_cycle_block()
            if block is None:
                fail([f"The archive ledger has no {CYCLE_SECTION} section and the template lacks it too: {TEMPLATE_PATH}"])
            head_at = [i for i, l in enumerate(lines_now) if l.strip() == ARCHIVE_SECTION]
            if not head_at:
                fail([f"Cannot find the {ARCHIVE_SECTION} heading line in the archive ledger — no valid insertion point for the section"])
            marked[head_at[0] : head_at[0]] = [(l, True) for l in block]
            section_added = True

        # Cycle resumption branch + the table-end insertion point
        lines_now = [l for l, _ in marked]
        a_cyc_span = section_line_range(lines_now, CYCLE_SECTION)
        for i in range(a_cyc_span[0], a_cyc_span[1]):
            cells = row_cells(lines_now[i])
            if cells and cells[0].isdigit():
                existing_cycles.setdefault(int(cells[0]), []).append(lines_now[i].strip())
        cyc_pipe = [
            i for i in range(a_cyc_span[0], a_cyc_span[1]) if lines_now[i].strip().startswith("|")
        ]
        if not cyc_pipe:
            fail([f"No table header/separator under the archive ledger's {CYCLE_SECTION} — appending at the table end cannot hold"])
        cyc_trailing = [
            lines_now[i].strip() for i in range(cyc_pipe[-1] + 1, a_cyc_span[1]) if lines_now[i].strip()
        ]
        if cyc_trailing:
            fail([f"Content found after the archive ledger's {CYCLE_SECTION} table — appending at the table end cannot hold: {cyc_trailing[0][:60]}"])
        for _, raw, num in cycle_moved:
            if num in existing_cycles:
                if len(existing_cycles[num]) > 1:
                    fail([f"Cycle {num} duplicated inside the archive ledger — fix the archive ledger first"])
                if existing_cycles[num][0] != raw.strip():
                    fail([f"Cycle {num}: the ledger row and the existing archive row differ — a human must determine which is the original"])
                cycle_resumed.append(num)
            else:
                cycle_to_insert.append(raw if raw.endswith("\n") else raw + "\n")
        pos = cyc_pipe[-1] + 1
        marked[pos:pos] = [(l, True) for l in cycle_to_insert]

    if to_append:
        if marked and not marked[-1][0].endswith("\n"):
            marked.append(("\n", True))
        marked += [(l, True) for l in to_append]
    archive_new = "".join(l for l, _ in marked)

    # 5. Compose the new ledger — remove exactly the archived Resolved/cycle lines
    removed_pairs = sorted(
        [(i, raw) for i, raw, _ in moved] + [(i, raw) for i, raw, _ in cycle_moved]
    )
    removed_idx = {i for i, _ in removed_pairs}
    ledger_new_lines = [l for i, l in enumerate(ledger_lines) if i not in removed_idx]
    ledger_new = "".join(ledger_new_lines)

    # 6. Verify every invariant — if even one fails, nothing is written
    problems: list[str] = []
    rebuilt = list(ledger_new_lines)
    for i, raw in removed_pairs:  # re-insert removed lines at their original positions → must equal the original
        rebuilt.insert(i, raw)
    if rebuilt != ledger_lines:
        problems.append("New ledger + re-inserted removed lines differ from the original — other lines changed")
    if [l for l, added in marked if not added] != archive_lines:
        problems.append("Removing the inserted lines from the new archive does not restore the old — changes beyond inserts/appends")
    new_lines = ledger_new.splitlines(keepends=True)
    new_span = section_line_range(new_lines, LEDGER_SECTION)
    leftover = resolved_rows(new_lines, new_span)[0] if new_span else []
    if new_span is None:
        problems.append("The Defect Ledger section disappeared from the ledger after archival")
    elif leftover:
        problems.append(f"Resolved rows remain in the ledger after archival: {' · '.join(f for _, _, f in leftover)}")
    new_cyc_span = section_line_range(new_lines, LEDGER_CYCLE_SECTION)
    if new_cyc_span is None:
        problems.append("The Cycle Log section disappeared from the ledger after archival")
    else:
        kept = len(cycle_data_rows(new_lines, new_cyc_span))
        if kept != len(ledger_cycles) - len(cycle_moved):
            problems.append(f"The ledger's cycle log has {kept} row(s) after archival — differs from the expectation (keep the latest {CYCLE_KEEP})")
    arch_new_lines = archive_new.splitlines(keepends=True)
    arch_new_span = section_line_range(arch_new_lines, ARCHIVE_SECTION)
    arch_ids = data_row_ids(arch_new_lines, arch_new_span) if arch_new_span else []
    for fid in moved_ids:
        if arch_ids.count(fid) != 1:
            problems.append(f"{fid} does not appear exactly once in the archive after archival ({arch_ids.count(fid)}×)")
    if len(arch_ids) != len(existing) + len(to_append):
        problems.append("The archive's Resolved row count differs from 'existing + appended'")
    arch_cyc_span = section_line_range(arch_new_lines, CYCLE_SECTION)
    arch_cycle_nums = (
        [n for _, _, n in cycle_data_rows(arch_new_lines, arch_cyc_span)] if arch_cyc_span else []
    )
    for num in cycle_moved_nums:
        if arch_cycle_nums.count(num) != 1:
            problems.append(
                f"Cycle {num} does not appear exactly once in the archive after archival ({arch_cycle_nums.count(num)}×)"
            )
    if cycle_moved and len(arch_cycle_nums) != len(existing_cycles) + len(cycle_to_insert):
        problems.append("The archive's cycle row count differs from 'existing + inserted'")
    if problems:
        fail(problems)

    # 7. Write — archive first, ledger second (an interruption in between means duplication, not loss)
    if archive_new != archive_text or created:
        archive_path.write_text(archive_new, encoding="utf-8")
    ledger_path.write_text(ledger_new, encoding="utf-8")

    remaining = data_row_ids(new_lines, new_span)
    kept_count = len(cycle_data_rows(new_lines, new_cyc_span)) if new_cyc_span else 0
    summary = ([f"{len(moved)} Resolved row(s)"] if moved else []) + (
        [f"{len(cycle_moved)} cycle-log row(s)"] if cycle_moved else []
    )
    print("=" * 60)
    print(f"[Archived] {' · '.join(summary)} → {archive_path.name}")
    print("=" * 60)
    if moved:
        print(f"  ✅ Resolved archived: {' · '.join(moved_ids)} (raw lines, unmodified)")
    if cycle_moved:
        print(
            f"  ✅ Cycles archived: {' · '.join(str(n) for n in cycle_moved_nums)} "
            f"(raw lines, unmodified — the ledger keeps the latest {CYCLE_KEEP})"
        )
    if created:
        print("  ✅ Archive ledger newly created (template copy)")
    if section_added:
        print(f"  ✅ {CYCLE_SECTION} section added to the archive ledger (legacy archive — template-identical insert)")
    if resumed:
        print(f"  ℹ️  Resumed: {' · '.join(resumed)} — already in the archive; append skipped, ledger removal only")
    if cycle_resumed:
        print(
            f"  ℹ️  Resumed (cycles): {' · '.join(str(n) for n in cycle_resumed)} — already in the archive; insert skipped, ledger removal only"
        )
    for w in warns:
        print(f"  ⚠️  {w}")
    print(f"  ✅ Ledger remaining: {len(remaining)} defect row(s) (Resolved 0) · cycle log {kept_count} row(s)")
    tally = f"Resolved {len(arch_ids)} row(s)"
    if arch_cyc_span is not None:
        tally += f" · cycles {len(arch_cycle_nums)} row(s)"
    print(f"  ✅ Archive total: {tally}")
    print("  → Next: re-run verify_findings_integrity.py (Record step 4)")
    sys.exit(0)


if __name__ == "__main__":
    main()
