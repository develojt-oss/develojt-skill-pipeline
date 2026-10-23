#!/usr/bin/env python3
"""verify_anchor_sync.py — STORYBOARD↔joblist appearance-anchor consistency check

Usage: verify_anchor_sync.py spec/joblist.md design/STORYBOARD.md

Checks (SKIP when design/STORYBOARD.md is absent — project has no appearance anchors):
  1. Ghost anchor      — a joblist anchor's SB ID absent from the STORYBOARD mapping tables → ERROR
  2. Duplicate placement — one SB ID carried on two or more joblist rows → ERROR
  3. Uncarried mapped UI — an FR-mapped SB ID carried on no joblist anchor → ERROR
  4. Uncarried [Decorative] — ERROR when the same screen has FR-mapped UIs (a row exists to
     carry it), INFO when the whole screen is decorative only (no row to carry it — the
     builder's human screen comparison is the line of defense)

The joblist's `## Past Issues` section is a history archive and is excluded from counting.
Anchor counting spans table rows (`|`-starting) only, up to the run of ·-joined SB IDs right after
`Appearance:` — SB IDs mentioned by a same-cell deferral-handoff note (builder workflow 4) or sitting
in prose outside tables (the template legend's notation example) are not anchors.
Rows whose mapped-FR cell is neither an FR/NFR ID nor [Decorative] are not checked
(that format belongs to the mapper's verification).
"""
import re
import sys
from pathlib import Path

SB_ID = re.compile(r'\bSB-\d{2}-\d{2}\b')
SPEC_ID = re.compile(r'\b(?:FR|NFR)-\d{2}-(?:\d{3}|E\d{2})\b')
# The anchor notation is `Appearance: SB-02-01·SB-02-05` (template spec) — only the run of ·-joined SB IDs
# right after `Appearance:` is the anchor. The boundary keeps the SB IDs of same-cell deferral-handoff notes
# ("reproduce …'s appearance anchor (SB-03-22) on this row" — a legitimate sentence builder workflow 4
# mandates) out of the anchor count. Notation deviations (comma-joined etc.) surface as uncarried FAILs.
ANCHOR_RUN = re.compile(r'[ \t]*SB-\d{2}-\d{2}(?:[ \t]*·[ \t]*SB-\d{2}-\d{2})*')


def parse_storyboard(text):
    """Extract {SB ID: FR set} and the decorative SB set from the mapping tables."""
    mapped, deco = {}, set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith('|'):
            continue
        cells = [c.strip() for c in stripped.strip('|').split('|')]
        if not cells or not re.fullmatch(r'SB-\d{2}-\d{2}', cells[0]):
            continue
        fr_cell = cells[-1]
        frs = set(SPEC_ID.findall(fr_cell))
        if frs:
            mapped[cells[0]] = frs
        elif '[Decorative]' in fr_cell:
            deco.add(cells[0])
        # Other values (format deviations) belong to the mapper's checks — not judged here
    return mapped, deco


def parse_joblist_anchors(text):
    """Extract {SB ID: [row SPEC ID, ...]} from work-row anchors (Past Issues excluded)."""
    anchors = {}
    in_past_issues = False
    for line in text.splitlines():
        if line.strip().startswith('#'):
            in_past_issues = line.strip().lstrip('#').strip().startswith('Past Issues')
            continue
        if in_past_issues or 'Appearance:' not in line:
            continue
        if not line.strip().startswith('|'):
            continue  # Table rows only — the `Appearance:` notation example in prose (template legend) is not an anchor
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        row_id = next((c for c in cells if SPEC_ID.fullmatch(c)), '(row ID unknown)')
        anchor_part = line.split('Appearance:', 1)[1]
        run = ANCHOR_RUN.match(anchor_part)
        for sb in SB_ID.findall(run.group(0) if run else ''):
            anchors.setdefault(sb, []).append(row_id)
    return anchors


def main():
    if len(sys.argv) != 3:
        print('Usage: verify_anchor_sync.py spec/joblist.md design/STORYBOARD.md')
        sys.exit(2)
    joblist_path, sb_path = Path(sys.argv[1]), Path(sys.argv[2])

    if not sb_path.exists():
        print(f'SKIP — {sb_path} absent (project has no appearance anchors)')
        sys.exit(0)
    if not joblist_path.exists():
        print(f'Error: {joblist_path} does not exist')
        sys.exit(2)

    mapped, deco = parse_storyboard(sb_path.read_text(encoding='utf-8'))
    anchors = parse_joblist_anchors(joblist_path.read_text(encoding='utf-8'))

    ghosts = sorted(sb for sb in anchors if sb not in mapped and sb not in deco)
    dupes = sorted(sb for sb, rows in anchors.items() if len(rows) > 1)
    missing_mapped = sorted(sb for sb in mapped if sb not in anchors)
    screens_with_fr = {sb.rsplit('-', 1)[0] for sb in mapped}
    missing_deco = sorted(sb for sb in deco if sb not in anchors)
    deco_errors = [sb for sb in missing_deco if sb.rsplit('-', 1)[0] in screens_with_fr]
    deco_infos = [sb for sb in missing_deco if sb.rsplit('-', 1)[0] not in screens_with_fr]

    print('=' * 60)
    print(f' Appearance-anchor consistency: {joblist_path} ↔ {sb_path}')
    print(f' STORYBOARD mapped UIs {len(mapped)} · [Decorative] {len(deco)} · joblist anchored SBs {len(anchors)}')
    print('=' * 60)

    if ghosts:
        print()
        print('❌ Ghost anchors — in the joblist but absent from the STORYBOARD mapping tables:')
        for sb in ghosts:
            print(f'     {sb} (rows: {", ".join(anchors[sb])})')
    if dupes:
        print()
        print('❌ Duplicate placements — one SB ID on two or more rows (in the ledger, one SB ID rides on exactly one row):')
        for sb in dupes:
            print(f'     {sb} (rows: {", ".join(anchors[sb])})')
    if missing_mapped:
        print()
        print('❌ Uncarried mapped UIs — FR-mapped but on no joblist anchor:')
        for sb in missing_mapped:
            print(f'     {sb} (mapped FRs: {", ".join(sorted(mapped[sb]))})')
    if deco_errors:
        print()
        print('❌ Uncarried [Decorative] — the same screen has mapped FR rows, yet it rides nowhere:')
        for sb in deco_errors:
            print(f'     {sb}')
    if deco_infos:
        print()
        print('ℹ️  Uncarried [Decorative] — no mapped FR on the screen, so no row to carry it (normal — the builder\'s human screen comparison is the line of defense):')
        for sb in deco_infos:
            print(f'     {sb}')

    if ghosts or dupes or missing_mapped or deco_errors:
        print()
        print('FAIL — reconcile the STORYBOARD and the joblist anchors.')
        sys.exit(1)

    print()
    print('✅ PASS — the appearance anchors are consistent with the STORYBOARD.')
    sys.exit(0)


if __name__ == '__main__':
    main()
