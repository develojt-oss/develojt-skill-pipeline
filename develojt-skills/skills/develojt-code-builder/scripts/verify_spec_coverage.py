#!/usr/bin/env python3
"""
SPEC.md coverage verification script

Extracts every FR/NFR/E item ID from SPEC.md and
checks that a matching @spec tag exists in the code.

Usage:
    python3 scripts/verify_spec_coverage.py src/ spec/SPEC.md
    python3 scripts/verify_spec_coverage.py src/ spec/SPEC.md --joblist spec/joblist.md

With --joblist: only 'completion-checked ([x]) rows' from the joblist become the check
targets, not the whole SPEC. This prevents partial work (e.g., only the first 10
implemented) from misjudging the remaining not-yet-worked items as 'missing'. That is,
it asks "is everything checked also tagged in the code?".
Unchecked rows are intended not-yet-work, so they are not checked.

Orphan references (@spec in the code but not in the SPEC) are always checked against
the 'full SPEC ID set' regardless of --joblist, and finding one is FAIL (exit 1) —
a ghost tag is a severed traceability chain, so it never ends as a mere warning.

"""

import sys
import os
import re
import json
import subprocess


#
# Extracts only completion-checked ([x]) SPEC IDs from the joblist.md 'Scaffolding' and
# 'Work Table (bundles)' sections. Both sections are progress-tracking targets;
# '## Past Issues' and '## Work Unit Definitions' are excluded.
# Bundle headers (### Bundle N) are not ##, so they never break the table.
#
def extract_checked_ids(joblist_path):
    """Returns: (set of completion-checked IDs, count of recognized tracked sections) — None on read failure"""
    id_re = re.compile(r'\b(?:FR|NFR)-\d+-\d*[0-9E]+\b')
    checked = set()
    section_count = 0
    in_tracked = False
    try:
        # Encoding defense: errors='ignore', same as the other 3 scripts
        lines = open(joblist_path, encoding='utf-8', errors='ignore').read().splitlines()
    except (OSError, ValueError):
        return None
    for line in lines:
        s = line.strip()
        if s.startswith('## ') and ('Scaffolding' in s or 'Work Table' in s):
            in_tracked = True
            section_count += 1
            continue
        if s.startswith('## ') and in_tracked:
            in_tracked = False
            continue
        if not in_tracked or not s.startswith('|'):
            continue
        if 'SPEC ID' in s:  # table header
            continue
        # Only rows whose Done cell is [x]/[X]. cells[0]=Done, cells[1]=ID (common to 3- and 4-column tables)
        cells = [c.strip() for c in s.strip('|').split('|')]
        if len(cells) >= 2 and cells[0] in ('[x]', '[X]'):
            for m in id_re.findall(cells[1]):
                checked.add(m)
    return checked, section_count


def extract_spec_ids(spec_path, rich=False):
    """
    Extracts IDs from SPEC.md's requirement tables (| ID | Source | EARS Type | Requirement |).

    Table rows are parsed per line, per cell — only rows whose first cell is an ID are requirement rows.
    (An unanchored regex also mismatched the behavior chain table's single-ID cells as rows.)
    Rows whose source cell is [Removed] and strikethrough (~~) ID rows are history-preservation rows, excluded from the targets.

    Returns: rich=False → {id: requirement text}
             rich=True  → {id: {source, ears_type, name}}
    """
    # Encoding defense: errors='ignore', same as the other 3 scripts
    with open(spec_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()

    # ID patterns: FR-XX-XXX, NFR-XX-XXX, FR-XX-E0X
    id_re = re.compile(r'^(?:FR|NFR)-\d+-(?:\d+|E\d+)$')

    spec_ids = {}

    for line in lines:
        s = line.strip()
        if not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.strip('|').split('|', 3)]
        if len(cells) < 4:
            continue
        # Strikethrough-ID rows (~~FR-…~~): history of post-agreement removal — excluded
        if cells[0].startswith('~~'):
            continue
        if not id_re.match(cells[0]):
            continue
        spec_id, source, ears_type, requirement = cells
        # Rows whose source cell is [Removed]: history preservation — excluded
        if '[Removed]' in source:
            continue

        if rich:
            spec_ids[spec_id] = {'source': source, 'ears_type': ears_type, 'name': requirement}
        else:
            spec_ids[spec_id] = requirement

    return spec_ids


def find_refs_in_code(src_path):
    """
    Extracts every ID referenced by @spec tags in the code.

    Returns: set of IDs
    """
    try:
        result = subprocess.run(
            ['grep', '-roh', '@spec [A-Z]*-[0-9]*-[0-9A-Z]*', src_path],
            capture_output=True, text=True, timeout=30
        )

        refs = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                # "@spec FR-05-001" → "FR-05-001"
                ref_id = line.replace('@spec ', '').strip()
                if ref_id:
                    refs.add(ref_id)
        return refs

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Fall back to Python when grep is unavailable
        refs = set()
        ref_pattern = re.compile(r'@spec\s+((?:FR|NFR)-\d+-(?:\d+|E\d+))')

        for root, _, files in os.walk(src_path):
            if any(skip in root for skip in ['node_modules', 'dist', '.git']):
                continue
            for f in files:
                # Same 7-language support as verify_refs/todo/comments (extension mismatch misjudges non-web projects)
                if f.endswith(('.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue',
                               '.py', '.cs', '.java', '.cpp', '.cc', '.cxx', '.h', '.hpp')):
                    filepath = os.path.join(root, f)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                        for line in fh:
                            for m in ref_pattern.finditer(line):
                                refs.add(m.group(1))
        return refs


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/verify_spec_coverage.py <src path> <SPEC.md path>")
        print("  e.g.: python3 scripts/verify_spec_coverage.py src/ spec/SPEC.md")
        sys.exit(1)

    src_path = sys.argv[1]
    spec_path = sys.argv[2]

    if not os.path.exists(src_path):
        print(f"❌ src path not found: {src_path}")
        sys.exit(1)

    if not os.path.exists(spec_path):
        print(f"❌ SPEC.md not found: {spec_path}")
        sys.exit(1)

    # Extract IDs from the SPEC — the full set is always kept as the baseline for orphan (ghost @spec) verdicts
    all_spec_ids = extract_spec_ids(spec_path)

    if not all_spec_ids:
        print("⚠️  Cannot extract FR/NFR items from SPEC.md.")
        sys.exit(1)

    spec_ids = dict(all_spec_ids)

    # Extract @spec from the code
    code_refs = find_refs_in_code(src_path)

    # References in the code but not the SPEC (orphan references = ghost @spec).
    # Even when --joblist narrows the scope, orphan verdicts run against the 'full SPEC ID set' —
    # early implementation of unchecked IDs really exists in the full set so it never misfires; only ghosts get caught.
    orphan_refs = code_refs - set(all_spec_ids.keys())

    # With --joblist: narrow the check targets to completion-checked rows only (partial-work support)
    scope_note = "full SPEC"
    if '--joblist' in sys.argv:
        idx = sys.argv.index('--joblist')
        if idx + 1 >= len(sys.argv):
            print("❌ --joblist must be followed by the joblist.md path.")
            sys.exit(1)
        joblist_path = sys.argv[idx + 1]
        if not os.path.exists(joblist_path):
            print(f"❌ joblist not found: {joblist_path}")
            sys.exit(1)
        result = extract_checked_ids(joblist_path)
        if result is None:
            print(f"❌ Cannot read the joblist: {joblist_path}")
            sys.exit(1)
        checked, section_count = result
        if section_count == 0:
            print("⚠️  No tracked sections ('Scaffolding'/'Work Table') found in the joblist — check the section headers.")
        # Keep only checked IDs (limited to those actually in the SPEC)
        spec_ids = {k: v for k, v in spec_ids.items() if k in checked}
        scope_note = f"against {len(checked)} joblist completion check(s)"
        if not spec_ids and not orphan_refs:
            print("⚠️  No completion-checked rows in the joblist. Nothing to check.")
            sys.exit(0)

    # Compare
    fr_ids = {k: v for k, v in spec_ids.items() if k.startswith('FR-')}
    nfr_ids = {k: v for k, v in spec_ids.items() if k.startswith('NFR-')}

    covered_fr = {k for k in fr_ids if k in code_refs}
    missing_fr = {k for k in fr_ids if k not in code_refs}
    covered_nfr = {k for k in nfr_ids if k in code_refs}
    missing_nfr = {k for k in nfr_ids if k not in code_refs}

    # --json mode: print the structured result and exit (--joblist scope filter and exit code applied identically)
    if '--json' in sys.argv:
        rich_ids = extract_spec_ids(spec_path, rich=True)
        items = []
        for sid in sorted(spec_ids.keys()):
            info = rich_ids[sid]
            category = 'FR' if sid.startswith('FR-') else 'NFR'
            covered = sid in code_refs
            # Find the file list carrying that @spec
            ref_files = []
            if covered:
                try:
                    r = subprocess.run(
                        ['grep', '-rl', f'@spec {sid}', src_path],
                        capture_output=True, text=True, timeout=10)
                    ref_files = [f.strip() for f in r.stdout.strip().split('\n') if f.strip()]
                except Exception:
                    pass
            items.append({
                'id': sid, 'source': info['source'], 'ears_type': info['ears_type'],
                'name': info['name'], 'category': category,
                'covered': covered, 'files': ref_files
            })
        print(json.dumps({
            'type': 'spec_coverage',
            'scope': scope_note,
            'items': items,
            'orphan_refs': sorted(orphan_refs)
        }, ensure_ascii=False, indent=2))
        sys.exit(1 if (missing_fr or missing_nfr or orphan_refs) else 0)

    # Print results
    total = len(spec_ids)
    covered = len(covered_fr) + len(covered_nfr)
    coverage_pct = (covered / total * 100) if total > 0 else 0

    print(f"\n{'='*60}")
    print(f"  SPEC.md coverage verification results")
    print(f"{'='*60}")
    print(f"  Scope:          {scope_note}")
    print(f"  Target items:   {total} (FR: {len(fr_ids)}, NFR: {len(nfr_ids)})")
    print(f"  Covered:        {covered}")
    print(f"  Unimplemented:  {len(missing_fr) + len(missing_nfr)}")
    print(f"  Coverage:       {coverage_pct:.1f}%")
    print(f"{'='*60}\n")

    if missing_fr:
        print(f"❌ Unimplemented FRs ({len(missing_fr)}):\n")
        for fid in sorted(missing_fr):
            desc = fr_ids[fid][:60] + '...' if len(fr_ids[fid]) > 60 else fr_ids[fid]
            print(f"  {fid}: {desc}")
        print()

    if missing_nfr:
        print(f"⚠️  Unimplemented NFRs ({len(missing_nfr)}):\n")
        for nid in sorted(missing_nfr):
            desc = nfr_ids[nid][:60] + '...' if len(nfr_ids[nid]) > 60 else nfr_ids[nid]
            print(f"  {nid}: {desc}")
        print()

    if orphan_refs:
        print(f"❌ @spec in the code but not the SPEC ({len(orphan_refs)}) — ghost tags (severed traceability chain):\n")
        for oid in sorted(orphan_refs):
            print(f"  {oid}")
        print()

    if missing_fr:
        print(f"FAIL — {len(missing_fr)} FR item(s) unimplemented.")
    elif missing_nfr:
        print(f"FAIL — every FR implemented; {len(missing_nfr)} NFR(s) unimplemented.")
    if orphan_refs:
        print(f"FAIL — {len(orphan_refs)} ghost @spec tag(s): they reference IDs absent from the SPEC. Fix the tags or check the SPEC.")
    if missing_fr or missing_nfr or orphan_refs:
        sys.exit(1)
    print(f"✅ PASS — every FR/NFR item is mapped in the code. (coverage {coverage_pct:.1f}%)")
    sys.exit(0)


if __name__ == '__main__':
    main()
