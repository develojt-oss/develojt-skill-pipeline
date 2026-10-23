#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# query_chain.py — operations-phase impact query (SPEC behavior chains only)
#
# The impact reverse-query tool used when adding/modifying/deleting requirements after
# development completes (operations). In the operations phase the PRD/joblist lifecycles
# are over, so only the SPEC is consulted (the develojt-code-changer delegation flow).
# It prints the peer IDs (simultaneous outcomes of one trigger) in every 'Observable
# Behavior Chain' containing the SPEC ID being changed — changing one link can break
# the chain, so this is the scope to re-examine together.
#
# The development phase (joblist-based bundle/series/behavior-chain, three axes) belongs
# to query_impact.py — separate from this tool. query_impact.py (development, joblist
# required) is left untouched (single-responsibility separation).
#
# Usage:
#   python3 query_chain.py <SPEC ID to change> <SPEC.md>
#   python3 query_chain.py --selftest          # run the built-in tests
#
# Exit codes: 0 — normal (with or without peers) / 2 — usage/file/ID-format error
#
import sys
import re

ID_RE = re.compile(r'(?:FR|NFR)-\d{2}-(?:\d{3}|E\d{2})')


def split_cells(row):
    """Splits one table row into a list of cells (strip outer |, then split)."""
    return [c.strip() for c in row.strip().strip('|').split('|')]


def is_divider(s):
    """Whether this is a table divider (|---| etc.)."""
    body = s.replace('|', '').strip()
    return body != '' and set(body) <= set('-: ')


def parse_chains(text):
    """Extracts each Related IDs row of the SPEC 'Observable Behavior Chain' tables as one chain (ID set).

    Only tables whose header has a 'Related IDs' cell count as chain tables. That cell's IDs are
    one trigger's simultaneous outcomes (co-occurrence). The column is located by header cell
    position, preventing false positives on arbitrary tables.
    (Same rule as the same-named function in query_impact.py — a self-contained copy, no module dependency.)
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


def query_chain(changed_id, spec_text):
    """Yields the sorted peer IDs of the behavior chains containing the changed ID, plus the matched chain count.

    No peers means an empty list — a standalone change not woven into any chain, which is normal (not an error).
    """
    chains = parse_chains(spec_text)
    chain_peers = set()
    matched = 0
    for chain in chains:
        if changed_id in chain:
            matched += 1
            chain_peers |= (set(chain) - {changed_id})
    return sorted(chain_peers), matched


def render(changed_id, peers, matched):
    """Renders the query result as deterministic human-readable output."""
    out = []
    out.append('=' * 60)
    out.append(f'  Impact scope (operations) — {changed_id} (IDs to re-examine together on change)')
    out.append('=' * 60)
    out.append('  Phase: operations (joblist lifecycle over — SPEC behavior chains only)')
    out.append(f'  · Same behavior chain ({len(peers)} IDs, {matched} chain(s)): {", ".join(peers) if peers else "none"}')
    out.append('  · Bundle/series: not produced (no joblist — series is checkable only when a deriver increment left notation in the SPEC)')
    out.append('=' * 60)
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# Built-in tests (--selftest) — verify chain parsing and querying on a synthetic fixture.
# ---------------------------------------------------------------------------

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

    chains = parse_chains(_FIX_SPEC)
    ok('parses 2 chains', len(chains) == 2)
    ok('chain contents', frozenset({'FR-06-002', 'FR-07-002', 'FR-14-002'}) in chains)

    # FR-07-002 — appears in both chains → peer union
    peers, matched = query_chain('FR-07-002', _FIX_SPEC)
    ok('matches both chains', matched == 2)
    ok('peer union (both chains)', set(peers) == {'FR-06-002', 'FR-14-002', 'FR-08-001', 'FR-25-001'})

    # FR-06-002 — one chain only
    peers2, matched2 = query_chain('FR-06-002', _FIX_SPEC)
    ok('matches one chain', matched2 == 1)
    ok('one-chain peers', set(peers2) == {'FR-07-002', 'FR-14-002'})

    # ID in no chain → empty result (not an error — a standalone change)
    peers3, matched3 = query_chain('FR-99-999', _FIX_SPEC)
    ok('empty result when not in any chain', peers3 == [] and matched3 == 0)

    passed = sum(1 for _, c in cases if c)
    total = len(cases)
    print('=' * 60)
    print(f'  query_chain built-in tests: {passed}/{total} passed')
    print('=' * 60)
    for name, c in cases:
        print(f'  {"✅" if c else "❌"} {name}')
    return passed == total


def main():
    if len(sys.argv) == 2 and sys.argv[1] == '--selftest':
        sys.exit(0 if _selftest() else 1)

    if len(sys.argv) != 3:
        print('Usage: python3 query_chain.py <SPEC ID to change> <SPEC.md>', file=sys.stderr)
        print('       python3 query_chain.py --selftest', file=sys.stderr)
        sys.exit(2)

    changed_id, spec_path = sys.argv[1], sys.argv[2]
    if not ID_RE.fullmatch(changed_id):
        print(f'Error: not an ID format: {changed_id} (e.g., FR-06-002, FR-14-E01)', file=sys.stderr)
        sys.exit(2)
    try:
        spec = open(spec_path, encoding='utf-8').read()
    except OSError as e:
        print(f'Error: cannot open file: {e}', file=sys.stderr)
        sys.exit(2)

    peers, matched = query_chain(changed_id, spec)
    print(render(changed_id, peers, matched))
    sys.exit(0)


if __name__ == '__main__':
    main()
