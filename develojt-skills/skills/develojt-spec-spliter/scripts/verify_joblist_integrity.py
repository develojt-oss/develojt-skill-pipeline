#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# verify_joblist_integrity.py — develojt-spec-spliter joblist integrity check
#
# Checks joblist.md's own format integrity (not SPEC comparison — that's verify_joblist_spec_sync.py).
# Checks:
#   1) The "Scaffolding"/"Work Table" tables have data rows
#   2) Column counts — scaffolding rows have exactly 3 cells (Done/SPEC ID/Notes),
#      bundle rows exactly 4 (Done/SPEC ID/Series/Notes)
#   3) The Done cell is [ ] or [x] (other notations like [X] disallowed)
#   4) The SPEC ID cell — empty is an error; format is ^(FR|NFR)-[0-9]{2}-([0-9]{3}|E[0-9]{2})$,
#      leftover template placeholders (FR-00-000, NFR-00-000) are errors
#   5) No SPEC ID appears in two or more rows (one ID = exactly one row)
#   6) ### headers in the Work Table section follow the "### Bundle N: name" format
# Table header rows are detected as the | row immediately before a divider (|---|) — structural, not a content heuristic.
#
# Usage:
#   python3 verify_joblist_integrity.py <path to joblist.md>
#
import sys
import re

ID_RE = re.compile(r'^(FR|NFR)-[0-9]{2}-([0-9]{3}|E[0-9]{2})$')
CHECK_RE = re.compile(r'^\[( |x)\]$')
BUNDLE_HEADER_RE = re.compile(r'^### Bundle \d+:\s*\S')
PLACEHOLDERS = ('FR-00-000', 'NFR-00-000')


#
# Detects a table divider (|---|:---:| etc.). A row of only empty cells (| | |) is not a divider.
#
def is_divider(s):
    if not s.startswith('|'):
        return False
    body = s.replace('|', '').strip()
    return body != '' and set(body) <= set('-: ')


#
# Splits one data row into a list of cells.
#
def split_cells(row):
    return [c.strip() for c in row.strip().strip('|').split('|')]


#
# Extracts the data rows of the "Scaffolding" and "Work Table" sections from the joblist.md body
# as (line number, section, row text), collecting bundle-header format problems along the way.
# "## Past Issues" and "## Work Unit Definitions" are excluded.
# Table header rows are identified as the | row immediately before a divider (structure-based — cell contents are not inspected).
#
def extract_job_rows(text):
    lines = text.splitlines()
    rows = []
    problems = []
    section = None  # None / 'scaffold' / 'bundle'
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('## '):
            if 'Scaffolding' in s:
                section = 'scaffold'
            elif 'Work Table' in s:
                section = 'bundle'
            else:
                section = None
            continue
        if section is None:
            continue
        if s.startswith('### '):
            if section == 'bundle' and not BUNDLE_HEADER_RE.match(s):
                problems.append(f"line {i + 1}: bundle header is not in the '### Bundle N: name' format → {s}")
            continue
        if not s.startswith('|'):
            continue
        if is_divider(s):
            continue
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ''
        if is_divider(nxt):  # the row right before a divider = the table header
            continue
        rows.append((i + 1, section, s))
    return rows, problems


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 verify_joblist_integrity.py <path to joblist.md>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    try:
        text = open(path, encoding='utf-8').read()
    except OSError as e:
        print(f"Error: cannot open file: {e}", file=sys.stderr)
        sys.exit(2)

    rows, problems = extract_job_rows(text)

    if not rows:
        problems.append("No data rows in the work tables (check the '## Scaffolding' / '## Work Table' sections and table headers).")

    id_rows = {}  # SPEC ID → [line numbers] (for duplicate detection)
    for line_no, section, row in rows:
        cells = split_cells(row)
        # Scaffolding rows have exactly 3 cells (Done/SPEC ID/Notes), bundle rows exactly 4 (Done/SPEC ID/Series/Notes)
        expected = 3 if section == 'scaffold' else 4
        section_name = 'scaffolding' if section == 'scaffold' else 'bundle'
        if len(cells) != expected:
            problems.append(f"line {line_no}: a {section_name} row must have {expected} cells but has {len(cells)} → {row}")
            continue
        done, spec_id = cells[0], cells[1]

        if not CHECK_RE.match(done):
            problems.append(f"line {line_no}: the Done cell is not in [ ] or [x] form ([X] disallowed) → '{done}'")
        if spec_id == '':
            problems.append(f"line {line_no}: the SPEC ID cell is empty → {row}")
        elif spec_id in PLACEHOLDERS:
            problems.append(f"line {line_no}: a template placeholder ({spec_id}) remains — fill in a real SPEC ID")
        elif not ID_RE.match(spec_id):
            problems.append(f"line {line_no}: invalid SPEC ID format (FR-xx-xxx / NFR-xx-xxx / FR-xx-Exx) → '{spec_id}'")
        else:
            id_rows.setdefault(spec_id, []).append(line_no)

    # The same SPEC ID in two or more rows is an error (one ID = exactly one row)
    for spec_id, line_nos in sorted(id_rows.items()):
        if len(line_nos) > 1:
            nos = ', '.join(str(n) for n in line_nos)
            problems.append(f"duplicate: {spec_id} appears in {len(line_nos)} rows (lines {nos}) — one ID must be exactly one row")

    print("=" * 60)
    print("  joblist integrity check")
    print("=" * 60)
    print(f"  work rows checked: {len(rows)}")
    print(f"  problems: {len(problems)}")
    print("=" * 60)

    if problems:
        print()
        for p in problems:
            print(f"  ❌ {p}")
        print()
        print("FAIL — fix the joblist format.")
        sys.exit(1)

    print()
    print("✅ PASS — the joblist format is valid.")
    sys.exit(0)


if __name__ == '__main__':
    main()
