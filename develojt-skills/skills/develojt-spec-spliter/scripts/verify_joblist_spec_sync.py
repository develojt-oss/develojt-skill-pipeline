#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# verify_joblist_spec_sync.py — develojt-spec-spliter SPEC↔joblist consistency check
#
# Checks the consistency between SPEC.md and joblist.md (bidirectional).
#   1) Omissions: FR/NFR IDs in the SPEC missing from the joblist → risk of dropped work (the most dangerous)
#   2) Ghosts: IDs in the joblist absent from the SPEC → the ledger points at requirements that don't exist
#
# ID collection is table-row based (ID mentions in prose or Notes/Series cells are never counted):
#   - SPEC: only the first cell (ID cell) of requirement table rows. Rows whose source cell is [Removed]
#     and rows with ~~strikethrough~~ IDs are history-preservation rows, so they are excluded.
#   - joblist: only the SPEC ID cell (2nd cell) of Scaffolding/Work Table data rows.
#     Sibling pointers in Notes cells (e.g., "follows FR-11-001 approach") can't stand in
#     for a row's existence, so they are not counted.
#
# This check guarantees "what must be done" (SPEC) and "what is being tracked" (joblist)
# have not diverged. Code behavior is not checked.
#
# Usage:
#   python3 verify_joblist_spec_sync.py <path to joblist.md> <path to SPEC.md>
#
import sys
import re

ID_RE = re.compile(r'(?:FR|NFR)-\d{2}-(?:\d{3}|E\d{2})')
PLACEHOLDERS = ('FR-00-000', 'NFR-00-000')  # template placeholders


#
# Splits one table row into a list of cells.
#
def split_cells(row):
    return [c.strip() for c in row.strip().strip('|').split('|')]


#
# Extracts the ID set from SPEC.md's requirement table rows.
# Counted only when a row's first cell matches the ID format exactly (prose, comments, and other tables naturally drop out).
# Rows whose source cell (2nd cell) is [Removed] and rows with ~~strikethrough~~ IDs are history-preservation rows, so they are excluded.
#
def spec_req_ids(text):
    ids = set()
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith('|'):
            continue
        cells = split_cells(s)
        if len(cells) < 2:
            continue
        id_cell, source_cell = cells[0], cells[1]
        if id_cell.startswith('~~'):  # strikethrough ID — history preservation of a removed requirement
            continue
        if '[Removed]' in source_cell:   # source cell [Removed] — a requirement removed after agreement
            continue
        if ID_RE.fullmatch(id_cell):
            ids.add(id_cell)
    return ids


#
# Extracts only the IDs in the SPEC ID cell (2nd cell) of the joblist's "Scaffolding" and
# "Work Table" section data rows (Past Issues excluded). Table header rows ("SPEC ID") and
# dividers drop out naturally since their cell values aren't ID-shaped.
# Bundle headers (### Bundle N) never break the table (### is not ##, so they pass through naturally).
#
def joblist_job_ids(text):
    in_tracked = False
    ids = set()
    for line in text.splitlines():
        s = line.strip()
        # Tracked-section start: "## 0. Scaffolding" or "## Work Table"
        if s.startswith('## ') and ('Scaffolding' in s or 'Work Table' in s):
            in_tracked = True
            continue
        # Any other ## section (e.g., Past Issues, Work Unit Definitions) ends the tracking
        if s.startswith('## ') and in_tracked:
            in_tracked = False
            continue
        if not in_tracked:
            continue
        if not s.startswith('|'):
            continue
        cells = split_cells(s)
        if len(cells) < 2:
            continue
        spec_id = cells[1]  # the SPEC ID cell — ID mentions in other cells are never inspected
        if spec_id in PLACEHOLDERS:
            continue
        if ID_RE.fullmatch(spec_id):
            ids.add(spec_id)
    return ids


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 verify_joblist_spec_sync.py <joblist.md> <SPEC.md>", file=sys.stderr)
        sys.exit(2)

    jl_path, spec_path = sys.argv[1], sys.argv[2]
    try:
        jl = open(jl_path, encoding='utf-8').read()
        spec = open(spec_path, encoding='utf-8').read()
    except OSError as e:
        print(f"Error: cannot open file: {e}", file=sys.stderr)
        sys.exit(2)

    spec_ids = spec_req_ids(spec)
    jl_ids = joblist_job_ids(jl)

    missing = sorted(spec_ids - jl_ids)   # in the SPEC, not in the joblist
    ghost = sorted(jl_ids - spec_ids)     # in the joblist, not in the SPEC

    print("=" * 60)
    print("  SPEC ↔ joblist consistency check")
    print("=" * 60)
    print(f"  SPEC IDs: {len(spec_ids)}   joblist IDs: {len(jl_ids)}")
    print(f"  omissions (in SPEC, not joblist): {len(missing)}")
    print(f"  ghosts (in joblist, not SPEC): {len(ghost)}")
    print("=" * 60)

    if missing:
        print()
        print("❌ Omissions — IDs in the SPEC but not the joblist (risk of dropped work):")
        for i in missing:
            print(f"     {i}")
    if ghost:
        print()
        print("❌ Ghosts — IDs in the joblist but not the SPEC (pointing at requirements that don't exist):")
        for i in ghost:
            print(f"     {i}")

    if missing or ghost:
        print()
        print("FAIL — reconcile the SPEC and the joblist.")
        sys.exit(1)

    print()
    print("✅ PASS — every ID in the SPEC and the joblist is consistent.")
    sys.exit(0)


if __name__ == '__main__':
    main()
