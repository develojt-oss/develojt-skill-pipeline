#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# query_impact.py — develojt-spec-deriver change track C1-c (standalone tool)
#
# This file is a standalone read-only tool with 0 modifications to the skill body (SKILL.md).
# The deriver change mode's body wiring is attached in C1-a (the SKILL.md version updates then).
#
# Impact reverse-query (P6): given one SPEC ID about to change, prints the IDs that must be
# re-examined together, along three axes. Consumed as the "re-examination scope" by the change
# track (deriver change mode, develojt-code-changer code-only edits) and by pdca Plan.
#
#   1) Same bundle  — peers in the same joblist bundle (### Bundle N / Scaffolding). They run
#                     together through physical dependency (calls, data structures, events),
#                     so they must be looked at together.
#   2) Same series  — peers sharing the joblist Series cell. Built the same *way*, so fixing
#                     the reference implementation can skew the whole series (pdca S1's advance query).
#   3) Same behavior chain — peers bound in the same row (Related IDs) of a SPEC 'Observable
#                     Behavior Chain' table. Simultaneous outcomes of one trigger; changing
#                     one link can break the chain.
#
# This tool is a **read-only static query** (axis-6 static analysis only). It never judges what
# to fix or whether a fix is safe — stale/ghost/orphan detection is already done by the existing
# gates (verify_joblist_spec_sync, verify_spec_coverage). This tool only prints, deterministically,
# the scope of "how far to look together" — the part that does not overlap with those gates.
#
# Usage:
#   python3 query_impact.py <SPEC ID to change> <joblist.md> <SPEC.md>
#   python3 query_impact.py --selftest          # run the built-in tests
#
# Exit codes: 0 — normal / 1 — changed ID not in the joblist (impact not computable) / 2 — usage/file error
#
import sys
import re

ID_RE = re.compile(r'(?:FR|NFR)-\d{2}-(?:\d{3}|E\d{2})')
PLACEHOLDERS = ('FR-00-000', 'NFR-00-000')
NO_SERIES = '—'  # no-series notation (em dash)


def split_cells(row):
    """Splits one table row into a list of cells (strip outer |, then split)."""
    return [c.strip() for c in row.strip().strip('|').split('|')]


def is_divider(s):
    """Whether this is a table divider (|---| etc.)."""
    body = s.replace('|', '').strip()
    return body != '' and set(body) <= set('-: ')


def parse_joblist(text):
    """Extracts (id→bundle, bundle→id set, id→series, series→id set) from the joblist.

    - Scaffolding (## 0. Scaffolding) is a 3-column table (Done, ID, Notes) — no series.
    - The work table (### Bundle N) is a 4-column table (Done, ID, Series, Notes) — cell 2 is the series.
    - IDs in other sections (Past Issues, Work Unit Definitions, …) are never counted as bundle/series members.
    """
    id_bundle = {}
    bundle_ids = {}
    id_series = {}
    series_ids = {}

    current_bundle = None
    in_series_table = False  # a bundle (### ) has a series cell / scaffolding doesn't

    for line in text.splitlines():
        s = line.strip()

        if s.startswith('## 0.') and 'Scaffolding' in s:
            current_bundle, in_series_table = 'Scaffolding', False
            continue
        if s.startswith('### Bundle'):
            current_bundle, in_series_table = s.lstrip('# ').strip(), True
            continue
        # Any other ## section (Past Issues, Work Unit Definitions, the Work Table header, …) ends the bundle context.
        # (### Bundle is not ##, and is caught separately above, so it doesn't break the table.)
        if s.startswith('## '):
            current_bundle, in_series_table = None, False
            continue
        if current_bundle is None or not s.startswith('|') or is_divider(s):
            continue

        cells = split_cells(s)
        if len(cells) < 2:
            continue
        spec_id = cells[1]
        if spec_id in PLACEHOLDERS or not ID_RE.fullmatch(spec_id):
            continue

        id_bundle[spec_id] = current_bundle
        bundle_ids.setdefault(current_bundle, set()).add(spec_id)

        if in_series_table and len(cells) >= 3:
            series = cells[2]
            if series and series != NO_SERIES:
                id_series[spec_id] = series
                series_ids.setdefault(series, set()).add(spec_id)

    return id_bundle, bundle_ids, id_series, series_ids


def parse_chains(text):
    """Extracts each Related IDs row of the SPEC 'Observable Behavior Chain' tables as one chain (ID set).

    Only tables whose header has a 'Related IDs' cell count as chain tables. That cell's IDs are
    one trigger's simultaneous outcomes (co-occurrence). The column is located by header cell
    position, preventing false positives on arbitrary tables.
    """
    chains = []
    chain_col = None  # index of the current table's 'Related IDs' cell (None = not a chain table)

    for line in text.splitlines():
        s = line.strip()
        if not s.startswith('|'):
            chain_col = None  # table ended
            continue
        if is_divider(s):
            continue
        cells = split_cells(s)
        # Header row: find the 'Related IDs' cell
        header_idx = next((i for i, c in enumerate(cells) if 'Related IDs' in c), None)
        if header_idx is not None:
            chain_col = header_idx
            continue
        if chain_col is None or chain_col >= len(cells):
            continue
        ids = set(ID_RE.findall(cells[chain_col]))
        if len(ids) >= 2:  # a chain needs 2+ IDs in one row to be 'bound together'
            chains.append(frozenset(ids))
    return chains


def query(changed_id, joblist_text, spec_text):
    """Computes the changed ID's impact scope (same-bundle, same-series, same-chain peers).

    Returns: dict, or None (changed ID not in any joblist bundle).
    """
    id_bundle, bundle_ids, id_series, series_ids = parse_joblist(joblist_text)
    chains = parse_chains(spec_text)

    if changed_id not in id_bundle:
        return None

    bundle = id_bundle[changed_id]
    bundle_peers = bundle_ids.get(bundle, set()) - {changed_id}

    series = id_series.get(changed_id)
    series_peers = (series_ids.get(series, set()) - {changed_id}) if series else set()

    chain_peers = set()
    matched_chains = 0
    for chain in chains:
        if changed_id in chain:
            matched_chains += 1
            chain_peers |= (set(chain) - {changed_id})

    union = bundle_peers | series_peers | chain_peers
    return {
        'bundle': bundle,
        'bundle_peers': sorted(bundle_peers),
        'series': series,
        'series_peers': sorted(series_peers),
        'matched_chains': matched_chains,
        'chain_peers': sorted(chain_peers),
        'union': sorted(union),
    }


def render(changed_id, result):
    """Renders the query result as deterministic human-readable output."""
    out = []
    out.append('=' * 60)
    out.append(f'  Impact scope — {changed_id} (IDs to re-examine together on change)')
    out.append('=' * 60)
    out.append(f'  Owning bundle: {result["bundle"]}')
    bp = result['bundle_peers']
    out.append(f'  · Same bundle ({len(bp)} IDs, physical dependency): {", ".join(bp) if bp else "none"}')
    series_label = result['series'] if result['series'] else 'none (—)'
    sp = result['series_peers']
    out.append(f'  · Same series [{series_label}] ({len(sp)} IDs, method consistency): {", ".join(sp) if sp else "none"}')
    cp = result['chain_peers']
    out.append(f'  · Same behavior chain ({len(cp)} IDs, {result["matched_chains"]} chain(s)): {", ".join(cp) if cp else "none"}')
    out.append('-' * 60)
    union = result['union']
    out.append(f'  ▶ Re-examination scope union, {len(union)} IDs: {", ".join(union) if union else "none"}')
    out.append('=' * 60)
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# Built-in tests (--selftest) — verify the parser and query rules on synthetic fixtures.
# ---------------------------------------------------------------------------

_FIX_JOBLIST = """# Job List — Fixture

## 0. Scaffolding (foundation layer — first)

| Done | SPEC ID | Notes / Hints |
|---|---|---|
| [x] | NFR-00-008 | serialization whitelist |
| [x] | FR-02-001 | central logger |

## Work Table (bundle units)

### Bundle 1: Notification plumbing

| Done | SPEC ID | Series | Notes / Hints |
|---|---|---|---|
| [x] | FR-01-001 | User guidance | reference implementation |
| [x] | FR-01-002 | User guidance | accompanies follow-up action |
| [x] | FR-01-E01 | — | duplicate suppression |

### Bundle 2: Storage

| Done | SPEC ID | Series | Notes / Hints |
|---|---|---|---|
| [x] | FR-04-001 | — | storage |
| [x] | FR-04-E01 | User guidance | follows FR-01-001 approach |
| [x] | FR-20-001 | Storage recovery | reference |

## Past Issues (reference)

| SPEC ID | Issue | Status |
|---|---|---|
| FR-99-001 | discarded | removed |
"""

_FIX_SPEC = """# SPEC — Fixture

## EP-06: Wins

**Observable Behavior Chain**

| Trigger (observable event) | Required simultaneous outcomes (observable) | Related IDs |
|---|---|---|
| Win after reels stop | tally, highlight, sound | FR-06-002, FR-07-002, FR-14-002 |

## EP-08: Celebration

**Observable Behavior Chain**

| Trigger (observable event) | Required simultaneous outcomes (observable) | Related IDs |
|---|---|---|
| Jackpot condition met | presentation, sound | FR-08-001, FR-07-002, FR-25-001 |
"""


def _selftest():
    cases = []

    def ok(name, cond):
        cases.append((name, bool(cond)))

    id_bundle, bundle_ids, id_series, series_ids = parse_joblist(_FIX_JOBLIST)

    # Bundle membership
    ok('collects scaffolding IDs', bundle_ids.get('Scaffolding') == {'NFR-00-008', 'FR-02-001'})
    ok('collects bundle 1 IDs', bundle_ids.get('Bundle 1: Notification plumbing') == {'FR-01-001', 'FR-01-002', 'FR-01-E01'})
    ok('id→bundle mapping', id_bundle.get('FR-04-E01') == 'Bundle 2: Storage')
    ok('excludes Past Issues IDs', 'FR-99-001' not in id_bundle)

    # Series membership
    ok('collects series (User guidance)', series_ids.get('User guidance') == {'FR-01-001', 'FR-01-002', 'FR-04-E01'})
    ok('series — is not a member', 'FR-01-E01' not in id_series and 'FR-04-001' not in id_series)
    ok('scaffolding has no series', 'NFR-00-008' not in id_series)

    # Behavior chains
    chains = parse_chains(_FIX_SPEC)
    ok('parses 2 chains', len(chains) == 2)
    ok('chain contents', frozenset({'FR-06-002', 'FR-07-002', 'FR-14-002'}) in chains)

    # Query — an ID hitting bundle + series + chain axes
    r1 = query('FR-01-001', _FIX_JOBLIST, _FIX_SPEC)
    ok('FR-01-001 bundle peers', r1['bundle_peers'] == ['FR-01-002', 'FR-01-E01'])
    ok('FR-01-001 series peers', r1['series_peers'] == ['FR-01-002', 'FR-04-E01'])
    ok('FR-01-001 no chains', r1['chain_peers'] == [])
    ok('FR-01-001 union', r1['union'] == ['FR-01-002', 'FR-01-E01', 'FR-04-E01'])

    # Query — an ID appearing in two chains (FR-07-002 appears in both)
    r2 = query('FR-07-002', _FIX_JOBLIST, _FIX_SPEC)
    # FR-07-002 is absent from the fixture joblist → None (impact not computable)
    ok('ID absent from joblist yields None', r2 is None)

    # Query — an ID whose series is — (no series peers), bundle peers only
    r3 = query('FR-04-001', _FIX_JOBLIST, _FIX_SPEC)
    ok('FR-04-001 no series peers', r3['series_peers'] == [] and r3['series'] is None)
    ok('FR-04-001 bundle peers', r3['bundle_peers'] == ['FR-04-E01', 'FR-20-001'])

    # Query — chain-hitting IDs (FR-06-002: no bundle → None? absent from joblist). Chain-only verification ends with parse.
    # Scaffolding ID query (no series, bundle=Scaffolding peers)
    r4 = query('FR-02-001', _FIX_JOBLIST, _FIX_SPEC)
    ok('scaffolding ID bundle peers', r4['bundle_peers'] == ['NFR-00-008'] and r4['series'] is None)

    passed = sum(1 for _, c in cases if c)
    total = len(cases)
    print('=' * 60)
    print(f'  query_impact built-in tests: {passed}/{total} passed')
    print('=' * 60)
    for name, c in cases:
        print(f'  {"✅" if c else "❌"} {name}')
    return passed == total


def main():
    if len(sys.argv) == 2 and sys.argv[1] == '--selftest':
        sys.exit(0 if _selftest() else 1)

    if len(sys.argv) != 4:
        print('Usage: python3 query_impact.py <SPEC ID to change> <joblist.md> <SPEC.md>', file=sys.stderr)
        print('       python3 query_impact.py --selftest', file=sys.stderr)
        sys.exit(2)

    changed_id, jl_path, spec_path = sys.argv[1], sys.argv[2], sys.argv[3]
    if not ID_RE.fullmatch(changed_id):
        print(f'Error: not an ID format: {changed_id} (e.g., FR-06-002, FR-14-E01)', file=sys.stderr)
        sys.exit(2)
    try:
        jl = open(jl_path, encoding='utf-8').read()
        spec = open(spec_path, encoding='utf-8').read()
    except OSError as e:
        print(f'Error: cannot open file: {e}', file=sys.stderr)
        sys.exit(2)

    result = query(changed_id, jl, spec)
    if result is None:
        print(f'❌ {changed_id} is not in any joblist bundle/scaffolding — impact scope cannot be computed.', file=sys.stderr)
        print('   (It may already be [Removed], or an ID not yet split.)', file=sys.stderr)
        sys.exit(1)

    print(render(changed_id, result))
    sys.exit(0)


if __name__ == '__main__':
    main()
