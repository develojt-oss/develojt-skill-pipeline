#!/usr/bin/env python3
r"""Structure-contract violation candidate detector (develojt-code-pdca C4 only) + structure metrics (--metrics).

A floor detector that reads spec/ARCHITECTURE.md (the structure contract) — its Layer map and
Dependency directions sections — as data, and scans only the two machine-checkable classes:
**the contract itself is the rules table** (no separate rules file — the structural counterpart
of enforced-rules' "recording is enforcement": only human-finalized contract sentences are checked).
  direction   cross-layer imports/references in a direction not in the Allowed table (file:line)
  unlisted    folders directly under src/ absent from the layer map (only those containing supported-language files)
This script's output is **candidates**, not defects — judgment (inside a comment/string? an exception
or coexistence the contract explicitly allows? a resolution error?) belongs to the checker via the C4
procedure in checker-rules.md. Therefore PASS (0 candidates) means "no candidates in the
machine-checkable classes", never "structure complied with".

Parsing rules (the contract grammar — builder templates/ARCHITECTURE-template.md):
  Layer map     the src/ path in the first cell of the table in the section headed 'Layer map' is a layer. Data rows without a
                path and {placeholder} rows are ⚠️ (not checked — contract-grammar maintenance material).
  Dependency    arrow chains (A → B → C) in the first (Allowed) cell of the table in the section headed
                'Dependency directions' register **adjacent pairs only**
  directions    (to allow a direct A→C reference, write that pair as its own row). Tokens are matched
                against layer paths or the path's last segment name; rows that fail matching or are
                not chains are ⚠️. Same-layer internal references are always allowed.
  ⚠️ rows are never candidates — they make visible the contract sentences that are not machine-checked
  (no silent burial).
  Header-row detection strips leading markdown decoration (backticks/bold) from the cell. A row
  enrolling the src root itself (src/) as one layer stays registered but gets a ⚠️ (visibility for
  a grammar that disables the sub-partition checks).
  Held verdicts: never judge by a contract that could not be read (missed-detection direction) —
  when 0 layers parse, unlisted candidates are not printed; when the direction section is absent or
  every direction data row fails to parse, direction candidates are not printed; both print a
  [CAUTION] tally instead (partial parses still check with the parsed rows only — an empty Allowed
  table is notified but still checked).

Import resolution is **existence-based** (the failure direction is missed detections — a candidate
detector never claims completeness; false positives would invite pass-shaped code mutations and
autonomy damage, so anything ambiguous is not detected):
  relative paths (./ ../), src/ absolutes, the @/ alias (→src/), and python dotted paths map to a
  layer only when the resolved file/directory actually exists; java/csharp dotted paths and cpp local
  #include only on a unique suffix match among the scanned files. Unresolvable references (external
  libraries, ambiguity) are outside the check.

Contract file resolution: a .md path argument wins; otherwise spec/ARCHITECTURE.md at the run
location. If neither exists, PASS (exit 0) as "C4 not applicable" — contract-less projects behave unchanged.

Grammar-check mode: passing only the contract .md with no scan targets prints the contract's parse
results (layers, allowed pairs, ⚠️) with no code checks — for verifying the notation right after the
contract is recorded (builder workflow 1 · architecture-lifecycle adoption/revision procedures).
⚠️ 0 → exit 0. In this mode a missing contract file is an error (no fake pass — exit 2).

--metrics: prints structure metrics only, with no judgment (collect-and-print only — isomorphic to
--inventory). Per-layer file counts, unlisted folders, cross-layer reference tallies, per-layer
fan-in/fan-out, largest subfolders. Observation material for drift (legal bloat/skew) — judgment
belongs to the human.

Supported languages: JavaScript, TypeScript, Vue, Python, C#, Java, C++ (java/csharp/cpp partial)
tests/ and __tests__/ are not checked (the contract governs product code — same as the other gates).

Usage:
    python3 scripts/verify_architecture.py src/                        # candidate detection (C4)
    python3 scripts/verify_architecture.py src/ path/to/contract.md    # explicit contract file
    python3 scripts/verify_architecture.py src/ --metrics              # structure metrics (no judgment)
    python3 scripts/verify_architecture.py src/ --all                  # ignore the candidate-rejection ledger — full recheck (on human instruction / checker calibration)
    python3 scripts/verify_architecture.py spec/ARCHITECTURE.md        # grammar-check mode (contract parsing only)

Exit codes: 0 — no candidates / not applicable / metrics (PASS) · 1 — candidates found (checker
on-site confirmation needed; in grammar-check mode: ⚠️ present) · 2 — usage/target error

Print cap: candidate detail lines are printed up to 16KB, and beyond that a `… N more … not printed` notice is printed (the
harness replaces tool output of roughly 30KB or more with a preview, so the tail would silently disappear). If the notice
appears, it is not exhaustive — narrow the target argument down to subfolders/files and re-run. Exit codes and count summaries
are based on the full set.

Candidate-rejection ledger: reads spec/findings-rejected.md at the run location (if present); candidates whose key matches
are not printed and are noted in the summary as `N excluded as matching the candidate-rejection ledger` (key = the printed
line minus `:line-number` — for unlisted-folder candidates, the folder line as-is).

"""

import os
import re

# ── Print cap: the harness replaces tool output of roughly 30KB or more with a 2KB preview + file, so the tail silently disappears.
#    Detail lines are printed only up to this cap, and the overflow count is left as a notice (preventing silent truncation — exit codes are based on the full set).
PRINT_MAX_BYTES = 16_000


def print_capped(lines: list[str], unit: str) -> None:
    """Print detail lines up to the cap; on overflow, print the remaining count and a re-run hint."""
    used = 0
    for i, line in enumerate(lines):
        size = len(line.encode('utf-8')) + 1
        if used + size > PRINT_MAX_BYTES:
            print(f'… {len(lines) - i} more{unit} not printed — print cap ({PRINT_MAX_BYTES // 1000}KB). '
                  f'Narrow the target argument down to subfolders/files and re-run to see the rest')
            return
        print(line)
        used += size


# ── Candidate-rejection ledger: spec/findings-rejected.md, where the Lead writes the keys (location/basis records) of candidates the checker rejected as "not a defect".
#    Candidates whose key matches are not printed (inheriting the recorded verdict). Without the file, same as before. Rows with a broken format are ignored (the re-judgment direction).
REJECTED_PATH = os.path.join('spec', 'findings-rejected.md')


def load_rejected(path: str = REJECTED_PATH) -> set[str]:
    """Collect the first cell (the key) of the candidate-rejection ledger's table. `\\|` inside a cell is turned back into `|`."""
    keys: set[str] = set()
    if not os.path.isfile(path):
        return keys
    with open(path, encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.strip()
            if not line.startswith('|'):
                continue
            cells = line.replace('\\|', '\x00').strip('|').split('|')
            key = cells[0].replace('\x00', '|').strip().strip('`').strip() if cells else ''
            if not key or key == 'Key' or set(key) <= set('-: '):
                continue
            keys.add(key)
    return keys
import sys
from collections import Counter

# Language → extension map (same set as verify_enforced_rules.py / verify_security.py)
LANG_EXTENSIONS = {
    'js':     ('.js', '.mjs', '.cjs', '.jsx'),
    'ts':     ('.ts', '.tsx'),
    'vue':    ('.vue',),
    'python': ('.py',),
    'csharp': ('.cs',),
    'java':   ('.java',),
    'cpp':    ('.cpp', '.cc', '.cxx', '.h', '.hpp'),
}
ALL_EXTENSIONS = tuple(ext for exts in LANG_EXTENSIONS.values() for ext in exts)

SKIP_DIRS = {'node_modules', 'dist', 'build', 'tests', '__tests__',
             '.git', '__pycache__', '.venv', 'venv', 'bin', 'obj'}

DEFAULT_CONTRACT_PATH = os.path.join('spec', 'ARCHITECTURE.md')
LAYER_SECTION_KEY = 'Layer map'
DIRECTION_SECTION_KEY = 'Dependency directions'
SRC_PATH_RE = re.compile(r'src(?:/[\w.\-]+)*/?')
ARROW_SPLIT_RE = re.compile(r'\s*(?:→|->)\s*')

# Per-language comment heads (skipped in the import scan — cpp keeps '#' so #include survives)
COMMENT_HEADS = {
    'js': ('//', '/*', '*'), 'ts': ('//', '/*', '*'), 'vue': ('//', '/*', '*'),
    'python': ('#',),
    'java': ('//', '/*', '*'), 'csharp': ('//', '/*', '*'),
    'cpp': ('//', '/*', '*'),
}

# Per-language import extraction — line-based. One capture = the module string
IMPORT_RES = {
    'js': [
        re.compile(r'''^\s*(?:import|export)\b[^;]*?\bfrom\s*['"]([^'"]+)['"]'''),
        re.compile(r'''^\s*import\s*['"]([^'"]+)['"]'''),
        re.compile(r'''\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)'''),
        re.compile(r'''\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)'''),
    ],
    'python': [
        re.compile(r'^\s*from\s+([.\w]+)\s+import\b'),
        re.compile(r'^\s*import\s+([.\w]+)'),
    ],
    'java': [re.compile(r'^\s*import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;')],
    'csharp': [re.compile(r'^\s*using\s+(?:static\s+)?([A-Za-z_][\w.]*)\s*;')],
    'cpp': [re.compile(r'^\s*#\s*include\s*"([^"]+)"')],
}
IMPORT_RES['ts'] = IMPORT_RES['js']
IMPORT_RES['vue'] = IMPORT_RES['js']

JS_RESOLVE_SUFFIXES = ('', '.js', '.mjs', '.jsx', '.ts', '.tsx', '.vue',
                       '/index.js', '/index.mjs', '/index.jsx',
                       '/index.ts', '/index.tsx', '/index.vue')
PY_RESOLVE_SUFFIXES = ('.py', '/__init__.py')


def lang_of(path: str) -> str | None:
    for lang, exts in LANG_EXTENSIONS.items():
        if path.endswith(exts):
            return lang
    return None


def collect_files(targets: list[str]) -> list[str]:
    """Collect supported-extension files from targets (isomorphic to verify_enforced_rules)."""
    files = []
    for target in targets:
        if os.path.isfile(target):
            files.append(os.path.normpath(target))
        elif os.path.isdir(target):
            for root, dirs, names in os.walk(target):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                files.extend(
                    os.path.normpath(os.path.join(root, n)) for n in sorted(names)
                    if n.endswith(ALL_EXTENSIONS))
        else:
            print(f"[ERROR] target does not exist: {target}", file=sys.stderr)
            sys.exit(2)
    return files


def read_lines(path: str) -> list[str]:
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read().splitlines()
    except OSError as e:
        print(f"[WARN] read failed: {path} ({e})", file=sys.stderr)
        return []


# ── Contract parsing (the contract is the rules table — only written sentences are checked) ──

def split_cells(line: str) -> list[str]:
    protected = line.strip().replace('\\|', '\x00')
    return [c.strip().replace('\x00', '|') for c in protected.strip('|').split('|')]


def section_table_rows(text: str, header_key: str) -> list[list[str]] | None:
    """Data rows (cell lists) of the `## ` section containing header_key. None if no section."""
    match = re.search(rf'^##[^\n]*{re.escape(header_key)}[^\n]*\n(.*?)(?=^## |\Z)',
                      text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    rows = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = split_cells(line)
        if not cells or all(re.fullmatch(r':?-+:?', c) for c in cells if c):
            continue  # separator row
        rows.append(cells)
    return rows


def norm_layer(path: str) -> str:
    return os.path.normpath(path.strip())


def strip_md_head(cell: str) -> str:
    """For header-row detection — strips leading markdown decoration (backticks/bold/italics) from the cell."""
    return cell.strip().lstrip('*_`').strip()


def parse_contract(text: str) -> tuple[list[str], set[tuple[str, str]], bool, int, int, list[str]]:
    """Parse the contract → (layers, allowed pairs, direction section present, layer data rows, direction data rows, ⚠️ list).

    Data-row counts exclude headers and include parse failures — used for the "rows exist but 0
    parsed" held verdict (missed-detection direction).
    """
    warnings: list[str] = []
    layers: list[str] = []
    layer_rows_n = 0

    layer_rows = section_table_rows(text, LAYER_SECTION_KEY)
    if layer_rows is None:
        warnings.append(f"the contract has no '{LAYER_SECTION_KEY}' section — 0 layers to check")
        layer_rows = []
    for cells in layer_rows:
        first = cells[0]
        if strip_md_head(first).startswith('Layer'):
            continue  # header row (fixed template grammar 'Layer (src/ path)' — decoration stripped before the check)
        layer_rows_n += 1
        if '{' in first:
            warnings.append(f"layer-map row '{first[:40]}' — template placeholder (fill it in; not checked)")
            continue
        m = SRC_PATH_RE.search(first)
        if not m:
            warnings.append(f"layer-map row '{first[:40]}' — no src/ path (not checked)")
            continue
        layer = norm_layer(m.group(0))
        if layer == 'src':
            warnings.append(f"layer-map row '{first[:40]}' — the src root itself as one layer (unlisted/direction checks disabled — possibly contract-grammar maintenance material)")
        if layer not in layers:
            layers.append(layer)

    # Token → layer matching: exact src/ path, or unique last-segment name
    name_map: dict[str, list[str]] = {}
    for layer in layers:
        name_map.setdefault(os.path.basename(layer) or layer, []).append(layer)

    def match_token(token: str) -> str | None:
        token = token.strip()
        m = SRC_PATH_RE.search(token)
        if m:
            cand = norm_layer(m.group(0))
            return cand if cand in layers else None
        word = re.sub(r'[^\w.\-]', '', token)
        hits = name_map.get(word, [])
        return hits[0] if len(hits) == 1 else None

    allowed: set[tuple[str, str]] = set()
    dir_rows_n = 0
    dir_rows = section_table_rows(text, DIRECTION_SECTION_KEY)
    has_direction_section = dir_rows is not None
    if dir_rows is None:
        warnings.append(f"the contract has no '{DIRECTION_SECTION_KEY}' section — 0 direction checks")
        dir_rows = []
    for cells in dir_rows:
        first = cells[0]
        if strip_md_head(first).startswith('Allowed'):
            continue  # header row (decoration stripped before the check)
        dir_rows_n += 1
        if '{' in first:
            warnings.append(f"dependency-directions row '{first[:40]}' — template placeholder (fill it in; not checked)")
            continue
        chain_src = re.sub(r'\([^)]*\)', '', first)  # strip parenthetical notes — "(one direction)" etc.
        tokens = [t for t in ARROW_SPLIT_RE.split(chain_src) if t.strip()]
        if len(tokens) < 2:
            warnings.append(f"dependency-directions row '{first[:40]}' — not an arrow chain (not checked)")
            continue
        matched = [match_token(t) for t in tokens]
        if any(m is None for m in matched):
            bad = [t.strip() for t, m in zip(tokens, matched) if m is None]
            warnings.append(f"dependency-directions row '{first[:40]}' — unmatched layer tokens {bad} (not checked)")
            continue
        for a, b in zip(matched, matched[1:]):
            allowed.add((a, b))
    return layers, allowed, has_direction_section, layer_rows_n, dir_rows_n, warnings


# ── Import resolution (existence-based — unresolvable means outside the check) ──────────────

def _exists_with(base: str, suffixes: tuple[str, ...]) -> str | None:
    for suf in suffixes:
        cand = base + suf
        if os.path.isfile(cand):
            return os.path.normpath(cand)
    if os.path.isdir(base):
        return os.path.normpath(base)
    return None


class Resolver:
    """Module string → an existing path under src/. None on failure (outside the check — missed-detection direction)."""

    def __init__(self, files: list[str]):
        self.files = files
        self.dirs = sorted({os.path.dirname(f) for f in files})

    def _suffix_unique(self, rel: str) -> str | None:
        """The scanned file/directory ending in rel (slash path), when exactly one exists."""
        hits = [f for f in self.files if f == rel or f.endswith(os.sep + rel)]
        if len(hits) == 1:
            return hits[0]
        if hits:
            return None  # multiple matches — ambiguous (outside the check)
        dhits = [d for d in self.dirs if d == rel or d.endswith(os.sep + rel)]
        return dhits[0] if len(dhits) == 1 else None

    def resolve(self, module: str, from_path: str, lang: str) -> str | None:
        from_dir = os.path.dirname(from_path)
        if lang in ('js', 'ts', 'vue'):
            if module.startswith(('./', '../')):
                return _exists_with(os.path.normpath(os.path.join(from_dir, module)),
                                    JS_RESOLVE_SUFFIXES)
            if module.startswith('@/'):
                return _exists_with(os.path.normpath(os.path.join('src', module[2:])),
                                    JS_RESOLVE_SUFFIXES)
            if module.startswith('src/'):
                return _exists_with(os.path.normpath(module), JS_RESOLVE_SUFFIXES)
            return None  # package aliases/external libraries — outside the check
        if lang == 'python':
            if module.startswith('.'):
                dots = len(module) - len(module.lstrip('.'))
                rest = module.lstrip('.')
                base = from_dir
                for _ in range(dots - 1):
                    base = os.path.dirname(base)
                target = os.path.join(base, rest.replace('.', os.sep)) if rest else base
                return _exists_with(os.path.normpath(target), PY_RESOLVE_SUFFIXES)
            direct = _exists_with(os.path.normpath(os.path.join('src', module.replace('.', os.sep))),
                                  PY_RESOLVE_SUFFIXES)
            if direct:
                return direct
            return self._suffix_unique(module.replace('.', os.sep) + '.py') \
                or self._suffix_unique(module.replace('.', os.sep))
        if lang in ('java', 'csharp'):
            rel = module[:-2] if module.endswith('.*') else module
            rel = rel.replace('.', os.sep)
            ext = '.java' if lang == 'java' else '.cs'
            return self._suffix_unique(rel + ext) or self._suffix_unique(rel)
        if lang == 'cpp':
            local = _exists_with(os.path.normpath(os.path.join(from_dir, module)), ('',))
            if local:
                return local
            root = _exists_with(os.path.normpath(os.path.join('src', module)), ('',))
            if root:
                return root
            return self._suffix_unique(os.path.normpath(module))
        return None


def layer_of(path: str, layers: list[str]) -> str | None:
    """The path's layer — longest prefix match (path-boundary aware)."""
    best = None
    for layer in layers:
        if path == layer or path.startswith(layer + os.sep):
            if best is None or len(layer) > len(best):
                best = layer
    return best


def iter_imports(path: str, lines: list[str]):
    """(line number, module string, source line) — lines starting with a comment head are skipped."""
    lang = lang_of(path)
    if lang is None:
        return
    heads = COMMENT_HEADS[lang]
    for no, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(heads):
            continue
        for rx in IMPORT_RES[lang]:
            for m in rx.finditer(line):
                yield no, m.group(1), stripped
                break  # first match per regex — no duplicate hits on one line


# ── Check 1·2: direction violations · unlisted top-level folders ────────────────────────────

def scan_direction(files: list[str], layers: list[str],
                   allowed: set[tuple[str, str]]) -> tuple[list[tuple], Counter]:
    """Direction-violation candidates + (for metrics) cross-layer reference tallies."""
    resolver = Resolver(files)
    candidates = []
    cross_refs: Counter = Counter()
    for path in files:
        from_layer = layer_of(path, layers)
        if from_layer is None:
            continue
        lang = lang_of(path)
        for no, module, line in iter_imports(path, read_lines(path)):
            target = resolver.resolve(module, path, lang)
            if target is None:
                continue
            to_layer = layer_of(target, layers)
            if to_layer is None or to_layer == from_layer:
                continue
            cross_refs[(from_layer, to_layer)] += 1
            if (from_layer, to_layer) not in allowed:
                candidates.append((path, no,
                                   f'direction violation candidate: {from_layer} → {to_layer} '
                                   f'(not in the Allowed table) — {line[:100]}'))
    return candidates, cross_refs


def top_dirs_with_code(src_roots: list[str], files: list[str]) -> dict[str, int]:
    """Directories directly under the src roots → supported-language file counts (0-file folders excluded)."""
    counts: dict[str, int] = {}
    for root in src_roots:
        root = os.path.normpath(root)
        for f in files:
            if not f.startswith(root + os.sep):
                continue
            rel = f[len(root) + 1:]
            if os.sep not in rel:
                continue  # file directly under the root — not a folder
            top = os.path.join(root, rel.split(os.sep)[0])
            counts[top] = counts.get(top, 0) + 1
    return counts


def scan_unlisted(src_roots: list[str], files: list[str],
                  layers: list[str]) -> list[tuple]:
    """Code-bearing top-level folders absent from the layer map (no ancestor/descendant relation to any layer)."""
    candidates = []
    for top, n in sorted(top_dirs_with_code(src_roots, files).items()):
        covered = any(top == L or top.startswith(L + os.sep) or L.startswith(top + os.sep)
                      for L in layers)
        if not covered:
            candidates.append((top, 0,
                               f'unlisted folder candidate: no place in the layer map ({n} supported-language files)'))
    return candidates


# ── --metrics: structure metrics (collect-and-print only — no judgment) ─────────────────────

def print_metrics(src_roots: list[str], files: list[str], layers: list[str],
                  cross_refs: Counter) -> None:
    print('## Structure metrics (collect-and-print only — no judgment, no gate. Drift observation material — judgment belongs to the human)')
    by_layer: Counter = Counter()
    outside = 0
    for f in files:
        L = layer_of(f, layers)
        if L:
            by_layer[L] += 1
        else:
            outside += 1
    print('\n[Files per layer]')
    for L in layers:
        print(f'  {L}: {by_layer.get(L, 0)}')
    if outside:
        print(f'  (outside all layers): {outside}')
    unlisted = scan_unlisted(src_roots, files, layers)
    if unlisted:
        print('\n[Unlisted top-level folders]')
        for top, _no, msg in unlisted:
            print(f'  {top} — {msg.split("(")[-1].rstrip(")")}')
    if cross_refs:
        print('\n[Cross-layer reference tallies (resolved only)]')
        for (a, b), n in sorted(cross_refs.items()):
            print(f'  {a} → {b}: {n}')
        fan_out: Counter = Counter()
        fan_in: Counter = Counter()
        for (a, b) in cross_refs:
            fan_out[a] += 1
            fan_in[b] += 1
        print('\n[Per-layer fan-out/fan-in (distinct layers referenced/referencing)]')
        for L in layers:
            print(f'  {L}: out {fan_out.get(L, 0)} / in {fan_in.get(L, 0)}')
    print('\n[Immediate subfolders per layer by file count, top 5 — bloat observation]')
    for L in layers:
        sub: Counter = Counter()
        for f in files:
            if f.startswith(L + os.sep):
                rel = f[len(L) + 1:]
                if os.sep in rel:
                    sub[rel.split(os.sep)[0]] += 1
        if sub:
            top5 = ' · '.join(f'{d}({n})' for d, n in sub.most_common(5))
            print(f'  {L}: {top5}')
    print(f'\n— {len(files)} files · {len(layers)} layers. Metrics are not verdicts — interpreting bloat/skew and proposing revisions belong to the human.')


def main() -> None:
    args = sys.argv[1:]
    metrics = '--metrics' in args
    show_all = '--all' in args
    args = [a for a in args if a not in ('--metrics', '--all')]
    contract_path = None
    targets = []
    for a in args:
        if a.endswith('.md'):
            contract_path = a
        else:
            targets.append(a)
    if not targets and (contract_path is None or metrics):
        print('usage: python3 verify_architecture.py <src directory or files...> '
              '[ARCHITECTURE.md] [--metrics] [--all]\n'
              '       python3 verify_architecture.py <ARCHITECTURE.md>            '
              '# grammar-check mode (contract parsing only — post-recording notation check)', file=sys.stderr)
        sys.exit(2)

    if contract_path is None:
        contract_path = DEFAULT_CONTRACT_PATH
    if not os.path.isfile(contract_path):
        if not targets:  # grammar-check mode — a missing contract to verify is an error (no fake pass)
            print(f'[ERROR] contract file not found: {contract_path}', file=sys.stderr)
            sys.exit(2)
        print(f'ℹ️  no structure contract ({contract_path}) — C4 not applicable (0 checks)')
        sys.exit(0)

    with open(contract_path, encoding='utf-8') as f:
        layers, allowed, has_direction_section, layer_rows_n, dir_rows_n, warnings = parse_contract(f.read())

    if not targets:
        # Grammar-check mode — only whether the machine can read the contract's notation (no code
        # checks; the builder runs this once right after recording the contract to confirm ⚠️ 0 —
        # this verifies notation, not content).
        for w in warnings:
            print(f'⚠️  {w}')
        tail = ' — ⚠️ rows are not machine-checked (contract-grammar maintenance material)' if warnings else ''
        print(f'Grammar check — {len(layers)} layers · {len(allowed)} allowed direction pairs · {len(warnings)} ⚠️{tail}')
        sys.exit(1 if warnings else 0)

    files = collect_files(targets)
    files = [f for f in files if lang_of(f)]
    src_roots = [t for t in targets if os.path.isdir(t)]

    dir_candidates, cross_refs = scan_direction(files, layers, allowed)

    if metrics:
        print_metrics(src_roots, files, layers, cross_refs)
        sys.exit(0)

    # Held verdicts — never judge by a contract that could not be read (missed-detection direction).
    # Partial parses still check with the parsed rows only.
    notices: list[str] = []
    unlisted_cands = scan_unlisted(src_roots, files, layers)
    if not layers:
        notices.append(f'unlisted check held — 0 layers parsed ({layer_rows_n} layer-map data rows · see ⚠️ for causes — '
                       f'contract-grammar maintenance material). {len(unlisted_cands)} code-bearing top-level folders not printed as candidates.')
        unlisted_cands = []
    else:
        if not has_direction_section:
            notices.append(f'direction check held — the contract has no dependency-directions section. '
                           f'{len(dir_candidates)} cross-layer references not printed as candidates.')
            dir_candidates = []
        elif not allowed and dir_rows_n > 0:
            notices.append(f'direction check held — 0 of {dir_rows_n} dependency-directions data rows parsed (all ⚠️ — '
                           f'contract-grammar maintenance material). {len(dir_candidates)} cross-layer references not printed as candidates.')
            dir_candidates = []
        elif not allowed:
            notices.append('0 allowed direction pairs — the dependency-directions table is empty, so every cross-layer '
                           'reference becomes a candidate (contract-grammar maintenance material unless total prohibition is intended).')

    candidates = dir_candidates + unlisted_cands
    rejected = set() if show_all else load_rejected()
    excluded = sum(1 for path, _no, msg in candidates if f'{path} [C4] {msg}' in rejected)  # key = the printed line minus :line-number
    candidates = [c for c in candidates if f'{c[0]} [C4] {c[2]}' not in rejected]
    rej_note = f' · {excluded} excluded as matching the candidate-rejection ledger (--all for everything)' if excluded else ''
    candidates.sort(key=lambda c: (c[0], c[1]))
    print_capped([f"{(f'{path}:{no}' if no else path)} [C4] {msg}" for path, no, msg in candidates], ' candidate(s)')

    for w in warnings:
        print(f'⚠️  {w}')
    for n in notices:  # held/empty-table notices — the expanded replacement of the old [CAUTION] guards (0 layers · 0 allowed pairs) (printed on both PASS and FAIL paths)
        print(f'[CAUTION] {n}')

    if not candidates:
        print(f'✅ PASS — no structure-contract violation candidates ({len(files)} files examined · '
              f'{len(layers)} layers · {len(allowed)} allowed direction pairs{rej_note})')
        if len(files) == 0:
            print('[CAUTION] 0 files examined — no supported-language files, so this PASS may be meaningless.')
        sys.exit(0)

    print(f'\n{len(candidates)} candidates ({len(files)} files examined · {len(layers)} layers · '
          f'{len(allowed)} allowed direction pairs{rej_note}) — each candidate is a confirmation target, not a defect.')
    print('The checker confirms each on-site and judges via the C4 procedure in checker-rules.md.')
    sys.exit(1)


if __name__ == '__main__':
    main()
